#!/usr/bin/env python3
"""Write the software bill of materials for everything this project ships.

    make sbom          write docs/SBOM.*.cdx.json
    make sbom-check    regenerate into a temporary directory and fail on a diff

    scripts/sbom.py --check --keep DIR
                       the same, with the fresh bills and a report.json left in
                       DIR, so a failed CI run can keep them as an artifact

Three bills, because there are three things that leave this machine:

    docs/SBOM.ingest.cdx.json   what is installed in the ingest container
    docs/SBOM.app.cdx.json      what the Vega app is built from
    docs/SBOM.cdk.cdx.json      what synthesizes and deploys the stack

All three are CycloneDX 1.6 JSON, written by the CycloneDX project's own tools,
and all three are generated with --output-reproducible so that running this
twice gives the same bytes. That is what makes the check in CI meaningful: if a
dependency moves and nobody regenerates, the check fails.

The same bytes need the same generators. Each tool writes its own name and
version into metadata.tools, and the compare treats that as content, which it
is: a bill says what wrote it. So the generator and the library under it are
both pinned here. cyclonedx-bom leaves cyclonedx-python-lib to a range, and
@cyclonedx/cyclonedx-npm leaves @cyclonedx/cyclonedx-library to one. On Oct 9,
2026 the hosted Audit runner resolved a different JavaScript library than the
one in the committed app bill, with the same package-lock.json on both sides,
and the Python bills matched that day by luck. After writing, this script reads
each fresh bill back and stops if a tool entry is not the pinned version, so a
generator this file does not pin cannot write a bill that CI, which installs
the pins, would then fail.

The one tool entry this file cannot pin is npm. cyclonedx-npm records the npm
that ran `npm ls`, and that npm comes with Node, so the sbom job in
.github/workflows/audit.yml pins its Node to the exact version whose npm the
committed bill names. .nvmrc stays at 22 for everything else. `make sbom` prints
the npm that wrote the app bill so a different one is seen before it is
committed.

When the compare fails, --check says which of three things happened: the
generators differ (the environment, so fix the pins), the components differ (a
dependency moved, so run make sbom), or neither, in which case the first
differing line is printed. The old message, "does not match what is
installed", sent readers to the lock file for a failure that was never about
the lock file.

What these do not cover, and it matters: the Debian packages inside the ingest
image. ffmpeg and its libraries are installed with apt at build time, and
listing them properly means reading the built image with a scanner, which needs
the image built. The base image is pinned by digest, which is the part that
makes the set of Debian packages knowable at all, and docs/SECURITY.md says so
rather than leaving a reader to assume the bill is complete.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The generators, each with the library it writes through. The versions are the
# ones recorded under metadata.tools in the committed bills, and
# pipeline/tests/test_aws_guard.py reads the bills to check that they agree
# with these lines and with the install step in .github/workflows/audit.yml.
CYCLONEDX_PY = "cyclonedx-bom==7.4.0"
CYCLONEDX_PY_LIB = "cyclonedx-python-lib==11.12.0"
CYCLONEDX_NPM = "@cyclonedx/cyclonedx-npm@6.0.1"
CYCLONEDX_NPM_LIB = "@cyclonedx/cyclonedx-library@10.3.0"


def pinned_version(spec: str) -> str:
    """The version in a pip or npm spec: 'a==1.2' and '@s/a@1.2' both give '1.2'."""
    return spec.rsplit("==" if "==" in spec else "@", 1)[1]


# How the pins above show up under metadata.tools in a bill they wrote: the
# name each tool records itself under, and the version it has to be.
PINNED_TOOLS = {
    "cyclonedx-py": pinned_version(CYCLONEDX_PY),
    "cyclonedx-python-lib": pinned_version(CYCLONEDX_PY_LIB),
    "cyclonedx-npm": pinned_version(CYCLONEDX_NPM),
    "cyclonedx-library": pinned_version(CYCLONEDX_NPM_LIB),
}

PYTHON_BILLS = [
    ("SBOM.ingest.cdx.json", "pipeline/infra/ingest/requirements.txt"),
    ("SBOM.cdk.cdx.json", "pipeline/infra/requirements.txt"),
]
APP_BILL = "SBOM.app.cdx.json"
REPORT = "report.json"
# How many added or removed components --check prints; report.json has them all.
SHOWN = 12


def cyclonedx_py() -> list[str]:
    """Installed, or through uvx with both pins. Either way the bill is read back.

    An installed cyclonedx-py is used as found, library and all, and
    refuse_unpinned() below catches it if that library is not the pinned one.
    """
    if shutil.which("cyclonedx-py"):
        return ["cyclonedx-py"]
    if shutil.which("uvx"):
        return ["uvx", "--from", CYCLONEDX_PY, "--with", CYCLONEDX_PY_LIB, "cyclonedx-py"]
    raise SystemExit(
        "cyclonedx-py is not installed and uvx is not available. "
        f"pip install {CYCLONEDX_PY} {CYCLONEDX_PY_LIB}"
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
    """From app/package-lock.json, deliberately, not from node_modules.

    An installed tree is platform specific: fsevents is there on a Mac and not
    on a Linux runner, so a bill read from node_modules would differ between the
    machine that wrote it and the machine that checks it, and the check in CI
    would fail for a reason that has nothing to do with anybody's dependencies.
    The lock file lists every package with its platform constraints, so it gives
    the same answer everywhere, and it is also what `npm ci` installs from.
    """
    app = REPO / "app"
    if not (app / "package-lock.json").exists():
        raise SystemExit("app/package-lock.json is missing")
    subprocess.run(
        [
            "npm",
            "exec",
            "--yes",
            # Both packages named, so the library is the pinned one rather than
            # the newest the caret range in cyclonedx-npm allows. The range
            # accepts the pin, so npm installs one copy and the tool loads it.
            # `npx --yes <tool>` alone pinned the tool and let the library
            # float, which is what failed on the hosted runner on Oct 9, 2026.
            f"--package={CYCLONEDX_NPM}",
            f"--package={CYCLONEDX_NPM_LIB}",
            "--",
            "cyclonedx-npm",
            "--output-format",
            "JSON",
            "--output-file",
            str(out),
            # The installed tree has peer dependency complaints that npm ls
            # reports as errors. They are the sample's, they do not change the
            # list of packages, and without this the tool writes nothing.
            "--ignore-npm-errors",
            "--package-lock-only",
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


# ------------------------------------------------------ reading a bill back


def read_bill(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tools_in(document: dict) -> dict[str, str]:
    """name -> version of each generator a bill says wrote it. npm is one of them."""
    tools = document.get("metadata", {}).get("tools", {})
    # CycloneDX 1.5 and later nest them under components; older bills list them.
    entries = tools.get("components", []) if isinstance(tools, dict) else tools
    return {entry["name"]: str(entry.get("version", "")) for entry in entries}


def describe_tools(path: Path) -> str:
    return ", ".join(f"{name} {version}" for name, version in tools_in(read_bill(path)).items())


def component_ids(document: dict) -> set[str]:
    """One string per component: the purl where there is one, else group/name@version."""
    ids = set()
    for component in document.get("components", []):
        purl = component.get("purl")
        if not purl:
            group = component.get("group")
            purl = f"{group + '/' if group else ''}{component.get('name')}@{component.get('version')}"
        ids.add(purl)
    return ids


def unpinned_generators(path: Path) -> list[str]:
    """Tool entries in a freshly written bill that are not the pinned versions."""
    ran = tools_in(read_bill(path))
    return [
        f"{path.name}: {name} {ran[name]} wrote it, and this script pins {pinned}"
        for name, pinned in PINNED_TOOLS.items()
        if name in ran and ran[name] != pinned
    ]


def refuse_unpinned(written: list[Path]) -> None:
    """Stop before a bill from an unpinned generator goes anywhere."""
    found = [line for path in written for line in unpinned_generators(path)]
    if not found:
        return
    print("A bill was written by a generator this script does not pin:")
    for line in found:
        print(f"  {line}")
    print()
    print("CI installs the pinned pair, so this bill would fail the compare there.")
    print(f"Install the same pair here:  pip install {CYCLONEDX_PY} {CYCLONEDX_PY_LIB}")
    print("or take cyclonedx-py off PATH and let uvx run the pinned pair. The npm side")
    print("is pinned by the command itself, so a wrong npm library means the range in")
    print(f"{CYCLONEDX_NPM} no longer accepts {CYCLONEDX_NPM_LIB}.")
    raise SystemExit(1)


def first_difference(committed: Path, fresh: Path) -> tuple[int, str, str]:
    """The first line that differs, one based, with both sides trimmed."""
    left_lines = committed.read_text(encoding="utf-8").splitlines()
    right_lines = fresh.read_text(encoding="utf-8").splitlines()

    def shown(lines: list[str], index: int) -> str:
        return lines[index].strip()[:120] if index < len(lines) else "(end of file)"

    for index, (left, right) in enumerate(zip(left_lines, right_lines)):
        if left != right:
            return index + 1, shown(left_lines, index), shown(right_lines, index)
    index = min(len(left_lines), len(right_lines))
    return index + 1, shown(left_lines, index), shown(right_lines, index)


def explain(committed: Path, fresh: Path) -> tuple[list[str], dict]:
    """Why two bills differ, in terms a reader can act on, and the same as data.

    Three causes are told apart: the generators differ, the components differ,
    or neither. The first is the environment and the fix is a pin; the second
    is a dependency that moved and the fix is `make sbom`; the third is shown
    by its first differing line.
    """
    before, after = read_bill(committed), read_bill(fresh)
    tools_before, tools_after = tools_in(before), tools_in(after)
    ids_before, ids_after = component_ids(before), component_ids(after)
    added, removed = sorted(ids_after - ids_before), sorted(ids_before - ids_after)

    lines = []
    if tools_before != tools_after:
        lines.append("the generators differ, so this is the environment and not a dependency:")
        for name in sorted(set(tools_before) | set(tools_after)):
            if tools_before.get(name) != tools_after.get(name):
                lines.append(
                    f"    {name}: committed {tools_before.get(name, 'absent')}, "
                    f"fresh {tools_after.get(name, 'absent')}"
                )
    lines.append(
        f"components: {len(ids_before)} committed, {len(ids_after)} fresh, "
        f"{len(added)} added, {len(removed)} removed"
    )
    for label, items in (("added", added), ("removed", removed)):
        for item in items[:SHOWN]:
            lines.append(f"    {label}: {item}")
        if len(items) > SHOWN:
            lines.append(f"    ... {len(items) - SHOWN} more {label}, all of them in {REPORT}")
    if tools_before == tools_after and not added and not removed:
        lines.append("same generators and the same components; the difference is elsewhere in the document")
    line_number, left, right = first_difference(committed, fresh)
    lines.append(f"first difference at line {line_number}:")
    lines.append(f"    committed: {left}")
    lines.append(f"    fresh:     {right}")

    report = {
        "matches": False,
        "committed": {
            "tools": tools_before,
            "components": len(ids_before),
            "bytes": committed.stat().st_size,
        },
        "fresh": {
            "tools": tools_after,
            "components": len(ids_after),
            "bytes": fresh.stat().st_size,
        },
        "added": added,
        "removed": removed,
        "first_difference": {"line": line_number, "committed": left, "fresh": right},
    }
    return lines, report


# --------------------------------------------------------------- summary


def summarise(paths: list[Path]) -> dict:
    """The counts, so a document can quote them instead of retyping them."""
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
        document = read_bill(path)
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


# ------------------------------------------------------------------ main


def write(docs: Path) -> int:
    """Write into a temporary directory, read back, then copy into docs/."""
    with tempfile.TemporaryDirectory() as temporary:
        fresh = write_all(Path(temporary))
        # Exits 1 here, before docs/ is touched, when a generator is not the
        # pinned one. The bills in docs/ stay as they were.
        refuse_unpinned(fresh)
        written = []
        for path in fresh:
            target = docs / path.name
            shutil.copyfile(path, target)
            written.append(target)
    for path in written:
        print(
            f"wrote {path.relative_to(REPO)} ({path.stat().st_size / 1024:.0f} kB), "
            f"by {describe_tools(path)}"
        )
    summary = REPO / "results" / "sbom.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(summarise(written), indent=2) + "\n")
    print(f"wrote {summary.relative_to(REPO)}")
    return 0


def check(docs: Path, fresh_dir: Path, kept: bool) -> int:
    """Regenerate into fresh_dir, compare byte for byte, and say why on a difference."""
    fresh = write_all(fresh_dir)
    unpinned = [line for path in fresh for line in unpinned_generators(path)]
    report: dict = {"pinned_generators": PINNED_TOOLS, "unpinned_generators": unpinned, "bills": {}}
    stale: list[tuple[str, list[str]]] = []
    for path in fresh:
        committed = docs / path.name
        name = str(committed.relative_to(REPO))
        if not committed.exists():
            stale.append((f"{name} has never been written", []))
            report["bills"][path.name] = {"matches": False, "committed": None}
        elif filecmp.cmp(path, committed, shallow=False):
            report["bills"][path.name] = {"matches": True, "tools": tools_in(read_bill(path))}
        else:
            lines, bill_report = explain(committed, path)
            stale.append((f"{name} does not match what the pinned generators wrote just now", lines))
            report["bills"][path.name] = bill_report
    (fresh_dir / REPORT).write_text(json.dumps(report, indent=2) + "\n")

    if not unpinned and not stale:
        pinned = ", ".join(f"{name} {version}" for name, version in PINNED_TOOLS.items())
        print(f"every bill of materials matches what the pinned generators write ({pinned})")
        return 0
    if unpinned:
        print("A generator that ran is not the one this script pins:")
        for line in unpinned:
            print(f"  {line}")
        print()
    if stale:
        print("The bill of materials is out of date:")
        for headline, lines in stale:
            print(f"  {headline}")
            for line in lines:
                print(f"    {line}")
        print()
        print("If the components changed, run: make sbom")
        print("If the generators differ, fix the pins in scripts/sbom.py and the sbom job of")
        print(".github/workflows/audit.yml; the bills do not need regenerating for that.")
    if kept:
        print(f"The fresh bills and {REPORT} are in {fresh_dir}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="fail if the committed bills are stale")
    parser.add_argument(
        "--keep",
        metavar="DIR",
        type=Path,
        help=(
            "with --check: write the fresh bills and report.json into DIR and leave "
            "them there, instead of a temporary directory, so CI can keep them"
        ),
    )
    args = parser.parse_args(argv)
    if args.keep is not None and not args.check:
        parser.error("--keep goes with --check")

    docs = REPO / "docs"
    if not args.check:
        return write(docs)
    if args.keep is not None:
        return check(docs, args.keep.resolve(), kept=True)
    with tempfile.TemporaryDirectory() as temporary:
        return check(docs, Path(temporary), kept=False)


if __name__ == "__main__":
    raise SystemExit(main())
