"""Recheck one retained positive case without playback, signing or app changes.

The input roots are read-only. Outputs are JSON plus analyzer stdout; decoded
frames exist only as numeric arrays in memory. Historical signatures are not
freshly verified by this bounded check, and no app trust is granted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import av
import numpy as np

SOURCE_SHA = "fdb4340eb6240f87bd37cae174591f3e74ca29817a2c60f9223c985745cc4345"
SOURCE_NAME = "HAZARD_wc_irminger_waves_without_sound_ooi.webm"


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def run(media: Path, work: Path, out: Path) -> dict:
    source = media / SOURCE_NAME
    assert digest(source) == SOURCE_SHA, "source differs from historical ledger"
    title = work / "titles" / SOURCE_SHA
    out.mkdir(parents=True, exist_ok=True)
    check = subprocess.run(
        [sys.executable, "-m", "flashmap", "check", str(source), "--profile", "wcag",
         "--json", str(out / "irminger-current-wcag.json")],
        capture_output=True, text=True, timeout=180,
    )
    (out / "source-check.txt").write_text(check.stdout + check.stderr)
    fresh = json.loads((out / "irminger-current-wcag.json").read_text())
    previous = json.loads((title / "maps/wcag.json").read_text())
    assert check.returncode == 1 and fresh["segments"], "known-positive source no longer flags"
    with av.open(str(title / "still.png")) as container:
        still = next(container.decode(video=0)).to_ndarray(format="rgb24").astype(np.float32)
    entries = []
    for preset in ("wcag", "broadcast", "extra-cautious"):
        plan_path = title / "plans" / f"{preset}.json"
        plan = json.loads(plan_path.read_text())
        assert plan["source_sha256"] == SOURCE_SHA and not plan["allow_dim"]
        rendition = title / "safe" / preset / "safe.mp4"
        frames = 0
        covered = [[] for _ in plan["intervals"]]
        with av.open(str(rendition)) as container:
            for frame in container.decode(video=0):
                assert frame.pts is not None and frame.time_base is not None
                ms = float(frame.pts * frame.time_base * 1000)
                rgb = frame.to_ndarray(format="rgb24").astype(np.float32)
                assert rgb.shape == still.shape
                mse = float(np.mean((rgb - still) ** 2))
                psnr = 10 * math.log10(255**2 / mse) if mse else 999.0
                for index, interval in enumerate(plan["intervals"]):
                    if interval["start_ms"] <= ms <= interval["end_ms"]:
                        covered[index].append(psnr)
                frames += 1
        intervals = [{"startMs": span["start_ms"], "endMs": span["end_ms"],
                      "frames": len(scores), "worstPsnrDb": min(scores) if scores else None,
                      "passed": bool(scores) and min(scores) >= 30}
                     for span, scores in zip(plan["intervals"], covered)]
        entries.append({"preset": preset, "decodedFrames": frames,
                        "renditionSha256": digest(rendition), "planSha256": digest(plan_path),
                        "mapSha256": digest(title / "maps" / f"{preset}.json"),
                        "intervals": intervals, "passed": bool(intervals) and all(x["passed"] for x in intervals)})
    return {"sourceSha256": SOURCE_SHA, "sourceBytes": source.stat().st_size,
            "sourceName": SOURCE_NAME, "analyzerExit": check.returncode,
            "sourceFindings": len(fresh["segments"]),
            "segmentsMatchHistoricalMap": fresh["segments"] == previous["segments"],
            "stillSha256": digest(title / "still.png"),
            "historicalReportSha256": digest(title / "verify/report.json"),
            "renditions": entries, "passed": all(x["passed"] for x in entries),
            "method": "Fresh WCAG analysis plus full-resolution numeric RGB comparison of every covered decoded frame to the retained still; 30 dB whole-frame PSNR floor; 999 is the finite sentinel for identical arrays (infinite PSNR).",
            "limits": ["No independent detector validation or fresh map-signature verification.",
                       "Whole-frame similarity is not exact pixel equality or a proof of safety.",
                       "No playback, image export, capture, signing, artifact regeneration or app trust change.",
                       "Retained historical plans are used; no new prepared bundle is created."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.media, args.work, args.out)
    (args.out / "recheck.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
