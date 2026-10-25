# Item 12: dependency remediation

The later [bounded fetch and locale follow-up](DEPENDENCY_FOLLOWUP.md) records
additional fixes and the newest residual ledger. This page retains the first
batch's exact source and evidence.

The reviewed local code is `7c35dadf924c32275a6898f6cf32e965191bd8cc`, based on
Claude's verified handoff `15ef46c6e23c8ba627492da23b1b147000031aa4`. This batch
reduces concrete host-tool defects without changing the app interface, player,
media, signing inputs or Amazon SDK versions. Item 12 remains partially complete:
the remaining audit findings and expired exception reviews still block acceptance.

The [receipt](../../results/overnight-2026-10-25/dependencies/receipt.json),
[exact lock delta](../../results/overnight-2026-10-25/dependencies/lock-delta.json)
and [primary advisory records](../../results/overnight-2026-10-25/dependencies/primary-advisories.json)
record the inputs and limits. Nothing was pushed, merged or published.

## Implemented changes

| Installed consumer | Selected dependency | Verified behavior and limit |
|---|---|---|
| React Native CLI server API 20.2.0, unchanged | body-parser 2.3.0 to 2.4.0, inside its declared `^2.2.2` range; required qs patch 6.16.1 | The actual CLI middleware no longer crashes its child process on trailing compressed bytes, and serves a subsequent request. Plain/gzip JSON, malformed JSON rejection and the second raw-body reader retain their behavior. Editor launch is intercepted. |
| FBJS scripts 1.2.0 and execa 0.7.0, unchanged | Only these consumers receive cross-spawn 6.0.6 instead of 5.1.0 | The existing fixed 6.x release handles long backslash arguments in a bounded child. Actual old consumers retain sync/async arguments, environment, failure results, streams and working directory. This is an explicit one-major override outside their old 5.x ranges; the newer 7.0.6 consumers stay unchanged. The Windows escaping function was checked on Linux, not a Windows native launch. |
| external-editor 2.2.0, unchanged | Only this consumer receives tmp 0.2.7 instead of 0.0.33 | Path-only requests reject escaping symlinks and traversal in string or non-string prefix/postfix values. Ordinary file mode/cleanup and the real editor's file round trip pass without launching an editor. This scoped pre-1.0 override is outside `^0.0.33`. It does not certify all editor filesystem race behavior. |

The generated lock also adds fixed spawn helpers already present elsewhere and
removes unused old cache helpers. npm reclassifies dev metadata on unchanged
logger/helper nodes. These are all recorded in the lock delta; there is no claim
that only the named package rows changed. Amazon locked nodes are byte-identical.

