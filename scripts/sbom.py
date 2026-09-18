#!/usr/bin/env python3
"""Write the software bill of materials for everything this project ships.

    make sbom          write docs/SBOM.*.cdx.json
    make sbom-check    regenerate into a temporary directory and fail on a diff

Three bills, because there are three things that leave this machine:

    docs/SBOM.ingest.cdx.json   what is installed in the ingest container
    docs/SBOM.app.cdx.json      what the Vega app is built from
    docs/SBOM.cdk.cdx.json      what synthesizes and deploys the stack

All three are CycloneDX 1.6 JSON, written by the CycloneDX project's own tools,
and all three are generated with --output-reproducible so that running this
twice gives the same bytes. That is what makes the check in CI meaningful: if a
dependency moves and nobody regenerates, the check fails.

What these do not cover, and it matters: the Debian packages inside the ingest
image. ffmpeg and its libraries are installed with apt at build time, and
listing them properly means reading the built image with a scanner, which needs
the image built. The base image is pinned by digest, which is the part that
makes the set of Debian packages knowable at all, and docs/SBOM.md says so
rather than leaving a reader to assume the bill is complete.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CYCLONEDX_PY = "cyclonedx-bom==7.4.0"
CYCLONEDX_NPM = "@cyclonedx/cyclonedx-npm@6.0.1"

PYTHON_BILLS = [
    ("SBOM.ingest.cdx.json", "pipeline/infra/ingest/requirements.txt"),
    ("SBOM.cdk.cdx.json", "pipeline/infra/requirements.txt"),
]
APP_BILL = "SBOM.app.cdx.json"


def cyclonedx_py() -> list[str]:
    """Installed, or through uvx. Either way it is the same pinned version."""
    if shutil.which("cyclonedx-py"):
        return ["cyclonedx-py"]
    if shutil.which("uvx"):
        return ["uvx", "--from", CYCLONEDX_PY, "cyclonedx-py"]
    raise SystemExit(
        "cyclonedx-py is not installed and uvx is not available. "
        f"pip install {CYCLONEDX_PY}"
    )


def python_bill(requirements: Path, out: Path) -> None:
    subprocess.run(
        cyclonedx_py()
        + [
            "requirements",
            str(requirements),
            "--output-format",
            "JSON",
            "--output-file",
            str(out),
            "--output-reproducible",
        ],
        check=True,
        cwd=REPO,
        stdout=subprocess.DEVNULL,
    )


def app_bill(out: Path) -> None:
    app = REPO / "app"
    if not (app / "node_modules").exists():
        raise SystemExit("app/node_modules is missing. Run npm ci in app/ first")
    subprocess.run(
        [
            "npx",
            "--yes",
            CYCLONEDX_NPM,
            "--output-format",
            "JSON",
            "--output-file",
            str(out),
            # The installed tree has peer dependency complaints that npm ls
            # reports as errors. They are the sample's, they do not change the
            # list of packages, and without this the tool writes nothing.
            "--ignore-npm-errors",
            "--output-reproducible",
        ],
        check=True,
        cwd=app,
        stdout=subprocess.DEVNULL,
    )


def write_all(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, requirements in PYTHON_BILLS:
        out = directory / name
        python_bill(REPO / requirements, out)
        written.append(out)
    out = directory / APP_BILL
    app_bill(out)
    written.append(out)
    return written


def summarise(paths: list[Path]) -> dict:
    """The counts, so a document can quote them instead of retyping them."""
    import json

    summary = {
        "generated_from": "CycloneDX 1.6 bills in docs/, written by scripts/sbom.py",
        "statement": (
            "Component counts from the committed bills of materials. The ingest "
            "bill covers the Python packages installed in the container and not "
            "the Debian packages apt installs, which needs the built image to "
            "read. The base image is pinned by digest."
        ),
        "bills": {},
    }
    for path in paths:
        document = json.loads(path.read_text())
        summary["bills"][path.name] = {
            "spec_version": document["specVersion"],
            "components": len(document.get("components", [])),
            "bytes": path.stat().st_size,
        }
    summary["published"] = {
        "ingest_components": summary["bills"][PYTHON_BILLS[0][0]]["components"],
        "cdk_components": summary["bills"][PYTHON_BILLS[1][0]]["components"],
        "app_components": summary["bills"][APP_BILL]["components"],
        "base_image_digest": BASE_IMAGE_DIGEST,
    }
    return summary


def base_image_digest() -> str:
    """Read the pinned digest out of the Dockerfile, rather than repeating it."""
    dockerfile = (REPO / "pipeline" / "infra" / "ingest" / "Dockerfile").read_text()
    for line in dockerfile.splitlines():
        if line.startswith("FROM ") and "@sha256:" in line:
            return line.split("@", 1)[1].split()[0]
    return "unknown"


BASE_IMAGE_DIGEST = base_image_digest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed bills are stale")
    args = parser.parse_args(argv)

    docs = REPO / "docs"
    if not args.check:
        import json

        written = write_all(docs)
        for path in written:
            print(f"wrote {path.relative_to(REPO)} ({path.stat().st_size / 1024:.0f} kB)")
        summary = REPO / "results" / "sbom.json"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(json.dumps(summarise(written), indent=2) + "\n")
        print(f"wrote {summary.relative_to(REPO)}")
        return 0

    with tempfile.TemporaryDirectory() as temporary:
        fresh = Path(temporary)
        stale = []
        for path in write_all(fresh):
            committed = docs / path.name
            if not committed.exists():
                stale.append(f"{committed.relative_to(REPO)} has never been written")
            elif not filecmp.cmp(path, committed, shallow=False):
                stale.append(f"{committed.relative_to(REPO)} does not match what is installed")
        if stale:
            print("The bill of materials is out of date:")
            for line in stale:
                print(f"  {line}")
            print()
            print("Run: make sbom")
            return 1
    print("every bill of materials matches what is installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
