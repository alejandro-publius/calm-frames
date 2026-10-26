# One native verification handoff

This is the single home verification queue for the preserved native fixes plus
the new dependency lock. It is not another full acceptance pass on fbe53bf. Keep completed #5/#6 and the accepted disclaimer. Use the final
full source SHA in the transfer's `SYNC_MANIFEST.json`; product changes end at
`fc83982220bf1b87774b75377e3b779043550cea`. No new native package exists in this
cloud. The received fbe53bf package hashes cannot identify the new build.
The dce5d40 and older transfers are preserved but superseded for new work. This
continuation repairs caregiver failure/delivery handling and produces editorial
assets. The source transfer manifest selects the latest canonical SHA. Native app source,
D1/D2/D3, dependency locks and generated inputs remain byte-identical to 67e10f0.
Reuse the verified 365be08 input archive included with the latest transfer; no
player regeneration was needed. Keep one native batch, bound to the final SHA. Do not build or import rejected
experiment `c1f57f4831d11f476b7e06d05cf7e239d2601374`; its dependencies failed
the first Audit gate. Do not rerun the completed device idle-timeout test.

## Separate worktree

When home, download the small local source transfer and verify its outer hash
against the handoff. In the extracted directory run `shasum -a 256 -c SHA256SUMS`.
Replace only these local path placeholders with actual locations:

```sh
CALM_TRANSFER="/absolute/path/to/extracted-transfer"
CALM_REPO="/absolute/path/to/existing/calm-frames"
CALM_NEW_TREE="/absolute/path/to/new/calm-frames-native-fixes-review"
CALM_SHA="$(python3 -c 'import json,re,sys; s=json.load(open(sys.argv[1]))["head"]; assert re.fullmatch("[0-9a-f]{40}",s); print(s)' "$CALM_TRANSFER/SYNC_MANIFEST.json")"

git -C "$CALM_REPO" status --short
git -C "$CALM_REPO" cat-file -e 37d10c2db57fc0868499adc133cff7560600d5cc^{commit}
git -C "$CALM_REPO" bundle verify "$CALM_TRANSFER/calm-frames-native-fixes.bundle"
git -C "$CALM_REPO" fetch "$CALM_TRANSFER/calm-frames-native-fixes.bundle" refs/heads/codex/native-defect-fixes-2026-10-25
git -C "$CALM_REPO" worktree add -b codex/native-fixes-review-2026-10-25 "$CALM_NEW_TREE" "$CALM_SHA"
git -C "$CALM_NEW_TREE" rev-parse HEAD
git -C "$CALM_NEW_TREE" status --short
```

Run sequentially and stop on error. These commands do not switch or reset the
original checkout. If the required base is absent, fetch the existing private
`codex/native-validation-handoff-2026-10-25` branch and verify 37d10c2 first.
If the destination or branch already exists, inspect it and choose a new name.
Do not force-reset it. The included binary patch is an alternative recovery
from the same base, never an extra patch to apply after bundle import.

## Locked setup and native build

Use the existing licensed Vega SDK 0.24.9914 / CLI 1.3.4 environment, pinned Node
22.23.2/npm 10.9.8 and JDK 21.0.12.1 from the successful fbe53bf build. Check
`node --version`, `npm --version` and `java -version` after loading that SDK
environment. The Mac previously selected Java 8 through its default selector;
use its already installed JDK 21, not an unverified fallback. No SDK download,
signing change or environment reinstall is required by this handoff.

```sh
cd "$CALM_NEW_TREE"
npm --prefix app ci --ignore-scripts --no-audit --no-fund
python3 docs/cloud-followup-2026-10-25/restore_generated_player.py \
  --archive "$CALM_TRANSFER/calm-frames-generated-player-inputs-365be08.zip" \
  --checkout "$CALM_NEW_TREE" --expected-head "$CALM_SHA"
npm --prefix app run check:native-inputs
npm --prefix app run typecheck
npm --prefix app run build:debug
git status --short
shasum -a 256 app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
shasum -a 384 app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
```

The shown package path is the established Apple Silicon target; use the actual
matching x86_64 output on Intel. The restore helper validates the exact archive,
all generation inputs and current HEAD, refuses linked destinations and cannot
overwrite tracked source. If inputs differ, preserve them and use normal
`npm --prefix app run setup:player` instead of bypassing the checks. Do not use
the broad build task with automatic lint fixes. Existing prebuild and postbuild
package gates remain active.

