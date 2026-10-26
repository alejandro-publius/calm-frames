# One exact-source Mac handoff

Import the final private ZIP into a new worktree. Preserve all existing branches,
the installed household, PIN, positions, rollback and frozen submission. This
handoff authorizes no push, merge, public upload or submission change.

The ZIP's `SYNC_MANIFEST.json` supplies the full source SHA, tree, branch,
prerequisite base, changed-file hashes and check scope. `SHA256SUMS` covers the
portable bundle, binary patch, generated-player ZIP and transfer records.
`TRANSFER_VERIFICATION.json` records import into an independent consumer and
patch reconstruction of the exact final tree. It does not claim a native build.

## Import without changing the current checkout

Use actual local paths for the extracted ZIP, existing private repository and a
new empty worktree location. The placeholders below are not asserted Mac paths.
Run `shasum -a 256 -c SHA256SUMS` inside the extracted transfer directory first.
Compare the outer ZIP hash with the hash supplied alongside the download.

```sh
CALM_TRANSFER="/absolute/path/to/extracted-transfer"
CALM_REPO="/absolute/path/to/existing/calm-frames"
CALM_NEW_TREE="/absolute/path/to/new/calm-frames-overnight-review"
CALM_SHA="$(python3 -c 'import json,re,sys; s=json.load(open(sys.argv[1]))["head"]; assert re.fullmatch("[0-9a-f]{40}",s); print(s)' "$CALM_TRANSFER/SYNC_MANIFEST.json")"

git -C "$CALM_REPO" status --short
git -C "$CALM_REPO" cat-file -e 15ef46c6e23c8ba627492da23b1b147000031aa4^{commit}
git -C "$CALM_REPO" bundle verify "$CALM_TRANSFER/calm-frames-overnight.bundle"
git -C "$CALM_REPO" fetch "$CALM_TRANSFER/calm-frames-overnight.bundle" refs/heads/codex/overnight-completion-2026-10-25
git -C "$CALM_REPO" worktree add -b codex/overnight-review-2026-10-25 "$CALM_NEW_TREE" "$CALM_SHA"
git -C "$CALM_NEW_TREE" rev-parse HEAD
git -C "$CALM_NEW_TREE" status --short
```

Run each command in order and stop on failure. If the required base is absent,
fetch the existing private `codex/final-handoff-2026-10-25` branch and verify the
base before retrying. If the review branch or destination already exists, inspect
it and choose a new name; never reset, delete or force-overwrite it. Fetching the
bundle imports objects and updates FETCH_HEAD only. The worktree command refuses
an existing branch. It does not switch the original checkout.

The binary patch is an alternative for inspection or exact-tree recovery from
the same base. Do not apply it on top of the bundle-imported source. The full
bundle retains local commit history, so prefer it for normal review.

## Prepare and build the native candidate

Use the repository's pinned Node 22.23.2/npm 10.9.8 and matching Vega SDK. The
cloud generated the ordinary player inputs but has no Vega SDK or native package.
Keep generated files and installed dependencies local and ignored.

```sh
cd "$CALM_NEW_TREE"
npm --prefix app ci --ignore-scripts --no-audit --no-fund
python3 docs/overnight-2026-10-25/restore_generated_player.py \
  --archive "$CALM_TRANSFER/calm-frames-generated-player-inputs-596418e.zip" \
  --checkout "$CALM_NEW_TREE" --expected-head "$CALM_SHA"
npm --prefix app run check:native-inputs
npm --prefix app run typecheck
npm --prefix app run build:debug
git status --short
```

Do not use the broad `npm run build` task here: it includes automatic lint fixes.
The debug native task retains the existing prepared-library, ambient and playback
proof prebuild gates plus package-content verification after build. A different
source or changed generation input requires normal `npm run setup:player`
regeneration instead of relabelling these generated inputs. A restore refusal
protects existing files; do not bypass it.

Record the actual package path, byte count, `shasum -a 256` and `shasum -a 384`,
source SHA, target architecture, SDK version and build log. Use the established
Mac installation procedure only after confirming the package identity and
retaining the rollback. No automatic uninstall, household reset, signing change
or real PIN entry is part of these commands. A Debug review package is not a
production release or publication approval.

## Native checks that remain

Keep #5 and the completed #6 two-size navigation observations. Do not repeat the
entire name-editor pass solely to transfer its evidence. Use a fictional test
profile, with any real PIN entered privately by the owner, and exclude typed
names, letter keys, PINs and account data from logs.

1. Check the new pause announcement once per real pause, including controls
   hiding and reappearing. Record any remaining upstream seekbar or intermittent
   resume-entry speech independently.
2. Check Reading comfort on/off for different profiles, relaunch persistence,
   Parents/More info wrapping, reading stops, scrolling, focus and VoiceView at
   1920 by 1080 and 1280 by 720. Do not corrupt household storage to test failure;
   controlled failure/retry is already covered by source tests.
3. Inspect Watch and card focus, footer reachability, native startup and scene
   transitions. Ask the owner whether the approved disclaimer must also be
   visible at rest. Navigation passing does not decide that layout preference.
4. Check recovery under a stricter profile without lowering protection or losing
   saved positions. The current consumer catalog has no caption tracks; do not
   report native caption restoration from unit tests.
5. Observe the other ambient titles and reduced-motion behavior. Long moving
   Forest/Sea Otters editions are absent; short previews are not substitutes.
6. Have the owner record picture, audio, palette, pace and comfort observations
   for this exact package. Leave unobserved items open. This is not medical
   validation, and source tests do not provide human acceptance.

The two existing native evidence archives listed in [WORK_STATUS.md](WORK_STATUS.md)
are still needed as actual readable bytes. Their capture work need not be redone.
Account/judge access and the residual dependency policy remain separate blockers;
see the [morning review](MORNING_REVIEW.md).

## Rollback and return receipt

The handoff's installed source is `a672f57d333dc0e3fada51b3175ca1711d1f9397`;
its recorded SHA-384 is
`480fd42d96096bb5a2b2c1a471fb0f498ab284118facd0561bdef19750e56506bded03dd3ec3e00204efced90ef30d59`.
The earlier retained rollback source is
`6a87937f9f185ac0760d6f8331184e34b876d92c`, recorded SHA-384
`b268be9946241be7e8efab64737e6672b907dfb2d9558cae6a90acb51349b1b02b63e68a7ea63fe4d259a8db432eb458`.
Verify the actual existing rollback bytes before relying on either recorded
hash. These binaries were not received or rebuilt in this cloud.

Rollback means installing the separately verified retained package through the
established procedure, without clearing app data. Older code ignores Reading
comfort and can drop that optional preference on its next household save. Names,
PIN, protection and positions must be retained; do not reset them to restore a
display preference. The submitted `bf2f615` fallback remains untouched.

Return one sanitized receipt with the transferred full SHA, new package SHA-384,
device/viewport, commands and outcomes, the exact native observations above,
owner decisions and unobserved items. Do not mark the release accepted, run paid
production or edit frozen materials from technical success alone.
