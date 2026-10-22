# Presentation drafts

**Proposals only.** Existing README, Devpost text, screenshot files and live submission are unchanged. The copy below describes the upgraded source `d96c088` evidenced by `13551e4`; the submitted baseline remains `bf2f615`. Review current rules and owner acceptance before using it publicly. No newer Claude benchmark is available in this package.

## Proposed README opening

> # Calm Frames
>
> Prepared nature scenes for Vega, with the evidence behind each edition.
>
> Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device.
>
> Choose a scene, see what will open, and inspect the record behind the selected edition. The preparation tools analyze and verify a title before exact catalog approval. The native player checks its route and signed maps, keeps unresolved pictures covered, and sends seeks through the guard.
>
> This review covers the preparation-recovery and Playback Proof upgrade. The submitted candidate remains separate. Start with the guided review, then inspect the release receipt and its limitations. This is a prototype for an approved packaged library, not a filter for other apps or all streaming content.

Use a labelled native Home capture beside this opening. Link “guided review” to the package entry point after integration. Keep the short product statement ahead of build identifiers; put exact source identity in the adjacent evidence note.

## Proposed Devpost story

### 🌊 Why I built it

Families choosing television content should not have to infer what a reassuring label means. Photosensitivity guidance gives a concrete reason to take flashing seriously, but it does not tell us that a particular app makes viewing medically safe. I wanted to make a bounded workflow inspectable: prepare a title, verify its output, and show the record behind the edition someone can choose.

The intended audience is families where a child has photosensitive epilepsy. I have not established product fit through interviews or clinical research. The prototype reduces exposure to flashing above published limits in the videos it plays; it is not a medical device.

### What it does

Calm Frames presents approved nature scenes on Vega. A viewer chooses Watch deliberately, can read how the selected scene ends, and can open Playback Proof. Source, Prepared and Selection separate the original findings, the checked output and the chosen edition's identity. A missing analyzer version stays visibly missing instead of being guessed.

The app plays its compiled approved library. It does not intercept Netflix, other applications or arbitrary streaming video. The proof page reports existing evidence; it does not analyze a video on demand or authorize new content.

### 🔎 How it is built

The offline preparation tools analyze sources, sign maps, render and verify prepared editions, and export only checked packages. Exact catalog approvals and build-time byte checks bind what ships. The native app uses Vega media APIs with signed-map checks, a cover layer and a guarded seek path. The upgrade adds interrupted-preparation recovery and a remote-readable proof record.

The release receipt records local source checks, exact package identity and virtual-device observations separately. Those are not hosted CI results or physical-TV validation. Recovery was exercised on one Mac/APFS, mostly with scripted analyzer scenarios and one real-analyzer scenario; no power-cut test was performed.

### What I learned

Native behavior mattered where browser previews could not answer: packaged asset URI forms, image-source support, a silent playback statistic, focus during deferred saves and incremental media staging. The accompanying friction draft preserves the expected and actual behavior and proposes narrow SDK improvements. Host lock-screen and browser-policy failures are kept out of those vendor-defect claims.

### Next steps

The submitted baseline is preserved while the upgrade undergoes owner review. Claude owns further native review, benchmarks and the replacement video. Audio and visual acceptance, physical-device and VoiceView work, current official-rule verification and genuine external user research remain open. Newer benchmark results are unavailable here. No adoption, medical outcome or competition score is claimed.

## Screenshot order and captions

| Order | Existing file | Proposed caption and evidence boundary |
|---|---|---|
| 1 | [Home](assets/home.png) | “Choose an approved scene. Existing native Home capture from `60c3bbb`, whose app/hook trees match submitted `bf2f615`; shown for journey context.” |
| 2 | [Details](assets/details.png) | “Know what opens and how it ends. Existing native Details capture from `60c3bbb`, not a new upgrade capture.” |
| 3 | [McWay playing](assets/f15-mcway-playing.png) | “The selected McWay edition on the upgraded `d96c088` virtual-device build. Still from a shorter run; the separate full-duration observation rests on traces.” |
| 4 | [Selection proof](assets/f04-proof-selection.png) | “Acadia's selected edition matches its approved record. Media bytes are checked at build time; the page does not rescan the video.” |
| 5 | [Reading stop](assets/f07-reading-wcag.png) | “The analysis record can be reached with the remote on `d96c088`. This is not a full VoiceView acceptance result.” |
| 6 | [Missing version](assets/f12-mcway-proof-prepared.png) | “Evidence limits stay visible: the output analyzer version is not recorded in this McWay report.” |
| Optional context | [Architecture](assets/architecture.png) | “Original project diagram of preparation, approval and guarded playback. Documentation, not a native app screen.” |

Do not sequence these as frames from one continuous recording. Preserve crop provenance and the visible content. Do not alter screens to make controls or proof look newer. Full media credits are in the [capture record](evidence/capture-history.md); retain them with public reuse.
