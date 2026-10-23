# Calm Frames 🌊

**A quiet place on your TV. Prepared nature scenes, deliberate playback, and a picture that stays.**

[![Vega OS](https://img.shields.io/badge/Vega_OS-native_TV_app-245a58)](app/)
[![Node 22](https://img.shields.io/badge/Node-22-53745b)](.nvmrc)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-53745b)](.python-version)
[![Apache 2.0](https://img.shields.io/badge/Code-Apache_2.0-c6854e)](LICENSE)

Calm Frames pairs a coastal, remote-first TV interface with an offline video preparation pipeline. Choose Ocean or Forest, inspect a title, and decide when to watch. McWay Falls offers five continuous minutes of a fixed coastal view at natural speed, then holds the final frame until you leave. Acadia, Sea otters and Forest open as still scenes, with short moving previews available separately.

**Demo status:** the [demo video](https://www.youtube.com/watch?v=6lAP1FH16vc) and the [Devpost entry](https://devpost.com/software/calm-frames) both show an earlier build than this branch, so they do not include the latest playback recovery, profile and onboarding work. A cut of the newer build is local and under review. The repository is private. The screenshots below reflect installed source `60c3bbb`, and the current build words a few labels differently; see [build and publication status](docs/presentation/README.md#build-and-publication-status) for exact evidence and revision scope.

![Calm Frames Home: a coastal map with Ocean and Forest, McWay Falls selected, and Watch as the primary action](docs/presentation/home.png)

<p align="center">
  <img src="docs/presentation/details.png" alt="McWay Falls details show the duration, nature sounds, final still, and an explicit Watch action" width="49%">
  <img src="docs/presentation/playback.png" alt="Native playback of the fixed McWay Falls cove and waterfall" width="49%">
</p>

<p align="center"><em>Real native app views: choose a place, understand the session, then watch.</em></p>

<details>
<summary><strong>After the scene: the final frame stays</strong></summary>

![The corrected ending retains the scene framing and shows a Back button; it does not repeat or automatically return Home](docs/presentation/ending.png)

The audio fades at the end. The extracted final frame remains until Back. This is an intentional stationary ending, not an endless video loop.

</details>

Screenshots are cropped from existing app-only native captures, with no reconstructed UI. McWay imagery: MoneySavingVideos, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). [Capture provenance and full credits](docs/presentation/README.md).

## Features

- **A connected coastal world.** Ocean and Forest share the same map, typography, warm surfaces and obvious remote focus across Home, Details and loading.
- **Sustained viewing with a deliberate ending.** McWay runs at natural speed with no cuts or repeated loop. Its final frame stays open; the other approved titles offer silent still scenes first.
- **Playback starts with a choice.** Watch is the primary action. Pause, resume and Back remain available; short previews are secondary actions.
- **Prepared media with traceable identity.** Offline analysis, signed maps, exact source and rendition hashes, and verification reports travel with each approved edition.
- **A guarded playback path.** The picture stays covered while verification is unresolved. Scheduled covers and seek guards are driven by the accepted map and household settings.
- **Local household preferences.** PIN-protected settings, presets, captions and stricter cover choices are stored on the device. Optional interface motion respects reduced motion.
- **Tools beyond the demo.** The [flashmap analyzer](flashmap/README.md), [Vega hook](hook/README.md) and [local preparation workflow](pipeline/LOCAL_LIBRARY.md) expose the underlying work separately.

## Architecture

![Calm Frames architecture: licensed sources pass through offline analysis, preparation and verification into an approved packaged library; the TV app verifies the selected route and map before guarded playback and the final still](docs/presentation/architecture.png)

[Readable diagram source and code map](docs/presentation/ARCHITECTURE.md) · [Vector version](docs/presentation/architecture.svg)

The preparation and playback boundaries matter:

1. **Prepare before playback.** `pipeline.local_library` coordinates ingest, flashmap analysis, signed maps and preset rendering. `pipeline.verify` checks the actual outputs. Ambient replacements have a separate checked export path.
2. **Bind trust to exact artifacts.** `pipeline.packaged_library` exports verified editions; app build checks enforce the compiled approval registry, reports and media budget. A file URL cannot introduce a new trusted signer.
3. **Verify again at the player.** `packagedLibrary.ts` matches the compiled catalog and route; `flashMap.ts` verifies the signed map. `useFlashGuard.ts` owns cover scheduling and the guarded seek entry point.
4. **Keep the ending explicit.** `continuousScene.ts` recognizes the exact McWay edition. `PlayerScreen.tsx` presents its final still through `AmbientScene.tsx` after playback ends, without automatic repeat or navigation.

This app plays its prepared catalog. It does not intercept Prime Video, other apps, or arbitrary streaming content.

<details>
<summary>Code paths behind the diagram</summary>

### Required tech at runtime

The installed app uses Vega's W3C media player. The remaining rows distinguish local preparation from runtime verification; they are code references, not extra hackathon requirements. Symbol names accompany line links so they remain checkable on this branch.

| Stage | Entry point | Responsibility |
|---|---|---|
| Native playback | `new VideoPlayer()` [source](app/src/utils/VideoHandler.ts#L157) | Create the Vega player |
| Runtime map | `verifyFlashMap` [source](app/src/calmframes/flashMap.ts#L217) | Check signed map identity and validity |
| Runtime catalog | `createPackagedLibrary` [source](app/src/calmframes/packagedLibrary.ts#L218) | Bind the packaged route and evidence |
| Runtime coverage | `useFlashGuard` [source](app/src/calmframes/useFlashGuard.ts#L159) | Coordinate cover state and player clock |
| Runtime seeking | `planSeek` [source](app/src/calmframes/seekSafety.ts#L113) | Plan a seek against covered intervals |
| Runtime ending | `continuousEndingForRoute` [source](app/src/calmframes/continuousScene.ts#L23) | Recognize the exact continuous edition |
| Offline preparation | `ingest_title` [source](pipeline/ingest.py#L212) | Orchestrate preparation |
| Offline verification | `verify_title` [source](pipeline/verify.py#L485) | Check actual output against its source |
| Offline package | `export_packaged_library` [source](pipeline/packaged_library.py#L437) | Export verified editions and reports |
| Offline replacement | `export_ambient_catalog` [source](pipeline/ambient_export.py#L24) | Independently reproduce replacement media |

</details>

## Engineering decisions

- **Long scenes over a short reel.** The original short-preview experience was rejected as uncomfortable and too brief. The current McWay edition uses one sustained camera view; legacy titles remain stationary by default. This design change is not a guarantee of individual comfort.
- **Integrity is separate from detection.** A valid signature establishes which map was approved. It does not establish medical safety or prove the analyzer found every issue.
- **Covers precede seeks.** Transport changes go through a shared guard rather than independent player writes. The native video surface is covered with an opaque layer, not hidden by changing its opacity.
- **Source tests are separate from native evidence.** Unit tests establish state contracts. Package verification establishes shipped bytes. Native observations establish only the specific interactions and images observed on that device.

## Tech stack

| Layer | Implementation |
|---|---|
| TV app | React Native, TypeScript, Vega OS and Amazon W3C media APIs |
| Design | Fraunces titles, Source Sans 3 controls, shared coastal geometry and focus tokens |
| Analysis | Python, flashmap, PyAV and ffmpeg |
| Preparation | Preset rendering, source/rendition hashes, Ed25519-signed maps and verification reports |
| Playback | Compiled catalog, map verification, cover scheduler and guarded seek engine |
| Checks | Jest, TypeScript, ESLint, Node checks, pytest and strict package validation |

## Running locally

Use the candidate branch after obtaining repository access. The default branch is older. Check `git rev-parse HEAD` and the [build record](docs/presentation/README.md#build-and-publication-status) before comparing a newly built package with the screenshots.

```sh
git clone --single-branch --branch claude/ocean-layout-fix-2026-10-19 https://github.com/alejandro-publius/calm-frames.git
cd calm-frames
git rev-parse HEAD
```

### App checks without a simulator

Use Node 22 from `.nvmrc` and the checked-in dependency lock.

```sh
cd app
npm ci --ignore-scripts
npm run typecheck
npm run lint
npm test -- --runInBand --ci
```

### Native build and launch

Requires an existing Vega SDK installation, Node 22 and JDK 21. The bundled catalog needs no signing private key or cloud account. A fresh household chooses its own PIN.

```sh
# From the repository root, with Node 22 selected:
source ~/vega/env
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
cd app
npm ci --ignore-scripts
npm run setup:player
npm run check:native-inputs
npm run build:debug
cd ..
```

For an Apple Silicon Mac, install the resulting aarch64 package. Start the virtual device only if it is stopped.

```sh
nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
vega device is-connected --device VirtualDevice
vega device install-app --device VirtualDevice \
  --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg --buildType Debug
vega device run-cmd --device VirtualDevice \
  --command 'vmsgr send pkg://io.github.alejandropublius.calmframes.main'
```

Intel targets need the matching x86_64 package. [Reviewer quickstart](docs/submission/REVIEWER_QUICKSTART.md) covers the environment and inspection commands; its dated historical receipts are not current build acceptance.

### Analyzer and pipeline checks

With Python 3.12, ffmpeg and ffprobe already available:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e './flashmap[dev]' matplotlib==3.11.2
.venv/bin/python -m pytest flashmap pipeline eval -q -m 'not slow'
.venv/bin/python eval/readme_sync.py --check
.venv/bin/python eval/style_check.py
```

New media follows the [local library workflow](pipeline/LOCAL_LIBRARY.md). Preparing a candidate does not automatically add it to the app or expand signer trust.

## Evidence and limits

These are recorded results with separate scopes, not a claim that the latest local revision has a green hosted CI run.

| Scope | Recorded result | Evidence |
|---|---|---|
| Integration branch, cloud session, October 23 | <!--n results/integration-2026-10-23/receipt.json:app.jest_passed -->1801<!--/n--> Jest tests passed, <!--n results/integration-2026-10-23/receipt.json:app.jest_skipped -->4<!--/n--> skipped; <!--n results/integration-2026-10-23/receipt.json:python.passed -->2001<!--/n--> Python tests passed, <!--n results/integration-2026-10-23/receipt.json:python.failed -->1<!--/n--> failed only because the container runs as root (it passes as an unprivileged user); TypeScript, lint and the app's own flash check passed. No simulator here; hosted CI runs through draft PR #2 | [Receipt](results/integration-2026-10-23/receipt.json), [integration status](docs/handoff-2026-10-23/INTEGRATION_STATUS.md) |
| Full source baseline before the ending-bounds fix | <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.fullJestPassed -->1698<!--/n--> Jest tests passed, <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.skipped -->4<!--/n--> skipped; TypeScript passed; lint <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.eslintErrors -->0<!--/n--> errors / <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.eslintWarnings -->108<!--/n--> warnings | [Source receipt](results/mcway-activation-2026-10-21/verification.json), [Jest log](results/mcway-activation-2026-10-21/final-jest.log) |
| Additional preparation and delivery checks | <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.nodeChecksPassed -->94<!--/n--> Node checks and <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.pythonDeliveryAndBudgetPassed -->121<!--/n--> Python delivery/budget checks passed | [Recorded verification](results/mcway-activation-2026-10-21/verification.json) |
| Latest local ending fix | Targeted ending tests, TypeScript and focused lint passed; native package built and installed | [Exact build and capture record](docs/presentation/README.md#build-and-publication-status) |
| Native observations | Full-duration playback, pause/resume and Back observed; corrected final-frame bounds inspected in the actual app | [Native screenshots and limits](docs/presentation/README.md#what-the-images-establish) |
| Prepared media budget | <!--n results/mcway-activation-2026-10-21/verification.json:preparedNamespaceBytes -->129255687<!--/n--> of <!--n results/mcway-activation-2026-10-21/verification.json:limitBytes -->134217728<!--/n--> bytes | [Exact activated bundle](results/mcway-activation-2026-10-21/verification.json) |

The older activation receipt's “not installed / Mac locked” note describes that earlier checkpoint. The linked current capture record documents the later installation and picture observations without rewriting the historical receipt.

**Still open:** replacing the demo video and updating the Devpost entry for this build, and subjective audio/comfort acceptance. Physical Fire TV measurements and full VoiceView acceptance are not claimed. Analyzer passes and simulator observations do not establish clinical safety. Calm Frames is not a medical device.

<details>
<summary>Historical screening corpus, separate from the shipped catalog</summary>

This September 17, 2026 WCAG screening run measures detector findings, not clinical safety, viewing comfort or current catalog approval. The complete per-source file counts below add up to <!--n results/screening.json:clips_analyzed_ok -->38<!--/n--> analyzed files. See [raw screening results](results/screening.json) for findings and scope. Hazardous research sources are not linked for playback here.

| Source group | Files |
|---|---|
| 1930 public-domain film | <!--n results/screening.json:per_source.1930 public-domain film.files -->2<!--/n--> |
| Blender open movies | <!--n results/screening.json:per_source.Blender open movies.files -->3<!--/n--> |
| DVIDS | <!--n results/screening.json:per_source.DVIDS.files -->2<!--/n--> |
| NASA ISS time-lapse | <!--n results/screening.json:per_source.NASA ISS time-lapse.files -->3<!--/n--> |
| NASA SVS 5011 | <!--n results/screening.json:per_source.NASA SVS 5011.files -->1<!--/n--> |
| Wikimedia Commons | <!--n results/screening.json:per_source.Wikimedia Commons.files -->16<!--/n--> |
| Wikimedia Commons fireworks | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.files -->4<!--/n--> |
| Wikimedia Commons lightning | <!--n results/screening.json:per_source.Wikimedia Commons lightning.files -->4<!--/n--> |
| unlabeled | <!--n results/screening.json:per_source.unlabeled.files -->3<!--/n--> |

</details>

## Media attribution and license

McWay footage and extracted still: **MoneySavingVideos**, *♥♥ Relaxing 3 Hour Video of a Waterfall on an Ocean Beach at Sunset*, [source on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:%E2%99%A5%E2%99%A5_Relaxing_3_Hour_Video_of_a_Waterfall_on_an_Ocean_Beach_at_Sunset.webm), [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Changes: first five-minute excerpt, downsampled to 720p, H.264/AAC encoding, a three-second ending audio fade, and an extracted final-frame still. Repository screenshots crop the native app capture to its picture area. No endorsement implied.

Other visible title imagery: **NPS Video, Acadia National Park**; **NOAA Fisheries**; **NPS: G Litten** for Prairie Creek and Redwood. See the [media ledger](media/LICENSES.csv), [NOTICE](NOTICE) and [screenshot credits](docs/presentation/README.md#media-credits). No agency endorsement implied.

Project code is [Apache 2.0](LICENSE). Media, fonts and sample-derived components retain their respective licenses; see [app notices](app/LICENSE-THIRD-PARTY). The documentation layout takes inspiration from [Tideline](https://github.com/alejandro-publius/tideline); the screenshots, architecture and implementation described here are Calm Frames.
