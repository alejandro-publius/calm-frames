"""Time and demonstrate preparation of an owned clip with the real analyzer.

Builds on eval/preparation_recovery.py rather than beside it. Its Lab runs
``python -m pipeline.local_library prepare`` as separate processes, SIGKILLs the whole
process group at an exact point, and compares ledgers, files and receipts. Here that
Lab gets the repository's owned, non-flashing Harbor story, assembled exactly as
eval/prepare_owned_harbor.py assembles it, and the real flashmap CLI.

    .venv/bin/python -m eval.preparation_benchmark --samples 3 \\
        --out results/preparation-benchmark-2026-10-22/benchmark.json \\
        --transcript results/preparation-benchmark-2026-10-22/transcript.txt

Every sample uses the same source, settings and work-directory path, and one Ed25519
test key pair made for the run:

  cold         prepare from nothing.
  warm         prepare again at once; every step should be reused.
  interrupted  prepare from nothing through the runner's ffmpeg wrapper, which writes
               half of the extra-cautious safe master and pauses; SIGKILL the process
               group there, then prepare again with the real ffmpeg.

Once, after the samples, starting from the first cold result:

  damage       flip one byte in the middle of a cached HLS segment, keeping its size
               and modification time;
  refresh      the local catalog refresh has to leave the damaged title out;
  repair       prepare again: the damaged step is rebuilt, the receipt is ready and
               names the cold run's bytes, and the refresh lists the title again.

Seconds are the wall-clock time of each command from start to exit, measured here.
Nothing is estimated and nothing is played. Only --out and --transcript are written
outside the temporary directory, which is removed at the end.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from eval.preparation_recovery import (
    HARNESS_ROOT,
    PRESETS,
    Lab,
    artifact_hashes,
    differences,
    flip_byte,
    git,
    now_utc,
    receipt_view,
    reran,
    sha256,
)
from eval.prepare_owned_harbor import assemble_owned_source

TITLE = "Harbor story (prepared locally)"
BLOCK_SUFFIX = "/safe/extra-cautious/safe.mp4"
DAMAGED = "safe/wcag/hls/seg_0_00002.ts"
NOT_STEP_OUTPUTS = {"state.json", "entry.json"}

LIMITATIONS = [
    "One owned clip (20 s, 1280x720, 24 fps) on one Mac. Timings depend on the clip's length, "
    "resolution and content, the machine and its load; they are not a rate for other videos.",
    "The interrupted run is stopped at one injected point, while the extra-cautious rendition is "
    "being written. How much a restart saves depends on where a real interruption lands.",
    "The interrupted runs pass every ffmpeg call through the runner's wrapper, which adds a "
    "process start per call before the kill; the restart and the other phases use ffmpeg directly.",
    "Real analyzer maps carry created_utc and a signature over it, so identities are compared "
    "without those fields, exactly as eval/preparation_recovery.py compares them.",
]


class OwnedLab(Lab):
    """The recovery runner's Lab around the owned Harbor source instead of its generated clip."""

    def __init__(self, code_root: Path, base: Path) -> None:
        super().__init__(code_root, base)
        self.source = assemble_owned_source(self.fixtures / "owned")
        self.sha = sha256(self.source.read_bytes())

    def prepare_command(self, key: str = "a") -> list[str]:
        command = super().prepare_command(key)
        command[command.index("--title") + 1] = TITLE
        return command


def prepare(lab: OwnedLab, env: dict[str, str]) -> tuple[dict, dict]:
    """One timed run of the prepare command, with the steps it ran and reused."""
    before = lab.ledger()
    run = lab.run(lab.prepare_command(), env=env)
    after = lab.ledger()
    ran = reran(before, after)
    receipt = run.receipt or {}
    verification = receipt.get("verification") or {}
    record = {"seconds": run.seconds, "exit": run.returncode, "status": run.status,
              "verification": verification.get("status"), "outcome": verification.get("outcome"),
              "steps": len(after), "steps_run": ran, "steps_reused": sorted(set(after) - set(ran))}
    return record, receipt


def unrecorded(lab: OwnedLab, ledger: dict) -> list[dict]:
    """Outputs in the title that no committed step vouches for: incomplete work.

    Files under work/ that no step lists are the steps' own scratch (frame grabs, luma
    metadata) rather than outputs, so they are counted apart, by scratch_files().
    """
    recorded = {name for record in ledger.values() for name in (record["outputs"] or {})}
    root = lab.title()
    found = []
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if (path.is_file() and not path.is_symlink() and name not in recorded and name not in NOT_STEP_OUTPUTS
                and not path.name.startswith(".") and not name.endswith(".tmp") and not name.startswith("verify/")
                and not name.startswith("work/")):
            found.append({"file": name, "bytes": path.stat().st_size})
    return found


