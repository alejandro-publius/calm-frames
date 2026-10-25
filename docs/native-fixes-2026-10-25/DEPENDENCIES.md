> Historical 64f792b pass. For the current source, dependency counts, compatible generated inputs and native queue, use the [cloud continuation](../cloud-followup-2026-10-25/README.md). Counts below describe that prior pass.

# Dependency remediation and remaining policy failures

Product source `a6bdb62276dd63603716509e24b2034451b46b44` removes two of the
15 previously recorded advisories. The [fresh audit](../../results/audit.json)
still exits nonzero: **13 distinct advisories (9 high, 4 moderate)** affect
25 npm package entries. The scanner's 14 high and 11 moderate totals count
package entries, not distinct advisories. Python scans found no advisories
across the 12 ingest, 14 CDK and 54 recorded development packages.

## Fixed with consumer evidence

**GHSA-vcc3-ghjq-m6fr, decode-uri-component.** The old 0.2.2 decoder is the only
vulnerable dependency identified inside both received fbe53bf app packages.
Its malformed-escape recursion could exhaust CPU. A bounded child-process
regression with repeated malformed escapes timed out before the fix. The fixed
0.5.1 decoder exports ESM; a blind leaf override breaks the CommonJS consumers.
The small [legacy adapter](../../app/vendor/decode-uri-component-legacy/README.md)
unwraps that export and retains legacy plus-to-space behavior without copying
the vulnerable parser. Actual query-string, navigation linking, source-map
resolution and a bundled Metro consumer pass. The old recursive implementation
is absent from that Metro test bundle. These are compatibility checks, not a
new native package inventory or a published performance benchmark.

**GHSA-w5hq-g745-h8pq, uuid.** The installed xcode 2.1.0 consumer only calls v4
without an output buffer and formats its 24-character object IDs. Its scoped
dependency now resolves 11.1.1. The old v3/v5 short-buffer behavior fails the
new regression; the fixed API rejects invalid bounds. Actual project
parse/write/reparse and v4 generation pass with xcode itself unchanged. The
vulnerable copy did not ship in the received app packages, and no exploit in
the observed v4 consumer is claimed.

Both lock changes were installed with `npm ci --ignore-scripts` using Node
22.23.2/npm 10.9.8. Normal typecheck, lint, full Jest, prepared-media checks and
129 Node checks pass. The normal Shaka build completed with these inputs.
All three SBOMs reproduce using cyclonedx-py 7.4.0, cyclonedx-python-lib 11.12.0,
cyclonedx-npm 6.0.1 and cyclonedx-library 10.3.0. Existing peer-resolution
warnings from the inherited SDK graph remain visible in the SBOM log.

## Remaining advisories

The [machine ledger](../../results/native-fixes-2026-10-25/residual-risk.json)
lists primary advisory URLs, exact installed nodes/versions, ranges, exposure
limits and next actions. No exception date was changed.

| Installed vulnerable component | Advisory IDs | Compatible-remediation boundary |
|---|---|---|
| braces 2.3.2, micromatch 3.1.10 | GHSA-grv7-fg5c-xmjg; GHSA-952p-6rrq-rcjv | Old Metro/sane glob consumers need a tested major-version migration; retain trusted repository patterns meanwhile. |
| node-notifier 5.4.5 | GHSA-5fw9-fq32-wv5p | Fixed major 8 changes the old Jest notification dependency; no watch notification service was started in this pass. |
| nested react-devtools-core 3.6.3 and React Native 0.60.6 | GHSA-rxrc-rgv4-jpvx; GHSA-7f53-fmmv-mfjv | Legacy SDK build graph needs a supported consumer migration. Do not replace the device's RN runtime by overriding this nested graph. |
| toml 3.0.0 | GHSA-82x6-q7mm-w9cf; GHSA-v5mp-jgw5-2x6j; GHSA-4qx8-w7c3-pj3p; GHSA-9j65-hcg3-gc64; GHSA-9qmh-m7c6-f92p | Existing narrow controlled-build approval through October 30 only: reviewed hashed manifests, bounded isolated builds. No two-major blind upgrade or renewed approval. |
| ws 1.1.5 / 3.3.3 | GHSA-3h5v-q93c-6h6q; GHSA-96hv-2xvq-fx4p | Legacy inspector code reads `socket.upgradeReq.url`; fixed major 5 needs its consumer migrated. Keep development endpoints local; that is a mitigation, not clearance. |
| yargs-parser 7.x | GHSA-p9pc-299p-vxgp | Older yargs consumers require migration of option/coercion contracts before a major override. Use reviewed local CLI inputs. |

Both `in-the-device-bundle` and `not-in-the-device-bundle` exception groups
expired on October 21. A package no longer shipping does not renew its expired
build-host risk acceptance. The five-advisory TOML approval does not cover the
other findings. Audit remains a release blocker; no owner acceptance is signed.

## Shipped versus development scope

The [received source-map-bound inventories](../../results/native-validation-fbe53bf-2026-10-25/native-results/)
show only decode-uri-component 0.2.2 among vulnerable copies in fbe53bf Debug
and Release. Top-level react-devtools-core 6.1.5 appears in Debug only; it is
not the flagged nested 3.6.3. The other vulnerable copies are installed build
dependencies, absent from those packaged bundles. RN/Kepler/navigation also
use device system bundles outside that app inventory.

This new source has no native package yet. Rebuild and bind each new source map
to its packaged bundle hash before asserting the decoder replacement actually
ships. Check device system resolution separately; do not turn an old inventory
or a tiny Metro test bundle into a current native acceptance claim.
