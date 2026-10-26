"""Real existing signed fixture and temporary app copies; no signer or TV writes."""
import json
import shutil
import subprocess

import pytest

from pipeline import PipelineError
from pipeline import edition_delivery as edition
from pipeline import package_delivery as review
from pipeline.hashing import sha256_file
from pipeline.tests.test_local_intake import ACADIA, BUNDLE, REPO, signed_package
from pipeline.tests.test_package_delivery import rewrite

__all__ = ["signed_package"]


@pytest.fixture
def app(tmp_path, signed_package):
    target = tmp_path / "checkout" / "app"
    source = REPO / "app"
    # Keep the delivery/rollback controls reachable after privacy enforcement.
    # The production library intentionally contains historical private reports.
    # Use its already portable signed Acadia bytes, plus a clearly synthetic
    # metadata-only baseline catalog. No map, report or signature is rewritten.
    assets = target / edition.ASSETS
    shutil.copytree(signed_package, assets)
    rewrite(assets, lambda value: value["titles"][0].update(title="Synthetic regression catalog"))
    shutil.copytree(signed_package / BUNDLE, assets / BUNDLE)
    for relative in (edition.REGISTRY, edition.GENERATED, *edition.TOOLS):
        (target / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target / relative)
    registry = json.loads((target / edition.REGISTRY).read_text())
    registry["catalogs"] = [entry for entry in registry["catalogs"] if entry["bundleId"] == BUNDLE]
    (target / edition.REGISTRY).write_text(json.dumps(registry))
    subprocess.run(["node", str(target / "tools/approved_prepared_libraries.mjs"), "--write"],
                   check=True, capture_output=True)
    return target


def stage(package, tmp_path):
    root = tmp_path / "reviews"
    ticket = review.stage_delivery(package, ACADIA, root)["ticket_id"]
    return root, ticket


def snapshot(directory):
    return {str(path.relative_to(directory)): sha256_file(path)
            for path in directory.rglob("*") if path.is_file()}


def remove_fixture(app):
    shutil.rmtree(app / edition.ASSETS / BUNDLE)


def test_existing_exact_fixture_is_idempotent(app, signed_package, tmp_path):
    root, ticket = stage(signed_package, tmp_path)
    before = snapshot(app)
    assert edition.plan_delivery(root, ticket, app)["files_to_add"] == []
    result = edition.apply_delivery(root, ticket, app)
    assert result["state"] == "applied_for_build"
    assert not result["can_watch"] and not result["installed"] and not result["approval_modified"]
    assert not result["generated_changed"]
    assert snapshot(app) == before
    assert edition.apply_delivery(root, ticket, app) == result


def test_retained_historical_private_report_blocks_delivery_without_rewriting_it(app, signed_package, tmp_path):
    source = REPO / "app" / edition.ASSETS
    legacy = json.loads((source / "catalog.json").read_text())
    digest = legacy["titles"][0]["verification"]["reportSha256"]
    shutil.copytree(source / legacy["bundleId"], app / edition.ASSETS / legacy["bundleId"])
    shutil.copyfile(source / "reports" / f"{digest}.json", app / edition.ASSETS / "reports" / f"{digest}.json")
    root, ticket = stage(signed_package, tmp_path)
    before = snapshot(app)
    with pytest.raises(PipelineError, match="local filesystem path"):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before


def test_missing_bundle_is_copied_without_replacing_regression_catalog(app, signed_package, tmp_path):
    root, ticket = stage(signed_package, tmp_path)
    complete = snapshot(app)
    remove_fixture(app)
    before = snapshot(app)
    plan = edition.plan_delivery(root, ticket, app)
    assert plan["files_to_add"]
    assert all(name.startswith(BUNDLE + "/") for name in plan["files_to_add"])
    edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == complete
    assert all(snapshot(app)[name] == value for name, value in before.items())
    assert edition.plan_delivery(root, ticket, app)["files_to_add"] == []


def test_target_checkout_approval_is_required(app, signed_package, tmp_path):
    root, ticket = stage(signed_package, tmp_path)
    (app / edition.REGISTRY).write_text('{"version":1,"catalogs":[]}')
    before = snapshot(app)
    result = edition.plan_delivery(root, ticket, app)
    assert result["state"] == "blocked"
    assert set(result["approval_request"]) == {"bundleId", "catalogSha256", "publicKeyFingerprint"}
    with pytest.raises(PipelineError, match="approval"):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before


