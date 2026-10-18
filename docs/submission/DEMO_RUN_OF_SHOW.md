# Current demo run of show

Updated October 18, 2026 for installed source `6f2570da4165acc752882a0c04ffe996cd072880`.
Package SHA-256: `8311d90bc34db2efaae77a8a5eda144d7d45cc3989035558860c1b4604e3e63b`.
This is a live walkthrough plan, about two minutes without extended explanations.
No screen/audio/video recording is authorized or claimed. The older October 17
run of show remains in Git history and describes a superseded interface.

## Starting point and exact keys

Start at Home with Acadia selected and Watch focused. The installed app was left
there after the non-capture walkthrough.

| Step | Remote action | What to explain |
| --- | --- | --- |
| Coastal world | Up selects Acadia's destination; Right selects Sea Otters; Select opens Sea Otters Details with Watch focused. | Two real videos are destinations on original static coastal artwork. Focus changes selection without autoplay. |
| Sea Otters | Select starts the video. Let it finish or press Back to Details Watch. Back again returns to the selected Sea Otters destination. | NOAA Fisheries footage of sea otters in the ocean at Unalaska, Alaska; 19.987 seconds, silent, plays once. No flagged intervals were found in the approved excerpt. |
| Acadia | From the Sea Otters destination: Left, Down, Left reaches Home Acadia Watch; Select starts Acadia. | The exact approved National Park Service rendition is selected. The opening uses static map art until the readiness gate passes. |
| Protected intervals | Let Acadia play uninterrupted. Under the current extra-cautious profile the intervals are 7.343 to 12.699 seconds and 28.113 to 31.593 seconds. | Verified ocean footage replaces flagged scenes. Original audio remains in the rendition. Opaque protection remains independent of the replacement presentation. |
| Controls | Down reveals hidden controls. Play/Pause toggles playback. During an eligible cover, Select on focused Skip skips the scene. | The native trace records cover requested before the playhead write. This is software evidence, not a screen-level timing measurement. |
| Return | End or Back returns to the launching screen. From Home Watch, Right, Select opens Acadia Details; Right, Select opens More info. Back walks out one level. | Details shows covered sections; More info contains source credits and limitations. |
| Close | Leave Home Acadia Watch focused. | Calm Frames works only with prepared videos inside this app. Detection can miss flashing; this prototype has not been medically validated. |

The shortest tested route from the starting point to Sea Otters playback is
**Up, Right, Select, Select**. From that playback, **Back, Back, Left, Down, Left**
restores the starting point. Full directions and Parents cancellation are in the
[owner walkthrough](../../results/sea-otters-flow-2026-10-18/OWNER_WALKTHROUGH.md).

## Evidence and limits

The [current evidence summary](../../results/sea-otters-flow-2026-10-18/validation-summary.json)
records 534 focused app tests, 11 attribution tests, one native build/install and
completed core routes. Native text checks include both Acadia replacement requests,
pause/resume, Skip, both real video identities, natural end/Back and control hide/reveal.
The earlier final-focus expectation was corrected: Down from Acadia's destination
reaches Details, then Left reaches Watch. No second install was needed.

These logs do not confirm pixels, audible output, visible focus quality or physical
Fire TV behavior. Loading/error/surface-loss recovery was checked in controlled tests;
no native fault was injected. The previous intermittent simulator slowdown remains
historical evidence; the latest successful run does not prove it can never recur.
The legacy Check playback diagnostic is excluded under extra-cautious because it
has only a WCAG map. Do not change household settings or trust to expose it.

## Before submission or any later recording

Owner visual/audio acceptance, an authorized current demo recording, judge access
and Devpost completion remain open. The existing submission checklist also records
an unanswered organizer question about third-party footage; no answer is claimed here.
Current source rights records cover both NPS Acadia and NOAA Fisheries B-roll.
Credit **National Park Service, Acadia National Park** and **NOAA Fisheries**;
no agency endorsement is implied. See [media/LICENSES.csv](../../media/LICENSES.csv)
and [NOAA source provenance](../../results/sea-otters-2026-10-18/provenance.json).
Do not show unprepared sources or the rejected 40-second NOAA candidate.
