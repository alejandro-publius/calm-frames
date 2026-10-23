"""Actual export/reproduction of benign test media with labelled sham intervals.

No shipped source, approval or signer is changed. The existing ephemeral test
key fixture signs generated maps. Real encoders, analyzers and export checks run.
"""
from __future__ import annotations

import json

import pytest

from pipeline import PipelineError, ambient_export, ffmpegtool
from pipeline.ambient import prepare_ambient_candidate
from pipeline.hashing import sha256_file
from pipeline.local_library import prepare_local_title
from pipeline.packaged_library import check_packaged_library, export_packaged_library

from .clips import make_calm_clip
from .conftest import needs_ffmpeg
from .test_app_playback_recipe import RealAnalyzerWithShamProfileUnion


@needs_ffmpeg
def test_real_export_reproduces_all_presets_and_rejects_substitutions(tmp_path, keypair, monkeypatch):
    private, public = keypair
    source = make_calm_clip(tmp_path / "benign-sham-source.mp4", seconds=8, fps=10,
                            width=160, height=90)
    work = tmp_path / "prepared"
    receipt = prepare_local_title(source, work, key=private, pub=public,
                                  title="Synthetic ambient export test",
                                  adapter=RealAnalyzerWithShamProfileUnion(source, private))
    assert receipt["status"] == "ready", receipt
    original = tmp_path / "original-package"
    manifest = export_packaged_library(work, original, pub=public)
    bundle = original / manifest["bundleId"]
    manifest_path = bundle / "manifest.json"
    title = manifest["titles"][0]
    maps = {p: bundle / title["maps"][p]["path"] for p in ("wcag", "broadcast")}
    ambient = tmp_path / "benign-ambient.mp4"
    ffmpegtool.run_ffmpeg(["-i", str(source), "-map", "0:v:0", "-c:v", "copy", "-an", str(ambient)])
    candidates = {p: tmp_path / f"candidate-{p}" for p in ambient_export.PRESETS}
    attribution = "Generated benign test media; sham source intervals are not detector findings."
    for p, out in candidates.items():
        prepare_ambient_candidate(source, ambient, maps=maps, preset=p, out_dir=out, attribution=attribution)

    def run(name, **changes):
        args = dict(source=source, ambient=ambient, source_manifest=manifest_path,
                    candidates=candidates, output=tmp_path / name,
                    verification_dir=tmp_path / f"verify-{name}", attribution=attribution)
        return ambient_export.export_ambient_catalog(**(args | changes))

    with pytest.raises(PipelineError, match="three candidate"):
        run("missing", candidates={"wcag": candidates["wcag"]})
    wrong = tmp_path / "wrong-source.mp4"
    wrong.write_bytes(b"not the authenticated source")
    with pytest.raises(PipelineError, match="actual source differs"):
        run("wrong-source", source=wrong)
    proposed = candidates["wcag"] / "candidate.mp4"
    before = proposed.read_bytes()
    proposed.write_bytes(before + b"tampered")
    with pytest.raises(PipelineError, match="metadata or media changed"):
        run("tampered")
    proposed.write_bytes(before)

    prepare = ambient_export.prepare_ambient_candidate
    def different_reproduction(*args, **kwargs):
        result = prepare(*args, **kwargs)
        out = kwargs["out_dir"] / "candidate.mp4"
        out.write_bytes(out.read_bytes() + b"different reproduction")
        return result
    with monkeypatch.context() as patch:
        patch.setattr(ambient_export, "prepare_ambient_candidate", different_reproduction)
        with pytest.raises(PipelineError, match="reproduction differs"):
            run("different")
    assert not (tmp_path / "different").exists()

    result = run("export")
    assert result["approved"] is False and result["existingSigner"] is True
    checked = check_packaged_library(tmp_path / "export", require_reports=True)
    assert checked["bundleId"] == result["bundleId"] != manifest["bundleId"]
    assert checked["publicKeyBase64"] == manifest["publicKeyBase64"]
    exported_title = checked["titles"][0]
    assert exported_title["sourceSha256"] == title["sourceSha256"]
    assert exported_title["maps"] == title["maps"]
    for p in candidates:
        assert exported_title["renditions"][p]["sha256"] == sha256_file(candidates[p] / "candidate.mp4")
    report = json.loads((tmp_path / "export/reports" / f"{result['reportSha256']}.json").read_text())
    assert all(proof["timingAudio"]["sourceEqualsOutput"] for proof in report["presets"].values())
    assert not list((tmp_path / "export").rglob("*.pem"))
    with pytest.raises(PipelineError, match="new export"):
        run("export")
