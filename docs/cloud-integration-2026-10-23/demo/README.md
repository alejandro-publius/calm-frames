# A place to return to

An unsubmitted production package draft, October 23, 2026. Media production is deferred until the product candidate is finished, selected and validated. Reconcile this story with that accepted build before generating manga, narration or a final video. The plan is 2:50 including credits, with a continuous 70-second native ambient excerpt. These are editorial targets, not measured output durations. Rowan is a fictional adult character, not an interviewed user or an efficacy claim.

Ready now:

- [Claude assembly-only handoff](CLAUDE_ASSEMBLY.md) and [exact narration-only text](narration-only.txt). The integration owner retains product decisions; Claude's delegated scope is demo assembly and ElevenLabs narration after product gates permit production.
- [Narration and storyboard](STORYBOARD.md), [five-image prompt](IMAGE_PROMPT.md), and [narration production plan](ELEVENLABS_PLAN.md).
- [Asset inventory](asset-manifest.json), with hashes of existing native references and explicit missing inputs.
- [Render plan](timeline.json), [renderer](render_demo.py), [focused checks](test_render_preflight.py) and [draft subtitles](captions.draft.srt).
- [Presentation drafts and architecture](../PRESENTATION_DRAFTS.md).

## Missing inputs, in one bundle

1. Actual Blackbox reference frames. Devpost and YouTube access is blocked in this executor; no match to Blackbox's visual style is claimed.
2. Five finished illustrations from the prompt, with provenance and review. No images have been generated here.
3. App-window recordings of the selected production source: Home, Details/Watch, uninterrupted McWay playback, leave/return/Resume, and Playback Proof. Include raw-take hashes, source/package identity, capture scope and edit ledger. Exclude PIN entry, desktop, microphone and Retry harness UI. The current plan targets application source 12125b2970342b5376b0bc7964383e547b407376; a different selected source requires reconciling the plan and evidence first.
4. A usable ElevenLabs secure binding and an available built-in voice, selected after product acceptance. The owner approved the exact current script, authorized selection of a calm built-in voice and explicitly authorized an unlimited budget. No further budget approval is pending. Keep generation to the eight planned cues with no automatic retries. Reapprove the script only if product reconciliation changes its text. No voice ID has been selected and no paid generation has occurred.

The [older replacement demo receipt](../../../results/replacement-demo-2026-10-22/demo.json) identifies source d96c088 and an MP4 outside Git. It cannot demonstrate current recovery/profile work. Preserve that file and the submitted baseline video. The existing native screenshots in the inventory are planning references, not substitutes for missing motion footage.

## Render when inputs arrive

After product acceptance and story reconciliation, copy timeline.json to a private working directory outside the repository. Fill each missing asset's absolute path, SHA256 and provenance from actual files and receipts. The recorded narration approval covers only the exact narration-cues.json hash; it does not approve unseen audio or the final video. Each spoken cue is a separate measured audio file, leaving silence between cues.

For native takes, also supply the selected installed package hash and a hashed JSON capture receipt whose source_commit, package_sha256, raw_take_sha256, capture_scope and production_capture fields match the actual take. Capture scope must be app_window_and_app_audio_only and production_capture must be true. Normalize those fields from the actual session owner's record, preserving its original evidence; do not invent a capture receipt to satisfy the checker.

    python3 docs/cloud-integration-2026-10-23/demo/render_demo.py \
      --manifest /absolute/path/to/completed-timeline.json --check-only
    python3 docs/cloud-integration-2026-10-23/demo/render_demo.py \
      --manifest /absolute/path/to/completed-timeline.json \
      --outdir /absolute/path/to/new-demo-output --render

The output directory must be new and outside the repository. The script writes a review MP4, measured-cue SRT and exact-input/output receipt. It does not publish, install, sign, change prepared media or call ElevenLabs. It preserves natural-speed footage and letterboxes instead of cropping controls. Illustrations stay still; there are no zooms, loops, flashing transitions or added music.

Preflight and refusal behavior were exercised with metadata/text fixtures. The real encoding path has not run because its assets and approvals are missing. No MP4, audio, output checksum or human acceptance is claimed from these checks.

Captions are a sidecar, not burned-in text. Required story/source labels and closing credits are included in that sidecar. Verify the intended player's subtitle display or arrange a separately reviewed burned-in pass. Do not claim captions are visible merely because the file exists.

## Acceptance

After rendering, run a full decode, the existing video gate, duration and caption checks against the exact MP4. Then inspect frames and listen/watch the full file at natural speed. Technical results do not establish human comfort, palette or full-video acceptance. Do not conceal a native transition defect with an undisclosed edit. Exact native compositor/decoder ordering remains an evidence gap.

The stated editing cutoff is October 23 at noon Pacific (19:00 UTC), not newly verified from official rules here. Keep incomplete work isolated and unsubmitted. A replacement needs exact-artifact validation, a permitted editing window and specific publication authorization.
