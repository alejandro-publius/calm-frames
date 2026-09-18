"""Replay the fuzz corpus against every reader that opens a flash map.

Three readers, three languages, one rule. eval/fuzz_maps.py builds the corpus and this file
runs it on every CI run, so a case that was once handled cannot quietly stop being handled.

Fail closed, stated so it can be checked:

    the map is refused, and the picture stays hidden;
    or the map is accepted, and every span it flags is hidden.

Anything else is a finding. An exception is a finding, because a reader that throws has told
the caller nothing about whether the picture is safe. A map that is accepted and then
produces a schedule missing one of its own segments is a finding, because the map was
believed and then not acted on.

Running this file as a program writes results/fuzz.json:

    python3 -m pytest eval/fuzz_maps_test.py      check every case
    python3 eval/fuzz_maps_test.py                check them and write results/fuzz.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

import fuzz_maps
from property_runner import RunnerUnavailable, SchedulerRunner, scheduler  # noqa: F401

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "eval" / "fuzz_corpus"
RESULT = REPO / "results" / "fuzz.json"

# `python -m pytest` puts the working directory on the path and running this file as a
# program does not, so the pipeline import would work under one and not the other.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

INDEX = json.loads((CORPUS / "index.json").read_text())
CASES = INDEX["cases"]
PUBLIC_KEY = INDEX["public_key_base64"]
SOURCE_SHA256 = INDEX["source_sha256"]
NOW_MS = INDEX["now_ms"]

# Rejections the app is allowed to give. Anything outside this set means the reader invented
# a category, which would not reach the wording in rejectionMessage.
KNOWN_REJECTIONS = {
    "missing",
    "unparseable",
    "wrong-version",
    "unsigned",
    "unknown-key",
    "bad-signature",
    "wrong-file",
    "stale",
}


def case_text(case: dict) -> str:
    return (CORPUS / case["file"]).read_text(encoding="utf-8")


def public_key_pem(tmp_path: Path) -> Path:
    from cryptography.hazmat.primitives import serialization

    path = tmp_path / "fuzz_key.pub.pem"
    path.write_bytes(
        fuzz_maps.fuzz_key()
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return path


# --------------------------------------------------------------------- the app's reader


def check_app(runner, case: dict) -> dict:
    """One case through app/src/calmframes/flashMap.ts, compiled and run for real."""
    answer = runner.call(
        {
            "job": "verify",
            "text": case_text(case),
            "publicKeyBase64": PUBLIC_KEY,
            "expectedSha256": SOURCE_SHA256,
            "nowMs": NOW_MS,
            "options": {},
        }
    )
    record = {"case": case["name"], "reader": "app"}
    if not answer.get("ok"):
        record["finding"] = f"the reader threw rather than answering: {answer.get('error')}"
        return record
    if answer["verdict"] == "rejected":
        record["verdict"] = "rejected"
        record["reason"] = answer["reason"]
        if answer["reason"] not in KNOWN_REJECTIONS:
            record["finding"] = f"unknown rejection category {answer['reason']!r}"
        return record
    record["verdict"] = "accepted"
    record["segments"] = answer["segmentCount"]
    record["reasons"] = answer["reasons"]
    if answer["scheduleError"]:
        # The app catches this and stays blocked, so it is fail closed and worth recording.
        record["schedule_refused"] = answer["scheduleError"]
        return record
    if answer["missed"]:
        record["finding"] = (
            "the map was accepted and then its own flagged moments were left showing at "
            f"{answer['missed']}"
        )
    return record


# ------------------------------------------------------------------ flashmap's reader


def check_flashmap(case: dict, tmp_path: Path) -> dict:
    from flashmap.sidecar import VerificationError, load_map, verify_map

    record = {"case": case["name"], "reader": "flashmap"}
    path = tmp_path / case["file"]
    path.write_text(case_text(case), encoding="utf-8")
    try:
        document = load_map(path)
    except VerificationError as error:
        record["verdict"] = "rejected"
        record["reason"] = str(error)[:200]
        return record
    except Exception as error:  # noqa: BLE001 - the point of the test
        record["finding"] = f"load_map threw {type(error).__name__}: {error}"
        return record

    try:
        report = verify_map(document, public_key_path=public_key_pem(tmp_path))
    except Exception as error:  # noqa: BLE001 - the point of the test
        record["finding"] = f"verify_map threw {type(error).__name__}: {error}"
        return record

    record["verdict"] = "accepted" if report.ok else "rejected"
    if not report.ok:
        record["reason"] = "; ".join(report.problems)[:200]
        return record
    # Accepted. Then the segments it carries have to make sense, because the pipeline builds
    # a hide plan straight from them.
    bad = [
        segment
        for segment in document.get("segments", [])
        if not isinstance(segment, dict)
        or not isinstance(segment.get("start_ms"), (int, float))
        or not isinstance(segment.get("end_ms"), (int, float))
        or segment["end_ms"] <= segment["start_ms"]
        or segment["start_ms"] < 0
    ]
    if bad:
        record["finding"] = (
            f"the map verified with {len(bad)} segment(s) that make no sense, for example "
            f"{bad[0]}"
        )
    return record


# ------------------------------------------------------------------ the pipeline's reader


def check_pipeline(case: dict, tmp_path: Path) -> dict:
    from pipeline.flashmap_adapter import MapFormatError, load_map

    record = {"case": case["name"], "reader": "pipeline"}
    path = tmp_path / case["file"]
    path.write_text(case_text(case), encoding="utf-8")
    try:
        document = load_map(path)
    except MapFormatError as error:
        record["verdict"] = "rejected"
        record["reason"] = str(error)[:200]
        return record
    except Exception as error:  # noqa: BLE001 - the point of the test
        record["finding"] = f"load_map threw {type(error).__name__}: {error}"
        return record

    record["verdict"] = "accepted"
    record["segments"] = len(document.segments)

    # Accepted, so the question is no longer whether the map is tidy but whether the plan
    # built from it hides everything the map flagged. A start before zero is an example of
    # untidy but safe: the plan clamps it to the beginning of the film and the whole flagged
    # span is still covered. That is fail closed, so it is noted rather than failed.
    from pipeline.hideplan import build_cover_intervals, is_covered

    try:
        intervals = build_cover_intervals(document.segments)
    except Exception as error:  # noqa: BLE001 - the point of the test
        record["finding"] = f"the plan could not be built: {type(error).__name__}: {error}"
        return record

    missed = []
    for segment in document.segments:
        if segment.end_ms <= segment.start_ms:
            record.setdefault("notes", []).append(
                f"segment of no length at {segment.start_ms} was dropped"
            )
            continue
        if segment.start_ms < 0:
            record.setdefault("notes", []).append(
                f"segment starting at {segment.start_ms} was clamped to the start of the film"
            )
        for time_ms in (
            max(0.0, segment.start_ms),
            max(0.0, (segment.start_ms + segment.end_ms) / 2),
            segment.end_ms - 1,
        ):
            if not is_covered(intervals, time_ms):
                missed.append(time_ms)
    if missed:
        record["finding"] = (
            "the map was accepted and then the plan left its own flagged moments showing at "
            f"{missed[:10]}"
        )
    return record


# ------------------------------------------------------------------------------- tests


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_flashmap_fails_closed(case, tmp_path):
    record = check_flashmap(case, tmp_path)
    assert "finding" not in record, record["finding"]


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_the_pipeline_loader_fails_closed(case, tmp_path):
    record = check_pipeline(case, tmp_path)
    assert "finding" not in record, record["finding"]


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_the_app_fails_closed(scheduler, case):
    record = check_app(scheduler, case)
    assert "finding" not in record, record["finding"]


def test_the_corpus_is_what_the_generator_makes(tmp_path):
    """A committed corpus that has drifted from its generator would test the past."""
    names = {case["name"] for case in CASES}
    generated = {name for name, _, _ in fuzz_maps.CASES}
    assert names == generated, (
        "eval/fuzz_corpus and eval/fuzz_maps.py disagree. Run "
        "python3 eval/fuzz_maps.py --write-corpus"
    )
    for case in CASES:
        assert (CORPUS / case["file"]).exists(), case["file"]


def test_a_good_map_is_still_accepted(scheduler, tmp_path):
    """The negative control.

    Every test above passes if the readers refuse everything, so one map that should be
    accepted has to be accepted, by all three readers, with its segment intact.
    """
    from flashmap.sidecar import verify_map
    from pipeline.flashmap_adapter import load_map as pipeline_load

    good = fuzz_maps.sign(fuzz_maps.base_map())
    text = json.dumps(good, indent=2, sort_keys=True)
    path = tmp_path / "good.flashmap.json"
    path.write_text(text, encoding="utf-8")

    answer = scheduler.call(
        {
            "job": "verify",
            "text": text,
            "publicKeyBase64": PUBLIC_KEY,
            "expectedSha256": SOURCE_SHA256,
            "nowMs": NOW_MS,
            "options": {},
        }
    )
    assert answer["ok"], answer.get("error")
    assert answer["verdict"] == "accepted", answer
    assert answer["segmentCount"] == 1
    assert answer["missed"] == []

    report = verify_map(good, public_key_path=public_key_pem(tmp_path))
    assert report.ok, report.problems
    assert len(pipeline_load(path).segments) == 1


# --------------------------------------------------------------------------- the report


def run_everything(tmp_path: Path) -> dict:
    records: list[dict] = []
    try:
        runner = SchedulerRunner()
        runner.__enter__()
    except RunnerUnavailable as error:
        runner = None
        records.append({"case": "*", "reader": "app", "finding": f"not run: {error}"})
    try:
        for case in CASES:
            records.append(check_flashmap(case, tmp_path))
            records.append(check_pipeline(case, tmp_path))
            if runner is not None:
                records.append(check_app(runner, case))
    finally:
        if runner is not None:
            runner.__exit__(None, None, None)

    findings = [record for record in records if "finding" in record]
    by_reader: dict[str, dict] = {}
    for record in records:
        entry = by_reader.setdefault(
            record["reader"], {"cases": 0, "rejected": 0, "accepted": 0, "findings": 0}
        )
        entry["cases"] += 1
        if record.get("verdict") == "rejected":
            entry["rejected"] += 1
        elif record.get("verdict") == "accepted":
            entry["accepted"] += 1
        if "finding" in record:
            entry["findings"] += 1

    return {
        "statement": (
            "Every case in eval/fuzz_corpus, through each of the three readers that open a "
            "flash map. Fail closed means the map is refused and the picture stays hidden, "
            "or the map is accepted and every span it flags is hidden. A reader that throws "
            "is a finding, because it has said nothing about whether the picture is safe."
        ),
        "tool": "eval/fuzz_maps_test.py",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "corpus": str(CORPUS.relative_to(REPO)),
        "totals": {
            "cases": len(CASES),
            "readers": len(by_reader),
            "checks": len(records),
            "findings": len(findings),
        },
        "by_reader": by_reader,
        "findings": findings,
        "records": records,
    }


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as work:
        report = run_everything(Path(work))
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['totals']['checks']} checks, {report['totals']['findings']} finding(s)")
    for finding in report["findings"]:
        print(f"  {finding['reader']}/{finding['case']}: {finding['finding']}")
    print(f"written to {RESULT}")
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
