# Residual dependency decision

The latest isolated follow-up fixes the legacy logger in `2f187d1`, retaining
the earlier compatible remediations documented below. Its [receipt](../../results/design-polish-2026-10-23/dependency-wave4/receipt.json)
records the exact source and limits. The Mac acceptance snapshot stays unchanged.

The first reviewed patch updated only launch-editor to 2.14.2
and top-level shell-quote to 1.11.0. Its clean install, normal typecheck, lint,
focused UI checks and pinned SBOM reproduction are recorded in the
[product receipt](../../results/cloud-integration-2026-10-23/product-validation/receipt.json).
The [complete residual ledger](../../results/cloud-integration-2026-10-23/product-validation/residual-risk.json)
maps every remaining GHSA ID to exact locked nodes, affected ranges, propagated
packages, historical exception groups, exposure evidence, mitigations and limits.
It is the pre-approval audit review. The later [owner approval receipt](../../results/cloud-integration-2026-10-23/product-validation/toml-approval.json) applies only to the TOML scope below.

At the earlier `3a7ddf0` checkpoint, matching npm 10.9.8 lockfile scans remove four IDs, reducing the unique count
from 34 to 30, with no additions. The remaining 57 package entries include
propagated findings; they are not 57 independent exploits. The oldest nested
shell-quote 1.6.1 remains under react-native-tscodegen-types because its old CLI
pins that exact version. It retains critical
[GHSA-w7jw-789q-3m8p](https://github.com/advisories/GHSA-w7jw-789q-3m8p)
and high [GHSA-395f-4hp3-45gv](https://github.com/advisories/GHSA-395f-4hp3-45gv).
The follow-up below now addresses that remaining leaf; these counts describe
the earlier checkpoint rather than the latest review lock.

## Legacy shell-quote remediation in the current review

The local review pins shell-quote to **1.11.0**, the fixed version already used
by the newer toolchain. npm resolves the old 1.6.1 copy inside the legacy
react-native-tscodegen-types subtree to that version. The SDK, legacy CLI 2.10.0,
React Native versions and TOML stay pinned as before. Removed array-map,
array-filter and array-reduce entries were dependencies of the old parser.

The installed old CLI's launchEditor.js consumes `parse(REACT_EDITOR)` and uses
direct `spawn` on the checked Unix path. Its actual module was exercised with
intercepted process creation, quoted executable paths and argument values.
No editor was launched and no shell payload was executed. The regression also
rejects newline-bearing structured quote tokens and preserves literal arguments.
It fails against the old installed parser and passes with the final locked tree.
These are build-tool compatibility checks, not a current native module inventory.

A fresh matching npm scan removes exactly
[GHSA-w7jw-789q-3m8p](https://github.com/advisories/GHSA-w7jw-789q-3m8p) and
[GHSA-395f-4hp3-45gv](https://github.com/advisories/GHSA-395f-4hp3-45gv), with no
new advisory IDs. The later comment/line-terminator advisory
[GHSA-pqg4-j6r4-53mv](https://github.com/advisories/GHSA-pqg4-j6r4-53mv) is also
outside the selected fixed version's affected range. See the
[before/after audit delta](../../results/design-polish-2026-10-23/cloud-finish/audit-delta.json),
[primary advisory records](../../results/design-polish-2026-10-23/cloud-finish/shell-quote-advisories.json)
and [exact validation receipt](../../results/design-polish-2026-10-23/cloud-finish/receipt.json).

The app SBOM was regenerated and reproduced with Node 22.23.2, npm 10.9.8,
CycloneDX npm 6.0.1/library 10.3.0 and the documented Python generators. A real
clean locked installation was used for normal typecheck, lint and app checks.
The existing image-size override and its malformed-input protections remain.
No SDK major upgrade, exception-date extension or owner acceptance was added.
The other Audit findings and both expired groups still block release acceptance.

## Lodash and Minimatch continuation

Local code commit `5bf123409d8d863e2dbefd73bc3b2046e264d89e` removes two
more vulnerable leaves while retaining SDK and API Extractor versions. All
Lodash consumers now resolve to the app's existing **4.18.1** dependency.
The old SDK 4.17.21 and API Extractor 4.17.23 copies are deduplicated. A
major-scoped override moves Minimatch **3.0.8 to 3.1.5**, a backport already
used in this lockfile. The TypeScript consumer stays on **10.2.6**. No other
locked package version changes.

The user benefit is a smaller build-tool attack surface without changing the
native interface or adopting an untested SDK upgrade. These packages consume
repository configuration, template options and glob patterns. This is not a
claim that a household can reach each vulnerability or that a new native
package has been audited.

| Removed advisory | Issue and selected fix |
|---|---|
| [GHSA-r5fr-rjxr-66jc](https://github.com/advisories/GHSA-r5fr-rjxr-66jc) | Lodash template import names can become code; 4.18.1 rejects invalid names. |
| [GHSA-f23m-r3pf-42rh](https://github.com/advisories/GHSA-f23m-r3pf-42rh) | Coerced path segments bypass Lodash prototype-deletion guards; fixed in 4.18.1. |
| [GHSA-xxjr-mmjv-4gpg](https://github.com/advisories/GHSA-xxjr-mmjv-4gpg) | Lodash unset/omit can delete prototype properties; fixed in 4.18.1. |
| [GHSA-3ppc-4f35-3m26](https://github.com/advisories/GHSA-3ppc-4f35-3m26) | Minimatch wildcard patterns can cause excessive backtracking; 3.1.5 includes the fixed 3.x backport. |
| [GHSA-7r86-cg39-jmmj](https://github.com/advisories/GHSA-7r86-cg39-jmmj) | Non-adjacent globstars can cause excessive recursive matching; fixed in the selected backport. |
| [GHSA-23c5-xmqv-rm74](https://github.com/advisories/GHSA-23c5-xmqv-rm74) | Nested extglobs can cause excessive backtracking; fixed in the selected backport. |

Fresh matching lockfile scans remove exactly those six IDs and add none:
**28 to 22 unique advisory IDs**. npm's propagated package entries move from
56 to 54 (critical 4, high 20, moderate 28, low 2). The moderate entry count
increases because npm recomputes propagated severity. The set of advisory IDs
only decreases. See the
[audit delta](../../results/design-polish-2026-10-23/dependency-wave2/audit-delta.json),
[primary advisory records](../../results/design-polish-2026-10-23/dependency-wave2/advisories.json)
and [validation receipt](../../results/design-polish-2026-10-23/dependency-wave2/receipt.json).

Regression checks exercise the installed SDK config loader and API Extractor's
inherited configuration and package matching. Harmless template compilation
and isolated prototype sentinels reproduce the old Lodash defects and pass
after replacement. No injected expression is invoked or built-in prototype
modified. The Minimatch check verifies the patched versions and ordinary
consumer behavior; no denial-of-service benchmark was run.

A fresh locked installation, normal app typecheck/lint/tests and existing
prepared-media guards pass. The new regression joins the existing CI command.
SBOMs reproduce with the documented pins. Existing npm tree/peer warnings in
SBOM generation remain identical to the previous receipt; reproduction does
not waive them. Fable's app code and tests, player, media, signatures and
exceptions are unchanged. There is no hosted or native result for this source.
The remaining findings and expired groups still block Audit acceptance.

## Isolated Ajv and Zod follow-up

Code commit `121270e802df1f150f09a4216319f1af1f1fd67b` on
`codex/dependency-followup-2026-10-23` is a reviewed local follow-up, not a change
to the Mac acceptance snapshot `6a87937`. Its app components, player, media,
signing and exceptions are unchanged. The installed build-tool contracts are
exercised directly in `app/tools/build_dependency_compat.test.mjs`, already run
by the existing CI command.

| Package | Compatible selection and limit |
|---|---|
| Ajv | Only major 8 moves from 8.12.0/8.13.0 to 8.18.0. Rushstack and TSDoc stay at their existing versions; ESLint's Ajv 6 stays unchanged. The consumers' narrow minor ranges require an explicit override. Draft/schema/format and valid/invalid config checks pass. |
| Zod | The hooks lint plugin's 4.6.5 moves to 4.6.6, within its accepted range. The plugin version and ordinary hook diagnostics stay unchanged. |

The lock also gains Ajv's `fast-uri` dependency. `uri-js` and `punycode` retain
their versions and become dev-only nodes. The regenerated app SBOM reproduces
with the documented generator pins and Node/npm versions. Its published count
was updated through `eval/readme_sync.py`, not by hand.

Matching fresh scans remove
[GHSA-2g4f-4pwh-qvx6](https://github.com/advisories/GHSA-2g4f-4pwh-qvx6) and
[GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), with
no added IDs:
<!--n results/design-polish-2026-10-23/dependency-wave3/receipt.json:audit_delta.unique_advisories_before -->23<!--/n-->
to
<!--n results/design-polish-2026-10-23/dependency-wave3/receipt.json:audit_delta.unique_advisories_after -->21<!--/n-->
unique IDs. The fresh baseline includes a Zod finding absent from the previous
recorded scan. Do not compare the older count directly to this result and infer
that the patch introduced an advisory. Propagated package counts are recorded
separately in the [audit delta](../../results/design-polish-2026-10-23/dependency-wave3/audit-delta.json).

The [primary advisory and upstream records](../../results/design-polish-2026-10-23/dependency-wave3/advisories.json)
and [check receipt](../../results/design-polish-2026-10-23/dependency-wave3/receipt.json)
keep the exposure limits explicit. Ajv now respects a selected regex engine for
data-supplied patterns and returns a validation error for invalid syntax.
Its default JavaScript regex engine is not a universal defense against hostile
patterns. The observed build-tool constructors do not enable `$data`.
Zod rejects oversized collections before parsing elements when applicable
leading size checks exist. Unbounded schemas still visit every element; the
test suite records that limit. No denial-of-service benchmark was run.

Regressions reproduced the old behavior using harmless patterns and small
collections, then passed after replacement. A clean locked install, normal
typecheck/lint/full app tests, actual build-tool checks, prepared-media guards
and SBOM reproduction pass. Source and runtime behavior are separate from
current native bundle inventory and human acceptance, which remain pending.

The affected WebSocket leaves are major 1 and 3; the oldest fixed upstream
version is major 5. They were excluded from this compatible batch. Other
findings and expired exceptions still block Audit. No new exception, renewed
date, owner acceptance, hosted result or release approval is implied.

## Isolated legacy logger follow-up

Code `2f187d1723f65c7a09fe566a1e13aea91bdbcbb4` scopes the existing legacy
Android CLI **2.9.0** to **logkitty 0.7.1**, the patched logger already used by
the modern CLI. The old copy was 0.6.1. Because this pre-1.0 minor version is
outside the old consumer's `^0.6.0` range, its installed command was exercised
directly before accepting the override. No SDK or CLI version changes.
The [lock delta](../../results/design-polish-2026-10-23/dependency-wave4/lock-delta.json)
records removal of the old logger and its unused dependency subtree, with no
added nodes or changes to other locked packages.

The [primary advisory](../../results/design-polish-2026-10-23/dependency-wave4/advisory.json)
is critical [GHSA-v8v8-6859-qxm4](https://github.com/advisories/GHSA-v8v8-6859-qxm4),
CVE-2020-8149. The [upstream fix](../../results/design-polish-2026-10-23/dependency-wave4/upstream-fix.json)
replaces shell-interpolated cleanup and PID lookup with direct executable and
argument calls. The user benefit is reducing build-host command-injection
exposure while retaining the existing toolchain. It does not change the native
interface, household data or playback protection.

The regression reproduces interpolation in the old installed module, then
verifies literal executable/argument handling and specific error codes in the
patched module. The actual legacy command retains React Native tag filtering,
priority filtering and formatted entry/error events. Process creation is
intercepted throughout: no ADB command or device is run. These checks establish
the tested host-call behavior, not arbitrary remote ADB argument safety or a
current native module inventory.

Fresh matching scans remove only that advisory, with none added:
<!--n results/design-polish-2026-10-23/dependency-wave4/receipt.json:audit_delta.unique_advisories_before -->21<!--/n-->
to
<!--n results/design-polish-2026-10-23/dependency-wave4/receipt.json:audit_delta.unique_advisories_after -->20<!--/n-->
unique IDs. The app-lock scan has no critical entries after this change.
Propagated totals and severity reclassification are recorded separately in the
[audit delta](../../results/design-polish-2026-10-23/dependency-wave4/audit-delta.json);
their counts are not independent exploits. Other findings and expired exceptions
still block Audit. This is not a whole-product vulnerability certification.

The [receipt](../../results/design-polish-2026-10-23/dependency-wave4/receipt.json)
records a clean locked install, normal typecheck/lint, installed build-tool
regressions, prepared-library validation and reproduced SBOMs using the pinned
generators. Existing peer/tree warnings are retained. The full app Jest suite
was not rerun for this logger-only batch; its earlier result remains tied to
its earlier source. The new logger regression joins the existing CI command,
but no hosted result is claimed. Mac acceptance remains on `6a87937`; this
isolated follow-up has not been added to that snapshot or published.

## Owner-approved narrow TOML deferral

The owner explicitly replied "approve" to the temporary, controlled-build
investigation deferral for **toml 3.0.0 only**, with review due **October 30,
2026**, covering exactly these five high severity findings:

| Advisory | Exposure described by the primary source |
|---|---|
| [GHSA-82x6-q7mm-w9cf](https://github.com/advisories/GHSA-82x6-q7mm-w9cf) | Uncontrolled recursion while parsing TOML. |
| [GHSA-v5mp-jgw5-2x6j](https://github.com/advisories/GHSA-v5mp-jgw5-2x6j) | Prototype pollution through a crafted key path. |
| [GHSA-4qx8-w7c3-pj3p](https://github.com/advisories/GHSA-4qx8-w7c3-pj3p) | Quadratic work from many array-of-tables headers. |
| [GHSA-9j65-hcg3-gc64](https://github.com/advisories/GHSA-9j65-hcg3-gc64) | Quadratic work from long dotted keys or table paths. |
| [GHSA-9qmh-m7c6-f92p](https://github.com/advisories/GHSA-9qmh-m7c6-f92p) | Excessive CPU from long integer literals. |

The observed consumer is Amazon's manifest builder 0.1.16, parsing the local
app manifest on the build host. Its dependency range is `^3.0.0`; the registry
patched version 5.0.1 is outside that range. Equal output for this one manifest
does not establish full SDK compatibility. The new database ranges classify
3.0.0 as affected, while their descriptions chiefly discuss 5.0.0. This review
did not reproduce exploits or prove the current native bundle excludes TOML.

Required controls for the proposed deferral: use only reviewed trusted manifest
inputs and record their hashes; isolate and bound the build process; do not
accept third-party manifests or expose a parser service; investigate a supported
vendor fix or a separately tested override before the review date. Confirm
these controls on the Mac before invoking its build. The proposal authorizes
neither untrusted input nor a public release.

**Status: explicitly approved and recorded as its own TOML-only exception.**
The two old groups retain their October 21 review dates and historical
acceptance text. TOML was removed from the old tooling group; only its five
current scanner IDs were generated into the new group. No native shipment
classification is asserted pending a current inventory. This does not renew
either old group, cover unrelated findings, make Audit green, approve medical
safety, or substitute for native and human acceptance. The owner's "approve"
did not establish Mac operator availability or confirm those host controls.

## Work that remains independent of that decision

- Continue reviewing the other advisory preconditions; shell-quote's reviewed
  leaf is now fixed. Historical absence from the October 11 bundle is not
  current absence evidence for any remaining package.
- Obtain current Release/Debug module inventories from the exact Mac build and
  preserve package hashes. No native build is available in this cloud executor.
- Run the unchanged Audit workflow against the pushed canonical SHA. Keep its
  failures visible. Do not use exception renewal to turn missing evidence green.
- Preserve the submitted fallback and keep this development branch unsubmitted
  until the applicable product gates are resolved. Neither fallback preservation
  nor a technical test is a claim of vulnerability-free or medically safe use.
