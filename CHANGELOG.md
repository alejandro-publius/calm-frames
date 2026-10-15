# Changelog

What changed in Calm Frames, written for the people who use it and the people
who review it. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**No version has been released yet.** The first tag will be the judged release,
cut from main once the review branch is merged into it. That tag gets its own
section here, and once it exists it never moves. Until then, everything that is
not on main sits under Unreleased.

**Where the dates come from.** Every date is the author date git records for the
commits an entry describes (`git log --date=short`), and the short hashes after
each entry name those commits. Work done on one day and committed on a later one
is listed under the later date, and the entry says so.

**No measured numbers here.** Measurements live in `results/` and reach the
documents through `eval/readme_sync.py`. A changelog entry describes a change
on its date, and a measurement can move after it, so where an entry is about a
measurement it names the results file instead of repeating the number.

## [Unreleased]

The review branch `codex/signed-scene-holds-2026-09-29`, published as draft pull
request #1, on top of main at 7110893 (2026-09-20). Main has not moved since.

### 2026-10-14

The final integration candidate `claude/final-candidate-2026-10-14`, built
from `93cf800` and not yet merged anywhere; `FINAL_HANDOFF.md` has the package.

#### Changed

- Every menu screen paints the approved ivory coast with the dimensional coastal artwork; playback keeps its dark controls. (b22d275)
- A pressed coastal primary keeps its ink fill, the storage error screen's Try again sits on the page where its focus ring clears 3 to 1, the play glyph is drawn at the text floor, and the declared frame inventory and the tests that named the dark palette for menu screens follow the coast. (93cf800)
- A failed player setup reaches the recovery screen at once instead of after the opening timeout, and the release helper never writes a supplied PIN into reviewer notes. (aa0494f, cfddc4a)
- The practice demo's two holds draw bundled copies of their signed stills, swapped in only on an exact match of the authenticated data URI, because the device's image loader refuses data URIs and showed black. (52138fe)
- The opening shell readies on a moving media clock when the device reports no frame counts, instead of ending on the recovery screen fourteen seconds into every playback. (ac5a610)
- The remote's Back closes one level at a time in setup, the profile picker and the remove-a-kid question instead of leaving the app. (487e5e5)
- Debug builds print breadcrumbs for the kid mode view, player mount and exit, focus changes, and artwork and still loads, so a device session without any capture can be judged from the log. (204f185, ac5a610)
- The README opens on the approved coast with labelled browser renders and the docs index lists the handoff and the submission packet. (69390ed)

#### Added

- Ledger rows, NOTICE sections and credits entries for the coastal artwork and for `harbor-illustrated.png`, the latter traced to a pixel-identical render of our own `harbor.svg`. (cf53d39, 58bd1a7)
- The submission packet under `docs/submission/` and the handoff `FINAL_HANDOFF.md`. (fbcbe20, 5065314)
- The coastal control files in the hook package mirror. (53ab01b)

### 2026-10-11

#### Added

