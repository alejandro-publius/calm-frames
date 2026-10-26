# Item 12: bounded fetch and locale follow-up

This local follow-up starts at `fea683258b7425e829beba521574e15355a598d6` and
checks code `7f3e135f0fec98ef2de72b1d6aaef504de964602`. It preserves the SDK,
React Native/DevTools graph, app source, media, manifest and exception file.
The [receipt](../../results/overnight-2026-10-25/dependencies-followup/receipt.json)
records exact code commits, commands, hashes and scope. No push, publication,
native acceptance or full-product audit pass is claimed.

## Implemented fixes

**Legacy fetch:** only isomorphic-fetch 2.2.1 now resolves the existing CommonJS
node-fetch 2.7.0 instead of 1.7.3. Both isomorphic-fetch and FBJS 1.0.0 stay at
their original versions. This is an explicit scoped override outside the old
`^1.0.1` requirement, with installed-consumer compatibility checks.

The actual FBJS/isomorphic fallback forwarded fictional authorization data to a
different host in the [before check](../../results/overnight-2026-10-25/dependencies-followup/fetch-before.log).
The fixed path strips authorization, cookie, cookie2 and www-authenticate on that
redirect, retaining ordinary headers. Same-host redirects, POST-to-GET behavior,
Request/Response cloning and body consumption, and the actual FBJS retry
wrapper's success/failure responses pass. FBJS still prefers an existing native
fetch implementation. The final fixture uses one owned loopback listener and a
test-owned Agent for two reserved hostnames: no DNS, external request, Mac
loopback alias or host interface change is needed. Mac execution is not claimed.

The majors are not identical in every API detail. Old `Headers.get` returns the
first duplicate value; 2.x joins them. `Headers.raw` also preserves the original
key casing in 2.x. The [direct comparison](../../results/overnight-2026-10-25/dependencies-followup/header-api-differences.json)
records both differences. The observed wrappers do not inspect duplicate values
or raw key casing; their transmitted headers and used response paths pass.
No universal Fetch API compatibility or HTTPS-downgrade runtime check is claimed.

npm initially retained the stale nested 1.7.3 lock entry despite the scoped
override. Removing only that stale entry and regenerating with npm 10.9.8
deduplicated onto the existing 2.7.0. A fresh locked install verifies the actual
resolution. The unused old node-fetch, encoding, nested iconv-lite and is-stream
nodes leave the lock; no new fetch version is introduced elsewhere.

**Locale cache:** only os-locale 2.1.0 now resolves CommonJS mem 4.3.0 instead of
1.1.0. The first fixed major is 4; the selected 4.x patch retains the tested API.
The old supplied cache retained expired entries without a reread, reproduced
with a small fixture in the [before check](../../results/overnight-2026-10-25/dependencies-followup/locale-before.log).
The fixed implementation removes them. Actual os-locale environment priority,
locale normalization, command parsing, sync/async memoization, explicit clearing
and failed/disabled-command fallback pass. Process results are controlled; no
host locale command is launched.

The observed locale consumer supplies no maxAge or custom cache options. This
removes a dormant vulnerable API from its dependency, not a demonstrated
household memory attack. mem's changed rejected-promise policy does not change
this consumer's fulfilled fallback result. The
[lock delta](../../results/overnight-2026-10-25/dependencies-followup/lock-delta.json)
includes its small cache-cleanup helpers and generated metadata changes.

## Verification and remaining risk

A fresh locked install with scripts skipped, normal app typecheck and the
combined actual-consumer regressions pass:
<!--n results/overnight-2026-10-25/dependencies-followup/receipt.json:tests.passed -->53<!--/n-->
passed,
<!--n results/overnight-2026-10-25/dependencies-followup/receipt.json:tests.failed -->0<!--/n-->
failed. Both new test files join the existing CI command without removing checks.
All three SBOMs reproduce using Node 22.23.2/npm 10.9.8 and the existing pinned
CycloneDX generators. Existing peer/tree warnings remain recorded.

The fresh [audit delta](../../results/overnight-2026-10-25/dependencies-followup/audit-delta.json)
removes exactly [GHSA-r683-j2x4-v87g](https://github.com/advisories/GHSA-r683-j2x4-v87g)
and [GHSA-4xcv-9jjx-gfj3](https://github.com/advisories/GHSA-4xcv-9jjx-gfj3), with
no additions. Unique IDs move from
<!--n results/overnight-2026-10-25/dependencies-followup/audit-delta.json:unique_advisories_before -->17<!--/n-->
to
<!--n results/overnight-2026-10-25/dependencies-followup/audit-delta.json:unique_advisories_after -->15<!--/n-->.
The before scan is the preceding same-day exact-lock result. Propagated package
totals are recorded separately and are not counts of independent exploits.
The remaining findings and both October 21 expired groups still block Audit.
The existing TOML-only controlled-build approval through October 30 is unchanged.

Concrete [migration barriers](../../results/overnight-2026-10-25/dependencies-followup/migration-barriers.json)
explain why the next two leaf overrides were not made:

- Old Metro InspectorProxy dereferences `socket.upgradeReq.url` in both device
  and debugger connection handlers. Fixed ws 5.2.7 passes the request separately
  and has no upgradeReq property. The inspector must migrate its handlers and
  verify handshakes; replacing only its leaf leaves that dereference invalid.
- The actual query-string 7.1.3 consumer calls the decoder returned by CommonJS
  require as a function. Fixed decode-uri-component 0.5.1 exports an ES-module
  namespace. Substitution makes ordinary `scene=Sequoia%20Trail` parsing throw
  `TypeError: decodeComponent is not a function`; the installed version passes.
  A consumer/adapter migration must preserve malformed-URL handling and navigation.

The [remaining ledger](../../results/overnight-2026-10-25/dependencies-followup/residual-risk.json)
keeps every advisory, exact locked node, source and existing review date.
Other legacy migrations were not proven compatible or proven broken by this
bounded follow-up. No blanket incompatibility claim is made for them.
Current native inventory evidence and native/human acceptance remain separate.

Integrate the code commits in the receipt, then this evidence/SBOM commit.
Re-run consolidated checks on the final candidate and update the generated
`docs/SECURITY.md` component marker through `eval/readme_sync.py`; this lane
leaves that presentation file untouched. This batch stops here as requested.

Status: the two scoped fixes are verified locally; overall item 12 remains partial.
