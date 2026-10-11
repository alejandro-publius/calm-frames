# English demo script

Finished local cut: `build/submission-redesign/Calm-Frames-demo-English.mp4`.
Actual Vega Virtual Device recordings and disclosed still captures, with editorial
brand/status cards. Narration is macOS Samantha text to speech in English.
Burned-in subtitles and a companion SRT are included. No human voice, customer
feedback, medical outcome or physical-device measurement is implied.

The 2:10 narration below is the approved sentence. The recorded cut named above
still carries the earlier sentence, as `results/redesign_demo_manifest_2026-10-10.json`
records, so it has to be re-rendered (`eval/assemble_demo.py`, then
`eval/check_video.sh` for wcag and broadcast, then the manifest) before it is
uploaded. That re-render rides the Mac rebuild on the Oct 11 list.

Encoded duration and hash: `results/redesign_demo_manifest_2026-10-10.json`.
Finished-file gates: `results/redesign_video_check.json` and
`results/redesign_video_check_broadcast.json`.

## Exact narration and cut

| Start | Duration | Narration |
|---|---|---|
| 0:00 | 6 s | Calm Frames. A calmer way to watch. |
| 0:06 | 10 s | Calm Frames is running on the Vega Virtual Device. This redesigned library contains the checked videos packaged with the app. |
| 0:16 | 12 s | Harbor is original, non-flashing media. The scene hold demo adds two scheduled holds. These are examples, not detected flashing. |
| 0:28 | 26 s | Watch the scheduled holds. The recorded tone and English captions continue while the picture holds a calm scene. |
| 0:54 | 22 s | The remote seeks, pauses, and resumes. Interrupted playback uses an opaque cover. This demonstrates behavior, not physical screen timing. |
| 1:16 | 9 s | A PIN protects parental controls. Incorrect entries stay locked, and Delete corrects a partial entry. |
| 1:25 | 12 s | Parents choose Standard, Broadcast, or Extra cautious. Each choice was tested in Vega. A child cannot relax the settings chosen for everyone. |
| 1:37 | 12 s | Settings survive restart. Scheduled demo holds are excluded from exposure history. Actual cover history is not saved across app restarts. |
| 1:49 | 21 s | This separate Harbor title uses real local preparation without the demonstration holds. The app plays its checked, packaged rendition. The source had no detected flashing. |
| 2:10 | 20 s | The saved AWS run published a signed title. The app uses its local library. Detection can miss flashing. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device. |
| 2:30 | 6 s | Calm Frames. A calmer way to watch. |

## Reproduce and publish

Run `.venv/bin/python eval/assemble_demo.py` on this Mac with FFmpeg, Pillow,
the recorded sources and Samantha installed. The assembler checks narration
length, retains native audio with disclosed gain and hashes every source.
Run `bash eval/check_video.sh build/submission-redesign/Calm-Frames-demo-English.mp4
--max-seconds 179 --out results/redesign_video_check.json` as one command; repeat
with `--profile broadcast` and the broadcast output path.

The app uses a compiled local library. Saved AWS publication is a separate
pipeline. Detection misses and unresolved dependency security findings are
stated. Practice holds are synthetic and excluded from exposure history.
Public upload, the video URL and logged-out viewing check remain pending.
