# Calm Frames

**A verified safety layer for Fire TV, for kids with photosensitive epilepsy.**

Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device.

---

## What it is

Calm Frames combines an offline video analyzer, a checked rendition pipeline and a Vega player for families affected by photosensitivity. Before playback, the pipeline analyzes the source, signs its flash map and verifies the prepared rendition. The player adds a scheduled cover, context images and guarded seeks, with audio and captions intended to preserve the story. Parent settings can make the standard floor stricter and now persist locally. A reusable hook and analyzer provide adoption paths for other developers. Detection, delivery integrity and physical screen behavior have separate limits, recorded below; a signature is not proof that every hazard was detected.

**Status, Oct 2 2026.** This is a build in progress for the Fire TV track of Build, Ship, Shape: Amazon Developer Hackathon. The analyzer, the pipeline, the cover layer and the measurement harnesses are built and tested. Nothing has been measured on a physical Fire TV stick yet, so there is no screen-level cover lead time. There is a software-level one from the virtual device: of the <!--n results/gate1_software_vvd.json:trials_attempted -->55<!--/n--> trials started, <!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> covered in time. Six produced no usable evidence and one was late. Counting the six as failures, which is the strict reading, that is <!--n results/gate1_software_vvd.json:in_time_strict_fraction -->0.8727<!--/n-->, not the <!--n results/gate1_software_vvd.json:in_time_fraction -->0.9796<!--/n--> you get from the trials that could be measured. Every number below says where it came from, and the rows with nothing in them are measurements that have not happened.

**Scene holds, Sep 29.** Hidden intervals can now show a checked still from the
preceding context, helping keep the story in view while audio and captions continue.
The pipeline binds each JPEG to the signed map and uses the same image in the
pre-covered rendition and the live-cover model. Missing images, uncertain
playback, seeks and image decode errors use an opaque black cover. This changes
the presentation, not the detector thresholds or hide timing. Native image and
caption composition still need a physical-device check.

The current [hackathon assessment](docs/HACKATHON_REVIEW.md) separates the
project score from missing submission evidence. The [continuation prompt](docs/CONTINUATION_PROMPT.md)
provides the next agent with an evidence-driven improvement loop.

## Contents

