"""Check only the supplied local package; mutations stay in disposable copies."""

import argparse
import base64
import json
import shutil
import tempfile
from pathlib import Path

from pipeline import PipelineError
from pipeline.hashing import fingerprint, sha256_file
from pipeline.local_intake import inspect_package
from pipeline.packaged_library import catalog_module


def canonicalize(root, manifest):
    old_id = manifest.pop("bundleId")
    new_id = fingerprint(manifest)
    manifest["bundleId"] = new_id
    (root / old_id).rename(root / new_id)
    text = json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    (root / new_id / "manifest.json").write_text(text)
    (root / "catalog.json").write_text(text)
    (root / "catalog.ts").write_text(catalog_module(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("source_sha256")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    original = inspect_package(args.package, args.source_sha256)
    records = [{"check": "original exact package verifies", "passed": True}]
    for case in [
        "wrong_source",
        "altered_media",
        "unsigned_map_rehashed",
        "wrong_public_key_rehashed",
        "missing_report",
    ]:
        with tempfile.TemporaryDirectory(prefix="calm-package-negative-") as temporary:
            root = Path(temporary) / "package"
            shutil.copytree(args.package, root)
            manifest = json.loads((root / "catalog.json").read_text())
            title = manifest["titles"][0]
            expected = args.source_sha256
            if case == "wrong_source":
                expected = "0" * 64
            elif case == "altered_media":
                with (root / manifest["bundleId"] / title["renditions"]["wcag"]["path"]).open(
                    "r+b"
                ) as handle:
                    handle.write(b"ALTERED")
            elif case == "unsigned_map_rehashed":
                entry = title["maps"]["wcag"]
                raw = json.loads(entry["text"])
                raw.pop("signature", None)
                entry["text"] = json.dumps(raw, indent=2, sort_keys=True) + "\n"
                path = root / manifest["bundleId"] / entry["path"]
                path.write_text(entry["text"])
                entry["sha256"] = sha256_file(path)
                manifest["files"][entry["path"]] = entry["sha256"]
                canonicalize(root, manifest)
            elif case == "wrong_public_key_rehashed":
                manifest["publicKeyBase64"] = base64.b64encode(bytes(32)).decode()
                canonicalize(root, manifest)
            elif case == "missing_report":
                shutil.rmtree(root / "reports")
            try:
                inspect_package(root, expected)
            except PipelineError:
                records.append({"check": case, "passed": True, "result": "refused"})
            else:
                raise AssertionError(case + " was accepted")
    assert inspect_package(args.package, args.source_sha256) == original
    records.append({"check": "original preserved and verifies after negatives", "passed": True})
    args.output.write_text(
        json.dumps(
            {"package": str(args.package), "identity": original, "checks": records}, indent=2
        )
        + "\n"
    )
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