The initial tmp 0.2.6 selection fixed the old string/symlink issues, but the fresh
scan identified [GHSA-7c78-jf6q-g5cm](https://github.com/advisories/GHSA-7c78-jf6q-g5cm),
its non-string type-confusion bypass. That intermediate lock is not the final
candidate. The bypass was reproduced before selecting fixed 0.2.7. Its
[intermediate scan](../../results/overnight-2026-10-25/dependencies/audit-tmp-0.2.6-intermediate.json)
is retained so this unsuccessful intermediate selection remains visible.

## Checks and audit result

All new guards were observed failing against the installed affected versions:
[request-parser crash](../../results/overnight-2026-10-25/dependencies/body-parser-before.log),
[argument escaping timeout](../../results/overnight-2026-10-25/dependencies/spawn-before.log),
[path containment](../../results/overnight-2026-10-25/dependencies/tmp-before.log)
and [type-confusion bypass](../../results/overnight-2026-10-25/dependencies/tmp-type-before.log).
No escaped file was written; temporary fixtures are owned and removed by tests.

The final tree passed a clean `npm --prefix app ci --ignore-scripts --no-audit
--no-fund` with Node 22.23.2/npm 10.9.8, the normal `npm --prefix app run typecheck`
and the actual-consumer regression command recorded in the receipt. Install
scripts were skipped; this did not rebuild Shaka, media or a native package.
The combined dependency regression result is
<!--n results/overnight-2026-10-25/dependencies/receipt.json:compatibility_tests.passed -->42<!--/n-->
passed and
<!--n results/overnight-2026-10-25/dependencies/receipt.json:compatibility_tests.failed -->0<!--/n-->
failed. The tests exercise the behaviors above, not just package versions.
The CI command adds these tests and keeps every existing check.

Matching npm lockfile scans remove these exact findings:

- [GHSA-27r3-jxmh-p828](https://github.com/advisories/GHSA-27r3-jxmh-p828): compressed-body decoder process crash.
- [GHSA-3xgq-45jj-v275](https://github.com/advisories/GHSA-3xgq-45jj-v275): argument-escaping regular-expression denial of service.
- [GHSA-52f5-9888-hmc6](https://github.com/advisories/GHSA-52f5-9888-hmc6): temporary-path symlink escape.
- [GHSA-ph9p-34f9-6g65](https://github.com/advisories/GHSA-ph9p-34f9-6g65): temporary prefix/postfix traversal.

Unique advisory IDs move from
<!--n results/overnight-2026-10-25/dependencies/audit-delta.json:unique_advisories_before -->21<!--/n-->
to
<!--n results/overnight-2026-10-25/dependencies/audit-delta.json:unique_advisories_after -->17<!--/n-->,
with none added in the final lock. npm package totals include propagated
findings, not independent exploits; both totals are retained in the
[audit delta](../../results/overnight-2026-10-25/dependencies/audit-delta.json).
The final npm audit exits 1 for its remaining findings. This is not a clean
Audit result, a native package audit or a whole-product security certification.

All three CycloneDX bills regenerate and reproduce with the existing pins:
Python generator 7.4.0/library 11.12.0 and npm generator 6.0.1/library 10.3.0,
using npm 10.9.8. The
[reproduction report](../../results/overnight-2026-10-25/dependencies/sbom-reproduction.json)
confirms byte equality. Existing peer/tree warnings remain in the logs and
receipt. Regeneration does not waive those warnings or the residual findings.

## Remaining work and integration

The [residual ledger](../../results/overnight-2026-10-25/dependencies/residual-risk.json)
lists every remaining GHSA ID, npm scanner ID, exact locked node/version,
affected range, historical exception group/date and next action. In particular:

- The remaining old ws 1.x/3.x and yargs-parser 7.x leaves have no fixed version
  within their existing major ranges. Do not silently replace the old SDK graph.
- decode-uri-component's fixed 0.5.1 is an ES module while the observed consumers
  call a CommonJS function; a direct override is not proven compatible.
- Other legacy parser, notification, fetch and cache upgrades need separate
  actual-consumer checks. The current batch does not accept their risk.
- The two old exception groups still have their October 21 review dates.
  Only the existing five-advisory TOML controlled-build deferral is owner-approved,
  through October 30. Its reviewed/hashed-manifest and isolated-build controls
  remain required. No dates, acceptance text or exception IDs were edited.
- Current native inventory is summarized in Claude's committed notes, but its
  original evidence ZIPs are not available in this executor. Do not infer current
  shipping exposure or native acceptance from this host-tool check.

Integrate all code commits in the receipt in order, including the final tmp
follow-up, then the SBOM/evidence commit. Do not stop at intermediate `2206e12`.
Run the consolidated candidate checks on the final integration SHA. Update the
generated SBOM component marker in `docs/SECURITY.md` through `eval/readme_sync.py`
when integrating; this lane leaves the presentation owner's file untouched.
The full app suite, Python audit, native build and hosted checks belong to the
consolidated candidate, not to an inferred result from this dependency-only run.

Status: compatible leaf fixes verified locally; item 12 and release acceptance remain open.
