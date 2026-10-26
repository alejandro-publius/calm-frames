# Approved ocean replacement installed for owner review

One native Debug build and one update/install completed successfully. The app is
running on the existing Vega VirtualDevice, left at Home with Watch focused.
The text-log collector is stopped. No recording, capture, PIN entry, Parents
navigation, household write, push or public release occurred.

## Installed identity

- App source: `4c0d291643e8f1d589e12d738f1e2409c68138aa`.
- Package SHA-256: `7292f7b56807e395f8180a99c0205be270d09f3be5982dd9bdfea240ed6c3f0f`.
- Package: `build/release/ocean-native-2026-10-18/calm-frames-ocean-aarch64-debug.vpkg`.
- Approved bundle: `d1abd36aa0cf3ba51d6e66c186c9a1c1deb9cf04b027919dd67a465722015e46`.
- Approved catalog SHA-256: `6b590929ffd622454803caf87354a653190dcb89afa12e906bbaaedfe0e9012d`.
- Existing signer: `98e4c9564d4ef219cc743a0e06372192b9aef573c4ce956987d5bfe255a11407`.

All 801 app inputs matched before/after build and before installation. The device's
transferred package matches the local package hash. Direct package inspection
matches the approved manifest and all six media/map assets. The source includes
the tested release fixes at `23a24c2`. Existing generations remain packaged; the
consumer registry selects only the approved replacement Acadia title.

## Native text evidence

The existing Extra cautious selection was preserved. Native prepared-playback
logs identify rendition `42d2abbe6ddd2f0a592bc5a1407da945a1c73fc6febedc68895b9f5294608a14`
and the exact approved bundle/report. No profile or household preference changed.

| Check | What the logs establish |
| --- | --- |
| Opening/loading | Plain cover requested at media 0, waiting clears, opening reports picture-shown at 350 ms. |
| First scheduled ocean interval | Baked-ambient requested with guard covered at 7,375 ms; clear at 12,705 ms. Exact baked span is 7,343-12,699 ms. |
| Second scheduled ocean interval | Baked-ambient requested with guard covered at 28,146 ms; clear at 31,602 ms. Exact baked span is 28,113-31,593 ms. |
| Natural completion | End, successful teardown and Home Watch return. |
| Pause/resume | During the next first interval, pause requests the opaque message cover; resume restores eligible baked-ambient. |
| Skip/seek | Cover requested before playhead write to 12,799 ms; opaque message retained while waiting, release after seek confirmation outside the interval. |
| Manual Back | Successful teardown and Home Watch return. |

Nine checks pass in `native-results.json`. `native-trace.log` retains CALM text
breadcrumbs, with duplicates preserved; `evidence-summary.json` removes adjacent
duplicates for reading. Raw application text logs remain locally under build/.
The logs establish software decisions and selected bytes, not displayed pixels.
Small differences between interval boundaries and logged media samples are event
sampling; these are not measured display-transition latencies.

## Audio, safety checks and limits

`package-media-proof.json` binds the earlier independent reproduction and original
audio/timing checks to the exact installed MP4s. All 1,804 video timestamps and
1,765 source audio packets, including their timing, match. Video duration remains
1693879/45000 seconds. The ocean input has no audio; original audio is preserved.
This proves packet continuity in the package, not sound heard from the simulator.

130 focused activation/playback tests, TypeScript, focused ESLint, native-input
checks, strict prepared namespace checks and built-package checks pass. The
previous export's 225 tests and tamper checks remain applicable. Loading, seeking,
error and household-addition fallbacks are covered by tests; no native error was
injected. Only the existing Extra cautious profile was exercised natively; all
three profiles passed activation and export tests. No real household cover values
were inspected or edited. Their read-only predecessor continuity is tested.

## Owner's remaining step

Press Watch on the already-open Home screen. Watch both ocean replacements and
listen across their transitions. This is the remaining visual/audio acceptance;
no additional approval or installation is needed for this review. The short otter
preview is not included. The original Claude checkout and concurrent sessions
were preserved.