Use the established package-scoped install on a disposable fictional household
for these checks. For the known Apple Silicon package and an already running
virtual device the commands are:

```sh
vega device is-connected --device VirtualDevice
vega device install-app --device VirtualDevice \
  --packagePath "$CALM_NEW_TREE/app/build/aarch64-debug/calm-frames-app_aarch64.vpkg" --buildType Debug
vega device run-cmd --device VirtualDevice \
  --command 'vmsgr send pkg://io.github.alejandropublius.calmframes.main'
```

Do not uninstall, clear storage, modify the real household or enter its PIN in
a script/log. Record package bytes, SHA-256/SHA-384, source, SDK and actual target
before observations. Release still needs its own normal build, package inventory
and launch/Watch/Back check; Debug success does not supply them.

## Short check list, at 1920 by 1080 and 1280 by 720

1. **D1, #1/#2/#4/#11:** for each of four titles, card Down reaches Watch;
   Watch Up returns to that same selected card. Repeat Details Up. Confirm the
   title and focus ring remain correct. Retain #6's accepted layout unchanged.
2. **D2, #11/#20:** in a fictional profile's unlocked Parents, toggle Reading
   comfort on and off. The saved switch and its state remain fully visible and
   focused; Back must not steal focus. Move away during a save and confirm focus
   is not pulled back. Spot-check a second profile and restart persistence;
   existing name/PIN acceptance need not be repeated.
3. **D3, #3/#11:** with VoiceView, opening a player must not announce a pause.
   After actual playback, pause, let controls settle, hide/show them, resume and
   pause again. Listen for one notice per real pause. Record actual speech and
   whether Dolby is active; do not alter the audio engine to make a pass. A
   restored paused position must still show visible guidance.
4. **First frame, #3/#9:** observe McWay opening/resume choice, Sea Otters and
   Forest preview openings/endings. Separate any uniform near-white route frame
   from first media pictures or dark ending frames. The recorder's change-only
   durations are lower bounds. Do not claim decoder timing from source tests.
5. **#10/#12/#19 and owner #8:** retain protection floors and profile positions
   during the available recovery route; do not import a never-merge harness or
   corrupt household storage to force errors. Bind new package inventories to
   their own source-map/bundle hashes and check the fixed decoder resolution. Confirm the
   updated manifest builder and locked toolchain build both Debug and Release.
   Queue unavailable retry/caption/reduced-motion observations truthfully. The
   owner separately reviews picture, sound, palette, pacing and reading comfort.
6. **#2/#3/#10/#13:** inspect only normally reachable error/recovery views in the
   fictional household at both sizes. Record the displayed recovery action and
   essential protection/caption guidance; mark unreached paths unobserved. Direct
   TV file selection is not implemented and authorized personal-edition delivery
   remains absent, so do not mark either passed or invent a native picker test.
   Cloud import/report/delivery-fixture checks are recorded separately. If a later
   authorized exact edition is supplied, bind its approval/build/installed hashes
   and test its library entry, presets, captions if present and Back without
   changing household data. No unsigned import or old harness can fill that gap.

Passing D1 can close its focus subcriteria; D2 can close #20's machine/native
focus/layout subcriteria; D3 can close the pause-speech defect. None alone
establishes complete #1/#3/#11, human #8, release #19 or 20/20. #12 also needs
the remaining audit policy resolved. #7 still needs licensed long editions;
#13 still lacks a native file picker and approved personal-edition integration.

## Rollback and return

Keep the existing fbe53bf Debug package available. Its received SHA-384 is
`2b98119e38dd32128827c6e4241722b34aa0ab34101d5dd9526d8abd4b97a17984d9cc645451ddb06c9f692b94426bdf`.
Verify those actual retained bytes before relying on them. Older a672f57 and
6a87937 rollback hashes remain in the [received handoff](../../START_HERE_CODEX.md).
No binary was recreated in the cloud. Roll back by installing the verified
retained package without clearing data; older code can drop the optional Reading
comfort flag on a later save, which does not authorize resetting other settings.

Return one sanitized receipt: full source SHA, package hashes, viewport/build,
each observation above, failures and unobserved items. Do not return PINs,
private names, raw household captures or the entire 111 MB archive. No remote
push, main merge, publication or submission change follows from this handoff.