- Two opt-in interface effects in parental controls, a gentle entrance for title artwork and quiet menu selection sounds, both Off for new and existing households and held still or silent by system reduced motion, screen reader state and the app's lifecycle; not yet built or observed on a device. (5887b75)
- `docs/MAC_FINISH.md`, the procedure for rebuilding, observing and recording the current source on the Vega Virtual Device, and release preparation that binds the simulator package, the demo and the review bundle to fresh evidence. (52ecf14)
- Prepared library exports keep each title's original verify report under `reports/`, and release preparation refuses a library whose reports are missing. (a7cade3)
- `eval/style_check.py`, which refuses an em or en dash and the three words CLAUDE.md bans in every tracked file we wrote, in CI and in `make ci`. (e2d6ec5, 52d24a4)
- A CI step that rebuilds the complete conformance report from its frozen design and saved rows and fails on any byte that differs. (e2d6ec5)
- A negative control for the app's own screen check, `node tools/ui_flashmap.mjs --negative-control`, which has to refuse a flashing sequence and a grating and measures the refusal rather than trusting an exit code. (ac93f9f, e39c10c)
- A lint rule that refuses playhead writes outside `useFlashGuard.ts`, with the sample's fallbacks and the two audio elements exempted by name, later widened to bracket syntax and increments. (f9d1d52, 4804a7d)
- The precision on clips that sit on a limit, published beside the pooled precision, and what the false positives cost a viewer, published beside the precision that explains them. (086c1f8, f9d1d52)
- `docs/MOCK_JUDGE_3.md`: four independent readers of a fresh clone, one per rubric lens, and what was fixed afterwards. (6dcce8d)
- Ledger rows in `media/LICENSES.csv`, and with them NOTICE and credits screen entries, for the shelf's two pictures, the calm gradient video, the prepared Harbor rendition and the menu sound. (1a97380, f9d1d52, 5887b75, 189fb36)
- The README opens with the product: badges, a labelled browser render, what a family sees, a one-minute try of the analyzer, a "Run the checks" block and a "How this is checked" section. (98ee292, 1b088d1, e592d28)
- More guards in the mutation gate: the five the branch had added, the cover proof's reach to the end of a span, and the two sound fixes. (ba819dc, 41c891e, cf864d4, 9bb14c6)
- Records of the green hosted CI and Audit runs on each pushed head, in `results/github_push_*.json`. (9afacc0, 7eb032f, 9bb14c6, 98ee292)
- `docs/design/README.md`, the one design page: identity, palette, contrast, type, spacing, focus, motion, sound, copy, accessibility, the renders and the limits, with `eval/tests/test_design_page.py` holding it, `tokens.json` and `calmStyles.ts` to each other and recomputing every listed contrast ratio. (fb81a3f, aa34bc1)
- `WRITEUP.md`, the one-page account of why Calm Frames is built the way it is, and `docs/README.md`, an index of every document split into what is for readers and what is a project record. (b340290, 5f256ae)
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates for a bug and a title check, a pull request template that carries the project's rules, and this changelog. (5f256ae)
- An index at the top of `docs/DECISIONS.md` of the twenty calls the design stands on, each linked to its entry or to the code that enforces it. (daeb91b)
- `eval/tests/test_doc_links.py`, which fails on any relative link or heading anchor in the repository's Markdown that lands nowhere. (c73831f)
- ruff over the Python code and strict mypy over the flashmap package, in CI, `make ci` and the pre-commit hooks, with the measured detector files left byte for byte as the conformance record hashes them. (561ad28)

#### Changed

- The dependency audit is green: `xmldom` is an npm alias of `@xmldom/xmldom` 0.8.15, the app's `lodash` is 4.18.1, and every other finding is sorted in `scripts/audit_exceptions.toml` by whether the shipped bundle holds it, with both groups due for review on Oct 21. (bfdd402)
- The artwork and TV layouts are polished: a more prominent Harbor illustration, taller library cards, quieter secondary navigation, clearer viewing settings, and more consistent setup and parental controls. (54dab0b)
- Browsing, saving feedback and setup are refined: a shorter library synopsis, saving feedback in a reserved header space, and a setup that lets a parent revise the room and preset without losing the confirmed PIN. (85c30f9)
- Profile choices stay in the remote focus order while a save is pending, notice actions sit apart from their announcement, and spoken credits include the licence conditions. (a7cade3)
- The Harbor demo says "Practice holds" again where a parent first meets it, and the video narration says the approved sentence in full. (c49fe49)
- The sample GitHub Action pins a commit on this repository and installs flashmap from its own checkout, since no tag and no PyPI release exist. (1b088d1, 4804a7d)
- The Makefile, `scripts/reproduce.py` and the screen check work on a box without fnm or the repository `.venv`. (1b088d1)
- Licence statements a public reader needs: Inter credited in NOTICE, the README and `docs/PRIOR_WORK.md`, and the Amazon proprietary notice on the player wrapper and the Shaka archive stated beside the MIT-0 grant. (5e653d6)
- The documents a fresh session reads first describe the Oct 9 scope instead of Sep 19's, and the docs keep the verified AWS deployment apart from credit coverage nobody has verified. (1e96efd, 5e653d6, ef8bbb4)

#### Fixed

- The cover proof measured a race: `cover_psnr` now compares exactly one frame, and verify samples the first, middle and last frame of every covered span, so the Python tests that had failed on ffmpeg 6.1.1 pass. (41c891e, 4f9d5f7)
- The press that turns Selection sounds on now sounds, and one stuck sound player no longer silences the menu. (9bb14c6)
- Three SHA-256 strings in the Oct 10 native receipt that a PIN scrub had rewritten have their digits back. (361761d)
- The app's bill of materials is written by the hosted runner's npm again, so the Audit job passes. (dbf9ff8)
- README line anchors that had drifted point at their symbols again, and the pipeline walkthrough gives verify the public key it needs, without which it refuses the title. (1e96efd, 1b088d1)
- The screen check says so when flashmap is missing instead of reporting a threshold failure, and checks the analyzer's real entry module. (1b088d1, 4804a7d)
- The video duration tests hand `check_video.sh` their own interpreter, so they pass in a clone with no `.venv`. (7eb032f)
- `pipeline/verify.py` named `CoverInterval` in an annotation without importing it; ruff found it. (561ad28)

