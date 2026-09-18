# Calm Frames

**A verified safety layer for Fire TV, for kids with photosensitive epilepsy.**

Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device.

---

## What it is

Calm Frames is a verified safety layer for kids with photosensitive epilepsy, and it is never a video player. Every frame of a title is checked before that title can play in kid mode, and the result is an Ed25519 signed flash map bound to the file's SHA-256. When a child plays the title, the player hides each flagged segment before it starts while the sound and the captions keep going, then says what was hidden. The layer adapts to the household, because a parent gives the TV size and the seat distance and picks a preset, and a household setting can only ever make it stricter than WCAG, never weaker. Voice, D-pad and on-screen cards all run through one seek function, so every path to a new playhead position is safe: if the target lands inside a flagged interval or its guard band, the picture is covered first and the seek happens second. Any Vega video app can add the same protection with a small hook, and any studio can check its own content before publishing with the open-source analyzer and its GitHub Action.

**Status, Sep 17 2026.** This is a build in progress for the Fire TV track of Build, Ship, Shape: Amazon Developer Hackathon. The analyzer, the pipeline, the cover layer and the measurement harnesses are built and tested. Nothing has been measured on a physical Fire TV stick yet, so there is no screen-level cover lead time. There is a software-level one from the virtual device, and one of its 49 trials covered late. Every number below says where it came from, and the rows with nothing in them are measurements that have not happened.

## Contents

