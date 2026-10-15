# Demo video: narration and shot plan

A plan for a 2:40 English video of the real app on the Vega Virtual Device.
Written Oct 14, 2026; nothing has been recorded or captured for it, and
recording is not yet authorized: it waits for the final visual approval, the
final release selection and native validation. The rules
ask for a video under three minutes that shows the project running on an actual
Fire TV device or the Fire TV/Vega simulator, public on YouTube or Vimeo, with
no third-party trademarks or copyrighted music.

The value shows first, then the whole core journey, then the technical
contribution. Native shots use the exact build that becomes the judged release;
the screen labels below are the Home and Details copy on the final candidate
`claude/final-candidate-2026-10-14` (package source `ac5a610`), and must be
re-read against the build that is actually recorded.

**Placeholders.** `[UNVERIFIED]` marks behavior nobody has observed on the
current build. Record it only if the native session confirms it; otherwise cut
the shot or use a labelled still from the receipt named. Never narrate a claim
the recording does not show.

## Shot plan

| Start | Length | Picture | Narration |
|---|---|---|---|
| 0:00 | 8 s | Cold open, native capture: a practice hold in progress. The calm still is held, the "Holding a calm scene" card is up, an English caption changes, the sound continues. No title yet. | This is Calm Frames holding a scene on the Fire TV simulator. The picture waits on a calm still. The sound and the captions keep going. |
| 0:08 | 6 s | Editorial card: the approved brand tile, `docs/brand/firetv-app-icon-1280x720.png`. | Calm Frames is a verified safety layer for families with photosensitive epilepsy. It reduces exposure to flashing above published limits in the videos it plays. It is not a medical device. |
| 0:14 | 12 s | Home, native, real D-pad presses: focus moves across Play, Details, Try picture holds, then up to Settings and Help. Keep the whole screen in frame, including "20 sec · No picture holds" and "Picture holds on supported videos. Audio continues." | Everything runs on Vega OS with the remote. The library is small on purpose: every title here was analyzed frame by frame before it could be chosen. |
| 0:26 | 10 s | Details of the practice demo: "20 sec · 2 practice holds", the picture timeline, the viewing settings line, focus on Play. | The practice demo is the same short film with two scheduled holds, so you can see the player work. They are examples, not detected flashing. Harbor itself has nothing above the limits. |
| 0:36 | 30 s | One continuous native take from Play: the "Practice hold coming up" countdown with Skip, the first hold with the calm still (the final candidate reported it loading at both holds) and changing captions, the gap, the second hold. Narration stops after ten seconds; leave the film's sound audible. | Before a hold, a countdown and a Skip. Then the picture holds on a checked still from just before, and the story carries on in sound and captions. |
| 1:06 | 14 s | Transport on the same title: pause, resume, then a seek back into a hold. Step the capture frame by frame afterwards: the cover must be on screen before the film moves. `[Pause, resume and Back were reported by the final candidate on the device (results/native-acceptance-2026-10-14/receipt.json); seeking by remote was not established there and the cover-first seek is covered by tests: keep this shot only if the recording session sees it]` | Every way of moving the playhead goes through one guarded function. Seek into a hold, and the cover is there before the picture moves. |
| 1:20 | 10 s | Back to Home with visible return focus, then Play on Harbor: it plays through with captions and no hold. | Back returns to where you were. The ordinary Harbor went through the same pipeline and came out with zero holds, so it simply plays. |
| 1:30 | 16 s | Settings (the parental controls): the PIN gate, a wrong PIN rejected with the tries remaining, Delete, the correct PIN. Then the settings: profile, viewing preset, television size and distance, chime, with motion and sounds Off. Use a test household created for the recording; never show or speak a real PIN. `[The PIN gate opened and Back returned on the final candidate; the settings interior is still unobserved on any Oct 13 or 14 build because the test household's PIN was not entered. Observed on the Oct 10 build, results/redesign_validation_2026-10-10.json]` | Parents set the viewing preset and the room behind a PIN. A child's profile can make the choices stricter, never looser. |
| 1:46 | 8 s | Help, from the Home header: the plain-language page with the supported-titles line and the detection limit. | Help says the limits out loud: supported titles only, and detection can miss flashing. |
| 1:54 | 22 s | Terminal, large type, no desktop visible: `python -m flashmap check harbor.mp4 --profile wcag` returning exit code 0, then `python -m flashmap verify` of the signed map, then the Action file `flashmap/examples/flash-check.yml` and the first screen of `hook/README.md`. Use the benign Harbor source only. | Underneath is flashmap, an open source analyzer for the published flash limits. It signs a map bound to the file's hash, and the player refuses a map it cannot verify. The same check runs as a GitHub Action on every pull request, and a drop-in hook gives any Vega video app the same guard. |
| 2:16 | 12 s | Editorial card from the Oct 9 AWS record: the unsigned clip refused, the signed clip published through S3, Fargate, DynamoDB and CloudFront. Text only; no account identifiers. | On AWS, a CDK stack runs the same pipeline. An unsigned clip was refused; a signed one was published. The TV app itself plays only the library compiled into it. |
| 2:28 | 8 s | Editorial limits card: "Detection can miss flashing. Simulator observations, not a television measurement. Not a medical device." | Detection can miss flashing, and these are simulator observations, not a television measurement. Calm Frames is not a medical device. |
| 2:36 | 4 s | Closing card: the mark and "A calmer way to watch". | A calmer way to watch. |

Total 2:40. About 330 narrated words at a calm pace, with 20 seconds of the
hold take left to the film's own sound.

## Recording rules

- Vega Virtual Device only, bundled benign media only. No file with the
  `HAZARD_` prefix is ever opened; the terminal shot uses the Harbor source.
- Capture with the existing window recorder (`eval/record_vega_window.m`, built to
  `build/finish-tools/calm-record-window`), which records the composited picture
  and native audio. It emits frames only when the window changes, so the quiet
  stretch of the Harbor play-through may need a labelled still
  ([../MAC_FINISH.md](../MAC_FINISH.md) section 4).
- Fill the capture manifest from `eval/assemble_demo.py --write-template` with
  the exact source commit, the installed package hash and every capture's hash,
  assemble, then run `eval/check_video.sh` under both profiles with
  `--max-seconds 179`. The finished file must pass both.
- Narration: the earlier cut used macOS synthetic speech, disclosed on screen.
  Keep the disclosure if that voice is used again, or record a human voice.
- Nothing from another service appears: no desktop, no browser chrome, no logos
  other than the project's own mark and the simulator the rules require.
- Label editorial cards and stills as such. Label the practice holds as
  scheduled examples.

## Claims that must stay out

No "prevents seizures", "seizure-proof" or any medical guarantee. No claim that
other streaming apps or DRM content are filtered. No "original story" or
"a Calm Frames original" labels. No timing number: the simulator does not
measure a television.