def test_new_catalog_under_known_signer_does_not_inherit_approval(app, signed_package, tmp_path):
    rewrite(signed_package, lambda value: value["titles"][0].update(title="Metadata-only test fixture"))
    root, ticket = stage(signed_package, tmp_path)
    assert edition.plan_delivery(root, ticket, app)["state"] == "blocked"
    with pytest.raises(PipelineError, match="approval"):
        edition.apply_delivery(root, ticket, app)


@pytest.mark.parametrize("mutation", ["canceled", "media", "valid replacement"])
def test_review_is_rechecked_at_action_time(app, signed_package, tmp_path, mutation):
    root, ticket = stage(signed_package, tmp_path)
    edition.plan_delivery(root, ticket, app)
    if mutation == "canceled":
        review.cancel_delivery(root, ticket)
    elif mutation == "media":
        next(signed_package.rglob("extra-cautious.mp4")).write_bytes(b"changed")
    else:
        rewrite(signed_package, lambda value: value["titles"][0].update(title="Replaced test fixture"))
    before = snapshot(app)
    with pytest.raises(PipelineError):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before


@pytest.mark.parametrize("mutation", ["conflict", "symlink", "hardlink", "parent symlink"])
def test_unsafe_destination_is_refused(app, signed_package, tmp_path, mutation):
    root, ticket = stage(signed_package, tmp_path)
    destination = next((app / edition.ASSETS / BUNDLE).rglob("extra-cautious.mp4"))
    if mutation == "conflict":
        destination.write_bytes(b"conflict")
    elif mutation in ("symlink", "hardlink"):
        outside = tmp_path / "outside"
        destination.rename(outside)
        if mutation == "symlink":
            destination.symlink_to(outside)
        else:
            destination.hardlink_to(outside)
    else:
        directory = app / edition.ASSETS / BUNDLE
        outside = tmp_path / "outside"
        directory.rename(outside)
        directory.symlink_to(outside, target_is_directory=True)
    with pytest.raises(PipelineError):
        edition.apply_delivery(root, ticket, app)


def test_mirror_check_failure_leaves_target_unchanged(app, signed_package, tmp_path, monkeypatch):
    root, ticket = stage(signed_package, tmp_path)
    remove_fixture(app)
    before = snapshot(app)

    def refuse(*_, **__):
        raise review.DeliveryError("Simulated strict check refusal")

    monkeypatch.setattr(edition, "_run_checks", refuse)
    with pytest.raises(PipelineError, match="strict check"):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before


def test_final_check_failure_rolls_back_only_own_changes(app, signed_package, tmp_path, monkeypatch):
    root, ticket = stage(signed_package, tmp_path)
    remove_fixture(app)
    before = snapshot(app)
    run = edition._run_checks

    def refuse_target(target, **kwargs):
        if target == app:
            (app / "unrelated-owner-note.txt").write_text("Concurrent owner's text")
            raise review.DeliveryError("Simulated target check refusal")
        run(target, **kwargs)

    monkeypatch.setattr(edition, "_run_checks", refuse_target)
    with pytest.raises(PipelineError, match="target check"):
        edition.apply_delivery(root, ticket, app)
    after = snapshot(app)
    assert after.pop("unrelated-owner-note.txt")
    assert after == before
    assert not (app / edition.ASSETS / BUNDLE).exists()


def test_partial_copy_failure_removes_partial_file(app, signed_package, tmp_path, monkeypatch):
    root, ticket = stage(signed_package, tmp_path)
    remove_fixture(app)
    before = snapshot(app)

    def fail_copy(source, destination):
        destination.write(source.read(10))
        raise OSError("simulated full disk")

    monkeypatch.setattr(shutil, "copyfileobj", fail_copy)
    with pytest.raises(OSError, match="full disk"):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before


def test_approval_changed_during_preflight_is_not_applied(app, signed_package, tmp_path, monkeypatch):
    root, ticket = stage(signed_package, tmp_path)
    remove_fixture(app)
    run = edition._run_checks

    def mutate_registry(target, **kwargs):
        run(target, **kwargs)
        (app / edition.REGISTRY).write_text(json.dumps({"version": 1, "catalogs": []}))

    monkeypatch.setattr(edition, "_run_checks", mutate_registry)
    with pytest.raises(PipelineError, match="changed"):
        edition.apply_delivery(root, ticket, app)
    assert not (app / edition.ASSETS / BUNDLE).exists()
    assert json.loads((app / edition.REGISTRY).read_text())["catalogs"] == []


