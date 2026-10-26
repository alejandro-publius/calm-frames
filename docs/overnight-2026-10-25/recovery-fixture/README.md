# Recovery fixture: dead Linux process groups

The cloud failure was in the SIGKILL test's completion check. Linux retained a dead orphan in each killed preparation process group, reparented to PID 1. `killpg(group, 0)` continued to find those entries even though `/proc` showed only zombie state `Z`, which cannot execute or write output. Both original recovery tests reproduced this failure before any change. Their sanitized [failure log](../../../results/overnight-2026-10-25/recovery-fixture/before.log) and exact [process observations](../../../results/overnight-2026-10-25/recovery-fixture/process-states.json) are retained; the original raw log remains in the external work evidence directory.

Commit `e575879d1147b101b802666dc70d0040aef409eb` changes only the preparation-recovery test file. The helper first uses the existing process-group absence check. On Linux, it can also finish if readable process metadata positively proves every remaining member of that group is a zombie. Live, mixed, unknown, missing, malformed or unreadable evidence does not receive this exception. Other platforms keep the previous absence-only behavior.

The real SIGKILL, preparation wait bounds, failed receipt and empty catalog before resume, ledger reuse, step timestamps, verification comparison and output hashes remain asserted. No production pipeline behavior, timeout, protection budget, media approval or signing configuration changed.

The focused run passed <!--n results/overnight-2026-10-25/recovery-fixture/checks.json:tests.passed -->15<!--/n--> tests, including both actual preparation interruption/resume cases and the process-state controls. The [receipt](../../../results/overnight-2026-10-25/recovery-fixture/checks.json) binds this result to the source file and hashes each evidence artifact.

The negative controls establish that the correction is not an unconditional pass: an actual unreaped child fails with the old helper, while an actual live child fails if state inspection is deliberately bypassed. After restoration, the helper controls pass. Synthetic mixed or unreadable process snapshots are refused. Ruff, repository style, whitespace and staged secret checks pass.

These are generated test-media recovery checks on Linux. They are not native Fire TV evidence, human audiovisual acceptance, hosted CI, or release approval. The integration owner must rerun the final suite on the combined source.