- [How it fits together](#how-it-fits-together)
- [Who it is for, and how it leaves this hackathon](#who-it-is-for-and-how-it-leaves-this-hackathon)
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

## Who it is for, and how it leaves this hackathon

Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device. Everything below is written inside that sentence.

Two of the Fire TV track's six priority categories are this project by name. It is **family entertainment**, because the whole thing exists so that a child can pick a title on the family television without a parent having to preview it first. And it is **multi-modal UX**, because voice, D-pad and on-screen cards are not three ways into the same app, they are three inputs to one seek function that covers the picture before it moves the playhead. A spoken "skip forward" and a press of the remote go through the same gate, and neither can land inside a flagged interval. That single flow is the part that does not work if you build it three times.

### The people

The Epilepsy Foundation's page on photosensitivity says this:

> For about 3% of people with epilepsy, exposure to flashing lights at certain intensities or to certain visual patterns can trigger seizures. This condition is known as photosensitive epilepsy or visually-provoked seizures.

Read that number carefully, because it is easy to repeat wrongly. It is about 3% **of people who have epilepsy**, not 3% of people. The same page says who it lands on:

> Photosensitive epilepsy is more common in children and adolescents, especially those with generalized epilepsy and with certain epilepsy syndromes, such as juvenile myoclonic epilepsy and epilepsy with eyelid myoclonia (Jeavon's syndrome). It becomes less frequent with age, with relatively few cases in the mid-twenties.

And what sets it off:

> Generally, flashing lights between the frequency of 5 to 30 flashes per second (Hertz) are most likely to trigger seizures. However, this number varies from person to person. The likelihood of such conditions combining to trigger a seizure is small.

That last sentence is the Epilepsy Foundation's own caution and it belongs here as much as the rest. This is not a common event. It is a rare event with a bad outcome, landing mostly on children, in front of a screen, and its first two items on that page's list of triggers are television screens and TV broadcasts with rapid flashes.

The Epilepsy Foundation's expert panel published its current consensus in *Epilepsia*: online on Nov 24, 2025, and in the February 2026 issue. Both dates are the same paper, and the citation below carries both, because a reader who meets one of them somewhere else should not think there are two. Two sentences from its abstract say why a tool like this one can exist at all:

> Media designers of video games, movies, TV productions, web videos, and artificial or virtual reality images are advised to avoid bright flashing patterns in the 10-20 Hz range, repetitive color flashes, and oscillating or static stripes of ~1-8 cycles per visual degree. Signal analysis or trained human inspectors can identify provocative visual patterns.

The same abstract records that "Government and regulatory agencies require screening of potentially provocative media in some nations", and calls visually provoked seizures "both an individual and public health problem".

**Signal analysis or trained human inspectors.** Broadcasters have had both for years. A living room has neither. A child picks a title, it plays, and nobody has looked at it. Calm Frames is the signal analysis, run before the title can be chosen, with the result signed and carried to the player.

**What these sources are not.** They are why the problem is real, not where our thresholds come from. Every threshold in this project comes from [`flashmap/docs/SPEC_SOURCES.md`](flashmap/docs/SPEC_SOURCES.md) and nowhere else, which means WCAG 2.2 SC 2.3.1 and ITU-R BT.1702-3. The 10 to 20 Hz range and the stripe guidance in the consensus paper are not implemented and are not claimed. Neither source says that hiding flagged segments prevents a seizure, and neither do we.

### Four things that outlive the deadline

The app is the demo. These four are the part that keeps working after the judging period, and none of them needs anyone to install Calm Frames.

**1. The hook, so any Vega video app gets the same protection.** The guard is one React hook with no knowledge of our screens, navigation or storage. [`docs/INTEGRATION_DIFF.md`](docs/INTEGRATION_DIFF.md) is the real `git diff` of adding it to a clean [AmazonAppDev/vega-video-sample](https://github.com/AmazonAppDev/vega-video-sample) checkout at tag `v0.24-RN83`: <!--n results/integration_diff.json:lines_added -->32<!--/n--> lines added and <!--n results/integration_diff.json:lines_replaced -->2<!--/n--> replaced across <!--n results/integration_diff.json:files_touched -->4<!--/n--> files. <!--n results/integration_diff.json:busiest_file_lines_added -->23<!--/n--> of those added lines are in one file, `src/screens/PlayerScreen.tsx`, and each of the other three files adds exactly <!--n results/integration_diff.json:other_files_lines_added_each.0 -->3<!--/n--> lines. `hook/tools/make_integration_diff.mjs` regenerates that patch from the pinned checkout, and `eval/integration_diff_stats.py` counts what is committed file by file, so every number in this paragraph is measured rather than asserted.

What an app gets for it: every flagged part of a title hidden before it starts while sound and captions keep going, a card ahead of it with a D-pad Skip and a card afterwards, a missing or stale or unsigned or wrong-hash map keeping the picture hidden, every seek path safe including Alexa and the remote's transport commands, and a VoiceView announcement for each card. What it costs: one rule, which is that nothing in the app writes `currentTime` or calls `fastSeek` any more. Everything goes through `guard.requestSeek`. The package README is [`hook/README.md`](hook/README.md). **The package is not published to npm yet**, but a Vega app can now install a locally packed tarball from a reviewed checkout. The offline consumer check uses that installed tarball, current Vega peer types, Metro resolution and React Native transforms, not repository-source aliases. The name `@calm-frames/flash-guard` was free when we checked on Sep 17, 2026, and that is the whole of the claim on it.

**2. The GitHub Action, so a studio can catch it before it ships.** [`flashmap/examples/flash-check.yml`](flashmap/examples/flash-check.yml) drops into any repository that holds images or video. Every pull request that adds or changes one is measured against WCAG 2.2 SC 2.3.1, and the job fails when a file goes over the general or red flash thresholds. Exit codes are `0` under the thresholds, `1` over them and `2` when flashmap could not tell, and a caller that treats `2` as a pass has a hole in it. The analyzer is Apache-2.0 and runs standalone, so this works for a studio, a game team, a marketing site or a documentation repository with animated GIFs in it, none of whom have to care that Calm Frames exists.

**3. The sidecar spec, so a map is portable.** [`docs/SIDECAR_SPEC.md`](docs/SIDECAR_SPEC.md) is the flash map format, version 1: what was measured, under which profile, with which colour assumptions, which segments were flagged, and an Ed25519 signature over a canonical serialization bound to the source file's SHA-256. It is written so that a player that has never seen our code can read a map it did not make, check the signature and the hash, and honour it. That is the difference between one app having a feature and a format existing. The spec also has a section on what a map does not say, which is the part a second implementer needs most.

**4. The feature request, because this should not be an app's job.** Photosensitivity is a property of a person, not of an app. A child should not have to hope that whichever app they opened happens to have built protection into it. The request we are filing with Amazon, as **Critical**, is a **system-wide Fire TV "dim flashing lights" setting** in Accessibility settings, next to the options already there, that any app can read and honour.

This is not a thing nobody has tried. Apple's Media Accessibility framework documents exactly this, and its developer page says:

> The Dim Flashing Lights setting allows the system to calculate, mitigate, and inform people about flashing lights in a piece of media.

> Dim Flashing Lights is a setting that allows a person to indicate that they want to avoid bright, frequent flashes of light on their Apple device. When a person turns on this setting, the device automatically dims video content when the system detects flashing or strobing effects.

A person turns it on at Settings, Accessibility, Motion. An app can read whether it is on, can register for a notification when it changes, and Apple ships `MAFlashingLightsProcessor`, described in the same documentation as "A class that processes a framebuffer object to detect and dim sequences of flashing lights". So the setting, the query, the change notification and the processing class all exist, and they are documented for app developers to use.

We have not found an equivalent on Fire TV. That is a statement about what we looked for and did not find, not a proof that nothing exists, and it is the first thing the request should be checked against by someone inside the Fire TV team. The gap we are describing is not the idea, it is the platform. A system setting turns this from one app's feature into a guarantee, gives every developer a single flag to respect, and would reach the children this project is about faster than any app could. It is request 1 in [`docs/FEEDBACK.md`](docs/FEEDBACK.md), at the top of the list of everything we would ask the Fire TV team for.

Two differences are worth being clear about, because they are the reason this project exists rather than being a copy. Apple's detection runs on the device, in real time, on the frames as they are drawn. Calm Frames analyses the whole title ahead of time, signs the result, and the player acts on a schedule rather than on what it has just seen, which is what makes it possible to cover a flash **before** its first frame instead of dimming after it starts. And Apple's approach needs no cooperation from the app, while ours needs a signed map, which means it only ever protects content somebody measured.

### How any of this would actually reach somebody

The rules ask whether a project "could realistically serve an audience beyond the hackathon", and give the Fire TV Appstore as the example. So, plainly, and without promising anything:

- **The analyzer and the Action need no distribution at all.** `flashmap` is Apache-2.0 and standalone. A studio, a game team or a documentation repository adopts it by copying one workflow file. That route is open today and needs nobody's permission.
- **The sidecar spec needs adoption, not distribution.** It is worth something the moment a second player reads a map it did not make. That has not happened and it is the thing we would most like to be asked about.
- **The hook needs publishing.** It is not on npm yet. Local tarball installation is checked with the current Vega peers, not a fresh registry or physical-device install.
- **The app itself would need the Fire TV Appstore, and we have not started that.** No developer account submission, no listing, no policy review. A safety claim in a store listing is a different bar from a safety claim in a README, and the wording would have to be checked by someone qualified before it went near a store. **We are not claiming a route we have not walked.**

The honest shape of it: three of the four things above can travel without us, and the app is the one that cannot. That is the opposite of how most entries are built, and it is deliberate.

### What has not been shown

- **Nobody outside this project has used it or commented on it yet.** No parent, no clinician, no studio. [`docs/VALIDATION.md`](docs/VALIDATION.md) is the place those quotes will go, and it is marked as empty until they arrive. Nothing in this README should be read as anyone else's endorsement.
- **It is not a medical device and it does not prevent seizures.** It reduces exposure to flashing above published limits in the videos it plays.
- **Only titles that passed verify are protected, and passing verify means two different things.** <!--n results/verify_pool.json:analyzed -->30<!--/n--> titles have a verdict. <!--n results/verify_pool.json:cover_proven_drawn -->7<!--/n--> had a flagged segment, a cover planned for it, and the cover measured on the rendition that plays. <!--n results/verify_pool.json:no_flagged_segments -->14<!--/n--> had no flagged segment at all: the analyzer looked and nothing was over the thresholds, which for cloud and sunset footage is the right answer and is not evidence that any cover works. <!--n results/verify_pool.json:failed -->9<!--/n--> failed and cannot play. **The 7 is the number to read as evidence**, and adding more calm footage raises the other one without adding any. Anything that was never through verify was never measured. The rest of what is not true yet is in [Limits](#limits), including the fact that no cover has been timed on a physical stick.

### Where the numbers here came from

The three numbers about the integration diff are markers pointing at `results/integration_diff.json`, and CI fails if they drift, the same as every other number in this README. The two quoted statistics are not ours: they are quoted from their sources below, with the date each was read, and they measure the problem rather than this project.

**Sources, re-read on Thu Sep 17, 2026.**

1. Epilepsy Foundation, "Photosensitivity and Seizures", reviewed by Elaine Wirrell MD.
   <https://www.epilepsy.com/what-is-epilepsy/seizure-triggers/photosensitivity>
   **How it was read.** The live page returned HTTP 403 to every automated request from this machine, which is a Cloudflare bot check rather than a missing page, so the text quoted above was read from the Internet Archive's capture of that URL taken on **Aug 16, 2026**: <https://web.archive.org/web/20260816074759/https://www.epilepsy.com/what-is-epilepsy/seizure-triggers/photosensitivity>. Quoting an archived capture is quoting what the page said on a date, not what it says today. Open the live URL in a browser and confirm these three sentences before the submission goes in.
2. Fisher RS, Wilkins A, Takahashi Y, Thio LL, Acharya J, Alkhaldi M, Baumer FM, Beran RG, Craiu D, French J, Mirza N, Parisi P, Solodar J, Szaflarski JP, Tolchin B, Kasteleijn-Nolst Trenite D. "Visually-provoked seizures: Consensus of the Epilepsy Foundation Working Group." *Epilepsia*. 2026;67(2):565-581. doi:[10.1111/epi.18702](https://doi.org/10.1111/epi.18702). Published online Nov 24, 2025.
   **How it was read.** The DOI resolves to Wiley Online Library, which returns HTTP 403 to automated requests, so the record was confirmed twice against databases instead: Crossref, and PubMed (PMID [41283196](https://pubmed.ncbi.nlm.nih.gov/41283196/)). Both agree on the title, all sixteen authors, the journal, volume 67, issue 2 and pages 565 to 581. The sentences quoted above are from the published abstract as PubMed renders it. **Only the abstract has been read.** Nothing in this project cites the body of that paper, and no threshold comes from it.
3. Apple Developer Documentation, Media Accessibility: "Flashing lights" (<https://developer.apple.com/documentation/mediaaccessibility/flashing-lights>) and "Responding to changes in the flashing lights setting" (<https://developer.apple.com/documentation/mediaaccessibility/responding-to-changes-in-the-flashing-lights-setting>).
   **How it was read.** Both pages render their text in the browser, so fetching the HTML returns the navigation and nothing else. The quoted sentences come from the documentation content that those same pages load, at `developer.apple.com/tutorials/data/documentation/mediaaccessibility/flashing-lights.json` and the matching path for the second page, both fetched on Sep 17, 2026. Nothing about Apple's implementation is claimed beyond what those two pages say.

## Required tech at runtime

Every row links the exact file and line in this repository. Line numbers are against the commit containing this README; the symbol name is given too, so a moved line is still findable.

| Required technology | Package | Called at | What it does here |
|---|---|---|---|
| **W3C media player** | `@amazon-devices/react-native-w3cmedia` | [`app/src/utils/VideoHandler.ts:147`](app/src/utils/VideoHandler.ts#L147) `new VideoPlayer()`, imported at [`:5`](app/src/utils/VideoHandler.ts#L5) `VideoPlayer`; attached to Shaka at [`:274`](app/src/utils/VideoHandler.ts#L274) `new ShakaPlayer(...)` | All playback. Calm Frames never replaces it and never lowers its opacity. It reads `currentTime`, `playbackRate` and the media events from it, and covers on top of it. |
| **W3C media player, video surface** | `@amazon-devices/react-native-w3cmedia` | [`app/src/screens/PlayerScreen.tsx:623`](app/src/screens/PlayerScreen.tsx#L623) `KeplerVideoSurfaceView`, imported at [`:17`](app/src/screens/PlayerScreen.tsx#L17) `KeplerVideoSurfaceView` | The hardware video layer at zIndex 0. The cover sits above it, which is what keeps the sound running while the picture is hidden. |
| **Vega Media Controls** | `@amazon-devices/kepler-media-controls` | Focus set at [`app/src/utils/VideoHandler.ts:158`](app/src/utils/VideoHandler.ts#L158) `setMediaControlFocus(...)`. The safe handler is [`app/src/calmframes/SafeMediaControlHandler.ts:54`](app/src/calmframes/SafeMediaControlHandler.ts#L54) `class SafeMediaControlHandler`, with `handleSeek` at [`:80`](app/src/calmframes/SafeMediaControlHandler.ts#L80) and `handleFastForward` at [`:107`](app/src/calmframes/SafeMediaControlHandler.ts#L107) | System and voice transport, and the path an Alexa "skip forward" arrives on. It can land the playhead inside a flagged interval without the remote being touched, so none of these handlers call `super`. Each one goes through [`app/src/calmframes/seekSafety.ts`](app/src/calmframes/seekSafety.ts), `planSeek` at [`:113`](app/src/calmframes/seekSafety.ts#L113). |
| **KeplerCaptionsView** | `@amazon-devices/react-native-w3cmedia` | [`app/src/screens/PlayerScreen.tsx:641`](app/src/screens/PlayerScreen.tsx#L641) `KeplerCaptionsView`, the element; the handle is set by [`:587`](app/src/screens/PlayerScreen.tsx#L587) `setCaptionViewHandle` | Captions, at zIndex 2, above the cover. One captions view per process. This is the reason a hidden segment is still followable: the words carry on over a black picture. |
| **Accessibility APIs** | `react-native` `AccessibilityInfo`, plus the `com.amazon.devconf.privilege.accessibility` privilege at [`app/manifest.toml:91`](app/manifest.toml#L91) | [`app/src/calmframes/announce.ts:58`](app/src/calmframes/announce.ts#L58) `announceForAccessibilityWithOptions(message, { queue: true })`; the card carries `accessibilityLiveRegion="polite"` at [`app/src/calmframes/CalmCard.tsx:75`](app/src/calmframes/CalmCard.tsx#L75) and `accessibilityRole="alert"` at [`:76`](app/src/calmframes/CalmCard.tsx#L76); the cover is hidden from the tree at [`app/src/calmframes/CoverLayer.tsx:74`](app/src/calmframes/CoverLayer.tsx#L74) `accessibilityElementsHidden` | VoiceView is told what is about to be hidden, and told it in a queue rather than by interrupting, because a child hearing "flashing part coming up" cut off halfway is worse than hearing it a beat later. The cover itself is taken out of the accessibility tree, so VoiceView never reads a black rectangle and focus never lands on it. |

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
| Trials started | <!--n results/gate1_software_vvd.json:trials_attempted -->55<!--/n--> | gate1_software_vvd.json |
| **In time, counting every dropped trial as a failure** | **<!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> of <!--n results/gate1_software_vvd.json:trials_attempted -->55<!--/n-->**, <!--n results/gate1_software_vvd.json:in_time_strict_fraction -->0.8727<!--/n--> (<!--n results/gate1_software_vvd.json:wilson_95_interval_strict.low -->0.7598<!--/n--> to <!--n results/gate1_software_vvd.json:wilson_95_interval_strict.high -->0.937<!--/n-->) | gate1_software_vvd.json |
| Trials counted | <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> | gate1_software_vvd.json |
| Covered in time | <!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> | gate1_software_vvd.json |
| Dropped, no position report either side | <!--n results/gate1_software_vvd.json:trials_dropped_no_timeupdate -->4<!--/n--> | gate1_software_vvd.json |
| Dropped, playback stalled mid-trial | <!--n results/gate1_software_vvd.json:trials_dropped_playback_stalled -->2<!--/n--> | gate1_software_vvd.json |
| Median lead | <!--n results/gate1_software_vvd.json:lead_ms.median -->488.4<!--/n--> ms | gate1_software_vvd.json |
| 95th percentile lead | <!--n results/gate1_software_vvd.json:lead_ms.p95 -->4097<!--/n--> ms | gate1_software_vvd.json |
| Longest lead | <!--n results/gate1_software_vvd.json:lead_ms.max -->6197.5<!--/n--> ms | gate1_software_vvd.json |
| Worst lead | <!--n results/gate1_software_vvd.json:worst_lead_ms -->-86<!--/n--> ms | gate1_software_vvd.json |
| Guard band | <!--n results/gate1_software_vvd.json:guard_band_ms -->500<!--/n--> ms | gate1_software_vvd.json |
| Required lead | <!--n results/gate1_software_vvd.json:required_lead_ms -->150<!--/n--> ms | gate1_software_vvd.json |

The median sits about where the 500 ms guard band puts it. **That is the friendliest row in the table and it is not the one to judge this by.** The 95th percentile lead is <!--n results/gate1_software_vvd.json:lead_ms.p95 -->4097<!--/n--> ms and the longest is <!--n results/gate1_software_vvd.json:lead_ms.max -->6197.5<!--/n--> ms, against a guard band of <!--n results/gate1_software_vvd.json:guard_band_ms -->500<!--/n--> ms. A cover that goes on four seconds early is safe and it is not the schedule working: it is the cover firing whenever the next position report happened to arrive, which on this clip was about every 6.5 s. So the scheduler is doing less of the work than the median suggests, and the position reports are doing more. Three things in that table matter more than the median.

**One cover was late.** The worst lead is negative: in one trial the cover went on 86 ms after the marker had already started. Every other pass fired at the first position report past the guard band, around 6.5 s into the clip. In that one, the report at 6.744 s was skipped and the cover fired at 7.079 s. The scheduler re-anchors to media time on every report and re-checks every 50 ms, so a 335 ms gap means the JavaScript thread was not available, not that the schedule was wrong. **The guard band has to be wider than the worst pause of that thread.** Nothing measures that pause on real hardware yet, and that is the first thing GATE 1 has to find out. It has been measured here, though, and the number is bad enough that it belongs in this section rather than one click away. Re-running the same harness with the host under load ([`results/under_load/gate1_software_vvd_load218.json`](results/under_load/gate1_software_vvd_load218.json), written up in [docs/GATES.md](docs/GATES.md)) gave <!--n results/under_load/gate1_software_vvd_load218.json:in_time -->8<!--/n--> of <!--n results/under_load/gate1_software_vvd_load218.json:trials_counted -->9<!--/n--> trials in time, a worst lead of <!--n results/under_load/gate1_software_vvd_load218.json:worst_lead_ms -->-454.6<!--/n--> ms, and a worst gap between two scheduler ticks of <!--n results/under_load/gate1_software_vvd_load218.json:worst_tick_gap_ms -->72755<!--/n--> ms. That is seventy-two seconds in which a 50 ms timer did not run. A guard band cannot be wider than that, which means the guard band is the wrong instrument for a machine under that much load, and the honest position is that we do not yet know what is.

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
| Clips in the pool | <!--n results/screening.json:totals.clips -->38<!--/n--> |
| Analyzed cleanly | <!--n results/screening.json:clips_analyzed_ok -->38<!--/n--> |
| flashmap could not decode | <!--n results/screening.json:clips_failed -->0<!--/n--> |
| Flagged segments found | <!--n results/screening.json:totals.flagged_segments -->456<!--/n--> |
| Sources with at least one flag | <!--n results/screening.json:totals.sources_with_at_least_one_flag -->6<!--/n--> |

Per source:

| Source | Files | Files with a flag | Flagged segments |
|---|---|---|---|
| Blender open movies | <!--n results/screening.json:per_source.Blender open movies.files -->3<!--/n--> | <!--n results/screening.json:per_source.Blender open movies.flagged_files -->3<!--/n--> | <!--n results/screening.json:per_source.Blender open movies.flagged_segments -->169<!--/n--> |
| 1930 public-domain film | <!--n results/screening.json:per_source.1930 public-domain film.files -->2<!--/n--> | <!--n results/screening.json:per_source.1930 public-domain film.flagged_files -->2<!--/n--> | <!--n results/screening.json:per_source.1930 public-domain film.flagged_segments -->229<!--/n--> |
| Wikimedia Commons | <!--n results/screening.json:per_source.Wikimedia Commons.files -->16<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons.flagged_files -->3<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons.flagged_segments -->19<!--/n--> |
| Wikimedia Commons fireworks | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.files -->4<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.flagged_files -->3<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons fireworks.flagged_segments -->21<!--/n--> |
| Wikimedia Commons lightning | <!--n results/screening.json:per_source.Wikimedia Commons lightning.files -->4<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons lightning.flagged_files -->3<!--/n--> | <!--n results/screening.json:per_source.Wikimedia Commons lightning.flagged_segments -->9<!--/n--> |
| DVIDS | <!--n results/screening.json:per_source.DVIDS.files -->2<!--/n--> | <!--n results/screening.json:per_source.DVIDS.flagged_files -->2<!--/n--> | <!--n results/screening.json:per_source.DVIDS.flagged_segments -->9<!--/n--> |
| NASA SVS 5011 | <!--n results/screening.json:per_source.NASA SVS 5011.files -->1<!--/n--> | <!--n results/screening.json:per_source.NASA SVS 5011.flagged_files -->0<!--/n--> | <!--n results/screening.json:per_source.NASA SVS 5011.flagged_segments -->0<!--/n--> |
| NASA ISS time-lapse | <!--n results/screening.json:per_source.NASA ISS time-lapse.files -->3<!--/n--> | <!--n results/screening.json:per_source.NASA ISS time-lapse.flagged_files -->0<!--/n--> | <!--n results/screening.json:per_source.NASA ISS time-lapse.flagged_segments -->0<!--/n--> |
| unlabeled | <!--n results/screening.json:per_source.unlabeled.files -->3<!--/n--> | <!--n results/screening.json:per_source.unlabeled.flagged_files -->0<!--/n--> | <!--n results/screening.json:per_source.unlabeled.flagged_segments -->0<!--/n--> |

The `unlabeled` row is three files that carry no source label in `media/LICENSES.csv`, and they are not content: they are the marker clips the timing harness plays against itself, so the honest count of screened footage is three lower than the pool total. `NASA ISS time-lapse` is three night time-lapses that decode cleanly and flash at nothing, so they contribute no segments. Both are in the table because every source in the results file has to be, and the Files column has to add up to the <!--n results/screening.json:clips_analyzed_ok -->38<!--/n--> analyzed cleanly. `eval/tests/test_screening_table_is_complete.py` fails if either stops being true, because this table had already lost a row once.

The plain `Wikimedia Commons` row is sixteen calm clips, clouds, waves and sunsets, downloaded to give the pool something that should not flash at all. Three of them do: two stretches of sea and a lake panorama, nineteen segments between them, every one on the general rule. Sunlight on moving water is a real thing to flag, not a bug in the analyser, and it is worth knowing before anyone claims a false positive rate from calm footage. Those sixteen are in the labelling pool now. A title joins it only once every candidate list has seen it, and the two ffmpeg based baselines were the last to run: they were re-run over every clip on Sep 19, on one ffmpeg version, which is what let the calm sixteen in. The pool is back to <!--n results/realclips_status.json:segments -->40<!--/n--> segments over <!--n results/realclips_status.json:titles -->16<!--/n--> titles.

One thing this run found, recorded rather than smoothed over: every one of those segments fired the general flash rule and not one fired the red flash rule, because the free pool holds no saturated red strobe and no sustained regular strobe. That gap closes by filming. The clips to film are listed in [`results/screening.json`](results/screening.json) under `self_filmed_needed`, each with what it has to show, how long to roll, and how fast it has to flash written as a multiple of the analyser's own per second limit.

An earlier version of this table had four failures, all Theora `.ogv`, which flashmap could not decode at the time. The decoder was fixed and those four titles were screened again on Sep 17. The result file records that re-run under `rescreens`, with the rows it replaced and the rows it kept, so the table above is one run of sixteen titles plus a re-run of four rather than a single sweep.

### How well the analyzer does, on the conformance suite

This is the number that says whether any of the rest is worth having. Recorded by the conformance suite into [`results/conformance.json`](results/conformance.json), whose ground truth is computed from the quoted spec text in a module that cannot import flashmap.

| What | Value |
|---|---|
| Clips measured and kept | <!--n results/conformance.json:published.clips_kept -->467<!--/n--> of <!--n results/conformance.json:published.clips_designed -->3000<!--/n--> designed |
| Windows judged | <!--n results/conformance.json:published.windows -->1401<!--/n-->, of which <!--n results/conformance.json:published.positive_windows -->324<!--/n--> are positive in the ground truth |
| Precision | <!--n results/conformance.json:published.flashmap_precision -->0.65<!--/n--> (<!--n results/conformance.json:published.flashmap_precision_lo -->0.605<!--/n--> to <!--n results/conformance.json:published.flashmap_precision_hi -->0.693<!--/n-->) |
| Recall | <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n--> (<!--n results/conformance.json:published.flashmap_recall_lo -->0.857<!--/n--> to <!--n results/conformance.json:published.flashmap_recall_hi -->0.924<!--/n-->) |
| Recall away from a limit | <!--n results/conformance.json:published.recall_away_from_limits -->1<!--/n--> over <!--n results/conformance.json:published.recall_away_from_limits_positive_windows -->244<!--/n--> positive windows |
| **Recall on clips that sit on a limit** | **<!--n results/conformance.json:published.recall_near_limits -->0.575<!--/n-->** over <!--n results/conformance.json:published.recall_near_limits_positive_windows -->80<!--/n--> positive windows |

**This run is partial and the file says so in its own statement field.** <!--n results/conformance.json:published.clips_measured -->475<!--/n--> clips were measured, <!--n results/conformance.json:published.excluded_clips -->8<!--/n--> were excluded and <!--n results/conformance.json:published.clips_kept -->467<!--/n--> kept, out of a committed design of <!--n results/conformance.json:published.clips_designed -->3000<!--/n-->. Nothing here should be read as a finished evaluation.

**What those two numbers mean for a child in front of the TV**, said plainly:

- Precision of <!--n results/conformance.json:published.flashmap_precision -->0.65<!--/n--> means roughly a third of the windows flashmap flags are not over the threshold. The cost of that is picture hidden that did not need hiding. It is the direction we would rather err in, and it is still a cost, because a title full of unnecessary covers is a title a child stops choosing.
- Recall of <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n--> means about one positive window in ten is missed across the whole suite. **That blended number flatters the part that matters, and the split says so.** Away from a limit, recall is <!--n results/conformance.json:published.recall_away_from_limits -->1<!--/n--> over <!--n results/conformance.json:published.recall_away_from_limits_positive_windows -->244<!--/n--> positive windows in <!--n results/conformance.json:published.recall_away_from_limits_clips -->289<!--/n--> clips. On the <!--n results/conformance.json:published.recall_near_limits_clips -->178<!--/n--> clips that sit **on** a limit it is <!--n results/conformance.json:published.recall_near_limits -->0.575<!--/n--> over <!--n results/conformance.json:published.recall_near_limits_positive_windows -->80<!--/n--> positive windows, which is closer to four missed in ten than one. A safety tool lives at the limit, so that is the number to judge it by, and it is the reason this is a layer that reduces exposure rather than one that removes it. It is also the reason the approved wording is the wording it is. [`eval/EVAL_RESULTS.md`](eval/EVAL_RESULTS.md) works through what that split means.

Neither number has anything to say about the red flash rule against real footage, because the pool has no saturated red strobe. The ablation in [`results/ablations.json`](results/ablations.json) shows what the red rule is carrying on the synthetic suite: with it on, <!--n results/ablations.json:detection.arms.default.recall.numerator -->88<!--/n--> of <!--n results/ablations.json:detection.arms.default.recall.denominator -->98<!--/n--> positive windows are found; with it off, <!--n results/ablations.json:detection.arms.red_rule_off.recall.numerator -->64<!--/n--> of <!--n results/ablations.json:detection.arms.red_rule_off.recall.denominator -->98<!--/n-->.

### Baselines

Three independent tools were run over the same pool, so flashmap can be compared against something rather than trusted on its own. Per-clip results are in [`results/baselines/`](results/baselines/): `ffmpeg_photosensitivity` (FFmpeg's own photosensitivity filter, a mitigator whose flags are inferred from where its output differs from the unfiltered decode), `naive_luma_diff` (whole-frame mean luma only, no area rule, no colour rule, no rate window) and `iris` ([EA IRIS](https://github.com/electronicarts/IRIS), a published photosensitivity analyser, through its own example app built from source at a pinned commit). None of the three is a conformance result and none is a safety claim.

**EA IRIS matters more than a column in a table, because it is also the fourth candidate list the real clip pool is the union of.** While it was missing, every recall this repository could have quoted off that pool was measured against a union our own detector had helped choose, and this page used to say the estimate was optimistic by an amount nobody could name. It is built now, natively rather than in the shared Docker VM for the reason in [docs/DECISIONS.md](docs/DECISIONS.md), and it has run over every clip in the pool and over the sixteen calm ones as well: <!--n results/pool_recall.json:published.iris_clips_analyzed -->32<!--/n--> analyzed, <!--n results/pool_recall.json:published.iris_clips_it_could_not_decode -->6<!--/n--> it could not decode, <!--n results/pool_recall.json:published.iris_flagged_segments -->6<!--/n--> segments flagged.

**The amount was zero.** Every window IRIS proposed had already been proposed by something else: <!--n results/pool_recall.json:published.iris_only_windows -->0<!--/n--> windows in the union came from IRIS alone, so flashmap's coverage of the union is <!--n results/pool_recall.json:published.flashmap_pool_recall -->0.6<!--/n--> with IRIS in it and <!--n results/pool_recall.json:published.flashmap_pool_recall_before_iris -->0.6<!--/n--> without. That is a measured zero, not a missing measurement, and it is the reason the caveat is gone rather than reworded. It says nothing about whether IRIS is a good analyser and everything about this pool: IRIS is far stricter than the other three here, and on natural footage its area rule and its one second transition window almost never both fire.

The number the caveat was about, now that it is real: against the pooled union of all four candidate lists, flashmap covers <!--n results/pool_recall.json:published.flashmap_pool_recall -->0.6<!--/n--> of the windows any of them proposed (<!--n results/pool_recall.json:published.flashmap_pool_recall_lo -->0.324321<!--/n--> to <!--n results/pool_recall.json:published.flashmap_pool_recall_hi -->0.763265<!--/n-->, bootstrap over titles), over <!--n results/pool_recall.json:published.union_windows -->2425<!--/n--> windows in <!--n results/pool_recall.json:published.titles -->28<!--/n--> titles. **Read that number carefully, because on its own it is misleading in both directions.** It is not recall against ground truth: a window counts as positive because some detector proposed it, not because a person looked at a plot and said a flash was there, so it cannot be compared with the conformance recall above. And the union is dominated by FFmpeg's filter, which flags broadly enough to be the only proposer of more than a third of it, so what looks like flashmap missing a third of the hazards is mostly flashmap declining to flag what a mitigator smoothed. The interval is wide because there are only <!--n results/pool_recall.json:published.titles -->28<!--/n--> titles to resample. The real number needs the labelling, and nobody has labelled anything yet.

### Not measured yet

These rows exist so nobody has to guess what is missing.

| What | Why it is empty |
|---|---|
| GATE 1: covers drawn early, filmed at 240 fps | Needs the Fire TV stick. |
| Any cover lead time at all, on any device | The one run that produced one was withdrawn, because the player never reported a position. See above. |
| GATE 3: end to end on the stick | Needs the stick. |
| Prevented exposure, in seconds | Computed from flash maps once the KPI run happens. Never by playing flashing content with the filter off. |
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
npm run build:debug                     # builds every architecture; the stick takes armv7
vega device is-connected                # not "vega device list", which crashes
vega run-app build/armv7-debug/calm-frames-app_armv7.vpkg
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

### The report page

```sh
python -m flashmap report VIDEO_OR_MAP --out report.html \
    --map broadcast=BROADCAST_MAP.json \
    --title "Some title" --license-csv media/LICENSES.csv
```

One HTML file for one title: the flash timeline, every span that went over the thresholds, what the player hides on each of the three household presets, the licence line and the hashes. It opens with the network off. There is no sibling asset, the CSS is inline and every picture is a PNG embedded as a data URI, so the file can be mailed to somebody as it is.

**It never shows a frame of the film.** There is no still, no poster and no thumbnail anywhere in it. The timeline is drawn from the numbers in the map and holds no picture data from the title at all, and the report says so on its own first screen.

The timeline is drawn so it cannot be a hazard of its own. Nothing thinner than eight pixels is drawn and nothing sits closer than eight pixels to its neighbour, and a lane never draws more than five bars, which is the regular pattern criterion the broadcast profile measures. A title with fifty spans has its neighbouring spans joined, closest first, until five bars are left, so a bar can cover calm time as well as flagged time. Every lane that was drawn coarser than the numbers says so in a line under it, and the tables carry the exact milliseconds.

Every picture the report draws goes through flashmap itself, under both profiles, in `flashmap/tests/test_report.py`. It has two negative controls, because without them a green run would prove nothing: a file flashing at 10 Hz, which the WCAG profile refuses, and a full frame of forty stripe pairs, which the broadcast profile refuses and the WCAG profile passes.

A judge who would rather not use a terminal can run the same thing from a page:

```sh
python -m pipeline.upload_server            # http://127.0.0.1:8765
```

Drop in a clip, get the report back. It runs on this machine only. The clip is measured by the pipeline's own analyzer door and deleted before the answer is sent, it is never played and there is no route that serves it back. **Nothing is deployed.** Anything that would reach AWS waits behind the same two locks as `make deploy`, and neither has ever been open here.

### The GitHub Action

Copy [`flashmap/examples/flash-check.yml`](flashmap/examples/flash-check.yml) into `.github/workflows/`. Every pull request that adds or changes an image or video is measured, and the job fails if the file goes over the general or red flash thresholds. The map format is [`docs/SIDECAR_SPEC.md`](docs/SIDECAR_SPEC.md).

### The pipeline

```sh
python -m pipeline.ingest VIDEO --workdir build/ingest  # probe, analyze, hide plan, rendition, posters
python -m pipeline.verify --workdir build/ingest --sha SHA256  # the publication gate
```

Ingest is idempotent and keyed by the source file's SHA-256, so a repeated run picks up where it stopped.

Scene holds are enabled by default when ingest has a signing key:

```sh
python -m pipeline.ingest VIDEO --workdir build/ingest --key /path/to/team_key.pem \
    --pub /path/to/team_key.pub.pem
```

For each covered interval, ingest selects an exact preceding source frame outside
every requested preset's guarded intervals and calm margin, with a five-second
lookback. If no eligible frame exists, extraction fails, or the still fails its
pattern check, it uses a flat neutral image. The inline JPEGs are bounded and
signed; intervals without a descriptor use black. Verification checks their
source provenance, bytes, and the encoded MP4, HLS and live-cover model before
publication. `--no-scene-holds` retains the legacy rendition and cover path.
Existing maps without scene holds remain supported. The wire contract is in
[`docs/SIDECAR_SPEC.md`](docs/SIDECAR_SPEC.md).

### A checked local library, without AWS

One command wraps ingest and verification and prints a readiness receipt:

```sh
python -m pipeline.local_library prepare /path/to/calm-video.mp4 \
    --workdir build/local-library --key /path/to/team_key.pem \
    --pub /path/to/team_key.pub.pem --title 'Our calm video' \
    --presets wcag,broadcast,extra-cautious
python -m pipeline.local_library catalog --workdir build/local-library
```

Use a benign clip, external signing keys and the normal pipeline dependencies.
Nothing is served, opened, played or uploaded automatically. The receipt links
only the prepared MP4, HLS, map and verification report, not the source video,
private key or cover model. `local-library.json` lists only complete checked
titles, and rebuilding it rechecks current artifact bytes against the receipt.
A failed re-import withdraws the old ready receipt. Overlapping imports into
the same workspace are refused rather than racing shared catalog writes.

The receipt says **ready for local playback of the prepared rendition**. To
include the checked titles in the next Vega build, export their prepared assets:

```sh
python -m pipeline.packaged_library export --workdir build/local-library \
    --output app/assets/raw/prepared-library --pub /path/to/team_key.pub.pem
python -m pipeline.packaged_library check --output app/assets/raw/prepared-library
cd app && npm run build:debug
```

The app selects the prepared rendition for the household's preset. The compiled
catalog keeps the analyzed source hash distinct from the rendition hash and
binds the local media, signed maps and extracted captions. Build checks verify
those exact bytes again inside every package. Playback rejects a substituted
route before loading its media and still performs the normal signed-map check.
This is a bounded library packaged at build time; adding titles requires a new
build. It does not establish native playback or physical-TV composition.

Local preparation now uses the app's profile unions and guard timings, with
opaque live fallback and a verified pre-covered picture. Its default analysis
room covers the current selectable room sizes. Signed per-interval scene images
remain available in the separate scene-hold pipeline and the labelled Harbor
practice demo; arbitrary prepared imports do not yet carry union scene images.

Detailed commands, exit statuses and workspace limits are in
[`pipeline/LOCAL_LIBRARY.md`](pipeline/LOCAL_LIBRARY.md).

In the app, setup now ends with a review of the chosen preset, television size
and seating distance. A checked title's viewing plan explains which maps were
checked, how scene holds fall back to an opaque cover, and the limits of the
protection. Pending or failed titles get no ready plan. These are presentation
changes; timing, seek guards and household floors are unchanged.

Household setup is saved locally for later app launches: the selected
child, profiles, room, preset, chime choice, salted PIN hash and failed-attempt
lockout are saved together in a versioned local record. The library opens only
after that record is read and validated. Unreadable or malformed records keep
it closed; a failed save offers a retry of the intended change. No plaintext
PIN or unlocked parent session is saved. The hide history remains in memory.
These paths are covered by app regressions, with native storage behavior on
physical Fire TV still awaiting validation.

### Read-only physical-TV preflight

After building a Debug package, check its actual bundled benign-media bytes
and the SDK's current device connection without installing or playing anything:

```sh
make hardware-preflight HARDWARE_PREFLIGHT_ARGS="--vpkg app/build/armv7-debug/calm-frames-app_armv7.vpkg"
```

An absent device returns a blocked receipt and exit status 2. After HUMAN
CHECKPOINT B, add `--device SERIAL --checkpoint-b-confirmed` and select the
package matching that physical device's architecture. The check requires the
pinned Vega OS build, developer mode and an explicit target; a virtual device
cannot qualify. Any printed install/launch commands are proposals, never
executed by this preflight.

The bundled calm gradient can check basic launch and seek behavior only: it
has audio but no captions or scheduled scene images. Caption/image composition
needs a separately prepared and integrated benign fixture. Screen timing
still needs a real TV and the HUMAN CHECKPOINT E1 camera recording. Do not run
`stick-day` unchanged on physical hardware: its timing runner uses virtual-device
QEMU host paths. A successful preflight is not a playback or safety result.

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
- **Scene-hold composition is not measured on a TV.** The encoded outputs and
  runtime guards have automated checks, but native image loading, aspect ratio,
  captions and cover timing still need a physical-device run with benign media.
- **Red flash coverage is untested against real footage**, because no free source in the pool has a saturated red strobe.
- **The room rule can only add hides.** A household cannot make Calm Frames weaker than WCAG. That is a design rule and it is enforced in code, but it also means a household cannot switch protection off for one title without leaving kid mode.
- **None of it has been seen running on a stick.** The guard hook, the PIN gate, the seek safety engine, the calm card and the VoiceView announcements exist in `app/src/calmframes/`, and the standalone [`hook/`](hook/) package that ships them to other apps exists too, with its own README and the integration diff above. What has not happened is any of it running on real hardware.

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
| [docs/RUBRIC.md](docs/RUBRIC.md) | The rules we are judged against, quoted from the hackathon's own pages |
| [docs/VALIDATION.md](docs/VALIDATION.md) | Outreach and what anyone outside this project has said. Empty so far, and it says so |
| [docs/FRICTION_LOG.md](docs/FRICTION_LOG.md) | Developer friction found while building, in Amazon's six-field format |
| [docs/OPEN_SOURCE_PR.md](docs/OPEN_SOURCE_PR.md) | The upstream contribution: what it fixes and why |
| [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md) | The demo video, timed |
| [docs/GATES.md](docs/GATES.md) | Every gate, checkpoint and kill rule, with evidence |
| [docs/STATUS.md](docs/STATUS.md) | Where each lane stands today |
| [docs/SIDECAR_SPEC.md](docs/SIDECAR_SPEC.md) | The flash map format, version 1 |
| [docs/EVAL_PLAN.md](docs/EVAL_PLAN.md) | Committed before any real clip was labelled |
| [eval/EVAL_RESULTS.md](eval/EVAL_RESULTS.md) | What the conformance run actually says, including where recall falls off |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Every call made, with why and what it cost |
