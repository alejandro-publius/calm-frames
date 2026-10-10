# Recorded demo shot manifest

The definitive machine-readable manifest is
`results/demo_manifest_2026-10-10.json`, including every source SHA-256,
source offset, output duration, narration and edit. These are completed local
captures, not planned footage. English synthetic narration is disclosed in
VIDEO_SCRIPT.md. No person appears in the recordings.

| Shot | Output start | Source | Type |
|---|---|---|---|
| 1 | 0 s | `docs/brand/firetv-app-icon-1280x720.png` | Editorial card |
| 2 | 6 s | `.logs/native-final-shelf.png` | Actual simulator still |
| 3 | 16 s | `.logs/native-practice-before-seek.png` | Actual simulator still |
| 4 | 28 s | `.logs/native-reviewed-harbor.mp4` | Actual simulator video with recorded audio |
| 5 | 53 s | `.logs/native-guarded-transport.mp4` | Actual simulator video with recorded audio |
| 6 | 73 s | `.logs/native-credits-return.png` | Actual simulator still |
| 7 | 81 s | `.logs/native-extra-selected2.png` | Actual simulator still |
| 8 | 91 s | `.logs/native-kid-history-visible.png` | Actual simulator still |
| 9 | 103 s | `.logs/native-broadcast-play.mp4` | Actual simulator video with recorded audio |
| 10 | 122 s | `build/submission/status-card.png` | Editorial card |
| 11 | 140 s | `docs/brand/firetv-app-icon-1280x720.png` | Editorial card |

## Observation scope

The continuous practice take shows both scheduled holds and their changing
English captions. The transport take shows real remote input effects, including
opaque fallback on interrupted playback. Prepared Harbor uses the checked local
rendition and has no detected flashing. It is distinct from practice Harbor.
Settings and PIN shots are clearly disclosed still captures of the actual app;
restart and correction were observed separately, not fabricated in the cut.

Native observations and package provenance are recorded in
`results/native_validation_2026-10-10.json`. Earlier captures precede only the
final exit-navigation cleanup; the final continuous Harbor take is recaptured
on the reviewed package. No claim that all older takes used the final package.

ScreenCaptureKit records the composited window and audio. The helper activates
Vega before capturing because background Stage Manager thumbnails can return
stale GPU frames. Do not take screenshots while a recording is running.

Review: native pictures, both holds, captions, brand readability and all footer
text were inspected in extracted frames. The English audio is synthesized from
the script; final audio levels and the complete video check are preserved.
Public upload and logged-out link verification remain pending.
