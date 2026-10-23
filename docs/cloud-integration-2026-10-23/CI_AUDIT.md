# Hosted checks and dependency review

Reviewed October 23, 2026. Baseline source: `6360417814d684d41c94789a9e406fc27de53c66` on draft PR #2, with application code at `12125b2970342b5376b0bc7964383e547b407376`. The canonical continuation adds contrast proposal `ae30cc7` and the two compatible lockfile updates recorded below. Baseline findings retain their original scope. No risk is accepted for the owner.

## Hosted state

The exact observed times, job steps and conclusions are in the linked JSON records. These are hosted results associated with the stated PR head, not native-device results or acceptance of a later local patch.

At 18:10:37 UTC, [the PR head check](../../results/cloud-integration-2026-10-23/hosted/pr-head.json) still returned `6360417`. The isolated local checkout had advanced to `ae30cc7fc70a3b68e07684912cd8a497fb04df70`, recorded in [checkout.sha](../../results/cloud-integration-2026-10-23/hosted/checkout.sha). The hosted results below belong to the PR head.

| Run | Result at this checkpoint | Evidence |
|---|---|---|
| Current CI `39997723491`, head `6360417` | Passed. All six jobs passed, including Python and the mutation gate. Python completed at 18:22:06 UTC. This does not certify the later local branch. | [Run](https://github.com/alejandro-publius/calm-frames/actions/runs/39997723491), [job record](../../results/cloud-integration-2026-10-23/hosted/current-ci.json) |
| Current Audit `39997723468`, head `6360417` | Failed. The dependency-audit step failed; SBOM, infrastructure and ARM64 image jobs passed. | [Run](https://github.com/alejandro-publius/calm-frames/actions/runs/39997723468), [job record](../../results/cloud-integration-2026-10-23/hosted/current-audit.json) |
| Previous CI `39994434980`, head `d95e9df` | Cancelled. It is not final CI acceptance. | [Record](../../results/cloud-integration-2026-10-23/hosted/previous-ci.json) |
| Previous Audit `39994434930`, head `d95e9df` | Failed, rather than cancelled. | [Record](../../results/cloud-integration-2026-10-23/hosted/previous-audit.json) |

The long ffmpeg installation completed. No job was cancelled, restarted or duplicated by this review. Complete hosted logs were unavailable: their redirected storage host is outside the environment allowlist. Job and annotation metadata do not provide every failing command's diagnostic text.

## What the dependency evidence establishes

The uploaded Mac risk report is readable. Its separate 19 supporting trial files were not supplied. The report's `d95e9df` package manifest, lockfile and native manifest are byte-identical to `6360417`; [review-scope.json](../../results/cloud-integration-2026-10-23/hosted/review-scope.json) records those hashes and the received report's identity.

This is not only a review-date failure:

- Both exception groups in [audit_exceptions.toml](../../scripts/audit_exceptions.toml) have `review_by = "2026-10-21"`. [dep_audit.py](../../scripts/dep_audit.py) rejects expired reviews. Their historical `accepted_by` text explicitly awaits the owner's confirmation; this task supplies none.
- The baseline lock contains `launch-editor` 2.14.1, pulled by `@react-native-community/cli-tools` 20.2.0 through `^2.9.1`. GitHub's advisory database and a fresh npm lockfile scan identify three new advisories affecting it. The canonical continuation updates it to 2.14.2.
- The lock contains `toml` 3.0.0, pulled by `@amazon-devices/kepler-module-manifest-builder` 0.1.16 through `^3.0.0`. Three new CPU/resource-consumption advisories are additional to the previously recorded recursion and prototype-pollution advisories.

| Package | Current primary-source findings | Exposure that must be assessed |
|---|---|---|
| `launch-editor` | [CLI flag interpretation](https://github.com/advisories/GHSA-r825-w8mm-5pxw), [Windows existence-check bypass](https://github.com/advisories/GHSA-587h-7wmj-h5pm), [Windows argument escaping](https://github.com/advisories/GHSA-698v-4r3x-3vcv). Patched-version metadata names 2.14.2. | Development tooling can invoke a host editor. The installed matching CLI-tools version passes the supplied file argument to `launch-editor`; its open-stack-frame middleware accepts that field from a POST body. The two Windows findings do not describe the known Mac/Ubuntu hosts, but the editor-flag finding is not Windows-only. Actual editor choice, dev-server reachability and untracked host files were not established here. |
| `toml` | [Array-of-tables complexity](https://github.com/advisories/GHSA-4qx8-w7c3-pj3p), [dotted-path complexity](https://github.com/advisories/GHSA-9j65-hcg3-gc64), [integer conversion cost](https://github.com/advisories/GHSA-9qmh-m7c6-f92p). Patched-version metadata names 5.0.1. | The matching Amazon manifest builder reads and parses the application manifest on the build host. Trusted repository input narrows the ordinary path; it does not establish zero risk for a builder processing changed or third-party input. Registry affected ranges classify 3.0.0 as affected, but no exploit was reproduced here; the new advisory descriptions chiefly discuss 5.0.0 internals. |

The [October 11 bundle inventory](../../results/bundle_packages_2026-10-11.json), built from `54dab0b`, contains neither package in its Release or Debug package lists. That is historical evidence, not a fresh inventory of the current native package. The current lock marks both as development dependencies. Neither fact makes build-host exposure irrelevant or supplies an unconditional product GO decision.

The fresh [npm scan](../../results/cloud-integration-2026-10-23/hosted/current-npm-audit-summary.json) uses Node 22.23.4 and npm 10.9.9 with `--package-lock-only`. It reports 34 unique advisory IDs, matching the Mac report's aggregate advisory count, but 106 affected or propagated package entries rather than the report's 58. The Mac trials used npm 11.12.1; hosted `dep_audit.py` uses an installed-tree `npm audit`. Do not present these differing scopes/toolchains as an exact reproduction of every reported count. The current scan preserves the lockfile hash and reports findings, not a passing audit. It did not run pip-audit.

## Bounded compatibility evidence

The registry currently lists Amazon CLI platform 0.22.14 and manifest builder 0.1.16 as latest. The builder still requests `toml ^3.0.0`; [package metadata](../../results/cloud-integration-2026-10-23/hosted/package-metadata.json) records the observation.

`launch-editor` 2.14.2 fits its parent's existing range. `toml` 5.0.1 does not fit the builder's `^3.0.0` range and would require an explicit override or supported vendor change. Being the advisory's patched version does not establish compatibility with the Vega build.

A [scratch-only comparison](../../results/cloud-integration-2026-10-23/hosted/toml-scratch-compatibility.json) downloaded the two TOML parser packages from the npm registry, verified registry integrity and SHA-1, and used Node 22.23.4. Both expose CommonJS `parse()`. They parsed the exact current manifest into identical JSON and the same three privilege names. No install scripts ran and no repository package inputs changed.

That test does not cover all TOML semantics, future manifest edits, SDK support, native builds or device behavior. The uploaded report's broader scratch-lockfile trials remain reported evidence until their files are supplied. Its proposed commands, review dates and blanket GO wording are not authority to change or approve anything.

## Compatible remediation applied in the canonical branch

Only two lockfile package entries change: `launch-editor` 2.14.1 to 2.14.2 and
top-level `shell-quote` 1.10.0 to 1.11.0. Both fit existing parent ranges.
The package manifest, TOML 3.0.0 and nested shell-quote 1.6.1 are unchanged.
The dependency patch itself does not change exceptions; the later explicit
TOML-only approval is recorded separately below. npm generated the lock in a scratch directory. The lowest
fixed shell-quote version avoids the additional operator parsing in 1.12.0.

[The product receipt](../../results/cloud-integration-2026-10-23/product-validation/receipt.json)
records the exact lock, source and SBOM hashes. A new real dependency directory
was installed with `npm ci --ignore-scripts --no-audit --no-fund`, matching the
hosted install's lifecycle policy. Normal `npm run typecheck`, normal lint and
the focused contrast/focus/layout suites pass without symlink reuse or adjusted
TypeScript flags. Lint retains its recorded warnings. Native Shaka/Vega builds
were not run. Pure parse/quote checks also preserve ordinary editor/task
arguments and all current package-script strings, while the fixed parser
rejects the demonstrated comment-token line terminators without executing them.

The SBOM was regenerated using Node 22.23.2/npm 10.9.8 and the repository-pinned
CycloneDX tools. All three bills reproduce; only the app bill changes. Matching
npm 10.9.8 lock-only scans remove four advisory IDs, with no additions:
`GHSA-587h-7wmj-h5pm`, `GHSA-698v-4r3x-3vcv`, `GHSA-r825-w8mm-5pxw` and
`GHSA-pqg4-j6r4-53mv`. Unique IDs fall from 34 to 30; 57 affected or propagated
package entries remain. These counts are scan scope, not proof of exploitation
or native safety. [Raw scans and receipt](../../results/cloud-integration-2026-10-23/product-validation/).

## Residual decision and acceptance boundary

The [residual-risk decision](DEPENDENCY_DECISION.md) names every remaining
advisory, its locked nodes, exposure evidence and limits. The owner explicitly
approved the narrow TOML investigation deferral through October 30, now recorded
as its own exception with required build controls. No blanket renewal occurred. The two historical groups remain
expired, and other findings remain unresolved. CI success cannot turn Audit
failure into acceptance.

Run CI and Audit once against the reviewed canonical branch's exact pushed
HEAD. Store the returned run SHAs separately from this upstream receipt; do not
push status-only commits to restart jobs. Before product acceptance, the
remaining dependency decision, native build/bundle inventory and applicable
[Mac and human checks](MAC_ACCEPTANCE.md) must be resolved. Preserve the submitted
fallback and frozen materials. No merge, public upload, media preparation,
unapproved exception-date change or native action occurred in this continuation.