def namespace_bytes(directory):
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())


def test_budget_overflow_is_refused_before_anything_is_written(app, signed_package, tmp_path):
    """A delivery that would take the library past its budget never touches the checkout.

    Retained valid metadata generations fill the isolated checkout. The next
    delivery must be refused before any real file or compiled catalog is written.
    """
    checker = (REPO / "app" / edition.TOOLS[1]).read_text()
    assert "const MAX_BYTES = 128 * 1024 * 1024;" in checker
    rewrite(signed_package, lambda value: value["titles"][0].update(title="Metadata-only test fixture"))
    root, ticket = stage(signed_package, tmp_path)
    requested = review.check_delivery(root, ticket)["approval_request"]
    added = namespace_bytes(signed_package / requested["bundleId"])
    generation = 0
    while namespace_bytes(app / edition.ASSETS) + added <= 128 * 1024 * 1024:
        generation += 1
        retained = tmp_path / f"retained-{generation}"
        shutil.copytree(signed_package, retained)
        rewrite(retained, lambda value, number=generation: value["titles"][0].update(title=f"Retained fixture {number}"))
        bundle = json.loads((retained / "catalog.json").read_text())["bundleId"]
        shutil.copytree(retained / bundle, app / edition.ASSETS / bundle)
    approval = dict(requested, consumer=True, label="Metadata fixture",
                    approvalReference="Unit test only; no real approval")
    (app / edition.REGISTRY).write_text(json.dumps({"version": 1, "catalogs": [approval]}))
    before = snapshot(app)
    with pytest.raises(PipelineError, match="exceeds its package budget"):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before
    assert not (app / edition.ASSETS / requested["bundleId"]).exists()


def test_changed_generated_module_is_restored_on_final_failure(app, signed_package, tmp_path, monkeypatch):
    rewrite(signed_package, lambda value: value["titles"][0].update(title="Metadata-only test fixture"))
    root, ticket = stage(signed_package, tmp_path)
    # Room for the edition, as the other rollback tests make it: the metadata-only
    # copy replaces the Acadia bundle instead of sitting beside it. Until Oct 19
    # this test kept both, the proposed checkout went over budget, and the
    # rollback it exists to check was never reached (the budget case is above).
    remove_fixture(app)
    requested = review.check_delivery(root, ticket)["approval_request"]
    # Test-only approval in the isolated temporary app. No production registry changes.
    approval = dict(requested, consumer=True, label="Metadata fixture",
                    approvalReference="Unit test only; no real approval")
    (app / edition.REGISTRY).write_text(json.dumps({"version": 1, "catalogs": [approval]}))
    before = snapshot(app)
    run = edition._run_checks

    def refuse_target(target, **kwargs):
        if target == app:
            assert sha256_file(app / edition.GENERATED) != before[str(edition.GENERATED)]
            raise review.DeliveryError("Simulated target refusal after generator")
        run(target, **kwargs)

    monkeypatch.setattr(edition, "_run_checks", refuse_target)
    with pytest.raises(PipelineError, match="generator"):
        edition.apply_delivery(root, ticket, app)
    assert snapshot(app) == before


def test_incompatible_tools_are_not_executed(app, signed_package, tmp_path):
    root, ticket = stage(signed_package, tmp_path)
    (app / edition.TOOLS[0]).write_text("throw new Error('do not run');")
    with pytest.raises(PipelineError, match="incompatible"):
        edition.apply_delivery(root, ticket, app)


def test_exit_zero_without_checker_receipt_is_not_success(app, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *_, **__: subprocess.CompletedProcess([], 0, b"", b""))
    with pytest.raises(PipelineError, match="structured receipt"):
        edition._run_checks(app, generate=True, node="node")


def test_overlap_refused(app, signed_package, tmp_path):
    root = app / "reviews"
    ticket = review.stage_delivery(signed_package, ACADIA, root)["ticket_id"]
    with pytest.raises(PipelineError, match="separate"):
        edition.plan_delivery(root, ticket, app)


def test_cli_plan_failure_is_machine_readable(app, signed_package, tmp_path, capsys):
    root, ticket = stage(signed_package, tmp_path)
    (app / edition.REGISTRY).write_text('{"version":1,"catalogs":[]}')
    assert edition.main(["plan", "--staging-root", str(root), "--ticket", ticket, "--app", str(app)]) == 1
    assert json.loads(capsys.readouterr().out)["state"] == "blocked"
