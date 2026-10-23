# Residual dependency decision

The smallest compatible reviewed patch updates only launch-editor to 2.14.2
and top-level shell-quote to 1.11.0. The clean install, normal typecheck, lint,
focused UI checks and pinned SBOM reproduction are recorded in the
[product receipt](../../results/cloud-integration-2026-10-23/product-validation/receipt.json).
The [complete residual ledger](../../results/cloud-integration-2026-10-23/product-validation/residual-risk.json)
maps every remaining GHSA ID to exact locked nodes, affected ranges, propagated
packages, historical exception groups, exposure evidence, mitigations and limits.
It is the pre-approval audit review. The later [owner approval receipt](../../results/cloud-integration-2026-10-23/product-validation/toml-approval.json) applies only to the TOML scope below.

Matching npm 10.9.8 lockfile scans remove four IDs, reducing the unique count
from 34 to 30, with no additions. The remaining 57 package entries include
propagated findings; they are not 57 independent exploits. The oldest nested
shell-quote 1.6.1 remains under react-native-tscodegen-types because its old CLI
pins that exact version. It retains critical
[GHSA-w7jw-789q-3m8p](https://github.com/advisories/GHSA-w7jw-789q-3m8p)
and high [GHSA-395f-4hp3-45gv](https://github.com/advisories/GHSA-395f-4hp3-45gv).
Changing that pin requires separate compatibility and reachability review.

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

- Review the nested shell-quote call sites and remaining advisory preconditions;
  historical absence from the October 11 bundle is not current absence evidence.
- Obtain current Release/Debug module inventories from the exact Mac build and
  preserve package hashes. No native build is available in this cloud executor.
- Run the unchanged Audit workflow against the pushed canonical SHA. Keep its
  failures visible. Do not use exception renewal to turn missing evidence green.
- Preserve the submitted fallback and keep this development branch unsubmitted
  until the applicable product gates are resolved. Neither fallback preservation
  nor a technical test is a claim of vulnerability-free or medically safe use.
