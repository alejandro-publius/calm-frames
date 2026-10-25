# Local integration candidate, October 24, 2026

Branch `claude/integration-2026-10-24`, local only: nothing here is pushed,
merged into main, published or submitted. The integration source is `d7ff886`;
the commit adding these notes changes documentation only.

## Inputs, each verified before use

| Input | Exact source | How it was checked |
|---|---|---|
| Base | `6a87937f9f185ac0760d6f8331184e34b876d92c` | present in this repository |
| Cloud dependency and privacy follow-up | `226d317a2a9eb22c2b16770ec0db15de5be4952e`, from `calm-frames-followup-226d317.zip` (237,073 bytes, sha256 `bb152edf8a81c1fec7a4a6b933584569acbbc2be73b683a71d164cdc547b7e04`) | the transfer receipt matched the ZIP's size and hash, the head, the base and the bundle and patch hashes; every member matched its SHA256SUMS; the bundle verified here and needs only `6a87937`; its seven commits and tree `c1f2a9b` match the manifest; imported as `codex/mac-followup-226d317` |
| Item 6 production fix | `dd1ec6c37f5d5ed86138bc38867d0b16b245a9b8` | named as the production fix in the item 6 export manifest; cherry-picked alone as `161c2f5`, because its parent is a fixture commit and a merge would have brought the fixture in |
| Item 11 | `claude/native-accessibility-2026-10-24` at `a800fb4` | merged as `a0c8816`, so production commits `4d4152c`, `3ede1fa`, `88c1716`, `eeaaf16`, `3b0174b` and notes `0eab3c4`, `a800fb4` keep their SHAs and cannot be applied twice; none was already in `226d317` |

Never brought in: the item 11 harness branches (`5e48655`, `4553ee3`), the item 6
fixture, test and harness commits (`6f5aa66`, `444ca91`, `c812685`, `78e8a2c`,
`b9cd627`), any made-up household or PIN constant, and any temporary entry
wiring. `app/index.js` is byte for byte the base's.

## Commits after `226d317`

| Commit | What |
|---|---|
| `161c2f5` | Item 6: each first run step opens at the top of its own scroller (from `dd1ec6c`) |
| `a0c8816` | Merge of item 11 |
| `738381d` | One test holding the merged name editor's announcement and its private trace together |
| `d7ff886` | The hook package mirror brought up to the cloud's private trace change |
| this commit | These notes and the ledger rows below |

## How the overlaps were resolved

- `ProfileNameEditor.tsx` merged without a conflict and keeps both sides. The
  letter keys keep the cloud's `traceFocus={false}`, and the draft field stays
  item 11's flush reading stop with its polite live region. Its trace id,
  `profile-name-field`, holds nothing typed. `nameEditorIntegration.test.tsx`
  holds both. Four breakages each turned it red at an assertion: tracing the
  letter keys again, dropping the live region, a fixed announcement, and a
  trace that carries what VoiceView says.
- `CHECKPOINT.md`: rows 10 and 12 are the cloud's, and row 11 joins both sides.
- The cloud changed `CalmTouchable.tsx` and a comment in `trace.ts` without
  syncing their copies in `hook/src/engine`, so `hookMirror.test.ts` fails on
  `226d317` itself. `d7ff886` is exactly what `node hook/tools/sync.mjs`
  writes. No item 6 or item 11 file is mirrored.

## Checks on `d7ff886`

- `npm ci --ignore-scripts` and `setup:player` with the cloud's lock (sha256
  `e1ca817d...2398`, as its manifest records). Node 22.23.2, npm 10.9.8.
- Typecheck passes. Lint has 0 errors; its 104 warnings are not in a changed
  file. The style check passes.
- CI's prepared-asset and tooling step passes all 87 Node tests, including the
  cloud's dependency and logger tests.
- The full app suite passes: 177 suites passed and 1 skipped; 1875 tests passed
  and 4 skipped. The first full run, before `d7ff886`, failed only
  `hookMirror.test.ts`.
