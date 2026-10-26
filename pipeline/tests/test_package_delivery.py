"""Existing signed Acadia fixture only; no keys, analysis, decoding or app writes."""
import json
import shutil

import pytest

from pipeline import PipelineError
from pipeline import package_delivery as delivery
from pipeline.hashing import fingerprint, sha256_file
from pipeline.packaged_library import catalog_module
from pipeline.tests.test_local_intake import ACADIA, BUNDLE, REPO, signed_package, store

# Share the existing signed fixture and the inert intake store; never mint a signer.
__all__ = ["signed_package", "store"]


def rewrite(package, change):
    value = json.loads((package / "catalog.json").read_text())
    old = value.pop("bundleId")
    change(value)
    value["bundleId"] = fingerprint(value)
    (package / old).rename(package / value["bundleId"])
    raw = json.dumps(value, indent=2, sort_keys=True) + "\n"
    (package / value["bundleId"] / "manifest.json").write_text(raw)
    (package / "catalog.json").write_text(raw)
    (package / "catalog.ts").write_text(catalog_module(raw))


def test_exact_approved_fixture_and_repeat_are_read_only(signed_package, tmp_path):
    before = {str(p): sha256_file(p) for p in signed_package.rglob("*") if p.is_file()}
    root = tmp_path / "reviews"
    first = delivery.stage_delivery(signed_package, ACADIA, root)
    assert first["state"] == "approved_for_build"
    assert first["approval_label"] == "Acadia: approved ocean replacement"
    assert not first["can_watch"] and not first["installed_by_staging"]
    second = delivery.stage_delivery(signed_package, ACADIA, root)
    assert first == second == delivery.check_delivery(root, first["ticket_id"])
    assert len(list(root.glob("*.json"))) == 1
    assert before == {str(p): sha256_file(p) for p in signed_package.rglob("*") if p.is_file()}


def test_new_catalog_under_same_signer_is_not_approved(signed_package, tmp_path):
    rewrite(signed_package, lambda value: value["titles"][0].update(title="Changed metadata fixture"))
    result = delivery.stage_delivery(signed_package, ACADIA, tmp_path / "reviews")
    assert result["state"] == "ready_for_approval" and result["approval_required"]
    assert result["blockers"] == ["Exact bundle and catalog membership are not approved."]
    assert not result["can_watch"]


def test_no_approval_even_when_signatures_validate_under_unregistered_key(signed_package, monkeypatch):
    monkeypatch.setattr(delivery, "approvals", lambda: [])
    result = delivery.inspect_delivery(signed_package, ACADIA)
    assert result["state"] == "ready_for_approval" and not result["can_watch"]
    assert "signer" in result["blockers"][1]


def test_wrong_signer_rehashed_manifest_fails_signature(signed_package):
    other = json.loads((REPO / "app/assets/raw/prepared-library/catalog.json").read_text())["publicKeyBase64"]
    rewrite(signed_package, lambda value: value.update(publicKeyBase64=other))
    with pytest.raises(PipelineError):
        delivery.inspect_delivery(signed_package, ACADIA)


@pytest.mark.parametrize("mutation", ["media", "catalog", "report", "source", "symlink"])
def test_tampering_or_wrong_identity_cannot_stage(signed_package, tmp_path, mutation):
    expected = ACADIA
    if mutation == "media":
        next(signed_package.rglob("extra-cautious.mp4")).write_bytes(b"tampered")
    elif mutation == "catalog":
        with (signed_package / "catalog.json").open("a") as f:
            f.write(" ")
    elif mutation == "report":
        next((signed_package / "reports").iterdir()).unlink()
    elif mutation == "source":
        expected = "f" * 64
    else:
        target = next(signed_package.rglob("extra-cautious.mp4"))
        copy = tmp_path / "outside.mp4"
        target.rename(copy)
        target.symlink_to(copy)
    root = tmp_path / "reviews"
    with pytest.raises((PipelineError, ValueError)):
        delivery.stage_delivery(signed_package, expected, root)
    assert list(root.glob("*.json")) == []


def test_valid_replacement_revokes_previous_review(signed_package, tmp_path):
    root = tmp_path / "reviews"
    original = delivery.stage_delivery(signed_package, ACADIA, root)
    rewrite(signed_package, lambda value: value["titles"][0].update(title="Replaced metadata fixture"))
    with pytest.raises(delivery.DeliveryError, match="changed"):
        delivery.check_delivery(root, original["ticket_id"])
    with pytest.raises(delivery.DeliveryError, match="replaced"):
        delivery.stage_delivery(signed_package, ACADIA, root)
    delivery.cancel_delivery(root, original["ticket_id"])
    replacement = delivery.stage_delivery(signed_package, ACADIA, root)
    assert replacement["ticket_id"] != original["ticket_id"]
    assert replacement["state"] == "ready_for_approval"


def test_cancel_blocks_old_ticket_and_keeps_export(signed_package, tmp_path):
    root = tmp_path / "reviews"
    ticket = delivery.stage_delivery(signed_package, ACADIA, root)["ticket_id"]
    assert delivery.cancel_delivery(root, ticket)["state"] == "canceled"
    assert delivery.cancel_delivery(root, ticket)["state"] == "canceled"
    with pytest.raises(delivery.DeliveryError, match="canceled"):
        delivery.check_delivery(root, ticket)
    assert (signed_package / BUNDLE).is_dir()
    assert delivery.stage_delivery(signed_package, ACADIA, root)["ticket_id"] != ticket


def test_staging_must_not_write_into_package_or_app(signed_package, monkeypatch):
    with pytest.raises(delivery.DeliveryError, match="separate"):
        delivery.stage_delivery(signed_package, ACADIA, signed_package)
    monkeypatch.setattr(delivery, "APP", signed_package)
    with pytest.raises(delivery.DeliveryError, match="outside app"):
        delivery.stage_delivery(signed_package, ACADIA, signed_package / "reviews")


def test_intake_stage_recheck_failure_clears_snapshot_and_cancel_revokes_ticket(store, signed_package):
    from pipeline import local_intake as intake
    from pipeline.hashing import fingerprint

    from .test_local_intake import ready

    path, job = ready(store)
    review = {**job["review"], "source_sha256": ACADIA}
    package = path / "runs" / "fixture" / "package"
    shutil.copytree(signed_package, package)
    snapshot = {**intake.inspect_package(package, ACADIA), "relative_directory": "runs/fixture/package"}
    intake.update(path, status="package_review", source_sha256=ACADIA,
                  review=review, review_digest=fingerprint(review),
                  package=snapshot)
    staged = store.action(job["id"], "stage-delivery")["delivery"]
    store.action(job["id"], "cancel")
    with pytest.raises(delivery.DeliveryError, match="canceled"):
        delivery.check_delivery(path / "delivery-reviews", staged["ticket_id"])
    intake.update(path, status="package_review", review=review, review_digest=fingerprint(review),
                  package=snapshot)
    store.action(job["id"], "stage-delivery")
    next(package.rglob("extra-cautious.mp4")).write_bytes(b"changed")
    with pytest.raises(PipelineError):
        store.action(job["id"], "check-delivery")
    assert intake.read_job(path)["delivery"]["state"] == "blocked"
    assert intake.read_job(path)["delivery"]["can_watch"] is False
    # A failed validation does not strand the cancellation handle.
    assert store.action(job["id"], "cancel-delivery")["delivery"]["state"] == "canceled"
