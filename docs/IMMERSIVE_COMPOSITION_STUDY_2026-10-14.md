# Immersive Harbor composition study — 14 October 2026

One alternative Home + Details composition, isolated on `codex/immersive-composition-study-2026-10-14`. Source: `c91b285026635a6b1323c6830d5be8813be8ceb4`. Base: `c8e4b346dc7ba323ca21972d489900c04d8530fa` (integrated application source `e05216284b2e3e85e8a73275432568c512c7317c`). The approved integration branch remains unchanged. Native task: `codex://threads/01a138bb-a422-7746-9293-caf676f250f3`.

## Composition

The original harbor fills more of the screen. Fraunces gives the title a clear focal point; Source Sans 3 keeps functional text readable. Home pairs the title and a brief story premise with a separate purpose/help area. Details places the actual 20-second runtime above the title and its viewing caveat beside Watch. The full viewing plan and safety note remain available through Viewing details. Existing dusk-coast colors, zen mark, coral action, gold focus indication and original artwork remain. Only Home and playable Details opt into the alternate scene composition; loading/help artwork keeps its established layout.

This is a TV composition with visible remote actions, not a new scrolling marketing page. Captures are static translations of actual component host trees, not simulator screenshots. No media asset, guard timing, verification, persistence, household data or dependencies changed. This bounded study was not packaged or installed; the previously built integrated package and its hash remain documented in [the integration receipt](DUSK_COAST_INTEGRATION_2026-10-14.md).

## Reference attribution

Mobbin has no callable connector here and its discover page exposes sign-in only; the user confirmed they have not signed in. No authenticated flow or Mobbin screen was inspected. [A24’s Past Lives page](https://a24films.com/films/past-lives) supplied an accessible information hierarchy: title, concise premise, primary action, then separate details. This is an information-architecture reference, not a claim to have inspected its exact rendered layout. No reference artwork was copied.

## Continuity port

Reviewed `b3bc111..d90a2309d7789c4f6449acf4cd870935ef5f096c` against integrated source `e052162`. Ported only that nine-file delta, not its older base, in commit `5a87ebae76a3e00fe5f02a3f8b0e7d1f5f097220`. Eight files applied cleanly; Home’s callbacks and focus selection were transferred manually around this study’s changed layout. The integrated PlayerOpening eyebrow stays TEXT_DIM (the old branch used FOCUS_RING). No visual regression from the older palette was imported.

The two changes have concrete value: a Harbor-opening player route paints PlayerOpening while its lazy module resolves; the loading stand-in suppresses duplicate live-status announcements. Home remembers whether Watch, Details or a poster launched the title, so one control requests return focus. The route still keeps Details open when playback began there; introduction returns target How it works. All 15 supplied tests were verified passing locally. Native loading duration, actual D-pad focus landing and VoiceView announcements remain unverified.

## Validation

Commands used (Node 22.23.2 on PATH):

```sh
npm --prefix app test -- --runInBand --coverage=false --watchman=false --testPathPattern='homeIntroduction.test|shelf.test|screens.test'
npm --prefix app test -- --runInBand --coverage=false --watchman=false --testPathPattern='appStackPlayerFallback.test|playerRouteFallback.test|returnFocus.test'
npm --prefix app run typecheck
python3 eval/preview/export_composition.py
/tmp/calm-home-preview-venv/bin/python eval/preview/render_composition.py
/Users/alexvintera/calm-frames/.venv/bin/python -m pytest eval/tests/test_design_page.py -q
git diff --cached --check
bash scripts/gitleaks_scan.sh staged
```

Results: 91 Home/Details tests + 15 continuity tests + two export/action fixtures passed; 21 design-token checks passed; typecheck and ESLint on all changed application/test files passed. Existing copy tests were updated to require the concise purpose statement and actual Harbor synopsis. No broader suite or native pass is claimed.

Both 1920×1080 and 1280×720 renders were inspected. All Home Watch/Details/How it works and Details Watch/Viewing details bounds remain inside the 5% safe area. An image review found synopsis text crossing the boat, so the lower gradient was strengthened and continued into a solid base. A conservative pixel check across the entire synopsis bounding box, with text hidden, measures minimum **7.11:1** against TEXT_DIM at both sizes. This verifies that static browser background only, not every native text or transition.

## Deliverables and remaining gate

- [Side-by-side comparison](../results/immersive-composition-2026-10-14/before-after.png)
- [Home 1080p](../results/immersive-composition-2026-10-14/1080/home.png), [Details 1080p](../results/immersive-composition-2026-10-14/1080/details.png)
- [Home 720p](../results/immersive-composition-2026-10-14/720/home.png), [Details 720p](../results/immersive-composition-2026-10-14/720/details.png)
- [Source/hash manifest](../results/immersive-composition-2026-10-14/manifest.json), [bounds](../results/immersive-composition-2026-10-14/bounds.json), [contrast](../results/immersive-composition-2026-10-14/synopsis-contrast.json), [Library IDs](../results/immersive-composition-2026-10-14/library-files.json)

Library upload succeeded for the comparison and both full-size screens. Returned version/identity xattrs were applied using the existing Python environment after system Python proved too old for the helper. No duplicate uploads were created.

Native interaction is still pending: earlier Computer Use app selection returned “Computer Use permissions are not granted.” No new permission evidence exists; no retry, Terminal UI bypass, app-data reset, household PIN action, installation or live validation was attempted for this study. The user must grant the requested Computer Use access before native inspection can resume. Mobbin sign-in/authorization is a separate pending user action. Neither blocker prevents reviewing this composition.
