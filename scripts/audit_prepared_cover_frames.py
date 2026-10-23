"""Headless numeric audit of every covered decoded frame in a staged library.

No player, image export, screen capture or signing operation is used. Run the
strict packaged-library check separately first. This check does not establish
detector validity, audio quality, TV output or safety outside covered intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import av
import numpy as np

from pipeline.flashmap_adapter import load_map
from pipeline.hideplan import build_app_playback_plan
from pipeline.layout import TitleLayout
from pipeline.local_library import _inputs_digest


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def audit(root: Path, preparation: Path) -> dict:
    catalog = json.loads((root / "catalog.json").read_text())
    bundle = root / catalog["bundleId"]
    results = []
    for title in catalog["titles"]:
        layout = TitleLayout(preparation, title["sourceSha256"])
        assert _inputs_digest(layout) == title["verification"]["checkedInputsSha256"], "preparation input digest changed"
        with av.open(str(layout.still_path)) as image:
            still = next(image.decode(video=0)).to_ndarray(format="rgb24").astype(np.float32)
        maps = {key: load_map(bundle / item["path"]) for key, item in title["maps"].items()}
        for preset, rendition in title["renditions"].items():
            path = bundle / rendition["path"]
            assert digest(path) == rendition["sha256"], "rendition bytes changed"
            plan = build_app_playback_plan(maps, source_sha256=title["sourceSha256"],
                                           duration_ms=title["durationMs"], preset=preset)
            assert not plan.allow_dim
            assert all(not document.raw.get("scene_holds") for document in maps.values())
            spans = [interval.to_dict() for interval in plan.intervals]
            records = []
            covered = [[] for _ in spans]
            with av.open(str(path)) as container:
                for frame in container.decode(video=0):
                    assert frame.pts is not None and frame.time_base is not None
                    pts = float(frame.pts * frame.time_base * 1000)
                    source_ms = pts + rendition["startOffsetMs"]
                    # Full 1280x720 numeric RGB decode, never shown or saved.
                    rgb = frame.to_ndarray(format="rgb24")
                    assert rgb.shape == still.shape
                    mse = float(np.mean((rgb.astype(np.float32) - still) ** 2))
                    psnr = 10 * math.log10(255 ** 2 / mse) if mse else 999.0
                    record = {"index": len(records), "ptsMs": pts,
                              "sourceMs": source_ms, "stillPsnrDb": psnr}
                    records.append(record)
                    for index, span in enumerate(spans):
                        # Render's ffmpeg between() expression includes both ends.
                        if span["start_ms"] <= source_ms <= span["end_ms"]:
                            covered[index].append(record)
            assert records and all(b["ptsMs"] > a["ptsMs"] for a, b in zip(records, records[1:]))
            details = []
            for span, frames in zip(spans, covered):
                assert frames, "planned interval contains no decoded frame"
                worst = min(frame["stillPsnrDb"] for frame in frames)
                # Fixed before the still comparison: the verifier's 30 dB floor.
                failures = [frame for frame in frames if frame["stillPsnrDb"] < 30]
                first, last = frames[0]["index"], frames[-1]["index"]
                details.append({"startMs": span["start_ms"], "endMs": span["end_ms"],
                                "coveredFrames": len(frames), "worstStillPsnrDb": worst,
                                "failedFrames": failures, "passed": not failures,
                                "before": records[first - 1] if first else None,
                                "first": frames[0], "last": frames[-1],
                                "after": records[last + 1] if last + 1 < len(records) else None})
            results.append({"preset": preset, "renditionSha256": rendition["sha256"],
                            "sourceSha256": title["sourceSha256"],
                            "stillSha256": digest(layout.still_path),
                            "checkedInputsSha256": title["verification"]["checkedInputsSha256"],
                            "decodedFrames": len(records), "startOffsetMs": rendition["startOffsetMs"],
                            "intervals": details, "passed": bool(details) and all(s["passed"] for s in details)})
    return {"bundleId": catalog["bundleId"], "method": "Full decoded RGB arrays; inclusive cover bounds from app-v1 plan; every covered frame RGB PSNR >= 30 dB against preparation still bound by checkedInputsSha256. A whole-frame similarity check, not exact pixel equality or detector validation.",
            "independentDetectorValidation": False, "nativePlayback": False,
            "results": results, "passed": all(item["passed"] for item in results)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.preparation)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "presets": len(result["results"])}))
    raise SystemExit(0 if result["passed"] else 1)