- `make test-hook-package` passes. `make pins` finds nothing loose.
- `make sbom-check` passes. `make audit` finds 21 npm advisories, none
  critical, and none in Python. Advisory 1243074 (`body-parser`, high) appeared
  after the cloud's scan of the same lock and has no exception. The two older
  exception groups expired on October 21. `make audit-check` fails on those
  three. They are recorded here, not re-dated.

## On the device

Vega Virtual Device, 1920 by 1080, each package installed package scoped.

| Package | Bytes | sha256 | sha384 |
|---|---|---|---|
| Candidate `d7ff886` | 132,679,215 | `e21eaf5f561f36573cf22d65930dd63bf1cdf7de4160f1397dd0a009bd6408f5` | `0dee4edc...9f66` |
| Harness A `937c27e`, never merge: the item 11 harness with the focus trace on | 130,748,953 | `f24d7149ea9e6ef5bc59e5f3f4971f879b43f194e7f76b606d60e4d56dd3602d` | `41ac7436...0e87` |
| Harness B `ec68707`, never merge: the item 6 fixture | 130,706,023 | `237a61b96576e37ea165e22a2fdfeab4f4af0d9763e69a0059c5786179f699b7` | `437b3aed...37c5` |
| Rollback, production build of `6a87937` | 132,661,830 | `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` | `b268be99...b458` |

- The candidate opens on the ordinary Home. With VoiceView on it says "Details:
  Acadia, button. Watch: Acadia, button. McWay Falls, 5 minutes, button,
  selected", as item 11 left it.
- Private trace, harness A, made-up household, debug trace on, a log stream
  whose filter counts but never writes a line naming a key: focus moved over
  six PIN keys with no key pressed, then over letter keys with one made-up
  letter typed. 0 key focus traces. Ordinary controls were traced: the menu
  buttons, Back, the profile chips, Add a kid, Edit name and the name field.
  No kept line names the made-up name.
- The merged name editor, harness A, VoiceView on: the field says the made-up
  draft with "4 of 16 characters", Down reads a letter key, Up returns to the
  field, and Back closes the editor without saving.
- Item 6 recheck, harness B, on the integrated code: the preset step opens at
  its top with Next; after Extra cautious the first Down only scrolls the list's
  padding and the second reaches Next; the room step opens at its top with its
  safety line; Next is reachable; the explainer opens at its top with Your
  household in full and Open library focused; the remote's Back walks one step
  and the room step opens at its top. The approved disclaimer still starts
  below the explainer's edge.
- Restored: the rollback package, ordinary Home, VoiceView off and silent.

The owner's PIN was not entered. The made-up PINs went in with every press
withheld, VoiceView off and no stream, log reader, filter or recorder running.
No playback was started, so no saved place changed. The earlier correction
stands: item 11's first pass moved McWay Falls from 0:36 to 0:55.

## Item 6 coverage

Observed in its own pass, on its fixture at `6a87937` with harness `b9cd627`:
footers visible and reachable at 1920 by 1080 and 1280 by 720, Back walking one
step, the longest choices, and the fix itself at both sizes. Rechecked here at
1920 by 1080 on the integrated code. Still needed on the integrated build: the
production first run on a fresh household, which this session cannot reach
without resetting the real one, and 1280 by 720. Still open from item 6: the
disclaimer below the explainer's edge, one extra Down on the preset step, and
the device turning its display off after idle time. The fixture's own control
test, which expected the keypad to be traced when nothing turns it off, now
fails on the never-merge harness because the cloud fix removed that trace.

## What stays open

- Item 11 stays partial. Still open: the seek bar's progress announcements
  (blocked upstream in Kepler UI Components 3.2.2); VoiceView's own Back or bare
  button as the resume prompt opens; reduced motion, which this virtual device
  cannot show; and, at 1280 by 720, Down from the Parents explainer to the
  footer, the profile chooser and the player.
- Owner listening, palette, comfort and full-video review stay pending.
- Hosted CI on this exact source, residual Audit findings and the native module
  inventory stay with the integration owner.
- Nothing here signs off medical safety, human comfort or the 20 items.
