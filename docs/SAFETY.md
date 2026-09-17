# Safety

## Rules for the team (read these first)

1. **Nobody watches strobes at full speed.** Hazard files carry the `HAZARD_` prefix, stay under `media/` (gitignored), never autoplay anywhere, and are inspected only as plots or as slowed, dimmed playback.
2. **Generated conformance clips are hazardous by design.** Generate, analyze and delete them in the same job. Never open them.
3. **Filming flashing footage:** whoever films is not photosensitive and doesn't look at the lights. People in frame give consent.
4. **Never play real flashing content with the filter off**, on any screen, for any test. Exposure the filter prevented is computed from the flash map, not shown.
5. **Never show real flashing content unfiltered in the video**, even for a second. Show luminance traces instead.
6. **Outreach:** ask only for feedback on wording and flow. Never show anyone flashes.

## How the repo enforces them

- `media/` is gitignored except `media/LICENSES.csv` and hash files, so hazard files can't be committed by accident.
- Plots of hazard files come from `eval/plots.py`, a separate script that does not import flashmap, so labeling stays independent of the analyzer.
- CI runs `flashmap check` on every image and video asset in the repo (planned in Phase 0.6), including the app's own screens and transitions.

## Wording

Say: "reduces exposure to flashing above published limits in the videos it plays; not a medical device."

Never say: "prevents seizures" or "seizure-proof".
