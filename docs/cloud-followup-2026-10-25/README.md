**Latest continuation:** [actual caregiver fixes, licensed-file verification and video](../cloud-deliverables-2026-10-25/README.md). The dependency record below remains valid for its stated source; the four-advisory migration decision is unchanged.

# Prior dependency continuation from cb96e21

Product/toolchain at this prior checkpoint: **`365be0813a8416399ada1d469b0db326d45917d4`** on
`codex/native-defect-fixes-2026-10-25`, continuing the verified clean checkpoint
`cb96e21ed8db8719ce066bd7f7cdff4f583d6ca0`. Later documentation commits are
identified by the full HEAD and tree in the verified transfer's `SYNC_MANIFEST.json`.

## Completed in this pass

- **Item 12:** fixed the legacy notifier advisory, reducing **5 to 4**. The
  actual old CLI and current Jest reporter pass consumer checks with notifier
  8.0.2 and the already-fixed UUID 11.1.1. No other retained package version
  changes. The Mac notification executable is byte-identical; native delivery
  was not tested. [All five original paths and exact migration boundaries](REMAINING_DEPENDENCIES.md).
- Corrected two earlier attributions: the notifier comes from the old CLI;
  the WebSocket header advisory applies only to the DevTools 3.3.3 copy, not
  the two 1.1.5 copies. The fragmentation advisory still affects all three.
- **Items 18/19:** updated the original ledger and the
  [single native verification queue](NATIVE_VERIFICATION.md). The current
  generated-player archive is bound to this lock. Older transfers remain
  preserved but must not be used as the latest source.

The [new receipt](../../results/residual-dependencies-2026-10-25/validation.json)
records a fresh locked install on Node 22.23.2/npm 10.9.8, normal typecheck/lint,
prepared-library/Playback Proof gates, all 150 Node tooling tests, normal player
generation and three reproduced SBOMs. Existing lint/peer warnings and a
nonfatal Metro probe cache-write warning remain visible. The new notifier's
five tests are included in the 150, not extra independent passes.

Audit still exits 1: **4 distinct advisories (3 high, 1 moderate)**, with nine
affected npm package entries and both October 21 exception groups expired.
No gate, exception, review date or owner acceptance changed. No new native
package, hosted CI or audiovisual acceptance is claimed.

## Preserved earlier work

The [prior receipt](../../results/cloud-followup-2026-10-25/validation.json)
belongs to the previous continuation through `09b3c55` and checkpoint `cb96e21`:

- [Eight prior dependency fixes](DEPENDENCIES.md) reduced 13 advisories to 5,
  with actual SDK parser/CLI/manifest/filter/watcher consumer evidence.
- [Local import recovery](IMPORT_RECOVERY.md) fixes damaged-record isolation,
  worker ownership until exit and recoverable oversized timestamps. Its 116-test
  intake/delivery run, overlapping 54-test final subset and real browser checks
  were not repeated because this pass did not change those files.
- The [licensed-content plan](LICENSED_CONTENT_PLAN.md) and
  [demo production-input plan](DEMO_PREPARATION.md) remain plans. No long edition,
  production footage, manga or narration was generated.

The earlier 1,905-test app run remains at `64f792b`; it was not relabelled as a
new run. Native UI, D1/D2/D3, coastal background, guard, household/PIN code,
pipeline, approved media, signing, disclaimer, judging package and approved
storyboard are unchanged from `cb96e21`.
[Preservation evidence](../../results/residual-dependencies-2026-10-25/preservation.json)
also checks the named never-merge exclusions remain outside ancestry.

## Remaining work

The [original ledger](../cloud-integration-2026-10-23/CHECKPOINT.md) remains
**6 complete, 12 partial, 2 blocked**. Completed **5, 6, 9, 14, 15, 18** stay
closed. No whole acceptance item closes from this dependency fix alone.

1. **#12:** remaining nested RN, DevTools and two WebSocket advisories need a
   supported SDK/tooling migration or a separately authorized compatibility
   project. The [exact options](REMAINING_DEPENDENCIES.md#where-the-remaining-migration-paths-stop)
   distinguish a demonstrated WebSocket API break from unverified renderer
   compatibility. That broader path is stopped; Audit remains blocking.
2. **#1/#2/#3/#4/#10/#11/#19/#20:** the one native queue covers focus, saved
   Reading comfort visibility, actual pause speech, route/media frames, recovery
   and exact new package inventories. No cloud result supplies these observations.
3. **#7/#13/#16:** qualifying licensed long files, approved personal-edition
   delivery and accepted-build raw demo takes remain missing. Short previews
   and reference JPEGs do not fill those gaps.
4. **#8/#17:** owner picture/sound/comfort observations and account/judge-access
   confirmation remain blocked. Technical checks do not establish human or
   medical acceptance.

Native work can wait until home. Manga, ElevenLabs and the production demo stay
parked until the product is accepted and frozen. No push, merge, purchase,
public upload or live-submission change occurred.
