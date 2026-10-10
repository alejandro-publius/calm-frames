# Calm Frames: the full terminal build prompt

**Current scope, Oct 9:** the user's later instructions supersede the hardware
and possible-teammate plan below. Solo entry, identity-verified Amazon Developer
account, Vega Virtual Device exclusively, no physical-TV or camera-timing
prerequisites. Use [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) for current
acceptance and blockers. Keep the historical specification thresholds intact.

This replaces `prompt-calm-frames.md`. It covers every Calm Frames step in one place: setup, day-one device probes, the build, the evaluation, the video and the submission. The roadblocks from the stress test are built in as dated gates with fallbacks, so Claude Code hits them on purpose, early, instead of by surprise.

## Set it up (5 minutes)
1. In a terminal: `mkdir calm-frames && cd calm-frames && git init`
2. Unzip `day-one-head-start.zip` and copy its `evkit`, `calm-timing`, `flashmap` and `calm-vega-notes` folders into `calm-frames/headstart/`.
3. Copy `rubric-amazon.md` to `docs/RUBRIC.md` and `outreach-kit.md` to `docs/outreach-kit.md`.
4. Save this file as `docs/BUILD_PROMPT.md`.
5. Run `claude` in the folder and paste the kickoff prompt below. (Or type: "Read docs/BUILD_PROMPT.md and follow the kickoff prompt, starting at Phase 0.")
6. After the first reply, paste the `/goal` line for the current phase (bottom of this file). If it stops at the turn limit, paste it again.

## Your steps (Claude Code stops and asks at each one)
| When | What you do |
|---|---|
| Today, Thu Sep 17 | Tell Claude Code which computer you're on. The Vega SDK needs a Mac (Apple silicon, or Intel until Dec 15) or Ubuntu installed directly on an x86_64 PC. On Windows, boot Ubuntu from an external SSD. |
| Today | Order a Vega OS stick: Fire TV Stick HD 2026 (AFTCL001, $34.99 list) or Fire TV Stick 4K Select (AFTCA002, $39.99 list). Skip the 2024 "Fire TV Stick HD with Alexa Voice Remote" (it runs Fire OS 7). If delivery is after Sat Sep 19, buy one at Target. |
| Today | Join the hackathon on Devpost, sign in to an Amazon Developer account, and request AWS credits at https://forms.gle/GaHFxSbBQNG9Kti6A (closes Oct 21 at noon PT, first come, first served). Put the AWS account on the Paid plan and set a $20 budget alarm. |
| Today | Check that your phone films 240 fps slow motion and that your TV has a game mode (motion smoothing off). |
| Fri Sep 18 | Send the epilepsy outreach emails Claude Code drafts from `docs/outreach-kit.md`. Ask only for a review of wording and flow; never show anyone flashes. |
| Stick arrives | Update it to Vega OS 1.2 (Settings > My Fire TV > About > Check for Updates), turn on Developer Mode, plug it into your computer by USB. |
| Sep 21 to 23 | Film 50 timing trials on the stick at 240 fps with exposure locked. The test clip has no flashing (gentle gray-to-white steps). |
| By Thu Sep 24 | Film your own flashing test footage (party strobe, toy emergency lights, camera flashes). Whoever films must not be photosensitive and must not look at the lights. Review it only as plots. |
| Oct 8 to 13 | Film 200+ screen-level events on the stick (filter always on, nobody watching the screen). |
| Oct 8 to 14 | Rachel (if on the team): double-label a subset of real clips from plots. |
| By Fri Oct 16 | Put any outreach reply (with permission) into `docs/VALIDATION.md`. |
| Oct 19 to 20 | Record the video from Claude Code's script. |
| Thu Oct 22 | Press submit on Devpost. The deadline is Fri Oct 23, 12:00 PT, and Cal Hacks starts that day. |

## Kickoff prompt

