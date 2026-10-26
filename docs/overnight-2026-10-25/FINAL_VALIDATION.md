# Final local validation

The last product-code commit is
`b603be9cb3a8dc13407f8f6f6408aad984f6f836` on
`codex/overnight-completion-2026-10-25`, descended from the independently verified
remote handoff `15ef46c6e23c8ba627492da23b1b147000031aa4`.
Later commits contain documentation, sanitized evidence and the isolated
generated-input restore helper. The external `SYNC_MANIFEST.json` identifies the
immutable final transfer SHA and tree, with verified bundle/patch checksums.
Nothing was pushed, merged, published or submitted overnight.

## Results and their scope

The [receipt](../../results/overnight-2026-10-25/final/receipt.json),
[commands and log hashes](../../results/overnight-2026-10-25/final/checks.json)
and [source hashes](../../results/overnight-2026-10-25/final/validated-source-hashes.json)
bind these results to the code that ran. This is local validation, not hosted CI
or native acceptance.

| Check | Result and boundary |
|---|---|
| Own clean locked app installation | Passed with Node 22.23.2/npm 10.9.8 and install scripts skipped; no reused node_modules symlink. Player generation was exercised separately. |
| Normal app suite | <!--n results/overnight-2026-10-25/final/receipt.json:results.app_tests.passed -->1900<!--/n--> passed; <!--n results/overnight-2026-10-25/final/receipt.json:results.app_tests.skipped_existing -->4<!--/n--> existing tests skipped. Existing coverage floors retained and passed. Covers the integrated Reading comfort change as well as retained player, household and navigation behavior. |
| Normal app typecheck and lint | Passed without adjusted TypeScript flags, both before and after verified generated inputs were restored. Existing lint warnings remain; no lint error is accepted. |
| Combined Python suite | <!--n results/overnight-2026-10-25/final/receipt.json:results.python_tests.passed -->2122<!--/n--> passed, no skip; <!--n results/overnight-2026-10-25/final/receipt.json:results.python_tests.deselected_normal_slow_marker -->2<!--/n--> slow tests excluded by the normal CI marker. The unchanged coverage floor passed. |
| Python Ruff and mypy | Passed with the repository's normal targets, including strict flashmap typing. |
| Release/package and dependency-consumer gates | <!--n results/overnight-2026-10-25/final/receipt.json:results.node_release_and_dependency_tests.passed -->119<!--/n--> passed; reports, approved baked ambient media and playback proof passed. No budget was raised. |
| Hook consumer, pins, build context and SBOM reproduction | Passed. The hook installed into a clean offline consumer. All pinned SBOM generators reproduce their committed outputs. |
| Demo renderer | <!--n results/overnight-2026-10-25/final/receipt.json:results.demo_preflight_tests.passed -->24<!--/n--> preflight tests passed. The real encoder smoke fixture is explicitly TEST ONLY; actual replacement footage/narration is missing. |
| Caregiver file workflow | Real HTTP/analyzer, report tampering, permission refusal, encrypted-MP4 refusal, reconnect, keyboard and browser layout checks passed. See [workflow evidence](personal-import/README.md). |
| Generated player | Normal setup passed; all required inputs and their provenance were verified, then normal native-input/typecheck/lint checks passed. This is not a Vega compilation. |
| Audit policy | **Failed as intended by the unchanged policy:** residual findings include two groups whose review expired October 21. Python sources returned no findings. The TOML-only approval remains unchanged through October 30. |
| Native and ARM64 build | **Blocked.** Vega/kepler SDK is absent. The pinned ARM64 container base pulled, but executing it on this x86_64 daemon returned an executable-format error. No privileged emulation was installed. |

The full Python run began at `596418e`. The only later Python change was two
test-fixture METHOD metadata lines; the final focused offline AWS suite passed
on that revision. Production Python, hook, evaluation and script bytes are
identical across those source points. The fixture keeps the ambient AWS guard,
environment and global session intact while refusing real network/identity
fallback. Earlier failing fixture runs are retained as diagnosis, not erased.

Final documentation, source-line links, numeric markers, style, helper boundary
checks and secret scanning run after the presentation is assembled. Their
exact final-source results are also included in the external transfer manifest.

## Preserved behavior and inputs

The [preservation receipt](../../results/overnight-2026-10-25/final/preservation.json)
checks all recorded approved runtime assets byte for byte. Media, fonts,
artwork, reports, signatures, native manifest semantics, coverage floors,
dependency exceptions, the judging package and approved narration remain
unchanged. Build-only generators moved out of the shipped asset directory;
no replacement media was invented.

Every supplied never-merge head and named fixture ID is absent from complete
candidate ancestry, as is rejected browser UI commit `76223f9`. The full set of
intermediate own-commit IDs on those branches was not supplied; that proof limit
remains explicit. No harness branch was imported or executed.

The [current advisory ledger](../../results/overnight-2026-10-25/dependencies-followup/residual-risk.json)
lists each remaining finding, exact installed nodes, primary source, exposure
limit and next action. Compatible fixes removed findings without changing the
SDK graph. Direct substitutes for the remaining URI decoder and WebSocket
consumer were demonstrated incompatible; a broader migration needs its own
bounded work and native evidence. Expired exceptions were not renewed.

## Next action

Use the [Mac handoff](MAC_HANDOFF.md) to import the exact local source into a
separate worktree and preserve rollback. The [original twenty-item ledger](../cloud-integration-2026-10-23/CHECKPOINT.md)
and [morning review](MORNING_REVIEW.md) retain every open acceptance criterion.
No test count, source check or technical package result is human comfort,
medical validation, judge access or permission to replace submitted materials.
