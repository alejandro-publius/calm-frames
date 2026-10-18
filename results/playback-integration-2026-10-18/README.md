# Bounded playback integration kit, October 18

Four isolated TypeScript modules and one targeted test file were added under
`app/src/calmframes/integration` and `app/test/calmframes/playbackIntegration.test.ts`.
[Integration guide](../../docs/integration/PLAYBACK_KIT.md) describes the exact
asset/edition/timeline contract and required renderer acknowledgment.

This work is separate from installed source `805f855` and package
`8e58685d579a740743e5d6e89b0fa8bbcce42e7a6189b9c92265575ea0c1e511`.
All 813 existing app inputs remain byte-identical. No production import references
the kit. No native build/install, playback or capture was performed for the kit.
Forest was already completed and pushed at `8126ec1` before this work.

Validation: 207 tests across eight suites pass, including 37 kit tests; TypeScript
and focused lint pass; ten package checks and the actual offline pack/install,
TypeScript, Metro and Babel checks pass. Logs are saved alongside this record.
The regression selection covers the kit plus authoritative signed-map, schedule,
clock, catalog, seek, system-control and mirror tests. The independent verifier
found and helped close pending resume cancellation, synchronization during an
operation, detached lifecycle callbacks, partial subscription rollback, failure
latching, preexisting loop state, overlapping dispatched transport and late play
completion. The final source review found no remaining scoped blocker.

The regression suite exposed older generated hook UI copies. The documented sync
script refreshed them and now includes their three coastal component dependencies;
the package declares the two additional Vega runtime peers. The actual offline
package test checks dependency closure, TypeScript consumers, Metro resolution and
Babel transformation. It does not publish a package or download dependencies.
The new prototype kit is not exported by that existing hook package.

Initial local test execution hit Watchman's state-directory permission limit;
`--watchman=false` avoids that service. The offline package check hit the shared
npm-cache permission limit; a task-specific temporary cache resolved it. No
permissions were changed. Initial mirror failures are documented above; final
logs are authoritative.

No ADBT MCP actions were available in the exposed tool inventory. No `adbt`
executable or builder-tools package was found in the checked executable/npm/global
locations. No installation or connection change was attempted. The read-only
`summarize_existing_log.py` derives three individual latency observations from
Forest's existing debug text log, with its SHA-256 in `existing-log-latency.json`.
Player-entry-to-readiness log intervals are approximately 1.110 s Forest,
1.155 s Sea Otters and 0.970 s Acadia; end-to-player-left log intervals are
0.650 s, 0.628 s and 0.689 s respectively. These are not actual displayed-frame
TTFF, cold-start measurements, percentile claims, CPU/memory profiles, audio
acceptance, physical timing or kit performance.

The owner needs no coding, package approval or another install to finish this
bounded kit. For the installed demo, the remaining immediate step is to look and
listen: confirm the three cards, concise help, Forest nature sound and Acadia's
replacement presentation. Submission recording, reviewer access and publication
remain separate owner actions. Physical timing belongs to future real-world
runtime-overlay validation, not the current simulator submission checklist.