#### Security

- CI and Audit run with a read only token, and every action they, the published flashmap action and its example use is pinned to a full commit; `scripts/check_pins.py` runs in CI, holds no exceptions, and refuses to report when its own negative control passes. (77c386c, d0ab78f)
- The app's coverage floors rise from the old placeholders to one point under what is measured, and the totals are written to each run's summary. (77c386c)
- Four identifiers that had no business going public are gone: the validation household's PIN digits, an organizer's name and address, session ids and a subscription tier in two results records, and the owner's account name in paths. None was a secret. (7568f05, e043d80)

### 2026-10-10

#### Added

- The native Harbor journey finished and recorded on the Vega Virtual Device: setup and PIN correction, saved settings, all three presets, playback, both practice holds with captions and audio, transport and remote recovery, with receipts in `results/native_validation_2026-10-10.json` and `results/redesign_validation_2026-10-10.json`. (cffdf7b, 1a8056b, 5c4ab1b)
- A checked English demo video of that build, its finished-file checks under both profiles, and the submission materials. (1a8056b, 5c4ab1b)
- `docs/COMPLETION_CHECKLIST.md`, the single completion checklist. (1a8056b)
- Bills of materials written reproducibly, with each generator and the library under it pinned so the same lock file gives the same bytes. (cffdf7b)
- `docs/AMAZON_SAMPLE_LICENSE_REVIEW.md`, the review of the proprietary notice inside Amazon's MIT-0 sample. (8271b38)
- The pushed branch, the verified review assets in a private draft release and the hosted check results, recorded. (402c167, d451a90)

#### Changed

- The approved native TV design and copy: the Inter typeface, new artwork for Harbor and the gradient, and reworked setup, shelf, details, parental controls and credits screens. (3576365)
- Parent setting focus holds through saves, and the report page's palette matches the app's. (eb20225)
- A title without a check is labelled without implying analysis is running, keeps the hidden-picture guidance while pending, and explains why it is unavailable once. (009857e, cba1a29, 73fbbed)

#### Fixed

- Player initialization and teardown races are closed, and the audit exceptions classify the shipped parser correctly. (c231443)

#### Security

- Dependency scanning refuses an empty, malformed or failed scanner response rather than accepting it as a clean audit. (8271b38)

### 2026-10-09, carrying the Oct 2 and 3 work

#### Added

- The durable household record, work from Oct 2 and 3 committed on Oct 9: profiles, room, preset, chime, salted PIN hash and lockout saved together in a validated, versioned local record, and a record that cannot be read keeps the shelf closed. (8154e27)
- The labelled Harbor demo: original CC0 artwork, a quiet tone, English captions and two practice holds with signed context images, under a demo key accepted only for its exact bundled identity. (8154e27)
- The packaged library: checked local preparation reaches the TV shelf through a bounded, immutable library compiled into the app, with source and archive checks in the build and in CI. (8154e27)
- The complete corrected conformance run in `results/`, after the generator's colour matrix and range encoding were corrected and logged as a deviation. (8154e27)
- A "Checking this title" card while a map is being checked, in place of the refusal card. (1d9e8e4)
- Harbor's poster is the first signed scene still its own map carries, and shelf posters show the name with what the copy is on a second line. (c1d1083, e845aa7)
- A debug line, stripped from Release builds, for every app state change and every media control call, with a test that fails if a callback the SDK declares has no override. (4fc2116)
- The record of the Oct 9 AWS deploy and both cloud runs in `results/aws_deploy_2026-10-09.json`, with a test that fails if it names the account. (187f945)
- Ledger rows for the timing marker clip and the Harbor story, both kept out of the labelling pool. (56ac3e5)
- Refreshed outreach drafts, a Discord check-in and questions for the organizers, none of them sent. (6702a9f)

#### Changed