- [How it fits together](#how-it-fits-together)
- [Required tech at runtime](#required-tech-at-runtime)
- [What has been measured](#what-has-been-measured)
- [Install and run](#install-and-run)
- [Limits](#limits)
- [Safety](#safety)
- [Licences and credits](#licences-and-credits)

## How it fits together

```
  a title arrives (upload, or a local file)
                 |
                 v
  +--------------------------------+          +--------------------------------+
  |  pipeline/                     |  frames  |  flashmap/  (Apache-2.0)       |
  |                                | -------> |                                |
  |  probe  -> analyze per preset  |          |  WCAG 2.2 SC 2.3.1             |
  |         -> hide plan           | <------- |  general flash + red flash     |
  |         -> kid-safe rendition  |   map    |  sliding 1 s window            |
  |         -> posters, trickplay  |          |  sliding 10 degree area window |
  |         -> sign (Ed25519)      |          |  letterbox and pillarbox aware |
  +---------------+----------------+          |  room rule: can only add hides |
                  |                           +--------------------------------+
                  v
        +--------------------+
        |  pipeline/verify   |   a title cannot be published until this passes
        +---------+----------+
                  |
        passes    |    refused: stays out of kid mode, with the reason recorded
                  v
  +-------------------------------------------+
  |  delivery: rendition + signed map          |
  |            + poster + trickplay            |
  +---------------------+---------------------+
                        |
                        v   signed map, bound to the file's SHA-256
  +----------------------------------------------------------------------+
  |  Fire TV (Vega OS) app                                                |
  |                                                                       |
  |   voice  ---+                                                         |
  |   D-pad  ---+--> one seek function: cover first, then seek            |
  |   card   ---+                                                         |
  |                                                                       |
  |   +---------------------------------------------------------------+   |
  |   |  KeplerCaptionsView        zIndex 2   captions stay readable   |   |
  |   |  CoverLayer                zIndex 1   the picture is hidden    |   |
  |   |  KeplerVideoSurfaceView    zIndex 0   the sound keeps going    |   |
  |   +---------------------------------------------------------------+   |
  |                                                                       |
  |   scheduler: a wall clock re-synced to media time, 500 ms guard band  |
  |   fail closed: missing, stale, unsigned, unparseable or wrong-hash    |
  |                map  ->  the picture stays hidden                      |
  +----------------------------------------------------------------------+

  Other Vega video apps add the same protection with a small hook.
  Studios check their own content in CI with the flashmap GitHub Action.
```

Two things in that picture are worth saying out loud.

**The cover is scheduled, not reacted to.** The player's own position reports are irregular. In the recorded run below, the longest gap between two of them was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms while the clip kept playing. Anything that waited for a position report before covering would have been that late. So the cover runs on a wall clock that is re-synced to media time at every report, and anything that makes the playhead uncertain, including a stall, a seek, a pause or the app going to the background, hides the picture at once instead of trusting the estimate.

**Verify is a gate, not a report.** `pipeline/verify.py` blocks publishing. A violation left in a rendition, a violation under the modelled cover, a tampered map, a wrong hash, or a poster taken from a flagged moment all fail it, and the title does not reach kid mode.

## Required tech at runtime

Every row links the exact file and line in this repository. Line numbers are against `main`; the symbol name is given too, so a moved line is still findable.

| Required technology | Package | Called at | What it does here |
|---|---|---|---|
| **W3C media player** | `@amazon-devices/react-native-w3cmedia` | [`app/src/utils/VideoHandler.ts:133`](app/src/utils/VideoHandler.ts#L133) `new VideoPlayer()`, imported at [`:3`](app/src/utils/VideoHandler.ts#L3); Shaka attached at [`:259`](app/src/utils/VideoHandler.ts#L259) | All playback. Calm Frames never replaces it and never lowers its opacity. It reads `currentTime`, `playbackRate` and the media events from it, and covers on top of it. |
| **W3C media player, video surface** | `@amazon-devices/react-native-w3cmedia` | [`app/src/screens/PlayerScreen.tsx:444`](app/src/screens/PlayerScreen.tsx#L444) `KeplerVideoSurfaceView`, imported at [`:17`](app/src/screens/PlayerScreen.tsx#L17) | The hardware video layer at zIndex 0. The cover sits above it, which is what keeps the sound running while the picture is hidden. |
| **Vega Media Controls** | `@amazon-devices/kepler-media-controls` | Focus set at [`app/src/utils/VideoHandler.ts:144`](app/src/utils/VideoHandler.ts#L144) `setMediaControlFocus(...)`. The safe handler is [`app/src/calmframes/SafeMediaControlHandler.ts:49`](app/src/calmframes/SafeMediaControlHandler.ts#L49), with `handleSeek` at [`:68`](app/src/calmframes/SafeMediaControlHandler.ts#L68) and `handleFastForward` at [`:89`](app/src/calmframes/SafeMediaControlHandler.ts#L89) | System and voice transport, and the path an Alexa "skip forward" arrives on. It can land the playhead inside a flagged interval without the remote being touched, so none of these handlers call `super`. Each one goes through [`app/src/calmframes/seekSafety.ts`](app/src/calmframes/seekSafety.ts), `planSeek` at [`:113`](app/src/calmframes/seekSafety.ts#L113). |
| **KeplerCaptionsView** | `@amazon-devices/react-native-w3cmedia` | [`app/src/screens/PlayerScreen.tsx:461`](app/src/screens/PlayerScreen.tsx#L461) the element; handle set at [`:416`](app/src/screens/PlayerScreen.tsx#L416) `setCaptionViewHandle` | Captions, at zIndex 2, above the cover. One captions view per process. This is the reason a hidden segment is still followable: the words carry on over a black picture. |
| **Accessibility APIs** | `react-native` `AccessibilityInfo`, plus the `com.amazon.devconf.privilege.accessibility` privilege at [`app/manifest.toml:91`](app/manifest.toml#L91) | [`app/src/calmframes/announce.ts:58`](app/src/calmframes/announce.ts#L58) `announceForAccessibilityWithOptions(message, { queue: true })`; the card carries `accessibilityLiveRegion="polite"` at [`app/src/calmframes/CalmCard.tsx:73`](app/src/calmframes/CalmCard.tsx#L73) and `accessibilityRole="alert"` at [`:74`](app/src/calmframes/CalmCard.tsx#L74); the cover is hidden from the tree at [`app/src/calmframes/CoverLayer.tsx:66`](app/src/calmframes/CoverLayer.tsx#L66) | VoiceView is told what is about to be hidden, and told it in a queue rather than by interrupting, because a child hearing "flashing part coming up" cut off halfway is worse than hearing it a beat later. The cover itself is taken out of the accessibility tree, so VoiceView never reads a black rectangle and focus never lands on it. |

The whole guard is one hook, [`app/src/calmframes/useFlashGuard.ts`](app/src/calmframes/useFlashGuard.ts). Give it a player and where the map is, and it verifies the map, builds the schedule, drives the cover, decides the card, announces it and hands back the one seek function every control has to use. It deliberately knows nothing about Calm Frames screens, navigation or storage, which is what makes it the thing another Vega app can drop in. Around it: the cover is [`app/src/calmframes/CoverLayer.tsx`](app/src/calmframes/CoverLayer.tsx), the scheduler is [`coverSchedule.ts`](app/src/calmframes/coverSchedule.ts) and [`mediaClock.ts`](app/src/calmframes/mediaClock.ts), the map check is [`flashMap.ts`](app/src/calmframes/flashMap.ts), the PIN is [`parentGate.ts`](app/src/calmframes/parentGate.ts) and the run harness is [`useCoverHarness.ts`](app/src/calmframes/useCoverHarness.ts).

Fail closed is the hook's starting state rather than an error path: `covered` begins true, and only a verified map turns it off.

**Device evidence.** Every run in this README posts its events to the machine that started it, because the device drops the app's console output under load. The raw event streams are committed: [`results/vvd_timeupdate_stats_events.json`](results/vvd_timeupdate_stats_events.json) and [`results/vvd_layering_rehearsal_events.json`](results/vvd_layering_rehearsal_events.json). Each line carries media time, wall-clock time and playback rate.

## What has been measured

Every number on this page is written as a marker that points at a file in [`results/`](results/). `python eval/readme_sync.py --check` fails if any of them drifts, and CI runs it on every push. A row with no number is a measurement that has not happened yet, and it is left empty on purpose.

### The app on a device

Recorded by `eval/vvd_smoke.py` into [`results/vvd_smoke.json`](results/vvd_smoke.json). **Vega Virtual Device, not the stick.**

| What | Value |
|---|---|
| Device build | <!--n results/vvd_smoke.json:device.build -->OS 1.2 (TV Ship/101520710)<!--/n--> |
| Package | <!--n results/vvd_smoke.json:package_id -->io.github.alejandropublius.calmframes<!--/n--> |
| Playback started events | <!--n results/vvd_smoke.json:playback_started_events -->2<!--/n--> |
| Seconds of play recorded | <!--n results/vvd_smoke.json:play_seconds -->40<!--/n--> |
| Segment fetches during play | <!--n results/vvd_smoke.json:segment_fetches_during_play -->8<!--/n--> |
| Streaming errors | <!--n results/vvd_smoke.json:streaming_errors -->0<!--/n--> |
| Crash lines | <!--n results/vvd_smoke.json:crash_lines -->0<!--/n--> |
| Peak memory, kB | <!--n results/vvd_smoke.json:peak_pss_kb -->353178<!--/n--> |

### Cover timing: a software-level number, and one late cover

**There is still no screen-level lead time, and there will not be one until the stick arrives.** What there is now is a software-level number from the virtual device, and the story of how it was almost published wrong is worth keeping, because an earlier version of this page had a figure that was not real.

A rehearsal run appeared to show all twenty markers covered in time with a worst lead of 449 ms. Those numbers have been withdrawn. The run they came from never actually played: the player reported positions between 0.17 s and <!--n results/gate1_rehearsal_vvd.json:furthest_position_the_player_reported_ms -->259<!--/n--> ms and got no further, while the cover scheduler, which runs on a wall clock by design, kept advancing its own estimate and fired every cover on time against that estimate. The analysis then agreed with itself. A stricter second script refused to count any of it, which is how it surfaced. Both analysis scripts now require a position report from the player before a lead time is counted.

Re-run under that rule, this is what the same evidence says:

| What | Value | Source |
|---|---|---|
| Markers in the clip | <!--n results/gate1_rehearsal_vvd.json:markers_in_schedule -->20<!--/n--> | gate1_rehearsal_vvd.json |
| Markers counted | <!--n results/gate1_rehearsal_vvd.json:markers_counted -->0<!--/n--> | gate1_rehearsal_vvd.json |
| Markers not counted, no position report | <!--n results/gate1_rehearsal_vvd.json:markers_not_counted -->20<!--/n--> | gate1_rehearsal_vvd.json |
That rehearsal clip is 20 markers long and none of them survived the rule. The measurement was then run again on a packed clip, across <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> usable trials from 22 app launches:

| What | Value | Source |
|---|---|---|
| Trials counted | <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> | gate1_software_vvd.json |
| Covered in time | <!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> | gate1_software_vvd.json |
| Dropped, no position report either side | <!--n results/gate1_software_vvd.json:trials_dropped_no_timeupdate -->4<!--/n--> | gate1_software_vvd.json |
| Dropped, playback stalled mid-trial | <!--n results/gate1_software_vvd.json:trials_dropped_playback_stalled -->2<!--/n--> | gate1_software_vvd.json |
| Median lead | <!--n results/gate1_software_vvd.json:lead_ms.median -->488.4<!--/n--> ms | gate1_software_vvd.json |
| Worst lead | <!--n results/gate1_software_vvd.json:worst_lead_ms -->-86<!--/n--> ms | gate1_software_vvd.json |
| Guard band | <!--n results/gate1_software_vvd.json:guard_band_ms -->500<!--/n--> ms | gate1_software_vvd.json |
| Required lead | <!--n results/gate1_software_vvd.json:required_lead_ms -->150<!--/n--> ms | gate1_software_vvd.json |

The median sits about where the 500 ms guard band puts it, which is the scheduler doing its job. Two things in that table matter more than the median.

**One cover was late.** The worst lead is negative: in one trial the cover went on 86 ms after the marker had already started. Every other pass fired at the first position report past the guard band, around 6.5 s into the clip. In that one, the report at 6.744 s was skipped and the cover fired at 7.079 s. The scheduler re-anchors to media time on every report and re-checks every 50 ms, so a 335 ms gap means the JavaScript thread was not available, not that the schedule was wrong. **The guard band has to be wider than the worst pause of that thread**, and nothing yet measures what that worst pause is on real hardware. That is now the first thing GATE 1 has to find out.

**The evidence rebuilds itself.** [`results/gate1_software_vvd.json`](results/gate1_software_vvd.json) ships with the events it was computed from, and `eval/verify_gate1_archive.py` runs in CI to rebuild the summary from those events and fail if the two ever disagree. That check exists because the first attempt to rebuild it by hand got 54 trials rather than 49, with one lead of 13.3 s, by splitting the passes on the wrong marker. The wrong answer looked completely ordinary.

A software-level figure measures the gap between the moment the app applied the cover and the moment the marker was due. Everything after the app sets its state, which is the React commit, the compositor, scan-out and the panel, is unmeasured, and all of it lands in the real figure. Treat this as an upper bound on how well the real thing can do. **GATE 1 is 50 trials filmed at 240 frames a second against a real Fire TV stick**, and nothing short of that is a lead time for this project.

### What the player does, which Amazon does not document

Measured in the same run, into [`results/vvd_timeupdate_stats.json`](results/vvd_timeupdate_stats.json). This is the evidence behind the scheduled-ahead design.

| What | Value |
|---|---|
| Position reports in the run | <!--n results/vvd_timeupdate_stats.json:timeupdate.count -->10<!--/n--> |
| Gap between them, median | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms |
| Gap between them, shortest | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.min -->75<!--/n--> ms |
| Gap between them, longest | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms |
| Smallest step `currentTime` reported | <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms |
| Worst gap between the app's estimate and the player | <!--n results/vvd_timeupdate_stats.json:worst_wall_clock_drift_ms -->2756<!--/n--> ms |
| Dropped video frames at the end of the run | <!--n results/vvd_timeupdate_stats.json:playback_quality_last.droppedVideoFrames -->0<!--/n--> of <!--n results/vvd_timeupdate_stats.json:playback_quality_last.totalVideoFrames -->1164<!--/n--> |

Read the drift figure with the gap figure. With no position report for over five seconds, the wall-clock estimate had run nearly three seconds away from the player by the time one arrived. That is why an uncertain playhead hides the picture rather than trusting the estimate.

### Layering

Recorded into [`results/vvd_layering_rehearsal.json`](results/vvd_layering_rehearsal.json).

| What | Value |
|---|---|
| Cover cycles driven | <!--n results/vvd_layering_rehearsal.json:layering.cover_cycles -->8<!--/n--> |
| Verdict | <!--n results/vvd_layering_rehearsal.json:layering.verdict -->inconclusive<!--/n--> |
| Media seconds advanced while covered | <!--n results/vvd_layering_rehearsal.json:layering.media_seconds_advanced_while_covered -->0.05<!--/n--> |

The harness side works and nothing crashed, but playback did not run in that take, so the run says nothing about whether the sound keeps going under a cover. It is recorded as inconclusive rather than dressed up. The real answer comes from filming a stick.

### Screening real footage

`flashmap` run over a licensed media pool, into [`results/screening.json`](results/screening.json). Every file was downloaded only after its source page was opened and its licence and credit line confirmed, recorded in [`media/LICENSES.csv`](media/LICENSES.csv). The files themselves are never committed.

| What | Value |
|---|---|
| Clips in the pool | <!--n results/screening.json:totals.clips -->20<!--/n--> |
| Analyzed cleanly | <!--n results/screening.json:clips_analyzed_ok -->16<!--/n--> |
| flashmap could not decode | <!--n results/screening.json:clips_failed -->4<!--/n--> |
| Flagged segments found | <!--n results/screening.json:totals.flagged_segments -->432<!--/n--> |
| Sources with at least one flag | <!--n results/screening.json:totals.sources_with_at_least_one_flag -->5<!--/n--> |

Per source:

| Source | Files | Files with a flag | Flagged segments |
|---|---|---|---|
| Blender open movies | <!--n results/screening.json:per_source.Blender open movies.files -->3<!--/n--> | <!--n results/screening.json:per_source.Blender open movies.flagged_files -->3<!--/n--> | <!--n results/screening.json:per_source.Blender open movies.flagged_segments -->169<!--/n--> |
| 1930 public-domain film | <!--n results/screening.json:per_source.1930 public-domain film.files -->2<!--/n--> | <!--n results/screening.json:per_source.1930 public-domain film.flagged_files -->2<!--/n--> | <!--n results/screening.json:per_source.1930 public-domain film.flagged_segments -->229<!--/n--> |
| Wikimedia Commons fireworks | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.files -->3<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.flagged_files -->2<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.flagged_segments -->16<!--/n--> |
| Wikimedia Commons lightning | <!--n results/screening.json:per_source.Wikimedia Commons lightning.files -->4<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons lightning.flagged_files -->3<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons lightning.flagged_segments -->9<!--/n--> |
| DVIDS | <!--n results/screening.json:per_source.DVIDS.files -->2<!--/n--> | <!--n results/screening.json:per_source.DVIDS.flagged_files -->2<!--/n--> | <!--n results/screening.json:per_source.DVIDS.flagged_segments -->9<!--/n--> |
| NASA SVS 5011 | <!--n results/screening.json:per_source.NASA SVS 5011.files -->1<!--/n--> | <!--n results/screening.json:per_source.NASA SVS 5011.flagged_files -->0<!--/n--> | <!--n results/screening.json:per_source.NASA SVS 5011.flagged_segments -->0<!--/n--> |

Two things this run found, both recorded rather than smoothed over. Every one of those segments fired the general flash rule and not one fired the red flash rule, because the free pool holds no saturated red strobe and no sustained regular strobe. And flashmap cannot decode Theora `.ogv`, which is what all four failures were.

### Baselines

Two independent tools were run over the same pool, so flashmap can be compared against something rather than trusted on its own. Per-clip results are in [`results/baselines/`](results/baselines/): `ffmpeg_photosensitivity` (FFmpeg's own photosensitivity filter, a mitigator whose flags are inferred from where its output differs from the unfiltered decode) and `naive_luma_diff` (whole-frame mean luma only, no area rule, no colour rule, no rate window). Neither is a conformance result and neither is a safety claim. The EA IRIS baseline is not built yet.

### Not measured yet

These rows exist so nobody has to guess what is missing.

| What | Why it is empty |
|---|---|
| GATE 1: covers drawn early, filmed at 240 fps | Needs the Fire TV stick. |
| Any cover lead time at all, on any device | The one run that produced one was withdrawn, because the player never reported a position. See above. |
| GATE 3: end to end on the stick | Needs the stick. |
| Prevented exposure, in seconds | Computed from flash maps once the KPI run happens. Never by playing flashing content with the filter off. |
| Titles verified end to end | The pipeline catalog is local state and is not in `results/` yet. |
| Test counts | The suites run in CI. No results file records their counts, so no number is published here. |
| Red flash segments from real footage | The free pool has none. Self-filmed red clips are the plan, under the rules in [docs/SAFETY.md](docs/SAFETY.md). |

## Install and run

### What you need

| Tool | Version | Why |
|---|---|---|
| Vega SDK | 0.24.9914 | The SDK this is pinned to |
| Vega CLI | 1.3.4 | Device and virtual device commands |
| Node | 22 (`.nvmrc`) | The sample declares `engines.node >= 22` |
| Python | 3.12 (`.python-version`) | flashmap, the pipeline and the measurement scripts |
| JDK 21 | for `npm install` only | The Shaka Player build runs in `postinstall` |

```sh
source ~/vega/env                       # Vega CLI and SDK
eval "$(fnm env)" && fnm use            # Node 22
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
```

### The app on the Vega Virtual Device

```sh
cd app
npm install                             # postinstall builds Shaka Player, so JAVA_HOME matters
npm run build:debug                     # a debug build: release builds strip console.log

cd ..
python3 eval/vvd_smoke.py --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
```

`eval/vvd_smoke.py` starts the virtual device if it is not running, installs and launches the app, drives the remote, plays a title and writes `results/vvd_smoke.json`.

Two things to know before you script against the device. `vega virtual-device status` says running before the device is usable, so wait for `vega device is-connected` instead. And `vega device list` crashes with a TypeError on this SDK, so use `vega device info`. Both are in the [friction log](docs/FRICTION_LOG.md), entries 6 and 8.

### The app on a Fire TV stick

```sh
cd app
npm install
npm run build:debug                     # armv7 for the stick
vega device is-connected                # not "vega device list", which crashes
vega run-app app/build/armv7-debug/calm-frames-app_armv7.vpkg
```

The stick needs Vega OS 1.2 with developer mode on, connected over USB. The package ID must not begin with `com.amazon`, or developer mode will not sideload it.

### The analyzer on its own

```sh
python -m pip install -e 'flashmap[dev]'

python -m flashmap keygen --out team_key
python -m flashmap analyze VIDEO --profile wcag --out MAP.json \
    --diag 55 --distance-ft 8 --key team_key.pem
python -m flashmap verify MAP.json VIDEO --pub team_key.pub.pem
python -m flashmap check VIDEO --profile wcag
```

Exit codes: `0` below the thresholds, `1` over them, `2` flashmap could not tell. A caller that treats `2` as a pass has a hole in it. The private key never enters the repository.

### The GitHub Action

Copy [`flashmap/examples/flash-check.yml`](flashmap/examples/flash-check.yml) into `.github/workflows/`. Every pull request that adds or changes an image or video is measured, and the job fails if the file goes over the general or red flash thresholds. The map format is [`docs/SIDECAR_SPEC.md`](docs/SIDECAR_SPEC.md).

### The pipeline

```sh
python -m pipeline.ingest --source VIDEO          # probe, analyze, hide plan, rendition, posters, sign
python -m pipeline.verify --title <sha256>        # the gate that blocks publishing
```

Ingest is idempotent and keyed by the source file's SHA-256, so a repeated run picks up where it stopped.

### AWS

The CDK app in [`pipeline/infra/`](pipeline/infra/) synthesizes and is unit tested. **Nothing is deployed and no AWS credentials have been used.** It has zero NAT gateways, a 20 US dollar budget alarm, private buckets, and a GitHub OIDC role so no AWS key is ever stored anywhere.

```sh
cd pipeline/infra && cdk synth            # safe: no account is touched
```

### The parent area and the demo PIN

The parent area is behind a four digit PIN, set on the device by whoever sets the app up. The PIN itself is never stored: what is stored is a salted, iterated hash of it ([`app/src/calmframes/parentGate.ts`](app/src/calmframes/parentGate.ts), which is also plain about what that does and does not buy).

**The demo PIN for judges is not set yet.** It will be published here and in the GitHub Release notes once the demo build exists. This README will not carry a made-up one.

## Limits

Worth knowing before trusting this with a child.

- **It is not a medical device, and it does not prevent seizures.** It reduces exposure to flashing above published limits in the videos it plays. Photosensitivity varies between people and published thresholds are a floor, not a promise.
- **Only titles that passed verify can play in kid mode.** Anything else is not protected, because it was never measured.
- **Live streams and other apps' content are out of scope.** So are DRM titles from other apps.
- **HDR is not measured.** flashmap refuses HLG and PQ input rather than measuring it with the wrong transfer curve.
- **Theora `.ogv` does not decode**, which is four of the twenty clips in the screening pool.
- **There is no screen-level cover lead time.** The software-level number above is the app's own timing on the virtual device, and it stops at the moment the app sets its state. Until GATE 1 is filmed on a stick at 240 fps, the timing claim in this README is an upper bound and a design argument, not a measurement of what a screen showed.
- **One cover in 49 went on after its marker started.** The cause looks like the JavaScript thread being unavailable for about a third of a second, which the 500 ms guard band did not cover. Until the worst thread pause is measured on real hardware, the right guard band is unknown.
- **The layering question is open.** The one recorded run is inconclusive, because playback did not run in that take.
- **Red flash coverage is untested against real footage**, because no free source in the pool has a saturated red strobe.
- **The room rule can only add hides.** A household cannot make Calm Frames weaker than WCAG. That is a design rule and it is enforced in code, but it also means a household cannot switch protection off for one title without leaving kid mode.
- **Phase 4 is landing as this is written.** The guard hook, the PIN gate, the seek safety engine, the calm card and the VoiceView announcements exist in `app/src/calmframes/`. What does not exist yet is the standalone `hook/` package that ships them to other apps, and none of it has been seen running on a stick.

## Safety

Read [docs/SAFETY.md](docs/SAFETY.md) before running anything in this repository.

Nobody on this project watches strobes at full speed. Hazard files carry the `HAZARD_` prefix, live under `media/` which is gitignored, never autoplay, and are inspected only as luminance plots or as slowed and dimmed playback. Generated conformance clips are hazardous by design and are made, measured and deleted in the same job. Exposure that the filter prevented is computed from the flash map. It is never demonstrated by playing flashing content with the filter off.

The approved wording, everywhere, is: **reduces exposure to flashing above published limits in the videos it plays; not a medical device.** Never "prevents seizures" and never "seizure-proof".

## Licences and credits

| What | Licence |
|---|---|
| Calm Frames, including `flashmap/`, `pipeline/` and `eval/` | Apache-2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE) |
| `app/`, derived from [AmazonAppDev/vega-video-sample](https://github.com/AmazonAppDev/vega-video-sample) at tag `v0.24-RN83` | MIT-0, see [app/LICENSE](app/LICENSE) |
| App third-party dependencies | [app/LICENSE-THIRD-PARTY](app/LICENSE-THIRD-PARTY) |
| Screening media | Per file in [media/LICENSES.csv](media/LICENSES.csv), with URL, licence, credit line, SHA-256, duration and resolution |

Screening media credits: Blender open movies (Cosmos Laundromat, Sintel, Tears of Steel, Big Buck Bunny) from Blender Foundation under CC BY 3.0, with the Tears of Steel credit scroll kept and Blender logos excluded; NASA Scientific Visualization Studio and ISS time-lapse footage, following NASA's credit-line guidance; DVIDS footage, which carries a non-endorsement notice; Wikimedia Commons fireworks and lightning footage under its per-file licences; two 1930 public-domain films.

Thresholds are quoted, with links, in [`flashmap/docs/SPEC_SOURCES.md`](flashmap/docs/SPEC_SOURCES.md). Nothing in this project may use a threshold that is not on that page, and the three things that could not be verified from a primary source are named there and are not used as thresholds.

## Where else to look

| File | What is in it |
|---|---|
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Every Devpost field, ready to paste |
| [docs/FRICTION_LOG.md](docs/FRICTION_LOG.md) | Developer friction found while building, in Amazon's six-field format |
| [docs/OPEN_SOURCE_PR.md](docs/OPEN_SOURCE_PR.md) | The upstream contribution: what it fixes and why |
| [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md) | The demo video, timed |
| [docs/GATES.md](docs/GATES.md) | Every gate, checkpoint and kill rule, with evidence |
| [docs/STATUS.md](docs/STATUS.md) | Where each lane stands today |
| [docs/SIDECAR_SPEC.md](docs/SIDECAR_SPEC.md) | The flash map format, version 1 |
| [docs/EVAL_PLAN.md](docs/EVAL_PLAN.md) | Committed before any real clip was labelled |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Every call made, with why and what it cost |
