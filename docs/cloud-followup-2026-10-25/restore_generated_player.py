"""Restore this handoff's verified generated inputs, never overwrite source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ARCHIVE_SHA256 = "2c939d4b38b5fff5676faa4928d828eff7c0bde93e2063f9b1a6b98246fb405e"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def restore(archive: Path, checkout: Path, expected_head: str) -> dict:
    checkout = checkout.resolve(strict=True)

    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()

    require(bool(re.fullmatch(r"[a-f0-9]{40}", expected_head)), "Supply the full SHA from the transfer manifest")
    require(Path(git("rev-parse", "--show-toplevel")).resolve() == checkout, "Choose the worktree root")
    require(git("rev-parse", "HEAD") == expected_head, "Worktree HEAD differs from the transfer manifest")
    require(not git("status", "--porcelain=v1", "--untracked-files=no"), "Preserve pending tracked edits; use a clean separate worktree")
    require(sha256(archive.read_bytes()) == ARCHIVE_SHA256, "Generated-input archive checksum mismatch")
    tracked = set(git("ls-files").splitlines())

    def destination(name: str) -> Path:
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, "Invalid archive path")
        path = checkout / relative
        for parent in [path, *path.parents]:
            if parent == checkout:
                break
            require(not parent.is_symlink(), "Do not restore through a linked file or subdirectory")
        return path

    with zipfile.ZipFile(archive) as zipped:
        manifest = json.loads(zipped.read("GENERATED_PLAYER_INPUTS.json"))
        require(manifest.get("artifact_kind") == "generated_player_inputs", "Wrong artifact kind")
        for name, recorded in manifest["build_inputs"].items():
            path = destination("app/" + name)
            require(path.is_file() and sha256(path.read_bytes()) == recorded["sha256"],
                    f"Build input differs: app/{name}; regenerate with setup:player instead")

        files = [entry for entry in manifest["files"]
                 if entry.get("portable_input") and not entry.get("metadata_only")]
        require(len(files) == 8, "Unexpected generated-file inventory")
        prepared: list[tuple[Path, bytes]] = []
        for entry in files:
            name = entry["path"]
            require(name.startswith("app/src/w3cmedia/") and name not in tracked, "Never overwrite tracked source")
            path = destination(name)
            data = zipped.read(name)
            require(len(data) == entry["bytes"] and sha256(data) == entry["sha256"], "Generated file checksum mismatch")
            if path.exists():
                require(path.is_file() and sha256(path.read_bytes()) == entry["sha256"],
                        f"Existing generated file differs: {name}; preserve it and use another worktree")
            else:
                prepared.append((path, data))

        # Validate every input and destination before writing any file. Exclusive
        # creation also refuses a file that appears after the preflight above.
        for path, data in prepared:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)
        return {
            "source_commit": expected_head,
            "generated_at_source": manifest["source_commit"],
            "archive_sha256": ARCHIVE_SHA256,
            "build_input_hashes_match": True,
            "verified_files": files,
            "new_files_written": len(prepared),
            "tracked_files_overwritten": False,
            "native_package_built": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(restore(args.archive, args.checkout, args.expected_head), indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Player inputs not restored: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
