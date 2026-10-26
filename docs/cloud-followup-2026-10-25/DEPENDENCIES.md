# Prior cb96e21 dependency work: eight removed; five remained

This is the preserved prior checkpoint. The [current follow-up](REMAINING_DEPENDENCIES.md)
fixes one more finding and corrects the old CLI and WebSocket attributions.

Product/toolchain source `29173032a71e7a052b6dc71575e4a160df88563a` continues
the earlier decoder/UUID fixes without changing native app source. The fresh
[audit](../../results/residual-dependencies-2026-10-25/audit-at-cb96e21.json) has **5 unique advisories: 3 high, 2 moderate**,
down from 13 at `64f792b`. Its package totals are 10 entries (9 high, 1 moderate),
which include transitive affected parents and are not unique-advisory counts.
Python reported zero advisories across the recorded 12/14/54-package scopes.
Audit still exits 1. Neither October 21 exception group was renewed.

## Changes and actual consumers

| Fixed findings | Small compatible change | Evidence |
|---|---|---|
| TOML: GHSA-82x6-q7mm-w9cf, GHSA-v5mp-jgw5-2x6j, GHSA-4qx8-w7c3-pj3p, GHSA-9j65-hcg3-gc64, GHSA-9qmh-m7c6-f92p | Only `@amazon-devices/kepler-module-manifest-builder@0.1.16` receives TOML 5.0.1 in place of 3.0.0. This is a tested consumer migration, not an unexamined major override. | Actual SDK manifest output is byte-identical before and after; declared privileges are retained. Bounded child tests refuse both scalar-path prototype mutations and check nesting/integer limits plus large table/dotted-path processing. |
| yargs-parser: GHSA-p9pc-299p-vxgp | Legacy parser requests resolve to fixed 13.1.2; both yargs 9.0.1 consumers stay unchanged. | Actual inspector CLI port defaults/options and Metro build aliases, arrays, booleans, required output and delimiter behavior pass. Prototype-pollution regression fails before and passes after. |
| braces: GHSA-grv7-fg5c-xmjg; micromatch: GHSA-952p-6rrq-rcjv | Existing fixed micromatch 4.0.8 / braces 3.0.3 now also serve the two old nested consumers. All other retained package entries are unchanged by this step; unreachable old glob dependencies are pruned. | The actual sane inclusion filter, old anymatch contracts and a real local watcher pass. A malformed-glob child that timed out before now finishes inside the unchanged 1.5-second/64 MiB bounds. No native watcher acceptance is inferred. |

The regression files are [legacy_parser_dependencies.test.mjs](../../app/tools/legacy_parser_dependencies.test.mjs)
and [legacy_glob_dependencies.test.mjs](../../app/tools/legacy_glob_dependencies.test.mjs).
They run in the existing CI Node gate. The lock was generated and installed with
Node 22.23.2/npm 10.9.8 using the repository's existing `.npmrc`. An initial
range-only glob override left old nested copies in the lock; the checks caught
that. The final exact pin removes those copies. No finding is suppressed.

The three SBOMs were regenerated/reproduced with cyclonedx-py 7.4.0,
cyclonedx-python-lib 11.12.0, cyclonedx-npm 6.0.1 and cyclonedx-library 10.3.0.
Inherited peer-graph warnings remain in the log. A matching SBOM records the
installed graph; it does not clear those warnings or certify the new native SDK
package. Full details and before/after failures are in the
[validation receipt](../../results/cloud-followup-2026-10-25/validation.json).

## Exact remaining findings and next boundary

The [machine risk ledger](../../results/cloud-followup-2026-10-25/residual-risk.json)
binds each primary advisory, range, locked path and version to this source.

| Component | Advisory | Why another blind override is not justified |
|---|---|---|
| node-notifier 5.4.5 | [GHSA-5fw9-fq32-wv5p](https://github.com/advisories/GHSA-5fw9-fq32-wv5p) | Its fixed major changes native notification executables and platform behavior used by old Jest. Need an isolated supported consumer/platform compatibility check; no notification service was started here. |
| nested react-devtools-core 3.6.3 | [GHSA-rxrc-rgv4-jpvx](https://github.com/advisories/GHSA-rxrc-rgv4-jpvx) | The old RN debug backend needs a coordinated supported consumer migration, not replacement of the unrelated device runtime. |
| nested React Native 0.60.6 | [GHSA-7f53-fmmv-mfjv](https://github.com/advisories/GHSA-7f53-fmmv-mfjv) | Comes through the SDK's old code-generation graph. Removing/replacing its graph requires evidence from the supported SDK generation/build flow. |
| ws 1.1.5 / 3.3.3 | [GHSA-3h5v-q93c-6h6q](https://github.com/advisories/GHSA-3h5v-q93c-6h6q), [GHSA-96hv-2xvq-fx4p](https://github.com/advisories/GHSA-96hv-2xvq-fx4p) | The old inspector reads `socket.upgradeReq.url`; fixed major 5 changes that API. Its device/inspector handshake must be adapted and verified before changing the leaf dependency. |

In the received **fbe53bf** Debug/Release inventories, these vulnerable copies
were not shipped in the package. Top-level devtools 6.1.5 is a different copy
present only in Debug. The received packages' vulnerable decoder was fixed in
the previous cloud pass. Those source-map-bound observations do not establish
the inventory of an unbuilt new package or the device's system bundles.

Build-host exposure remains. Use reviewed repository inputs and bounded local
builds; keep development endpoints local and avoid exposing debug services.
Those are mitigations, not accepted risk or a green audit. Both expired groups
remain release blockers. The old five-advisory TOML deferral is historical now
that its findings are removed; it supplies no approval for the other packages.
No exception, owner signature, review date or scanner gate was changed.