```
ROLE AND MODE
You are the lead engineer on Calm Frames, my entry for Build, Ship, Shape: Amazon Developer Hackathon (https://amazonappdev2026.devpost.com). Primary track: Fire TV ($25,000 cash plus $15,000 AWS credits for first). Mini challenges: Open Source (primary) and AWS Builder (also selected; a project can win at most one track prize and one mini challenge prize). You run in my terminal on my computer.
Work on your own. Make reasonable calls, record each in docs/DECISIONS.md (date, decision, why, what it costs), and keep going. Stop and ask me only at a HUMAN CHECKPOINT or when a KILL rule fires. Keep docs/STATUS.md current (done, next, blocked, what you need from me) and end every block of work with one status line.
Create CLAUDE.md at the repo root with the hard rules from this prompt and the current phase, and update it at every phase change so a fresh session picks up where we left off.
Use subagents and ultracode workflows for parallel lanes: (1) flashmap and the conformance suite, (2) the Vega app, (3) the pipeline and CDK, (4) baselines and evaluation, (5) docs, friction log and feedback. At every milestone run a separate verifier agent that tries to break each claim and number before it reaches the README, Devpost text or video. Commit small and often.

THE WINNING THESIS (point every decision at this)
The official rubric lists a "simple video player" as an obvious Fire TV idea, and names viewing that adapts to the household and flows that combine voice, D-pad and visuals as creative. Calm Frames must never read as a video player. It is a verified safety layer for kids with photosensitive epilepsy:
- every frame of a title is analyzed before it can play in kid mode, and the result is a signed flash map;
- the player hides each flagged flashing segment before it starts while sound and captions keep going, then says what was hidden;
- it adapts to the household (preset, TV size, seat distance) and can only get stricter than WCAG, never looser;
- voice (Alexa transport commands), the D-pad and on-screen cards work as one flow, and every seek path is safe;
- any Vega video app can add it with a small hook, and studios can check content before publishing with the open-source analyzer and GitHub Action.
Lead with this in the README, the Devpost text and the first 20 seconds of the video.
Past winners were mostly thin (mocked data, no measured evaluation). We win Tech Implementation (ties go to Tech) with measured numbers, intervals and CI-regenerated results. Nothing mocked is ever shown as real.

ME AND THE TEAM
Alex Velazquez (UC Berkeley CS, GitHub alejandro-publius), possibly with teammate Rachel Selbrede. Grand Prize winner at Build with DataHub. Standard: code enforces the guarantees, every number is measured and regenerated by CI, and nothing mocked is shown as real. Student budget. Hardware: my computer, one Vega OS Fire TV stick, a TV, a phone that films 240 fps.

KEY DATES (Pacific Time)
- Thu Sep 17: machine confirmed, repo created, friction log started, stick ordered, AWS credits requested.
- Sat Sep 19: Vega SDK and Vega Virtual Device (VVD) running; the renamed sample plays a title on the VVD.
- Mon Sep 21: stick on Vega OS 1.2 (else the SDK 0.23 fallback).
- Wed Sep 23: GATE 1, overlay timing on the stick (Fri Sep 25 at the latest if the stick arrived late).
- Fri Sep 25: GATE 2, screening day (enough real flashing segments with confirmed licenses).
- Fri Oct 2: GATE 3, end to end on the stick: upload, map, verify, safe rendition, kid-mode playback.
- Mon Oct 12: upstream open-source pull request opened.
- Tue Oct 13: 200-event screen-level test filmed and analyzed.
- Fri Oct 16: outreach validation in docs/VALIDATION.md (if any reply came).
- Sun Oct 18: feature freeze.
- Mon Oct 19 to Tue Oct 20: video.
- Wed Oct 21: final checks (the AWS credit form also closes at noon).
- Thu Oct 22: submit (deadline Fri Oct 23, 12:00 PT).
- Nov 9 to 20: judging. Keep the backend and demo links live through Dec 3 (winners announced) under the budget alarm, and never move the judged release tag.

WHAT THE RULES REQUIRE (check the repo against this list at every phase)
- The project runs on Fire OS or Vega OS; any framework is fine. The demo video shows it running on a real Fire TV device or the Fire TV/Vega simulator.
- A public GitHub repo with all source, assets and instructions needed to run it, and an open-source license file that GitHub detects and shows in the About box.
- Text description; video under 3 minutes, public on YouTube or Vimeo, English, with no third-party trademarks or copyrighted music unless permitted.
- Product feedback for every tool, API and SDK used, answering Amazon's five questions: which tools and for what; what worked well; what needs work; onboarding from zero to hello world; would you build with them again, yes or no and why.
- AWS Builder: describe which AWS services were used and how. Open Source: contribution URL, project repo URL, GitHub username, and what we did, how it works and why it matters.
- Optional feature requests (with Critical, Important or Nice-to-have) and friction log entries (task, steps, expected vs actual, severity, workaround, suggestion). Friction logs can add up to 10% to the final score.
- Judges test through the repo and the video. Judging may include automated AI analysis, so the README must make the required-tech usage and the results easy to find.
- Work must be new in the submission period (it opened Aug 31). Record anything reused in docs/PRIOR_WORK.md (the head-start kits were written Sep 15 to 16).

PHASE 0: MACHINE AND REPO (first hours, today)
0.1 Detect and print: OS and version (sw_vers or lsb_release -a), CPU architecture, total and free memory, free disk, whether /dev/kvm exists (Linux), and versions of git, gh, node, npm, python3, ffmpeg, docker, jq.
    Supported for the Vega SDK 0.24: macOS on Apple silicon; macOS on Intel (0.24 is the last Intel release and Intel support ends Dec 15, 2026, after judging); Ubuntu 20.04 or newer on x86_64, installed directly on the machine with KVM (the VVD runs on QEMU/KVM; VirtualBox is not supported, and the VVD struggles with less than 2 GB of free memory). Windows and WSL are not supported.
    HUMAN CHECKPOINT A: if the machine is not supported, stop and tell me. The fix is booting Ubuntu from an external SSD (2 to 4 hours). KILL if there is no supported machine by Sat Sep 19.
0.2 Install what's missing (Homebrew or apt): the Node version the Vega docs require, Python 3.11+, ffmpeg with libx264 and libvpx, Docker, gh, jq, pipx or uv. Write every version to docs/ENVIRONMENT.md.
0.3 Repo layout (one monorepo):
    app/        the Vega app, forked from AmazonAppDev/vega-video-sample (MIT-0)
    flashmap/   the Python analyzer package (from headstart/flashmap), Apache-2.0
    pipeline/   ingest, kid-safe rendition, verify (Python); CDK in pipeline/infra
    hook/       a React Native for Vega package (useFlashGuard) plus the sidecar spec
    eval/       conformance generator, baselines, camera harness (from headstart/calm-timing), plot-only labeling tools
    results/    committed JSON results, the only source for any number we publish
    media/      gitignored video files; media/LICENSES.csv and hashes are committed
    docs/       RUBRIC, PLAN, STATUS, DECISIONS, GATES, ENVIRONMENT, EVAL_PLAN, SAFETY, LICENSES, FRICTION_LOG, FEEDBACK, SUBMISSION, VIDEO_SCRIPT, PRIOR_WORK, VALIDATION, SIDECAR_SPEC, INTEGRATION_DIFF
    headstart/  my starter kits
0.4 Head start: read every README in headstart/ and all of headstart/calm-vega-notes/ (VEGA_QUICKSTART.md, VEGA_APIS.md, DEVICES.md, FACT_CHECK.md, STRESS_TEST.md) before writing code. Install the kits (pip install -e for flashmap, calm-timing and evkit) and run their tests (at handoff: flashmap 97, calm-timing 51, evkit 120, all passing). Build on them; don't rewrite them. Useful commands:
    python3 -m flashmap keygen --out team_key
    python3 -m flashmap analyze VIDEO --profile wcag --out MAP.json --diag 55 --distance-ft 8 --key team_key.pem
    python3 -m flashmap analyze VIDEO --profile broadcast --out MAP.json --peak-nits 200
    python3 -m flashmap verify MAP.json VIDEO --pub team_key.pub.pem
    python3 -m flashmap check VIDEO [VIDEO ...] --profile wcag
    python3 -m calmtiming make-clip --out markers.mp4 --duration 120 --markers 20
    python3 -m calmtiming roi / analyze / combine   (see its README for flags)
    python3 -m evkit.friction add --task "..."   and   python3 -m evkit.friction stats
    python3 -m evkit.readme_sync README.md --check --results-dir results
0.5 License: Apache-2.0 LICENSE at the repo root (so GitHub shows it in the About box), a NOTICE file for attributions, and the sample's MIT-0 notice kept in app/.
0.6 CI (GitHub Actions, using the evkit templates): lint, type checks, pytest, the app's unit tests, make reproduce, readme_sync --check, gitleaks, and flashmap check on every image and video asset in the repo.
0.7 Friction log from minute one, in docs/FRICTION_LOG.md through evkit.friction. Every install snag, doc gap, confusing error and workaround goes in, with a concrete suggestion. Target 20 to 30 real entries by Oct 18.
0.8 Name check: search GitHub, Devpost and the Fire TV Appstore for "Calm Frames". If it's taken, pick another name and record why.
0.9 HUMAN CHECKPOINT F (Fri Sep 18): draft short outreach emails from docs/outreach-kit.md for me to send. Ask only for feedback on wording and flow.

PHASE 1: VEGA DAY-ONE PROBES (VVD by Sep 19, stick Sep 21 to 23)
1.1 Install Vega SDK 0.24 following headstart/calm-vega-notes/VEGA_QUICKSTART.md and https://developer.amazon.com/docs/vega/0.24/. Pin it.
1.2 Fork AmazonAppDev/vega-video-sample into app/ and pin the commit. Day-one fixes, before anything else:
    - Rename the package ID (the sample uses com.amazondeveloper.keplervideoapp) to my own reverse domain, for example io.github.alejandropublius.calmframes. Developer mode only sideloads packages that don't start with com.amazon.
    - Remove the sample's [[components.task]] and [[components.service]] entries (account login, personalization, install and EPG sync) and everything that needs them. On SDK 0.24 with React Native 0.83 these can crash the app at launch.
    - Ban setNativeProps with a lint rule (it throws a TypeError on React Native 0.83). Drive all UI through state.
    - The sample README lists a black screen with audio-only playback after back navigation. Add a regression test for our navigation flows.
1.3 Build and run on the VVD: npm install, npm run build:app, vega virtual-device start, then vega run-app with the .vpkg for the host architecture. Play a Blender title. Log every snag.
1.4 HUMAN CHECKPOINT B (stick arrives): I update it and turn on developer mode (follow https://developer.amazon.com/docs/vega/0.24/developer-mode.html: the center-button sequence, then vega devmode login and vega devmode enable-device --code). Connect over USB first. Then you confirm the OS on the device (cat /etc/os-release). SDK 0.24 needs Vega OS 1.2 (build 2101020054720).
    If it's still on 1.1 by Mon Sep 21: ask on the Amazon developer forum OS 1.2 update thread, retry the update, and fall back to SDK 0.23 with a matching sample tag (2 to 4 hours). If that also fails by Sep 23, tell me; we go VVD-only for development and keep trying the stick.
1.5 Layering test on the stick (10 minutes): a full-screen black View toggles every 5 seconds over a Blender title with captions on. Pass: the picture is fully hidden every time, captions stay visible above the cover, audio never stops, no crash. I film it; you log the result in docs/GATES.md.
    If the video shows through or draws on top: try a transparent WebView overlay (Amazon staff said that works), then switch to Plan B as the primary path.
    If captions disappear under the cover: draw the cues yourself as React Native Text from textTracks, above the cover (about 3 hours).
    Don't try to hide video by lowering the surface view's opacity; staff replies suggest props don't reach the hardware video layer.
1.6 GATE 1, timing (by Sep 23; Sep 25 at the latest):
    - Make the 2-minute marker clip and its schedule with calm-timing (20 non-flashing gray-to-white steps).
    - Drive a black overlay from the schedule with a 500 ms guard band, leaving the kit's reference patch uncovered.
    - On every timeupdate, seeking and seeked event, log currentTime with a wall-clock timestamp and getVideoPlaybackQuality(). Amazon doesn't document how often timeupdate fires or how precise currentTime is, so measure it.
    - Scheduler design: a wall-clock scheduler on the UI thread (Reanimated is already a dependency of the sample), re-synced to media time on every timeupdate, aware of playbackRate and pauses. Cover at once on waiting, stalled, seeking, pause and app backgrounding.
    - HUMAN CHECKPOINT E1: I film 50 trials on the stick at 240 fps (exposure locked, TV in game mode, motion smoothing off). You run calmtiming roi, analyze and combine.
    - PASS: the cover is fully on at least 150 ms before the marker in at least 48 of 50 trials. Report the Wilson 95% interval, median, p95 and worst lead time in results/gate1_timing.json. One tuning round is allowed.
    - KILL for on-device timing: under 48 of 50, or any marker uncovered, after tuning. Plan B becomes the primary path and the entry still stands.

PLAN B (build it anyway; it's defense in depth)
The pipeline writes a kid-safe HLS rendition per preset. Each flagged segment plus its guard band is replaced by a still poster frame (ffmpeg overlay with enable='between(t,a,b)'), audio and caption tracks untouched. Kid mode always plays this rendition, and the on-device countdown card and cover run on top as a second layer. If GATE 1 fails, the video and README say plainly that protection comes from the pre-covered rendition and the on-device layer is best effort.

PHASE 2: FLASHMAP V1 AND SCREENING DAY (Sep 18 to 25)
2.1 flashmap already implements WCAG 2.3.1 general and red flashes (including the saturated-red chromaticity rule), ITU-R BT.1702-3 for SDR, sliding 10-degree area windows of several sizes, Ed25519-signed maps bound to the file's SHA-256, and correct color handling (untagged HD decodes as BT.709, untagged SD as BT.601, yuvj formats as full range). Treat headstart/flashmap/docs/SPEC_SOURCES.md as the only source for thresholds. Never re-derive a threshold from memory; if a rule needs a new number, quote the spec text and link it in SPEC_SOURCES.md first.
2.2 Add, each with tests:
    - variable frame rate input (use real frame timestamps, never an assumed fps);
    - letterbox and pillarbox detection (area is measured on the picture, and the report says so);
    - robustness to burned-in subtitles and small UI overlays;
    - chunked analysis with overlap, plus a property test that chunked output equals whole-file output;
    - the room rule: hide a segment if it breaks the WCAG window OR the window computed from the family's TV size and seat distance. The room setting can only add hides, never remove them ("never weaker than WCAG");
    - a versioned JSON schema for the map sidecar in docs/SIDECAR_SPEC.md (keep flashmap's current map format as version 1);
    - the GitHub Action (action.yml) that fails a pull request adding images or videos that break WCAG 2.3.1, with a sample workflow and a test repo fixture;
    - tagged, untagged and full-range test clips in the suite.
2.3 The BT.1702-3 HDR rule is a stretch goal (first item on the cut list).
2.4 GATE 2, screening day (by Fri Sep 25):
    - Candidate pool: headstart/calm-vega-notes/STRESS_TEST.md section 4 (Blender open movies, NASA ISS lightning time-lapses, NASA SVS 5011, NOAA NSSL B-roll, DVIDS flare and fireworks footage, Wikimedia Commons lightning and fireworks clips, 1930 public-domain films, Apple's sample video for baseline sanity only).
    - Download a file only after you've opened its source page and confirmed the license and credit line. Record URL, license, credit line, SHA-256, duration and resolution in media/LICENSES.csv. Files live under media/ (gitignored). Never commit hazardous media.
    - Known license conditions: Tears of Steel is CC BY 3.0 only while the credit scroll is kept; Blender logos are excluded from the Blender Studio licenses (cut them from anything we show); DVIDS asks for a non-endorsement notice and says insignia may be trademarks; follow the NASA credit-line guidance; keep the Hell's Angels (1930) title out of the video (trademark); anything marked "verify" must be verified or dropped.
    - Rename anything flagged to HAZARD_<name>. Never open hazard files in a player. Inspect them only as luminance and area plots made by eval/plots.py, a separate script that does not import flashmap.
    - Run flashmap (and IRIS once it builds) over the whole pool. Write per-source counts of flagged segments to results/screening.json.
    - PASS: at least 15 real flagged segments from at least 4 sources (a planning target, not a spec number). If short: HUMAN CHECKPOINT C (my self-filmed clips), then 1930 public-domain films. The README states the real mix, including how many positives are self-filmed.
2.5 Baselines, each in Docker with a pinned version and a make target:
    - EA IRIS (BSD-3-Clause; C++ with CMake, Ninja and vcpkg; the repo has no Dockerfile, so write one; -v for the video, -j for JSON; per-frame codes 0 pass, 1 warning, 2 extended failure, 3 failure). vcpkg builds OpenCV slowly, so start this on day one.
    - Apple VideoFlashingReduction (MIT; the Swift version on a Mac with Xcode, or the MATLAB version under Berkeley's license). It outputs a 0 to 100 risk score from whole-frame average luminance and is causal, so state the threshold used.
    - ffmpeg's photosensitivity filter (drop its first second of output, which misfires even on a static gray clip), re-analyzed with the same metrics.
    - Naive mean-luminance differencing.
    - Optional: Amazon Nova on Bedrock, which samples video at 1 frame per second for clips up to 16 minutes, to show why a sampled vision model can't do this job.

PHASE 3: THE PIPELINE (Sep 23 to Oct 2)
3.1 Local first. pipeline/ingest.py takes a video and does, idempotently and keyed by SHA-256:
    probe (fps timestamps, color tags, resolution, duration) -> flashmap analyze for each preset (WCAG, broadcast, extra-cautious) -> hide plan (segments plus guard band, merged, red segments always opaque) -> kid-safe HLS rendition per preset (Plan B) with audio and captions untouched -> verify -> BIF trickplay generated from the safe rendition only -> poster frames chosen from calm moments -> signed map -> catalog entry.
3.2 The verify step blocks publishing if anything fails:
    - re-run flashmap on each safe rendition: zero violations for that preset;
    - render the on-device cover schedule over the original video (poster, black or dim, modeled in linear light, the stricter case) and re-run flashmap: zero violations;
    - check that every BIF frame and poster comes from a calm moment;
    - check the map signature and hash.
    A title can't appear in kid mode until verify passes.
3.3 Dim mode is allowed only for general (non-red) segments at 90% or darker, and verify must model it. Red segments always get an opaque cover, because dimming doesn't change the red-to-total ratio that WCAG's red rule keys on.
3.4 AWS, with CDK:
    - S3 (private), and CloudFront with signed URLs (or origin access control) for streams, maps, posters and BIFs;
    - one Fargate task (ARM64) triggered by S3 upload notifications, running the same ingest container as local;
    - DynamoDB on demand for the catalog (or a JSON catalog in S3 if simpler);
    - natGateways: 0 with public subnets. The CDK default adds a NAT gateway per availability zone, $65 to $100 a month;
    - least-privilege IAM, a GitHub OIDC deploy role (no stored keys), cost tags, and an AWS Budgets alarm at $20;
    - no Step Functions, EventBridge, Cognito or AgentCore unless the cut list is empty and time remains;
    - make deploy works from a fresh clone, and make destroy leaves nothing billable. Estimate monthly cost in docs/DECISIONS.md (the stress test estimate was under $15 a month without NAT gateways).
3.5 HUMAN CHECKPOINT D: I confirm the AWS account is on the Paid plan (Free plan accounts can't use promotional credits), the budget alarm exists, and the credit request is in.
3.6 Ingest 20 to 30 licensed titles (about 12 Blender films, 4 to 5 NASA ISS time-lapses, 1 NASA SVS visualization, 3 to 8 self-filmed clips).
3.7 GATE 3 (Fri Oct 2): upload a title, get a verified map and safe rendition, and play it in kid mode on the stick with the countdown card and cover. Log it in docs/GATES.md with device logs.

PHASE 4: THE APP (Sep 28 to Oct 13)
4.1 Playback only through @amazon-devices/react-native-w3cmedia (Shaka), rendered in KeplerVideoSurfaceView, captions in KeplerCaptionsView (only one captions view per process is supported). Kid mode plays the safe rendition; the on-device layer runs on top.
4.2 Scheduler: load the whole verified map before play starts. Compute hide intervals (segment start minus guard band to segment end plus guard band; default guard band 500 ms), merge overlaps, and enforce a minimum cover length so nothing flickers.
    - 5 seconds before an interval: a card, "Flashing part coming up", with a Skip button that has D-pad focus.
    - During the interval: the cover (poster frame, or black; opaque for red), drawn as a React Native view above the video surface and below the captions, while audio and captions continue.
    - After it: a one-line card such as "Hid 4 seconds of flashing. Sound and captions kept playing."
4.3 Fail closed. A missing, stale, unsigned, unparseable or wrong-hash map means the picture stays hidden and a card says the title isn't checked yet. Kid mode never lists unverified titles.
4.4 Seek safety. Every way of moving the playhead goes through one function, with tests for each:
    - the focused seek bar (Vega doesn't let apps override D-pad focus movement, so use a focused seek bar);
    - D-pad fast forward and rewind, and BIF trickplay previews (BIFs come only from the safe rendition);
    - Alexa and remote transport commands through Vega Media Controls (@amazon-devices/kepler-media-controls): a KeplerMediaControlHandler subclass from @amazon-devices/react-native-w3cmedia passed to VideoPlayer.setMediaControlFocus, overriding handleSeek, handleSkipForward, handleSkipBackward, handleFastForward, handleRewind and handleStartOver, with the manifest opt-in these commands need.
    Rule: if the target lands inside an interval or its guard band, cover first, then seek, and keep the cover until playback is confirmed outside the interval.
4.5 Accessibility:
    - VoiceView announcements for every card: an aria-live="polite" card plus AccessibilityInfo.announceForAccessibilityWithOptions with { queue: true }, and the com.amazon.devconf.privilege.accessibility privilege in manifest.toml;
    - 10-foot type sizes, strong visible focus states, no motion and no autoplaying previews in kid mode;
    - the app's own screens and transitions pass flashmap: record every screen and transition on the VVD and check the recordings in CI or before every release.
4.6 Parent area behind a local PIN: preset (WCAG, broadcast, extra-cautious), TV size and seat distance (can only add hides), a log of what was hidden and when, and per-title status (verified, pending, failed).
4.7 Kid home: poster grid with shield badges, no autoplaying previews, and a details page with a still flash-map strip showing where the hidden parts are.
4.8 One flow across voice, D-pad and visuals: the countdown, Skip and seek safety behave the same whether Maya uses Alexa, the remote or the on-screen card. Test all three and show all three in the video.
4.9 The drop-in hook: hook/ ships useFlashGuard for any Vega app that uses react-native-w3cmedia. Give it the player and the map URL; it handles the schedule, cover, cards, announcements and seek safety. Prove it with a diff against a clean vega-video-sample checkout in docs/INTEGRATION_DIFF.md, ideally under 60 lines.
4.10 Device performance on the cheapest stick with the App KPI Visualizer (vega exec perf kpi-visualizer): cool-start time to first frame under 1.5 s, time to fully drawn under 8.0 s (mark it with useReportFullyDrawn), foreground memory under 400 MiB, video fluidity above 99%. Write results/kpi.json.
4.11 Offline safety net for judges: bundle one short non-hazardous title (self-filmed or CC BY) and its signed map inside the .vpkg, so the app still works if the backend is down.

PHASE 5: EVALUATION (plan committed Sep 29; runs Oct 5 to 16)
5.1 Commit docs/EVAL_PLAN.md before labeling any real clip: metrics, thresholds, sample sizes, exclusion rules and the exact analysis scripts. Changes after that are logged as deviations.
5.2 Conformance suite: about 3,000 generated clips with ground truth computed from the spec text, not from flashmap. Vary:
    - flash rate 1 to 30 Hz; luminance step size and the darker-image condition;
    - flashing area 1 to 60% of the screen; red vs near-red;
    - frame rate 24 to 60 fps plus variable; resolution 480p to 4K; compression level; SDR (HDR only if built).
    Put 40% of clips near a threshold. Report precision and recall per one-second window with Wilson 95% intervals, plus error curves along each threshold. Generated clips are hazardous by design: generate, analyze and delete them in the same job, and never open them. Cross-check a stratified sample against IRIS (agreement and kappa) and against the TRACE ground-truth generator from Jordan's HCII 2025 paper, if it's public.
5.3 Real clips: about 40 segments from the screening pool, labeled by blind pooled review of plots from eval/plots.py. Rachel double-labels a subset for Cohen's kappa. Bootstrap over titles for intervals. Report positives per source.
5.4 Baselines (Phase 2.5) on the same sets with the same metrics, in one table.
5.5 Screen-level test (HUMAN CHECKPOINT E2, Oct 8 to 13): at least 200 events on the stick, filmed at 240 fps with exposure locked and calibrated against a luminance step chart. Film a static gray screen before each run to check for backlight flicker.
    Events are non-flashing markers under a sham flash map, plus real flagged titles played only with the filter on and nobody watching the screen. Never play real flashing content with the filter off; compute the exposure the filter prevented from the flash map instead.
    Report leaks (0 of 200 gives an upper bound near 1.5% at 95%) and cover lead time (median, p95, worst). The harness ingests my recordings with calmtiming roi, analyze and combine.
5.6 Ablations: remove the red rule, the area rule, the darker-image rule and sRGB linearization, one at a time; guard band 0, 100, 250 and 500 ms; dim vs opaque cover.
5.7 Red team, each case an automated test where possible: seeking or Alexa-skipping into a segment; rapid scrubbing; trickplay; rebuffering and stalls; backgrounding and resume; missing, stale, tampered or wrong-hash maps; variable frame rate; letterboxing; burned-in subtitles; the app's own transitions; clock drift across a 2-hour title; playback speed changes.
5.8 Every number in the README, Devpost text and video comes from results/*.json through evkit readme_sync, and CI fails on drift. make reproduce rebuilds every table and figure offline from committed results.

PHASE 6: SECURITY AND ENGINEERING (all the way through)
- gitleaks in CI and as a pre-commit hook. No keys in the repo; AWS through GitHub OIDC only.
- The map-signing private key never enters the repo. The app ships the public key; document key rotation.
- Make targets: make test, make reproduce, make deploy, make destroy, make release. make release builds .vpkg files for armv7, aarch64 and x86_64 and attaches them to a GitHub Release with install steps and the demo PIN.
- Pin dependency versions. Publish flashmap to PyPI with trusted publishing (no stored token) and the hook to npm, if time allows (PyPI and npm accounts are my step).

PHASE 7: SUBMISSION PACKAGE (Oct 14 to 22)
7.1 README, written for people and for automated review:
    - the thesis in one paragraph, then stills (no GIFs, nothing that flashes);
    - an architecture diagram;
    - a "required tech at runtime" table linking the exact lines that call the W3C media player, Vega Media Controls, the accessibility APIs and KeplerCaptionsView, plus timestamped device logs;
    - the results table (synced from results/);
    - install steps for the stick and the VVD, the demo PIN, and how to run the pipeline;
    - limits, safety wording, licenses and credits.
7.2 docs/SUBMISSION.md with every Devpost field ready to paste: name, tagline, description, track (Fire TV), mini challenges (Open Source and AWS Builder), repo URL, video URL, testing instructions, product feedback (Amazon's five questions for every tool), AWS services and how we used them, the Open Source fields, feature requests with priorities (include a system-wide Fire TV "dim flashing lights" setting), and the friction log entries. Mark every field that needs me.
7.3 Open Source mini challenge. The rubric rewards meaningful features with tests, fixes that unblock other developers, and new integration patterns, and calls README and typo fixes obvious. Ship flashmap (CLI, conformance tests, GitHub Action, sidecar spec) and the hook, and open one real upstream pull request by Oct 12 so the contribution URL exists:
    - first choice: a pull request to AmazonAppDev/vega-video-sample adding the optional flash-guard integration, with tests;
    - if that repo doesn't take outside pull requests, a fix or feature with tests for a library we depended on and found lacking during the build.
    It doesn't need to be merged by the deadline.
7.4 The video (docs/VIDEO_SCRIPT.md with timestamps, under 3:00; judges don't have to watch past 3:00). Follow VIDEO RULES below.
7.5 Final checks on Wed Oct 21:
    - a fresh clone passes make test and make reproduce;
    - make deploy works from scratch;
    - the release .vpkg installs on the stick;
    - README numbers match results/;
    - the license shows in GitHub's About box;
    - the video link works while logged out;
    - flashmap check on the final video file returns 0 violations (commit the result);
    - the secrets scan is clean.
    Then tag the judged release.
7.6 HUMAN CHECKPOINT G (Thu Oct 22): I press submit. Afterward, keep everything live through Dec 3 under the budget alarm and never move the judged tag.

VIDEO RULES
- Open with the real stick running the app, next to a terminal where vega device list shows it connected.
- Film only inside our app (the Fire TV home screen shows other companies' app tiles). Cut Blender logos, mute or credit film music, keep the Tears of Steel credits if it appears, and keep the Hell's Angels title out.
- Never show real flashing content unfiltered, even for a second. Show luminance traces instead.
- The memorable moment, inside the first 60 seconds: the countdown card, then the calm hold with captions running and sound playing, while a camera-fed meter beside the TV stays at 0 and the trace shows the flashes that were hidden. Then Maya says an Alexa skip command that would land inside a flagged part, and the picture stays covered.
- The human story: Maya, 12, picks a movie at a sleepover with no adult screening it first; her dad set her preset and room size behind a PIN. Label Maya on screen as a composite persona.
- Show household adaptation (preset and room settings) and the three input modes (voice, D-pad, card) working as one flow.
- Show the drop-in hook diff for a few seconds, and the Action failing a pull request that adds a flashing asset.
- Wording on screen and in the voiceover: "reduces exposure to flashing above published limits in the videos it plays; not a medical device." Never "prevents seizures" or "seizure-proof".
- Every number on screen comes from results/ and matches the README.

IMPACT CASE (re-check each page before quoting it)
- About 3% of people with epilepsy are photosensitive, more often children and adolescents, and flashing at 5 to 30 per second is the most likely trigger (Epilepsy Foundation, https://www.epilepsy.com/what-is-epilepsy/seizure-triggers/photosensitivity).
- A 2025 Epilepsy Foundation working group consensus advises media designers to avoid bright flashing in the 10 to 20 Hz range (Fisher et al., Epilepsia 2026;67(2), doi:10.1111/epi.18702).
- Other platforms have partial answers (Apple's Dim Flashing Lights setting, desktop tools such as FlashFilter, research prototypes that detect and overlay in real time). Re-check whether Fire TV has any before claiming it has none.
- Our gap: whole titles verified before play, fail-closed playback, seek safety across voice and remote, room-aware thresholds that are never weaker than WCAG, and a hook any Vega video app can add.
- Beyond the hackathon: studios and app makers can check content before publishing with the Action and sidecar spec, and the feedback proposes a system-level Fire TV setting.
- Put any outreach reply, quoted with permission, in docs/VALIDATION.md by Oct 16.

SAFETY FOR THE TEAM (hard rules)
- Nobody watches strobes at full speed. Hazard files carry the HAZARD_ prefix, stay under media/ (gitignored), never autoplay anywhere, and are inspected only as plots or slowed, dimmed playback.
- Generated conformance clips are hazardous: generate, analyze, delete, never open.
- Whoever films flashing footage is not photosensitive and doesn't look at the lights. People in frame give consent.
- docs/SAFETY.md states these rules at the top.

CUT LIST (cut in this order if behind; log each cut in docs/DECISIONS.md)
1. The BT.1702-3 HDR rule
2. The Nova baseline
3. Step Functions, EventBridge, Cognito and AgentCore (already out unless time remains)
4. The Apple baseline (keep IRIS, ffmpeg and naive)
5. Real-clip set reduced from 40 to 25
6. PyPI and npm publishing (keep GitHub Releases)
7. The details-page flash-map strip
Never cut: flashmap correctness, the verify step, fail-closed playback, seek safety, Plan B, the camera test, the friction log, the safety rules.

KILL RULES (all fallbacks keep the entry alive; log each in docs/GATES.md and tell me in one paragraph)
- No supported computer by Sep 19: stop and tell me.
- Stick not on Vega OS 1.2 by Sep 21: SDK 0.23 path. Still stuck by Sep 23: VVD for development while we keep trying the stick.
- Layering test fails: try the transparent WebView overlay, then make Plan B primary.
- Timing gate fails after one tuning round: Plan B primary, and the on-device layer is described as best effort.
- Too few real flagged segments on Sep 25: self-filmed clips and 1930 public-domain films, and the README states the mix.
- AWS blocked (no credits, account issue): run the same ingest container locally, serve from S3 only or bundle titles in the release, and say so in the README.

STRETCH (only after everything above is done)
- A Strands agent on AgentCore uses Amazon Nova on Bedrock to write a spoiler-free one-line description of each hidden segment. It may write only description fields, and a CI test proves the hide schedule is byte-identical with Bedrock switched off. (This also strengthens the AWS Builder case.)
- The BT.1702-3 HDR rule.
- Preset suggestions from the parent's past overrides, stored only on the device.

OUT OF SCOPE
Live streams, other apps' DRM content, an Alexa skill, AAC, a phone upload page (use an upload script), and accounts beyond the local PIN.

STYLE
Plain, warm writing everywhere. No em dashes or en dashes anywhere (docs, UI text, comments, commit messages). Don't use the words "genuinely", "honestly" or "straightforward". Label composite personas, sham maps and estimates. Nothing mocked is shown as real.

HOW TO REPORT
After each phase, update docs/STATUS.md and tell me in chat: what's done, the numbers (from results/), open risks, what you need from me, and the next step.

START NOW
Begin with Phase 0. Before writing any code, print: the detected machine and whether the Vega SDK supports it, the tool versions, the repo plan, the parallel lanes you'll run, and every HUMAN CHECKPOINT with its date.
```

