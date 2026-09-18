# Verify pass 1: family profiles (e86aa1f) and the map registry (262200b)

Date: 2026-09-17, late. Verifier lane, read only. Everything below was checked against the
committed versions at 262200b, exported with `git archive` into a scratch directory, with the
app's `node_modules` and the repo's `.venv` linked in and `PYTHONPATH` pointed at the exported
flashmap, so nothing in the shared tree was touched and no dirty file from another lane was
measured. Scratch tests written for this pass live in that export only and are not committed.

## FAILS

Nothing. No claim in either commit message, docstring or DECISIONS entry was found to be false.
I could not construct a profile, by any route the code allows or by 5000 random pairs of floor
and profile including NaN, negative, infinite, string and unknown-preset values, that hides less
than the household floor or less than WCAG.

## HOLDS WITH A CAVEAT

- **"Every refusal ends with the picture hidden" (262200b).** HOLDS WITH A CAVEAT. Every
  refusal is `ok: false` and every message says "the picture stays hidden" (all eleven reasons
  tested, plus the nine attack cases below). But nothing in `app/src` or `hook/` calls
  `lookupMap` (`git grep` at 262200b finds no call site outside the file itself), and the guard
  in `useFlashGuard.ts` never consults the registry. Hiding the picture is the caller's contract,
  not something the app does today. The commit says the hook does not export it yet; it should
  also say the app does not use it yet.
- **"Thirty days against a map's ninety" (262200b).** HOLDS, and the residual it leaves is real
  and worth stating in plain words wherever the registry is described. With the fixture key
  (derivable from the phrase in `make_registry_fixture.py`, by design) I built an older index
  listing the sham `registry_swapped_map.json` for the hazard clip, served both, and the reader
  returned `ok: true, segments: 0, hiddenMs: 0` at 19 days after that index's date, and
  `registry-stale` at 31 days. So whoever serves the files can roll a title back to "nothing to
  hide" for up to thirty days after the honest set replaced it. Declared in the module docstring
  and DECISIONS; not stated as a number of days of exposure anywhere a judge would read.
- **DECISIONS: "nothing stops an older child watching under a younger one's profile. That gets
  them more hidden, not less, so it fails safe."** HOLDS WITH A CAVEAT: the reasoning is one
  directional. The shelf picker has no lock, so a younger kid can pick the older kid's profile
  and get less hidden than their own profile, down to the household floor. The floor is enforced
  against everyone; anything a parent sets above it for one kid is advisory. The commit message's
  claim "no profile that can hide less than the house" is still true.
- **Per-profile hidden-segment logs (e86aa1f).** HOLDS WITH A CAVEAT. The model and its tests
  are right (keyed by id, survives rename, capped, "Everyone" merges newest first, and the
  parent area reads `logForProfile`, seen red in F3 below). But `KidModeScreen.tsx` holds
  `profileLogs` in a `useState` with no setter and the player cannot post into it, so in the
  running app every kid's record is empty. DECISIONS says so. The commit message's "one kid
  opening the parent area sees their own record and not another kid's" is true of an empty record.
- **Up to four kids, each with a preset and room (e86aa1f).** HOLDS (`MAX_PROFILES = 4`,
  `addProfile` refuses, `clampFamily` truncates, the screen hides "Add a kid" and says so).
  Caveat: the family, like the PIN before it, lives in React state only, so the four kids and
  their settings are gone on the next launch, and they are all called Kid because there is no
  keyboard. Both are in DECISIONS or the screen's header comment, neither is in the commit message.
- **The parent area is truthful about the floor only on the preset axis.** HOLDS WITH A CAVEAT.
  `describeFloorEffect` compares presets only (`profiles.ts` line 284). Reproduced: floor
  85 inch at 4 feet, Sam set to the same preset with a 32 inch television at 12 feet; the guard
  runs with the floor's room (correct, stricter), but the parent area's room line reads "32 inch
  television, seats about 12 feet away" with no note. Safe direction, untruthful display.
- **"No profile can be weaker than the household floor" rests half on code and half on a
  table.** HOLDS. The WCAG half is code alone: every preset's `mapProfiles` includes `wcag` and
  `coverOptionsFor` floors the guard band and minimum cover at 500 and 400 ms whatever the
  preset. The household half picks the stricter preset by `PRESET_STRICTNESS`, a hand-written
  rank that the code never derives from what the presets contain. A future preset ranked wrongly
  would be caught by the test "agrees with what the presets actually do", not by the code. For
  the three presets that exist the rank is right: maps `[wcag]`, `[wcag, broadcast]`,
  `[wcag, broadcast]`; guard 500, 500, 1000; minimum cover 400, 400, 800.
- **"The path may not leave the index" (262200b).** HOLDS for entry paths (A8 below, and six bad
  shapes refused without a fetch). Caveat: `resolveMapUrl('https://maps.example',
  'maps/bursts.wcag.json')` returns `https://maps/bursts.wcag.json`, another host, because the
  base is cut at the last slash and a pathless origin's last slash is the one in `https://`. The
  registry URL is the app's own configuration, not attacker input, so this is a bug and not a hole.
