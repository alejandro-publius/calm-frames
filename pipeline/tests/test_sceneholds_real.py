"""Real CLI integration on benign media with explicitly labelled sham hides.

The source analyzer must actually read the generated calm clip and find no
violations before this test seeds two sham source intervals. Every image,
complete rendition, HLS output, cover model and signature check still goes
through the actual flashmap CLI. This is presentation integration evidence,
not evidence about detector recall or a physical screen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence

from pipeline.ffmpegtool import run_ffmpeg
from pipeline.flashmap_adapter import (
    CommandResult,
    FlashmapAdapter,
    FlashMapDoc,
    load_map,
)
from pipeline.ingest import IngestOptions, ingest_title
from pipeline.probe import probe_video
from pipeline.registry import load_private_key, sign_document, write_registry
from pipeline.sceneholds import read_scene_holds

from .clips import make_calm_clip
from .conftest import needs_ffmpeg


class RealAnalyzerWithLabelledShamSourceHides(FlashmapAdapter):
    """Only source intervals are sham; all measurement commands are real."""

    def __init__(self, source: Path, private_key: Path) -> None:
        # An explicit command cannot inherit the fake-analyzer environment
        # override used by the separate pipeline unit tests.
        super().__init__(command=[sys.executable, "-m", "flashmap"])
        self.source = source.resolve()
        self.private_key = private_key
        self.commands: list[tuple[list[str], int]] = []
        self.measured_source_was_clean = False

    def _run(
        self, args: Sequence[str], *, timeout_s: float | None = None
    ) -> CommandResult:
        result = super()._run(args, timeout_s=timeout_s)
        self.commands.append(([str(arg) for arg in args], result.returncode))
        return result

    def analyze(self, video: str | Path, **kwargs) -> FlashMapDoc:
        measured = super().analyze(video, **kwargs)
        if Path(video).resolve() != self.source:
            return measured

        assert measured.is_clean, "the benign test source unexpectedly has violations"
        assert measured.raw["generator"]["name"] == "flashmap"
        self.measured_source_was_clean = True
        document = dict(measured.raw)
        document["test_sham_intervals"] = {
            "label": "Sham source hides for scene-hold integration, not measured findings",
            "original_measured_segment_count": measured.violation_count,
        }
        document["segments"] = [
            {"start_ms": 0, "end_ms": 500, "reason": "red"},
            {"start_ms": 4500, "end_ms": 5000, "reason": "general"},
        ]
        document["summary"] = {
            **document["summary"],
            "pass": False,
            "flash_pass": False,
            "segment_count": 2,
            "general_segment_count": 1,
            "red_segment_count": 1,
            "hidden_ms": 1000,
        }
        output = Path(kwargs["out_path"])
        write_registry(sign_document(document, load_private_key(self.private_key)), output)
        sham = load_map(output)
        sham.preset = kwargs["profile"]
        return sham


@needs_ffmpeg
def test_real_cli_checks_sham_hides_with_neutral_and_preceding_context(tmp_path, keypair):
    private_key, public_key = keypair
    source = make_calm_clip(
        tmp_path / "benign_story_sham_hides.mp4",
        seconds=7,
        fps=10,
        width=160,
        height=90,
        subtitles=True,
    )
    analyzer = RealAnalyzerWithLabelledShamSourceHides(source, private_key)
    result = ingest_title(
        source,
        tmp_path / "out",
        IngestOptions(
            presets=["wcag"],
            key=str(private_key),
            pub=str(public_key),
            x264_preset="ultrafast",
            poster_count=1,
            bif_interval_ms=3000,
        ),
        adapter=analyzer,
    )

    assert analyzer.measured_source_was_clean
    assert result.verify_passed, result.verify_report
    assert result.publishable
    document = json.loads(result.layout.map_path("wcag").read_text())
    assert document["test_sham_intervals"]["original_measured_segment_count"] == 0
    holds = read_scene_holds(result.layout, "wcag")
    assert [(hold.start_ms, hold.end_ms) for hold in holds] == [(0, 1000), (4000, 5500)]
    assert holds[0].frame_ms is None
    assert holds[0].origin == "neutral"
    assert holds[1].frame_ms is not None
    assert 2000 <= holds[1].frame_ms < holds[1].start_ms
    assert holds[1].origin == "source"
    assert holds[0].sha256 != holds[1].sha256

    prepared = probe_video(result.layout.safe_master("wcag"))
    assert prepared.has_audio
    assert prepared.has_subtitles
    subtitle_arguments = ["-map", "0:s:0", "-f", "webvtt", "-"]
    source_captions = run_ffmpeg(["-i", str(source), *subtitle_arguments]).stdout
    prepared_captions = run_ffmpeg([
        "-i", str(result.layout.safe_master("wcag")), *subtitle_arguments
    ]).stdout
    assert source_captions == prepared_captions
    assert "still talking" in prepared_captions
    delivered_captions = "\n".join(
        path.read_text() for path in result.layout.hls_dir("wcag").glob("*.vtt")
    )
    assert "hello from the caption track" in delivered_captions
    assert "still talking" in delivered_captions

    checks = {check["name"]: check["passed"] for check in result.verify_report["checks"]}
    expected_checks = {
        "map_signature:wcag",
        "scene_assets:wcag",
        "safe_rendition_clean:wcag",
        "rendition_matches_source:wcag",
        "cover_actually_drawn:wcag",
        "cover_model_clean:wcag",
        "scene_model_drawn:wcag",
        "hls_rendition_clean:wcag",
        "hls_timing_matches_master:wcag",
        "scene_hls_drawn:wcag",
        "scene_output_patterns:safe:wcag",
        "scene_output_patterns:model:wcag",
        "scene_output_patterns:hls:wcag",
    }
    assert expected_checks <= checks.keys()
    assert all(checks[name] for name in expected_checks)

    # Pin real command coverage rather than accepting a successful verdict
    # whose JPEG, delivered HLS or output-resolution checks never executed.
    analyses = [args for args, _ in analyzer.commands if args[0] == "analyze"]
    for hold in holds:
        image_commands = [args for args in analyses if Path(args[1]).resolve() == hold.path.resolve()]
        assert len(image_commands) >= 2, "producer and verifier must both analyze the JPEG"
        assert all(args[args.index("--profile") + 1] == "broadcast" for args in image_commands)
    for output in (
        result.layout.safe_master("wcag"),
        result.layout.cover_model_path("wcag"),
        result.layout.master_playlist("wcag"),
    ):
        profiles = {
            args[args.index("--profile") + 1]
            for args in analyses
            if Path(args[1]).resolve() == output.resolve()
        }
        assert {"wcag", "broadcast"} <= profiles, str(output)
    signature_commands = [
        (args, code) for args, code in analyzer.commands if args[0] == "verify"
    ]
    assert signature_commands
    assert all(code == 0 for _, code in signature_commands)
    assert all(code == 0 for args, code in analyzer.commands if args[0] == "analyze")
