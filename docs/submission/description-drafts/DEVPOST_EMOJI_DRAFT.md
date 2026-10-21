# Calm Frames: Devpost story draft

Editorial status: separate presentation draft, not pasted or submitted. Based on published source `63e20d5` and installed app `60c3bbb`. The final video remains under separate review. Do not supply team membership, personal survey answers or legal acceptance from this copy. This file leaves the existing submission draft and video work untouched.

Suggested tagline: **Quiet nature scenes for Vega TV, with prepared media and control over when motion starts and stops.**

---

# 🌊 Calm Frames

### A quiet place on your TV. A scene with time to breathe.

Calm Frames brings Ocean and Forest into a remote-first TV experience. Choose a place, understand what will happen, and decide when to watch.

The moving McWay Falls scene stays with one fixed coastal view for five minutes at natural speed. When it finishes, the audio fades and the final frame stays until you leave.

**CHOOSE → UNDERSTAND → WATCH → SETTLE**

## 💡 Inspiration

A nature app should not feel like a rushed highlight reel.

Early feedback made that problem concrete: the short clips changed and ended too quickly, and the viewing experience was uncomfortable. Passing an analyzer did not mean the experience worked for the person watching.

We changed the product around that feedback. McWay now provides sustained viewing with a deliberate ending. Acadia, Sea otters and Forest remain available as silent still scenes, with moving previews as separate choices.

## 🎮 What it does

→ Browse Ocean and Forest on a coastal map.

→ Open Details to see the scene, duration and expected ending.

→ Choose Watch explicitly; browsing does not start a video.

→ Pause, resume or use Back when you want to leave.

→ Let McWay finish without an automatic repeat or sudden return Home.

→ Stay with its final picture for as long as you choose.

The same warm surfaces, Fraunces titles, Source Sans 3 controls and visible focus connect Home, Details and loading. Household settings live behind a PIN. Optional interface motion respects reduced motion.

## 🛠️ How we built it

The TV app uses React Native, TypeScript and Amazon's Vega W3C media APIs. The nature library is prepared before playback, with a Python pipeline and ffmpeg.

**SOURCE → ANALYZE → PREPARE → VERIFY → PACKAGE**

Each edition keeps a source identity, a rendition identity, signed analysis maps and verification reports. Build checks match approved registrations and packaged bytes. At runtime, the selected route and signed map must match the compiled catalog before the picture can be uncovered.

The player keeps a separate cover scheduler and guarded seek path. A new media file cannot grant itself trust by supplying its own key. The shipped catalog can be built and played without distributing a signing private key.

## 🧩 Challenges we solved

**Making ambient viewing feel sustained.** We replaced the short-reel default with a continuous licensed scene and explicit stationary endings. McWay uses natural speed, no inserted cuts and no repeated loop.

**Getting the native ending right.** A final-frame image initially enlarged beyond the intended bounds. We corrected its native viewport sizing and inspected the actual ending again. The hold now retains the scene framing and a clear Back action.

**Keeping media identity intact.** The source, encoded rendition, signed map and final still have different roles. We kept those roles explicit while preparing every preset and preserving the other approved titles.

**Separating tests from what people experience.** Source tests, file verification and native observations answer different questions. None is a substitute for the final picture and sound review.

## ✅ Results and evidence

The recorded full source baseline passed <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.fullJestPassed -->1698<!--/n--> app tests with <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.skipped -->4<!--/n--> skipped. TypeScript passed; lint reported <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.eslintErrors -->0<!--/n--> errors and <!--n results/mcway-activation-2026-10-21/verification.json:sourceChecks.eslintWarnings -->108<!--/n--> warnings. The later ending-bounds fix passed its targeted tests, TypeScript and focused lint.

The aarch64 Debug package is built and installed. Native sessions observed full-duration playback, pause/resume, Back and the corrected final-frame picture. The repository contains actual native screenshots, a code-linked architecture map and the exact build and media evidence.

These are recorded checks, not a claim of a new full-suite run after every documentation change or green hosted CI on the latest candidate.

[Code, screenshots and evidence](https://github.com/alejandro-publius/calm-frames/tree/claude/ocean-layout-fix-2026-10-19). The repository is private; authorized reviewers need access.

## 🧰 Built with

📺 Vega OS and Amazon W3C media APIs

⚛️ React Native and TypeScript

🐍 Python and the project's flashmap analyzer

🎞️ ffmpeg and PyAV

🔏 Ed25519 signatures and exact-file hashes

🧪 Jest, pytest, Node checks, TypeScript and ESLint

🎨 Fraunces and Source Sans 3

Codex/ChatGPT and Claude assisted development, debugging, editing and tests. The TV app does not call a generative-AI service at runtime.

## 🔎 Limits and current status

Calm Frames plays its prepared catalog. It does not filter other apps, Prime Video or live TV.

“No flagged scenes” describes an analyzer finding. It is not a safety certificate. Calm Frames is not a medical device, has not been clinically validated, and cannot guarantee individual comfort or detection of every hazard.

Final edited-demo review, public video upload and Devpost submission remain open. Physical Fire TV timing measurements and full VoiceView acceptance are not claimed.

## 🌱 What's next

The next steps are to finish reviewing the edited demo and its sound, complete the required submission details, and gather feedback on the sustained viewing flow. Physical-device and broader accessibility testing remain future work.

Longer or additional scenes would require suitable licensed sources, the same preparation and verification process, and exact edition approval. They are not shipped features of this build.

## 🎞️ Media credits

McWay Falls footage and final still: **MoneySavingVideos**, *♥♥ Relaxing 3 Hour Video of a Waterfall on an Ocean Beach at Sunset*, [source](https://commons.wikimedia.org/wiki/File:%E2%99%A5%E2%99%A5_Relaxing_3_Hour_Video_of_a_Waterfall_on_an_Ocean_Beach_at_Sunset.webm), [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).

Changes: first five-minute excerpt, downsampled to 720p, H.264/AAC encoding, a three-second ending audio fade, and an extracted final-frame still. Native screenshots are cropped to the app picture area. No endorsement implied.

Other visible title imagery: **NPS Video, Acadia National Park**; **NOAA Fisheries**; **NPS: G Litten** for Prairie Creek and Redwood. No agency endorsement implied. The repository's media ledger and NOTICE preserve the individual source credits and terms.