- The Harbor practice cards follow the real card pattern word for word, and none of them says anything was hidden. (3fabb47)
- Harbor comes first on the shelf with the D-pad focus, and the calm gradient comes last. (986d169)
- Captions start on for a title that ships them, and the caption menu knows which track is showing. (ed4abd2)
- The card hangs above the caption band, and the practice label sits on a corner plate. (a15442d)
- The CDK CLI pin moves to 2.1142.0, the version the deploy needed, with a test that checks it against the library. (3d8caf5)
- `make deploy` carries the cloud signing key parameter through and says when it is left out. (8aadb07)
- The docs describe the Oct 9 deploy and what it does not mean, and the completeness claims are out of the README, the pull request notes and the diff page. (ce8ffe8, 8e69535, 1e534e1, 3e6ef0e, e4ac05e, a2da6e2, eb36428, a722979, 4798828)

#### Fixed

- OK on a countdown card belongs to Skip, so the player no longer pauses under the card. (0bbb04d)
- Profile history clears only after the removal is saved, caption Off turns the native track off, and the final video gate requires strictly less than its duration limit. (8154e27)
- The colour fidelity tolerance is sized from one 8-bit code, so the x86 CI runner passes. (eb59c69)
- Three README line links that the player changes had moved point at their lines again. (956bc65)

#### Security

- A separate cloud demo signing key, which the app does not trust, so a map signed in the cloud plays on no TV. (187f945, ce8ffe8)
- The image build and git both leave out the CDK lookup cache, which holds the account id, and the image build leaves out generated egg-info and pytest caches. (956bc65, d3bfcb7)
- The push script's AWS lock is anchored the way the deploy guard's is. (c9a087b)

### 2026-09-29

#### Added

- Signed scene holds: a checked still from before a hide, bound to the signed map, verified in the prepared MP4, HLS and live cover models, and shown in place of black, with interrupted holds kept black. (e41b79d)
- Local preparation receipts, `pipeline.local_library`, which publish only checked artifacts, withdraw a failed re-import and refuse unsafe paths and overlapping imports. (53cd81b)
- Household viewing plans: the app reviews the chosen household before opening the library, and each verified title explains its preset, room, checked maps and fallback. (53cd81b)
- A CI check of the real hook tarball in a clean offline consumer. (53cd81b)
- A read-only benign hardware preflight. (c5724de)

#### Changed

- The mutation checks refuse a baseline overwrite and an unexpected survivor. (e41b79d)

#### Security

- Metro's vulnerable `image-size` resolution is replaced by a small local adapter over the official fixed parser, with the SDK and Metro versions left as they were. (c5724de)

## main, 2026-09-17 to 2026-09-20

What main holds, up to 7110893.

### 2026-09-18 to 2026-09-20

#### Added

- Conformance clips for the pattern rule, made, measured and deleted in one job, and its spacing test, with the ITC guidance note quoted from an archived copy and no threshold moved. (9098831, 7110893)
- A producer for the hide log, so the parent area shows what was hidden after the player has closed. (f23d964)
- The sidecar spec covers pattern segments. (24f32b7)
- EA IRIS as a fourth candidate list for the labelling pool. (f7770a7)
- A pinned ffmpeg in the container, and a check that a baseline table cannot mix ffmpeg versions. (1467a77)
- A resume section in CLAUDE.md, so a session with no memory starts right. (f109053)

#### Changed

- A pattern has to repeat, not just alternate, so readable text no longer counts as one. (57dedc3)
- A pattern segment always gets an opaque cover because it is a pattern. (73cb8b1)
- Both ffmpeg baselines re-run on one version. (c8ca1da)
- Choosing a profile moves nothing on screen, chosen is a word rather than a colour, and removing a child asks first and then removes the record. (ac1f92f, 46e0944, 89d2686)
- The chime reaches the platform with our own asset. (e840678)
- The report page's timeline cannot form a pattern, and CI checks the page as a reader sees it. (6c514b8, 947eb40)

#### Fixed

- A black edge bar is read as a stripe, not a pillarbox, so a six pair strobe no longer passes. (acd3537)
- `flashmap check` no longer crashes on a pattern. (947eb40)
- The independence guard's docstring said it had been seen to refuse when it had not; it has now been broken on purpose and refused. (2c81da2)
- An empty test file that had kept the app job red is gone. (31ed9ce)
- The check the numbers job runs needs nothing installed, as that job installs nothing. (bba0514)

#### Security

- The shelf asks the signed registry first, and a tampered index gets no fallback. (feb9cf5)

### 2026-09-17

#### Added

