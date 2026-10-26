# Verification report privacy

The source fix generates `source_path` as `sha256:<exact source digest>` before
the report is serialized, hashed into the verification ledger, copied into a
local receipt, or referenced by an exported catalog. The field remains a string
and the report schema is unchanged. Successful signature checks retain the
result and return code without copying CLI output containing host paths.
Failed checks retain local paths and diagnostic output, and cannot be exported.

Preparation's verification fingerprint includes the new representation version.
An old cache therefore reruns verification, leaving unchanged signed maps and
renditions cached. The existing ledger, artifact hashes, map signatures, exact
source binding and publication refusal checks still apply. There is no report
redaction or signature repair during export.

Export and report attachment refuse local filesystem paths in report strings,
including nested JSON evidence. Both native prebuilds already use
`--require-reports`; that gate now also requires portable reports. Native archive
checks always apply the same requirement. Plain directory checks remain useful
for inspecting historical integrity, and are not distribution approval.

## Historical artifacts and regeneration boundary

No packaged report, signed map, media file, approval record or trust root was
changed. The unavailable Release candidate
`742b15aec9743ef5db7905e426e925fb2b7291d042e9130b960364a7ce88168d`
is not repaired by this source change and was not built or published here.

The bounded source-report check found the four personal-path reports beginning
`9daf7a6eb07e`, `be5f6ecc536b`, `d39321373a7d` and `fd6387755e95`.
Report `18802e65a692` also retains cloud workspace paths in successful signature
diagnostics. All five retain valid historical hashes but fail the distribution
privacy guard. The baked-ambient report `4043445adbb8` passes both checks.

The owner must rerun preparation with the original exact media and preparation
workspace, retaining the existing signer configuration. The new verification
cache version forces fresh evidence and receipt hashes; do not manually edit a
report or its ledger. Export the regenerated receipts into a fresh directory,
then review the resulting catalog identities through the existing exact approval
process. Do not retain old path-bearing report generations in the new package.
Unchanged signed maps can be reused after signature verification. If the normal
preparation requires a map to be regenerated, only the owner-held existing signer
may sign it. No new signer or trust root is part of this fix.

After that, run the strict report/approval gates and build a new native Release
package on the Mac. Check that new package's bytes and privacy before any
separately authorized distribution. The previous package's approval does not
transfer. This work makes no native build, device, licensing or Audit claim.

## Focused validation

Cloud results on October 26: 193 focused Python tests and 81 Node tests passed.
Ruff, staged gitleaks, style, published-number drift and whitespace checks passed.

Python and Node regression controls cover POSIX, Windows, UNC, file-URI and home
paths, Unicode directories, paths inside details and nested analyzer JSON,
matching-but-rebound hashes, media identifier mismatch, unchanged report schemas,
historical integrity, immutable export refusal, and archive rejection.
The real benign-media export test preserves signed maps and exact delivered-media
hashes. The cache migration test reruns only verification and preserves signed-map
and rendition bytes. Existing wrong-source and signature-tamper controls pass.
Removing each language's path or media-identifier guard makes its focused tests
fail; the generator regression also failed before the implementation changed.

Current source assets intentionally fail `node app/tools/check_prepared_library.mjs
--require-reports` pending regeneration. A passing historical integrity check or
source test run does not mean those assets are ready to ship. CI's Vega prepared
asset step also invokes the strict gate through `playback_proof.mjs --check` and
fails on these historical paths. Keep that failure visible until regenerated
evidence clears it; do not bypass the guard to make CI green.