## Keep it running (paste the line for the current phase)

Sep 17 to 23:
```
/goal Phases 0 and 1 are done or waiting only on my steps: docs/ENVIRONMENT.md shows a supported machine and tool versions; all head-start tests pass in CI; the renamed, stripped sample plays a Blender title on the Vega Virtual Device; the layering test and GATE 1 timing harness are ready for my stick recordings; docs/GATES.md, docs/STATUS.md and CLAUDE.md are current, and you have listed exactly what you need from me. Or stop after 60 turns.
```

Sep 24 to Oct 2:
```
/goal Phases 2 and 3 are done: results/screening.json and media/LICENSES.csv are committed with per-source counts; flashmap v1 passes its tests, including the chunking property test and the room rule; IRIS, ffmpeg and naive baselines run in Docker; docs/EVAL_PLAN.md is committed; the local pipeline and the CDK stack (natGateways 0, budget alarm) produce a verified map, a kid-safe rendition and BIFs for at least 5 licensed titles; the GATE 3 steps are ready for me to confirm on the stick. Or stop after 80 turns.
```

Oct 3 to 16:
```
/goal Phases 4 and 5 are done except my filming: kid mode plays verified titles with the countdown card, cover, captions, VoiceView announcements, fail-closed maps and seek safety for every seek source; the hook package and docs/INTEGRATION_DIFF.md exist; the conformance suite, baselines, ablations and red-team tests write results/*.json with intervals; the camera harness ingests my recordings; the upstream pull request is open; README numbers sync from results and CI is green. Or stop after 100 turns.
```

Oct 17 to 22:
```
/goal The submission is ready except my human-only steps: a fresh clone passes make test and make reproduce; make deploy works from scratch; .vpkg releases are attached with install steps and the demo PIN; the final video file passes flashmap with 0 violations; docs/SUBMISSION.md has every Devpost field filled; the friction log has at least 20 real entries; and you have printed docs/SUBMISSION.md and docs/GATES.md. Or stop after 60 turns.
```