- **"parent-area-profile at 47 lines and 23 controls" (e86aa1f).** HOLDS on the numbers, the
  name is mixed. The ten foot case that measures 47 lines and 23 controls is `parent-area-one-kid`;
  `parent-area-profile` is the frame name the flash run uses. There is also a third new case,
  `parent-area-family`, at 46 lines and 22 controls, which the message does not mention.
- **"npm run ui:flashmap says no segment broke the thresholds across 24 screens and
  transitions" (e86aa1f).** HOLDS, reproduced: `PASS ... below the wcag thresholds`, 24 frames,
  exit 0, run with the exported (committed) flashmap. Caveat: `docs/STATUS.md` line 88 still
  says "20 screens and transitions". Not a README number, but it is a published number that is
  now stale.
- **`verify_registry` in `pipeline/registry.py` "checks the same things" as the app reader.**
  HOLDS WITH A CAVEAT: it does not check the date. A signed index dated 2020 passes
  `python -m pipeline.registry --check` with no problems. The app refuses it. Producer side
  only, so no exposure, but the docstring overstates.
- **"Every entry goes through verifyFlashMap" (262200b).** HOLDS as a builder claim (every map
  is verified with `public.verify` before it is indexed; the builder refused both the retired-key
  fixture map and a bursts map re-signed by another key when I fed them to it) and as a lookup
  claim for the one entry that is used. The app does not re-verify entries it does not fetch.

## HOLDS

- Signed index keyed by the video's SHA-256, one entry per profile, carrying path, signature,
  date and counts. HOLDS: `docs/SIDECAR_SPEC.md` "The registry, version 1", the builder, the
  reader and the committed fixture all agree, and the fixture rebuilt by
  `make_registry_fixture.py` in the export is byte-identical to the five committed files.
- The entry carries the map's signature, so a validly signed but wrong map cannot be swapped in.
  HOLDS: existing test (A6 docstring), plus my run serving a bursts map re-signed by a key the
  app does not hold under the honest index: `map-refused` / `unknown-key`.
