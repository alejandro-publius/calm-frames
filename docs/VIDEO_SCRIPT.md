# English demo script

The finished local cut is `build/submission/Calm-Frames-demo-English.mp4`.
It uses actual Vega Virtual Device footage, disclosed native still captures,
and editorial brand/status cards. Narration is macOS Samantha text to speech,
in English, with burned-in subtitles and a companion SRT. No human voice,
customer feedback, medical outcome or physical-device measurement is implied.

The current encoded duration and hash are in
`results/demo_manifest_2026-10-10.json`; `results/video_check.json` records the
finished-file duration and WCAG gate. The broadcast profile also passes in
`results/video_check_broadcast.json`. The duration is strictly below three minutes.
The raw takes remain under `.logs/`; the review bundle preserves used sources.

## Exact narration and cut

| Start | Duration | Narration |
|---|---|---|
| 0:00 | 6 s | Calm Frames. A calmer way to watch. |
| 0:06 | 10 s | This accessibility prototype is running on the Vega Virtual Device. Its shelf contains checked, packaged videos. |
| 0:16 | 12 s | Harbor is original, non-flashing media. This practice title uses two scheduled holds to demonstrate scene continuity. The intervals are synthetic, not detected flashing. |
| 0:28 | 25 s | Watch the practice holds. The recorded tone and English captions continue while a calm scene is held. |
| 0:53 | 20 s | Here the remote seeks forward and backward, pauses, and resumes. The player uses an opaque fallback when playback is disrupted. This is behavior, not a screen timing measurement. |
| 1:13 | 8 s | A parent PIN protects settings. Wrong entries stay locked, and a partial entry can be corrected with Delete. |
| 1:21 | 10 s | Parents choose Standard, Broadcast, or Extra cautious. Stricter choices cannot relax the household floor. Each prepared preset was played in the simulator. |
| 1:31 | 12 s | Room settings, the selected profile, and the chime switch survive restart. Practice holds are excluded from exposure history. Actual cover history is kept in memory. |
| 1:43 | 19 s | This separate Harbor title went through real local preparation, with no synthetic detector intervals. The app plays the verified rendition compiled into its catalog. This source had no detected flashing. |
| 2:02 | 18 s | The saved AWS run published a signed title, but this app consumes its local library. Detection can miss flashing. Calm Frames is not a medical device. Dependency security findings remain open. |
| 2:20 | 6 s | Calm Frames. A calmer way to watch. |

## Reproduce and publish

Run `.venv/bin/python eval/assemble_demo.py` on this Mac with FFmpeg, Pillow,
the source captures and the Samantha voice installed. Then run
`bash eval/check_video.sh build/submission/Calm-Frames-demo-English.mp4 --max-seconds 179`.
The editor checks each narration length, preserves native audio with disclosed
level gain, and records all source hashes. It never synthesizes app footage.

The prototype is a compiled local library. The saved AWS run is separate.
Detection misses are disclosed, live overlay timing is not guaranteed, and
open dependency security findings remain visible. Practice intervals are
synthetic and labelled. Practice does not create exposure-history entries.

The public video URL and logged-out viewing check remain pending publication.
