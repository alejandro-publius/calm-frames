# English demo script and recording plan

**Superseded.** The canonical demo script is
[submission/DEMO_RUN_OF_SHOW.md](submission/DEMO_RUN_OF_SHOW.md), about 90
seconds, for installed source `9cc57ca`. This October 13 plan is kept as a
record. Do not record from it.

This is the next recording plan for the current cinematic design. It is a plan,
not a claim that a new native video exists. The October 10 cut and its exact
narration remain preserved in `results/redesign_demo_manifest_2026-10-10.json`
and [SHOT_MANIFEST.md](SHOT_MANIFEST.md). Do not replace their source identities.

The story follows a family's viewing journey: choose a title, understand its
practice holds, keep the sound and captions going, then show the parent and
preparation controls behind the experience. The first app shot should show
actual D-pad interaction. Use the original non-flashing Harbor media throughout.

## Next recording plan

The target is 2:36, leaving room below the required three-minute limit. These
are planned edit lengths; the assembled file is measured separately. The exact
narration is also the default in `eval/assemble_demo.py`. Review each claim
against the fresh native observations before filling the capture manifest.

| Start | Length | Picture to record | Narration |
|---|---|---|---|
| 0:00 | 6 s | Editorial opening using the approved Calm Frames brand tile. | Calm Frames helps families affected by photosensitivity share a calmer movie night. |
| 0:06 | 10 s | Record real D-pad focus across Watch now, More info and the Harbor demo shelf card. Keep the full library in view. | On the Vega Virtual Device, families browse checked titles with a remote. The quiet library opens directly into a story. |
| 0:16 | 12 s | Open Harbor demo, show the Practice holds label and the picture timeline, then focus Watch demo. | Harbor is our original, non-flashing demo film. Two scheduled practice holds show the player in action. These are examples, not detected flashing. |
| 0:28 | 26 s | One continuous native take containing both practice holds, changing English captions and the recorded tone. Leave the un-narrated remainder audible. | When the picture holds a checked still, the recorded tone and English captions continue. Watch both scheduled holds, without showing hazardous footage. |
| 0:54 | 22 s | Record pause, resume, forward/back seek and the opaque interruption fallback. Preserve the real action order. | Every seek passes through the same guard. Pause, skip or go back with the remote; interrupted playback keeps an opaque cover in place. |
| 1:16 | 9 s | Use a synthetic test household to show a wrong PIN, Delete and correction. Record the actual remote interaction. | Parental controls stay behind a PIN. A clear Delete action makes corrections easy. |
| 1:25 | 12 s | Show the viewing preset, room and separate motion/sound settings. Capture enabled effects separately for acceptance before featuring them. | Parents choose the viewing preset and room. Child profiles can only make settings stricter. Gentle artwork motion and selection sounds are optional. |
| 1:37 | 12 s | An actual native still of the observed history state. Separately observe restart persistence; never imply this still demonstrates a restart. | The household choices stay saved after restarting. Practice holds never enter exposure history, and actual cover history clears when the app restarts. |
| 1:49 | 21 s | Play the prepared Harbor title, which has no practice holds, after its checked details page. | This version of Harbor went through the real preparation pipeline. Its signed map is checked before playback; the rendition is packaged with the app. |
| 2:10 | 20 s | Editorial status card: saved AWS publication is separate from the app's local library; include detection limits and the approved medical-device wording. | AWS has also published a signed title through a separate cloud pipeline. Detection can miss flashing. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device. |
| 2:30 | 6 s | Editorial closing using the approved mark and brand line. Mention the reusable analyzer and hook. | A reusable analyzer and player hook, built for calmer family viewing. |

## Presentation

The assembler uses the app's bundled Inter fonts, teal background, cream
subtitles and saffron capture labels. It fits the complete source image above
a dedicated subtitle area, preserving the bottom of the app and its own
captions. Narration appears in short cues of at most two measured lines, then
clears so the native footage can carry the scene. The companion SRT uses the
same cues. Cue timing is estimated from spoken word share and the measured
narration length; check it against the actual voice before publication.

Narration is disclosed as macOS Samantha synthetic speech. Native audio is mixed
at its captured level through a peak limiter, with no automatic boost. Listen to
the complete result: a limiter is not proof that the film tone, menu sounds and
narration are all intelligible. Keep the longer holds/transport shots quiet after
the voice finishes so a judge can hear what the player does.

Actual stills, native recordings and editorial cards remain visibly labelled.
The Harbor practice holds are scheduled examples, not detector findings. The
saved AWS publication is a separate pipeline; the app uses its local packaged
library. This recording does not measure physical television timing.

## Assemble the matching cut

Follow [MAC_FINISH.md](MAC_FINISH.md) for the current build and native capture.
Generate a fresh, unfilled plan:

```sh
.venv/bin/python eval/assemble_demo.py --write-template .logs/final-capture-plan.json
```

Supply the full source commit, installed package hash, actual capture files and
their hashes. Use fresh output paths. Run `--dry-run`, assemble on the Mac, then
run `eval/check_video.sh` under both WCAG and broadcast with `--max-seconds 179`.
Check the finished audio, subtitle timing, source framing and every narration
claim. Preserve the finished-video checks and the new source manifest.

Browser previews can illustrate the design in the project gallery, clearly
labelled as previews. They cannot replace the native footage required by the
Fire TV track. Publication, the final video URL and logged-out viewing remain
separate steps after the matched recording is ready.
