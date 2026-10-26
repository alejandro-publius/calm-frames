# Calm Frames: hiding a flash before it plays

Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device. This page is the short version of why it is built the way it is; the [README](README.md) has the measurements and [docs/README.md](docs/README.md) the rest of the documents.

## The problem

Flashing on a screen is a known seizure trigger for some people with photosensitive epilepsy, and the Epilepsy Foundation's own page says it is more common in children and adolescents. The published limits for how much flashing is too much are WCAG 2.2 success criterion 2.3.1 and, for broadcast, ITU-R BT.1702; [flashmap/docs/SPEC_SOURCES.md](flashmap/docs/SPEC_SOURCES.md) quotes both with links.

A parent today has two options: preview everything first, or trust that a title is fine. Calm Frames tries to give a third: every frame of a title is measured before it can play in kid mode, and the player hides each part the analyzer flags, on a schedule set before it plays, while the sound and captions, when a video has them, keep the story going.

## Why it is harder than putting a black box over the bad part

**The cover has to be early, not fast.** A detector that watches the picture as it plays has already shown the first flashing frames by the time it decides. So the analysis runs offline over every frame, writes down where the flashing is, and the player schedules the cover ahead of it. The player's own position reports cannot drive that schedule: in a recorded run on the virtual device the longest gap between two of them was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms while the clip kept playing. The cover runs on a wall clock re-synced to media time at every report, and anything that makes the playhead uncertain (a stall, a seek, a pause, the app going to the background) hides the picture at once. For a prepared title this is the second of two layers: the player plays a rendition in which every flagged part is already covered in the pixels, which verify checks, and the scheduled cover sits on top of it. Acadia differs: its flagged parts are replaced rather than covered, checked by analyzing the whole rendition again, and the opaque cover gives way to that replacement only during steady playback.

**Every way of moving the playhead is a way in.** Voice, the D-pad, the on-screen card and the system's media controls can all seek. If any one of them can land inside a flagged part, the rest do not matter. So there is one function that moves the playhead, it asks for the cover before it moves the playhead, and a lint rule refuses any other write to the playhead, apart from the sample's own fallbacks, which are exempted by name. That is the order of the calls; that the cover is on screen before the new frame is, has still to be seen frame by frame on the device.

**The map has to be the map for this file.** A flash map for a different cut of a film is worse than none, because it hides the wrong seconds with confidence. A map is an instruction to hide, so the player has to know who vouched for it: each map is signed, and bound to the file's SHA-256 so it can only describe this file, and the player fails closed: a missing, stale, unsigned, unreadable or wrong-hash map keeps the picture hidden.

**The story has to survive the hide.** A child watching a black screen for a few seconds has lost the thread. The cover sits under the captions and over the video surface, so captions stay readable and the sound keeps playing, and a card says what is coming and what was hidden. On Acadia, approved footage from the opening seconds of the same park video replaces the flagged scenes in the prepared copy, with the opaque cover kept as the fallback; by the records, nearly all of what the replacements show comes from that opening's near-black stretch, and no recorded check has looked at those frames. On the labelled Harbor demo, which is bundled for regression work and not offered on the current Home, a checked still from just before the hide stands in for black.

**A household can only make it stricter.** Parents set a preset and the room (screen size and viewing distance), and those settings can only add hides; nothing in the parent area can make the player weaker than the WCAG floor. The room is the subtle part: WCAG's area limit is a share of a 10 degree visual field, and the analyzer turns the screen size and the viewing distance into how much of the picture that field covers in this room, checked in addition to the default window, never instead of it.

## How the system makes that trustworthy

The work is split so that each part can be checked on its own:

- **flashmap** measures every frame against the general and red flash rules and writes the map. It uses the published arithmetic, not a trained model: the limit is a count of flashes in any one second over a share of the screen, so every frame is read with its own timestamp and every flag traces to a sentence in the spec. It is open source and runs as a CLI and a GitHub Action, so a studio can check its own content in CI.
- **The pipeline** prepares a kid-safe rendition and signs the map. **Verify** is a gate, not a report: a violation left in the rendition, a violation under the modelled cover, a tampered map, a wrong hash or a poster taken from a flagged moment all stop the title, and it proves the cover is drawn at the first frame, the middle and the last frame of the first six covered spans of each preset, with the whole rendition analyzed again.
- **The app** reads only maps it can verify, schedules the cover, and routes every seek through the one function.

The checks are tested by breaking them. A mutation gate breaks each safety guard on purpose and runs the tests that should notice, and CI fails if a guard can be broken without a test noticing, unless the edit is written up as equivalent, one that cannot change what the program does. The map readers are fuzzed with malformed maps. Every published number in the README and the docs is written against a file in `results/`, and CI fails if a document drifts from its source. The "How this is checked" section of the README lists every job.

## Honest limits

- **It is software timing, not screen timing.** The cover lead time was measured inside the app on the Vega Virtual Device; no physical television and no camera have been used. The strict reading of that run, counting the trials that produced no evidence as misses, is <!--n results/gate1_software_vvd.json:in_time_strict_fraction -->0.8727<!--/n-->.
- **The analyzer misses flashing that sits right on a limit more often than not.** On the generated conformance clips its recall is <!--n results/conformance_current_report_2026-10-02.json:published.flashmap_recall -->0.85<!--/n--> overall but <!--n results/conformance_current_report_2026-10-02.json:published.recall_near_limits -->0.469<!--/n--> on clips near a limit, and its precision near a limit is <!--n results/conformance_current_report_2026-10-02.json:published.precision_near_limits -->0.573<!--/n-->. The near-limit numbers are the ones to judge it by; the README has the full table.
- **Detection is only as good as the pool it was tested on.** The free footage pool has no saturated red strobe, so red flash detection is tested on the generated conformance clips only.
- **Only checked titles are protected.** Live streams, other apps and DRM titles are out of scope.
- **A signature proves which map belongs to which file, not that every hazard was found.**

Within those limits it turns a parent's "I have to watch it first" into a check that runs before the title is ever offered to a child.