- The repository, its Apache-2.0 licence, the environment record and the plan. (387c173)
- The app: Amazon's vega-video-sample at tag v0.24-RN83 added unchanged as `app/`, cut to one interactive component, and playing a Blender title on the Vega Virtual Device. (cf8b752, 3230b7e, f192962)
- flashmap v1, the analyzer, written from scratch. (3915569)
- The local pipeline, the verify step that blocks publishing, the CDK skeleton, and an ingest container that publishes nothing unchecked. (8f6e909, e8fa33d)
- The player's safety layer: countdown, cover and after cards, fail-closed maps, every seek through one function, and the parent area behind a PIN, reachable from the app's first screen. (9da186f, 8a155ff)
- Family profiles, none of which can hide less than the household. (e86aa1f)
- A signed registry of signed maps, and lookup by file hash in the hook. (262200b, 9696b81)
- A chime before the cover, which cannot sound without one. (79b8f78, 4b36b4d)
- The regular pattern rule from ITU-R BT.1702-3, in the broadcast profile only. (98b181b, a253210)
- A self-contained report page for a title, and a local upload page for it. (7d5ae79)
- The drop-in hook for other Vega video apps, and the app's own screens and images checked by flashmap, with a negative control for the images. (c520e85, 89f5cbe)
- CI on Ubuntu runners, with a check that published numbers match `results/`. (060a383)
- The mutation gate, which breaks each safety guard on purpose and requires its tests to go red. (aed79f1, b667f73)
- Property tests, a map fuzz corpus and playback fuzzing on the virtual device, with a CI job for them. (73afb19, 0f6141c)
- A software-level cover lead time on the virtual device, and the late cover it found. (540b1b3, b801653)
- The licensed media ledger, plot-only inspection of hazard files, the baselines, the evaluation plan and the outreach drafts. (daec5b7)
- Credits that say the same thing on the TV and in the repository, written from the ledger, held to it in CI and reachable in the app. (e518dab, 0e847c4, 02a9ea3)
- The rubric quoted from the rules pages, the product feedback, the friction log, the video script, the shot manifest and the submission draft. (0ff7f14, 00001c3, b14bc5e, 62bdd1e, e604e13, e654b74)
- Mock judges 1 and 2. (1f3580f, 3057335)
- The mark, the app tile and the palette. (30ac82e, 044038b)
- A ten foot pass over every screen, measured rather than looked at. (968ee4f)
- The camera meter for the screen-level test, validated on simulated footage. (62be0c6)
- The upstream contribution's branch, two commits with their tests. (fd19f9e)
- The verifier lane's two passes, `docs/VERIFY_PASS_1.md` and `docs/VERIFY_PASS_2.md`, the second of which found the pattern hazard fixed on Sep 18. (1db1237, 6d9270a)
- A gate on the final video file, and a cost estimate for the stack. (42f61da, f74e39e)

#### Changed

- The GATE 1 rehearsal number is withdrawn, because the run it came from never played. (1fc9db8)
- Dropped trials count as failures and that number is published first, and the lead time's spread is published beside its median. (ce2dd25, 54afadf)
- The recall and precision the impact section was leaving out are published. (d6e8ad7, ae53e5f)
- Title counts add up, and a title with nothing to hide is no longer counted as one with a proven cover. (00b2e3b, 7b6d168)
- The scratch pad beside the friction log stops shipping. (95af469)

#### Fixed

- The drift checker reads marker keys that contain a space, which it had been skipping without a word. (18cb257)
- The player subtracts the rendition start offset, which has a bar of its own rather than borrowing the guard band. (4436eda, 475fe3a)
- The media clock stops while the player waits for data, and a seek into a stall no longer reports a position the player never gave. (52cdad4, b10b8d8)
- Theora files decode. (e654b74)
- The app's lock file is committed, so `npm ci` runs in CI instead of every run resolving versions fresh. (0adbff1)
- CI installs matplotlib, whose absence had hidden a real failure. (e756a3a)
- The deploy guard puts the project's Python first, so a fresh clone does not deploy with the wrong one. (2165a04)
- `flashmap check` counts every kind of finding and names it, instead of reporting none for a pattern. (d14356f)

#### Security

- Secret scanning with gitleaks, in CI and as a pre-commit hook. (606d0c1, e654b74)
- Both AWS deploy locks are tested, after one was found open since the day it was written. (2ab4046)
- The threat model, and a test that a map signed by a revoked key is refused. (7eef51b)
- Both dependency ecosystems are audited, and every exception says why in writing. (13a854f)

[Unreleased]: https://github.com/alejandro-publius/calm-frames/compare/main...codex/signed-scene-holds-2026-09-29