- A validly signed index whose entry points at a map for a different video fails closed. HOLDS:
  I signed one with the fixture key (entry for the bursts hash pointing at the calm map with the
  calm map's real signature); `verifyRegistry` accepts the index, `lookupMap` returns
  `map-refused` / `wrong-file`, "the map is bound to a different file than the one about to play".
- An index that omits a file that has a map fails closed. HOLDS: `not-listed`, nothing fetched
  but the index (existing test). Without the key the only way to make such an index is a replay,
  which is the thirty day caveat above.
- An expired index fails closed. HOLDS: `registry-stale` at bound plus one millisecond, accepted
  at the bound (existing test), and at 31 days in my rollback run.
- The registry honours the app's revoked-key handling. HOLDS: the app has one current key and
  no list; an index re-signed by a retired key is `registry-unknown-key` (not `bad-signature`),
  a map signed by a retired key served under an honest index is `map-refused` / `unknown-key`,
  and the builder refuses to index such a map ("was signed by a key this build does not hold").
  The shipped `OFFLINE_PUBLIC_KEY_BASE64` is not the reconstructible fixture key.
- A map whose signature matches the entry but whose hash does not match the video: HOLDS, by
  construction it cannot exist (the signature covers `source.sha256`), and the nearest thing to
  it, the wrong-video index above, is refused on the hash.
- A tampered entry fails closed. HOLDS: five unsigned edits all `registry-bad-signature` and
  `ok: false` through `lookupMap` (A4 reproduced below).
- Reproducible bytes. HOLDS: the copytree-and-utime test (P3 reproduced red below) and the
  byte-identical fixture rebuild.
- One household PIN. HOLDS: `PinGateState` sits beside the family in `KidModeScreen`, never in a
  profile, and the parent area stays unlocked while switching kids (existing test).
- Profile picker on the kid home screen. HOLDS: `KidHomeScreen` renders `ProfilePicker` when
  given profiles, `KidModeScreen` passes the family and wires `selectProfile`; not drawn on an
  empty shelf.
- Both new states in `ALL_UI_FRAMES` and through the ten foot pass. HOLDS: the uiCapture test
  asserts both frames are listed; the ten foot pass has three new cases, all green.
- "Seven more on the app side and fifteen on the pipeline side" seen-to-fail docstrings. HOLDS:
  eight app docstrings including the headline one, fifteen pipeline docstrings.

## Numbers

| Number | Where | Backing | Result |
| --- | --- | --- | --- |
| kid-home-profiles: 9 lines, 4 controls | e86aa1f message | `app/build/ui-capture/ten-foot.json`, written by `tenFoot.test.tsx` (gitignored build output, not `results/`) | reproduced, 9 and 4 |
| parent-area-profile: 47 lines, 23 controls | e86aa1f message | same file, case `parent-area-one-kid` | reproduced, 47 and 23 |
| worst text contrast 5.12 to 1, worst focus contrast 3.39 to 1 | e86aa1f message | same file, `totals` | reproduced, 5.12 and 3.39 |
| 24 screens and transitions, no segment | e86aa1f message | `npm run ui:flashmap` (CI runs it; no `results/` file) | reproduced, 24 frames, exit 0 |
| pytest `-m "not slow" pipeline` green at 307 | 262200b message | the run | export: 307 passed. Shared tree today: 335, because another lane added `test_upload_server.py` |
| app: 24 suites, 377 tests | 262200b message | the run | export: 24 and 377. Shared tree today: 25 and 395 (another lane's `chimeCue.test.tsx`) |
| tsc clean | 262200b message | `npx tsc --noEmit` | shared tree: exit 0 (the export shows four TS2742 errors caused only by my symlinked `node_modules`) |
| 30 days index, 90 days map | code, DECISIONS, message | `DEFAULT_MAX_REGISTRY_AGE_MS`, `DEFAULT_MAX_MAP_AGE_MS`, asserted in tests | holds |
| 0.11337023775422096 and 0.35041709851304664 | e86aa1f message | field fraction of 85 inch at 48 inches and 55 inch at 96 inches | arithmetic checks, and reproduced in F2 |
| 20 screens and transitions | `docs/STATUS.md` line 88 | stale, now 24 | needs updating |

## Seen-to-fail claims reproduced

Three picked at random from the 26 such claims across both commits
(`random.Random("e86aa1f+262200b verify pass 1").sample(range(26), 3)`), each applied to the
export, the test run, the file restored and diffed against the commit afterwards.

1. **A8, `mapRegistry.test.ts`: `isInsideRegistry` returning true for everything.** Claimed:
   `Expected: false / Received: true / at Object.toBe (test/calmframes/mapRegistry.test.ts:422:37)`.
   Got exactly that: `✕ that leaves the index is refused without being fetched`, `Expected: false`,
   `Received: true`, `at Object.toBe (test/calmframes/mapRegistry.test.ts:422:37)`; 1 failed, 15 passed.
2. **P3, `test_registry.py`: `_relative` handing back the absolute path.** Claimed: `assert
   b'{\n  "creat...sion": 1\n}\n' == b'{\n  "creat...sion": 1\n}\n'`, `At index 479 diff: b'p' != b's'`.
   Got exactly that, at `test_registry.py:182`. The same mutation also reddens four other tests
   (path assertion, command line check, stranger key, fixture rebuild), which the docstring does not
   claim and which is consistent with a broad mutation.
3. **P15, `test_registry.py`: one character of the fixture's `payload_sha256` changed.** Claimed:
   `AssertionError: assert ['signature payload_sha256 does not match the index body'] == []`.
   Got exactly that at `test_registry.py:523`; 1 failed. Note this is a fixture mutation, not a code
   mutation, and the app reader ignores `payload_sha256` (the spec calls it a debugging field), so
   only the pipeline test catches it.

Extras, outside the random pick, because they are the claims the two features exist for:

- **F1**, `effectiveSettings` returning `chosen.preset`: 5 failed, first "is never weaker than the
  household floor, whatever it picks", `expect(received).toContain(expected) // indexOf`,
  `Expected value: "broadcast"`, `Received array: ["wcag"]`. Matches.
- **F2**, room comparison `<=` flipped to `>`: 1 failed, `expect(received).toBeLessThanOrEqual(expected)`,
  `Expected: <= 0.11337023775422096`, `Received: 0.35041709851304664`. Matches.
- **F3**, parent area reading `allProfileHides()` for `logForProfile()`: 1 failed, `Expected substring:
  "Robin title"`, `Received string: "16:00 Sam title: hid 4 seconds at 1:00"`. Matches (the "16:00"
  is local time and would read differently on a UTC runner).
- **A4**, `verifyEd25519` in `verifyRegistry` made unreachable: 1 failed, the array diff
  `"points the player at another map", - false, + true`. Matches.

## Attack log for the registry reader (scratch, export only)

| Case | Result |
| --- | --- |
| honest index and map | `ok: true`, 3 segments, 10200 ms |
| older signed index plus older signed map, 19 days later | `ok: true`, 0 segments (the declared rollback residual) |
| same, 31 days later | `registry-stale` |
| signed index whose bursts entry names the calm map | `map-refused` / `wrong-file` |
| honest index, map re-signed by another key | `map-refused` / `unknown-key` |
| index re-signed by another key | `registry-unknown-key` |
| five unsigned edits to the index | `registry-bad-signature` each |
| six entry path shapes that leave the index | refused, nothing fetched |
| builder given a retired-key map or an other-key map | `RegistryError`, "a key this build does not hold" |
| `python -m pipeline.registry --check` on a signed index dated 2020 | passes (no date check on the producer side) |
