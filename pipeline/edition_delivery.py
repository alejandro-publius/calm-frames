"""Plan/apply an already exact-approved edition to an operator-selected app checkout.

This copies verified immutable assets, never approves a signer/catalog, replaces the
regression catalog, builds, installs, or grants playback. Use a quiescent isolated
checkout; a directory lock serializes this command's writers. Validation happens in
a temporary mirror before the target changes, followed by a strict target check.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from . import PipelineError
from . import package_delivery as review
from .hashing import sha256_file
from .local_library import _file, _json, _lock, _path_inside

ASSETS = Path("assets/raw/prepared-library")
GENERATED = Path("src/calmframes/approvedPreparedCatalogs.ts")
REGISTRY = Path("config/approved-prepared-libraries.json")
# Every file check_prepared_library.mjs imports, or the proposed checkout cannot
# run it. Until Oct 19 ambient_report.mjs was missing, so every delivery was refused.
TOOLS = (
    Path("tools/approved_prepared_libraries.mjs"),
    Path("tools/check_prepared_library.mjs"),
    Path("tools/ambient_report.mjs"),
)


def _app(path: Path) -> Path:
    path = Path(path).absolute()
    if path.resolve() != path or not path.is_dir():
        raise review.DeliveryError("Choose an existing app directory without symlinks.")
    for relative in (REGISTRY, GENERATED, *TOOLS, ASSETS / "catalog.json", ASSETS / "catalog.ts"):
        _file(path / relative, path)
    for relative in TOOLS:
        if sha256_file(path / relative) != sha256_file(review.APP / relative):
            raise review.DeliveryError("The selected checkout has incompatible delivery checker tools.")
    return path


def _checked(root: Path, ticket: str) -> dict:
    """Caller holds the review lock, preventing cancellation during application."""
    previous = _json(review._ticket(root, ticket), root)
    if previous.get("state") == "canceled":
        raise review.DeliveryError("This delivery review was canceled. Stage a fresh review.")
    current = review.inspect_delivery(Path(previous["package_directory"]), previous["source_sha256"])
    if (current["inventory_sha256"] != previous["inventory_sha256"]
            or current["catalog_sha256"] != previous["catalog_sha256"]):
        raise review.DeliveryError("The staged package changed. Stage a fresh review.")
    return dict(current, ticket_id=ticket)


def _review_root(root: Path, app: Path) -> Path:
    root = Path(root).absolute()
    if root == app or root.is_relative_to(app) or app.is_relative_to(root):
        raise review.DeliveryError("App and reviews must be separate directories.")
    if not root.is_dir():
        raise review.DeliveryError("Stage a review before planning its delivery.")
    return review._root(root)


def _snapshot(app: Path) -> dict[str, str]:
    paths = [app / p for p in (REGISTRY, GENERATED, *TOOLS)]
    total = 0
    for directory, directories, names in os.walk(app / ASSETS, followlinks=False):
        for name in directories:
            _path_inside(Path(directory) / name, app)
        for name in names:
            paths.append(Path(directory) / name)
        if len(paths) > 10000:
            raise review.DeliveryError("The prepared namespace has too many entries.")
    result = {}
    for path in paths:
        _file(path, app)
        total += path.stat().st_size
        if total > 80 * 1024 * 1024:
            raise review.DeliveryError("The existing delivery inputs exceed the review bound.")
        result[str(path.relative_to(app))] = sha256_file(path)
    return result


def _plan(root: Path, ticket: str, app: Path) -> dict:
    current = _checked(root, ticket)
    package = Path(current["package_directory"])
    for other in (root, package):
        if other == app or other.is_relative_to(app) or app.is_relative_to(other):
            raise review.DeliveryError("App, package and reviews must be separate directories.")
    wanted = current["approval_request"]
    approved = next((entry for entry in review.approvals(app)
                     if all(entry[key] == value for key, value in wanted.items())), None)
    manifest = _json(package / "catalog.json", package)
    reports = {"reports/" + title["verification"]["reportSha256"] + ".json"
               for title in manifest["titles"]}
    files = {name: digest for name, digest in current["files"].items()
             if name.startswith(current["bundle_id"] + "/") or name in reports}
    missing = []
    for name, digest in files.items():
        destination = _path_inside(app / ASSETS / name, app)
        if destination.exists():
            if sha256_file(_file(destination, app)) != digest:
                raise review.DeliveryError("An existing immutable asset conflicts with the package.")
        else:
            missing.append(name)
    return {
        "version": 1, "state": "ready_to_apply" if approved else "blocked",
        "ticket_id": ticket, "approval_request": wanted,
        "blockers": [] if approved else ["The target checkout lacks this exact approved tuple."],
        "app_directory": str(app), "package_directory": str(package),
        "inventory_sha256": current["inventory_sha256"], "files": files,
        "files_to_add": missing, "files_already_present": sorted(set(files) - set(missing)),
        "can_watch": False, "installed": False, "approval_modified": False,
        "next_step": "Checked app build/install and native acceptance remain separate operator actions.",
    }


def plan_delivery(root: Path, ticket: str, app: Path) -> dict:
    app = _app(app)
    root = _review_root(root, app)
    with _lock(root):
        _snapshot(app)
        return _plan(root, ticket, app)


@contextmanager
def _checkout_lock(app: Path):
    descriptor = os.open(app, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise review.DeliveryError("Another edition delivery owns this checkout.") from exc
        yield
    finally:
        os.close(descriptor)


def _run_checks(app: Path, *, generate: bool, node: str) -> None:
    for relative, flag in ((TOOLS[0], "--write" if generate else "--check"),
                           (TOOLS[1], "--require-reports")):
        try:
            result = subprocess.run([node, str(app / relative), flag], cwd=app, check=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.decode("utf-8", errors="replace")[:4000]
            raise review.DeliveryError(f"Delivery check refused the proposed checkout: {detail}") from exc
        except subprocess.TimeoutExpired as exc:
            raise review.DeliveryError("Delivery check timed out; no build/install is authorized.") from exc
        try:
            receipt = json.loads(result.stdout)
            valid = (isinstance(receipt, dict) and
                     (type(receipt.get("approvedCatalogs")) is int if relative == TOOLS[0]
                      else receipt.get("prepared_library") == "checked"))
        except ValueError:
            valid = False
        if not valid:
            raise review.DeliveryError("Delivery checker did not return a successful structured receipt.")


def _copy_new(source: Path, destination: Path, app: Path, created: list[Path], directories: list[Path]) -> None:
    _path_inside(destination, app)
    missing = []
    parent = destination.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    for directory in reversed(missing):
        directory.mkdir()
        directories.append(directory)
    # Exclusive creation never replaces an asset another process wrote.
    with destination.open("xb") as output:
        identity = os.fstat(output.fileno()).st_ino
        try:
            with source.open("rb") as input_file:
                shutil.copyfileobj(input_file, output)
        except BaseException:
            if destination.lstat().st_ino == identity:
                destination.unlink()
            raise
        created.append(destination)


def _replace_generated(destination: Path, content: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def apply_delivery(root: Path, ticket: str, app: Path, *, node: str = "node") -> dict:
    app = _app(app)
    root = _review_root(root, app)
    with _lock(root), _checkout_lock(app):
        plan = _plan(root, ticket, app)
        if plan["state"] != "ready_to_apply":
            raise review.DeliveryError("Exact approval is missing in the selected checkout; run plan for its tuple.")
        before = _snapshot(app)
        original_generated = (app / GENERATED).read_bytes()
        created: list[Path] = []
        directories: list[Path] = []
        generated_bytes: bytes | None = None
        with tempfile.TemporaryDirectory(prefix="calm-edition-") as temporary:
            # Node's entrypoint guard compares the real module URL with argv. macOS
            # temp paths may begin /var while their real path starts /private/var.
            mirror = Path(temporary).resolve() / "app"
            for relative in before:
                destination = mirror / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(app / relative, destination)
            for name in plan["files_to_add"]:
                destination = mirror / ASSETS / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(plan["package_directory"]) / name, destination)
            _run_checks(mirror, generate=True, node=node)
            if _snapshot(app) != before or _plan(root, ticket, app) != plan:
                raise review.DeliveryError("Delivery inputs changed during checks; retry from a stable checkout.")
            try:
                for name in plan["files_to_add"]:
                    _copy_new(mirror / ASSETS / name, app / ASSETS / name, app, created, directories)
                generated_bytes = (mirror / GENERATED).read_bytes()
                if generated_bytes != original_generated:
                    _file(app / GENERATED, app)
                    _replace_generated(app / GENERATED, generated_bytes)
                _run_checks(app, generate=False, node=node)
                # Recheck approval, source and cancellation before declaring success.
                current = _plan(root, ticket, app)
                if current["state"] != "ready_to_apply" or current["inventory_sha256"] != plan["inventory_sha256"]:
                    raise review.DeliveryError("Review inputs changed during application.")
                protected = set(before) - {str(GENERATED)}
                after = _snapshot(app)
                if any(after.get(name) != before[name] for name in protected):
                    raise review.DeliveryError("Existing delivery inputs changed during application.")
                if (app / GENERATED).read_bytes() != generated_bytes:
                    raise review.DeliveryError("Compiled catalogs changed during application.")
            except BaseException:
                # Keep unrelated concurrent changes. Remove only files still matching our copy.
                if (generated_bytes is not None and (app / GENERATED).is_file()
                        and not (app / GENERATED).is_symlink()
                        and (app / GENERATED).read_bytes() == generated_bytes):
                    _replace_generated(app / GENERATED, original_generated)
                for path in reversed(created):
                    relative = str(path.relative_to(app / ASSETS))
                    if path.exists() and not path.is_symlink() and sha256_file(path) == plan["files"][relative]:
                        path.unlink()
                for directory in reversed(directories):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
                raise
        return dict(plan, state="applied_for_build", checks="generator and strict delivery passed",
                    generated_changed=generated_bytes != original_generated)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["plan", "apply"])
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--app", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        operation = apply_delivery if args.command == "apply" else plan_delivery
        result = operation(args.staging_root, args.ticket, args.app)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1 if result["state"] == "blocked" else 0
    except (OSError, ValueError, KeyError, PipelineError) as exc:
        print(json.dumps({"state": "blocked", "can_watch": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