def scratch_files(lab: OwnedLab, ledger: dict) -> int:
    recorded = {name for record in ledger.values() for name in (record["outputs"] or {})}
    root = lab.title() / "work"
    return sum(1 for path in root.rglob("*") if path.is_file()
               and path.relative_to(lab.title()).as_posix() not in recorded) if root.is_dir() else 0


def same_bytes(receipt: dict, reference: dict) -> bool:
    return (artifact_hashes(receipt_view(receipt, real_analyzer=True))
            == artifact_hashes(receipt_view(reference, real_analyzer=True)))


def spread(values: list[float]) -> dict:
    return {"samples": values, "median": round(statistics.median(values), 2),
            "min": min(values), "max": max(values)}


def machine() -> dict:
    def text(command: list[str]) -> str:
        try:
            return subprocess.run(command, capture_output=True, text=True, timeout=30).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            return ""

    ffmpeg = text(["ffmpeg", "-version"]).splitlines()
    flashmap = text([sys.executable, "-c", "import flashmap; print(getattr(flashmap, '__version__', ''))"])
    return {"platform": platform.platform(), "machine": platform.machine(),
            "cpu": text(["sysctl", "-n", "machdep.cpu.brand_string"]),
            "logical_cpus": os.cpu_count(), "memory_bytes": int(text(["sysctl", "-n", "hw.memsize"]) or 0),
            "macos": text(["sw_vers", "-productVersion"]), "python": platform.python_version(),
            "ffmpeg": ffmpeg[0] if ffmpeg else "", "flashmap": flashmap or "unknown"}


def describe(source: Path) -> dict:
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,"
         "r_frame_rate,sample_rate,channels", "-of", "json", str(source)],
        capture_output=True, text=True, check=True).stdout)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next((s for s in probe["streams"] if s["codec_type"] == "audio"), {})
    num, den = (int(part) for part in video["r_frame_rate"].split("/"))
    return {"what": "the owned, non-flashing Harbor story: picture animated by eval/render_harbor.py with "
                    "synthesized ambience, and the neutral captions from eval/benign_story.py, assembled by "
                    "eval/prepare_owned_harbor.py",
            "sha256": sha256(source.read_bytes()), "bytes": source.stat().st_size,
            "seconds": round(float(probe["format"]["duration"]), 3), "width": video["width"],
            "height": video["height"], "fps": round(num / den, 3), "video_codec": video["codec_name"],
            "audio": f"{audio.get('codec_name')} {audio.get('sample_rate')} Hz, {audio.get('channels')} channel(s)"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="where the JSON results are written")
    parser.add_argument("--transcript", help="where the plain-text account is also written")
    parser.add_argument("--samples", type=int, default=3, help="repetitions of cold, warm and interrupted")
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error("--samples must be at least 1")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg and ffprobe are needed", file=sys.stderr)
        return 2

    lines: list[str] = []

    def say(line: str) -> None:
        lines.append(line)
        print(line, flush=True)

    started, clock = now_utc(), time.monotonic()
    base = Path(tempfile.mkdtemp(prefix="calm-benchmark-")).resolve()
    checks: list[dict] = []

    def expect(condition: bool, description: str) -> None:
        checks.append({"check": description, "result": "pass" if condition else "fail"})
        if not condition:
            say(f"  FAILED: {description}")

    samples: list[dict] = []
    demonstration: dict = {}
    try:
        lab = OwnedLab(HARNESS_ROOT, base)
        env = lab.env(real_analyzer=True)
        fixture = describe(lab.source)
        say(f"source   {fixture['seconds']} s, {fixture['width']}x{fixture['height']}, {fixture['fps']} fps, "
            f"sha256 {fixture['sha256'][:12]}")
        say(f"analyzer the real flashmap CLI; presets {', '.join(PRESETS)}")
        reference_receipt: dict = {}
        reference_identity: dict = {}
        for index in range(1, args.samples + 1):
            lab.reset(from_reference=False)
            cold, cold_receipt = prepare(lab, env)
            identity = lab.identity(cold_receipt, real_analyzer=True)
            full_master = lab.title() / BLOCK_SUFFIX.lstrip("/")
            cold["extra_cautious_master_bytes"] = full_master.stat().st_size if full_master.exists() else None
            if index == 1:
                reference_receipt, reference_identity = cold_receipt, identity
                shutil.copytree(lab.live, lab.reference_copy, symlinks=True)
            say(f"sample {index}  cold     {cold['seconds']:7.2f} s  {cold['status']}, {cold['outcome']}, "
                f"{len(cold['steps_run'])} of {cold['steps']} steps run")
            warm, warm_receipt = prepare(lab, env)
            warm_diff = differences(identity, lab.identity(warm_receipt, real_analyzer=True))
            say(f"          warm     {warm['seconds']:7.2f} s  {warm['status']}, {len(warm['steps_run'])} run, "
                f"{len(warm['steps_reused'])} reused")

            lab.reset(from_reference=False)
            marker = lab.markers / f"block-{index}"
            blocked = lab.env(real_analyzer=True, extra={
                "CALM_FRAMES_FFMPEG": str(lab.ffmpeg_wrapper), "RECOVERY_REAL_FFMPEG": lab.real_ffmpeg,
                "RECOVERY_BLOCK_SUFFIX": BLOCK_SUFFIX, "RECOVERY_BLOCK_MARKER": str(marker)})
            kill = lab.kill_at(lab.start(lab.prepare_command(), env=blocked), marker.exists)
            at_kill = lab.ledger()
            incomplete = unrecorded(lab, at_kill)
            dead = {"kill": kill, "committed_at_kill": sorted(at_kill), "incomplete_files": incomplete,
                    "scratch_files_without_record": scratch_files(lab, at_kill),
                    "receipt_status_at_kill": lab.receipt_status(), "listed_at_kill": lab.listed()}
            partial = ", ".join(f"{item['file']} ({item['bytes']} of {cold['extra_cautious_master_bytes']} bytes)"
                                for item in incomplete) or "none"
            say(f"          kill     {kill['after_s']:7.2f} s  while the extra-cautious master was half written; "
                f"{len(at_kill)} steps committed; outputs with no record: {partial}; "
                f"receipt {dead['receipt_status_at_kill']}")
            restart, restart_receipt = prepare(lab, env)
            restart_identity = lab.identity(restart_receipt, real_analyzer=True)
            diff = differences(identity, restart_identity)
            say(f"          restart  {restart['seconds']:7.2f} s  {restart['status']}, "
                f"{len(restart['steps_reused'])} reused, {len(restart['steps_run'])} rebuilt; identity "
                f"{'equals the cold run' if not diff else 'DIFFERS: ' + '; '.join(diff)}")

            expect(cold["status"] == "ready" and cold["verification"] == "passed",
                   f"sample {index}: the cold run is ready and verification passed")
            expect(warm["status"] == "ready" and not warm["steps_run"],
                   f"sample {index}: the warm run is ready and reuses every step")
            expect(not warm_diff, f"sample {index}: the warm run's identity equals the cold run's")
            expect(kill["every_process_in_the_group_ended"], f"sample {index}: every process of the killed run ended")
            expect(any(item["file"] == BLOCK_SUFFIX.lstrip("/")
                       and 0 < item["bytes"] < (cold["extra_cautious_master_bytes"] or 0) for item in incomplete),
                   f"sample {index}: a partial extra-cautious master was on disk without a record")
            expect(dead["receipt_status_at_kill"] != "ready" and not dead["listed_at_kill"],
                   f"sample {index}: nothing was ready or listed while the run was dead")
            expect(restart["status"] == "ready" and restart["outcome"] == cold["outcome"],
                   f"sample {index}: the restart is ready with the cold run's outcome")
            expect(set(restart["steps_reused"]) == set(at_kill),
                   f"sample {index}: every step committed before the kill was reused")
            expect("rendition:extra-cautious" in restart["steps_run"],
                   f"sample {index}: the interrupted rendition was rebuilt")
            expect(not diff, f"sample {index}: the restart's identity equals the cold run's")
            samples.append({"sample": index, "cold": cold, "warm": {**warm, "identity_differences": warm_diff},
                            "interrupted": {**dead, "restart": restart,
                                            "kill_plus_restart_seconds": round(kill["after_s"] + restart["seconds"], 2),
                                            "identity_differences": diff}})

        lab.reset(from_reference=True)
        listed_before = lab.refresh()
        target = lab.title() / DAMAGED
        stat = target.stat()
        before_hash = sha256(target.read_bytes())
        flip_byte(target)
        os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        after = target.stat()
        damaged_hash = sha256(target.read_bytes())
        listed_damaged = lab.refresh()
        say(f"damage   flipped one byte of {DAMAGED} (size {after.st_size} bytes and modification time kept)")
        say(f"refresh  the local catalog lists {listed_damaged} title(s) (before the damage: {listed_before})")
        repair, repair_receipt = prepare(lab, env)
        listed_after = lab.refresh()
        diff = differences(reference_identity, lab.identity(repair_receipt, real_analyzer=True))
        say(f"repair   {repair['seconds']:7.2f} s  {repair['status']}, rebuilt {', '.join(repair['steps_run']) or 'nothing'}; "
            f"receipt {'names the cold run' if same_bytes(repair_receipt, reference_receipt) else 'DIFFERS from the cold run'}"
            f"'s bytes; the refresh lists {listed_after}")
        demonstration = {"damaged_file": DAMAGED, "sha256_before": before_hash,
                         "sha256_after_damage": damaged_hash,
                         "size_kept": after.st_size == stat.st_size, "mtime_kept": after.st_mtime_ns == stat.st_mtime_ns,
                         "listed_before": listed_before, "listed_while_damaged": listed_damaged,
                         "repair": repair, "listed_after_repair": listed_after,
                         "receipt_names_cold_bytes": same_bytes(repair_receipt, reference_receipt),
                         "identity_differences": diff}
        expect(listed_before == 1 and listed_damaged == 0, "the refresh left the damaged title out")
        expect(repair["status"] == "ready" and "rendition:wcag" in repair["steps_run"],
               "the repair rebuilt the damaged rendition and is ready")
        expect(demonstration["receipt_names_cold_bytes"] and not diff, "the repaired title equals the cold run")
        expect(listed_after == 1, "the refresh lists the repaired title again")
    finally:
        shutil.rmtree(base, ignore_errors=True)

    def phase(name: str) -> dict:
        return spread([sample[name]["seconds"] for sample in samples])

    summary = {
        "cold_seconds": phase("cold"), "warm_seconds": phase("warm"),
        "kill_after_seconds": spread([s["interrupted"]["kill"]["after_s"] for s in samples]),
        "restart_seconds": spread([s["interrupted"]["restart"]["seconds"] for s in samples]),
        "steps": samples[0]["cold"]["steps"] if samples else 0,
        "steps_reused_on_restart": sorted({len(s["interrupted"]["restart"]["steps_reused"]) for s in samples}),
        "steps_rebuilt_on_restart": sorted({len(s["interrupted"]["restart"]["steps_run"]) for s in samples}),
        "checks": len(checks), "checks_passed": sum(1 for c in checks if c["result"] == "pass"),
    }
    results = {
        "tool": "eval/preparation_benchmark.py",
        "command": " ".join(["python -m eval.preparation_benchmark",
                             *("<path>" if os.path.isabs(arg) else arg for arg in (argv if argv is not None else sys.argv[1:]))]),
        "tested_commit": git(HARNESS_ROOT, "rev-parse", "HEAD"),
        "tested_tree_has_uncommitted_changes": bool(git(HARNESS_ROOT, "status", "--porcelain", "--untracked-files=no")),
        "started_utc": started, "finished_utc": now_utc(), "seconds": round(time.monotonic() - clock, 1),
        "measured_not_estimated": "every seconds value is the wall-clock time of one command, measured by this tool",
        "machine": machine(),
        "fixture": fixture if samples else {},
        "settings": {"presets": list(PRESETS), "analyzer": "the real flashmap CLI (python -m flashmap)",
                     "command": "python -m pipeline.local_library prepare <source> --workdir <dir> --key <test key> "
                                "--pub <test key> --presets " + ",".join(PRESETS) + f" --title '{TITLE}'",
                     "encoding": "the pipeline's defaults for local preparation (app-v1 recipe)",
                     "keys": "one Ed25519 test pair made for this run and deleted with its directory",
                     "interruption": f"the runner's ffmpeg wrapper cuts {BLOCK_SUFFIX.lstrip('/')} in half and pauses; "
                                     "the process group is SIGKILLed there"},
        "samples": samples, "integrity_demonstration": demonstration, "summary": summary, "checks": checks,
        "limitations": LIMITATIONS,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n")
    if args.transcript:
        Path(args.transcript).write_text("\n".join(lines) + "\n")
    say(f"{summary['checks_passed']} of {summary['checks']} checks passed; results in {out}")
    return 0 if summary["checks_passed"] == summary["checks"] else 1


if __name__ == "__main__":
    sys.exit(main())
