> Historical source excerpt copied from `docs/PREPARATION_RECOVERY.md` at `13551e4`. Local references now point to immutable source or bundled assets. Publication wording describes its original checkpoint, not current status.

# Preparation recovery

Preparing a title runs about eight steps per preset, plus shared ones, over
minutes of analysis and encoding, and the result is published only by verify.
This page says what can interrupt or damage that work, what the pipeline does
about each case since October 21, and how to reproduce the evidence. The code is
the ledger in `pipeline/state.py`, the file writes and locks in
`pipeline/durable.py`, the step runner and publication in `pipeline/ingest.py`,
the catalog in `pipeline/catalog.py` and the receipt in
`pipeline/local_library.py`.

## Failure model

- **The process stops anywhere.** A crash, SIGKILL, an out of memory kill or a
  stopped container can end a run between two steps, halfway through writing an
  output, or halfway through writing the ledger. A kill sent only to the Python
  process, rather than its process group, can leave an ffmpeg or analyzer child
  running and writing after its parent is gone.
- **The machine stops.** After a power loss, writes and renames that had only
  reached memory can be missing or torn.
- **A cached file changes.** An output can go missing, be cut short, have bytes
  changed at the same size with its modification time put back, be replaced by
  a link, or be a valid file made from other inputs.
- **The ledger cannot be read.** It can be truncated, not JSON, not UTF-8, the
  wrong shape, or carry one bad record among good ones.
- **An input changes.** A setting, the signing key, or an upstream output that
  comes out different when it is rebuilt.
- **Two runs overlap.** The same title prepared twice at once, or two titles
  updating one kid mode index.

## What the base commit did

At `bf2f615` a step was skipped when its fingerprint matched and its output
files existed. Four steps (probe, still, trickplay and posters) also compared
output hashes. The others, including analysis, plans, renditions and cover
models, trusted the file name, and the HLS segments were not recorded at all.
A step's fingerprint included its parents' fingerprints, never their bytes.
The ledger was replaced through a fixed `state.json.tmp` without being flushed,
and a JSON syntax error was the only damage it handled. `pipeline.ingest` took
no lock. The same scenarios, run against that commit with `--code-root`, are
in `results/preparation-recovery-2026-10-21/evidence-bf2f615.json`;
<!--n results/preparation-recovery-2026-10-21/evidence-bf2f615.json:summary.failed -->8<!--/n--> of
<!--n results/preparation-recovery-2026-10-21/evidence-bf2f615.json:summary.scenarios -->16<!--/n-->
did not meet their expectation there:

- A killed rebuild left the old rendition record in place, vouching for a
  master half the size of the real one. The restart reused it and failed.
- Same-size damage to an HLS segment went through verify again and came out
  with a ready receipt naming the damaged bytes. The fake analyzer does not
  measure pictures; with the real one verify would have measured the damaged
  segment, but the receipt would still have named bytes the pipeline never
  made. Damage to a plan or to the luminance record was never rebuilt.
- Same-size damage to a safe master or a published map, a deleted HLS segment
  and a new signing key each left the title failed, with the ledger still
  vouching for the damaged or stale files, so every later run would fail the
  same way until a manual `--force`. Whether verify notices damage to a
  rendition at all depends on where the damage lands and what it samples;
  nothing rebuilt it.
- A ledger holding valid JSON of the wrong shape crashed the command with a
  traceback, and one that was not UTF-8 failed the preparation.
- A second `pipeline.ingest` of the same title ran to completion beside the
  first, rewriting its files, and published.
- A truncated ledger was handled by preparing again, as now, but the
  unreadable file was overwritten rather than kept.

Interrupting a first preparation, killing verification, changing the guard
band and failing verification already behaved there as they do now.

Verify was always the last gate, and it caught some of this: a stale
signature fails it, and so does a plan whose intervals no longer match its map.
It could not rebuild what it caught, so those titles stayed blocked until a
manual `--force`, and it was never designed to notice bytes that change
without changing what it measures, such as a plan field it does not compare.

## How recovery works

1. **Every output is hashed when its step commits.** A ledger record holds the
   step's fingerprint and the SHA-256 of each output, as a path relative to the
   title. A step is reused only when the fingerprint matches and every output is
   a regular file, reached without a link, with exactly the recorded bytes. HLS
   playlists and segments are outputs of the rendition step.
2. **Identities flow downstream, not fingerprints.** A step's identity is its
   fingerprint together with its output hashes, and each fingerprint includes
   the identity of every step it depends on. A rebuilt step that comes out
   different therefore redoes everything built from it; one that comes out
   byte for byte the same leaves its dependents valid.
3. **Withdraw, work, commit.** Before a step does any work its record is
   removed from the ledger, durably. The record is written back only after the
   work returned and every output exists. A run killed halfway through
   rewriting an output can never leave a record vouching for it.
4. **One writer per file.** The analyzer's own map is kept in
   `work/analysis/<preset>.json`, and the signed-map step writes the published
   `maps/<preset>.json` from it, so no step's recorded output is rewritten in
   place by another step.
5. **State files are replaced atomically and flushed.** The ledger, catalog
   entries, the kid mode index, the verify report and local receipts are written
   to a new temporary file created with `O_EXCL | O_NOFOLLOW` under a name nobody
   can predict, flushed (`F_FULLFSYNC` on macOS, `fsync` elsewhere), renamed over
   the old file, and the directory is flushed after the rename. A reader sees
   the old version or the new one.
6. **A ledger that cannot be read is never trusted.** Readers treat it as empty.
   The next write moves it aside to `state.json.malformed` and the title is
   prepared again from its source. A single record with the wrong shape is
   dropped on its own. Records written before output hashes were kept are still
   read, so existing receipts can be checked, but they never skip work.
7. **Publication is last, and only for bytes that held still.** A re-run takes
   the title out of the kid mode index, then out of its entry, before any cached
   artifact is trusted. Verify is keyed by the hashes of every artifact it
   checks, scene-hold images included. If any of them changes while verify runs, the verdict is not
   recorded and nothing is published. A pass is flushed to the device, artifacts
   first, and published to the entry and then the index. A failed verification
   is recorded but never reused as a pass.
8. **A receipt names only verified bytes.** Verify's ledger record lists the
   hash of every artifact it checked, and a local receipt is refused unless each
   file it names still has that hash, so a late write by a leftover child can
   only refuse a receipt, never put new bytes into one.
9. **One preparation per title.** `pipeline.ingest` holds an exclusive lock on
   `titles/<sha256>/.ingest.lock` and refuses at once when another process has
   it. Updates to the shared `catalog.json` hold `.catalog.json.lock` for one
   read and write, waiting at most 30 seconds. The local library's own
   workspace lock is unchanged.

Retries are bounded: a step runs at most once per invocation and the next
invocation is the retry; the only loops are the index lock's 30 second wait and
at most eight attempts at a temporary name. The recovery code deletes nothing:
an unreadable ledger is renamed aside, replacing an earlier
`state.json.malformed`, and a temporary file is removed only by the write that
created it, when that write fails.
Source identity, preset isolation, the safe path checks, signature checks and
every verification threshold are unchanged. Maps signed with one key are never
reused for another, because the signing key's public identity is part of the
analysis fingerprint.

## Reproduce

```sh
.venv/bin/python -m eval.preparation_recovery \
    --out results/preparation-recovery-2026-10-22/evidence.json --mutations
```

It needs ffmpeg and ffprobe on the path. On the Mac that produced the evidence
it took <!--n results/preparation-recovery-2026-10-22/evidence.json:seconds -->627.9<!--/n-->
seconds, most of them the mutations. In a temporary directory it makes one
calm generated clip and two Ed25519 test key pairs, runs every scenario through
the pipeline's own command lines as separate processes, and removes the
directory. The real flashmap CLI is used for one scenario and the fake analyzer
from `pipeline/tests` for the rest. Kills are SIGKILL to the whole process group.
`--quick` skips the timed sweep and the real analyzer. `--code-root DIR` runs
the same scenarios against another checkout; that is how the base commit's file
above was made. `--mutations` then breaks each recovery guard in a copy of the
code, with the mutation gate's own harness, and runs the recovery tests against
it. The runner exits 0 only when every scenario met its expectation and every
mutation was caught.

Each scenario in the JSON names the requirement it covers, the procedure, what
was expected, what was observed and `pass` or `fail`. A recovered or repaired
result is compared with an uninterrupted run of the same source, keys and
settings at the same path: ledger fingerprints and output hashes, the SHA-256 of
every file in the title, the verify report and the receipt. Ledger completion
times, the verify report's start and finish times, and the two receipt digests
that cover those files record when something ran, so they are left out, and the
evidence names them. With the real analyzer, maps carry `created_utc` and a
signature over it, so they are compared without those three fields.

The focused tests are in `pipeline/tests/test_preparation_recovery.py`,
including two that SIGKILL real preparations and restart them.

## Results

On the commit named in `results/preparation-recovery-2026-10-22/evidence.json`, the integrated branch,
<!--n results/preparation-recovery-2026-10-22/evidence.json:summary.passed -->16<!--/n--> of
<!--n results/preparation-recovery-2026-10-22/evidence.json:summary.scenarios -->16<!--/n-->
scenarios met their expectation, and
<!--n results/preparation-recovery-2026-10-22/evidence.json:guard_mutations.totals.killed -->24<!--/n--> of
<!--n results/preparation-recovery-2026-10-22/evidence.json:guard_mutations.totals.mutations -->24<!--/n-->
guard mutations made the recovery tests fail, after the same tests passed
unmutated. The first evidence, for `7ff4a37` before integration, is kept in
`results/preparation-recovery-2026-10-21/evidence.json`. Read the scenarios themselves for where each kill landed and which
steps ran again. The generated clip differs from run to run, so encoded sizes
differ between evidence files; within one run every comparison is exact.

## Limitations

- No power was cut. The durability claims rest on `fsync`, and on macOS
  `F_FULLFSYNC`, doing what the operating system says they do. The evidence
  comes from one Mac, on APFS.
- On a filesystem that cannot flush a directory, several network and FUSE
  filesystems among them, that refusal is tolerated, and a rename may not
  survive a power loss even though the file contents do.
- The locks are advisory `flock` locks on one machine. A work directory shared
  between machines, for example over NFS, is not serialized, and other tools
  that write into a workspace without taking the lock are not stopped by it.
- The fake analyzer's flagged spans are scripted, so the scenarios show the
  pipeline's recovery and publication gates, not flash measurement. Hashing,
  binding, signing, rendering, packaging and verification are real.
- The identity comparisons rely on ffmpeg and x264 producing the same bytes for
  the same input on one machine, which these runs observed. Another build or
  thread count can change encoded bytes; the pipeline then rebuilds what depends
  on them, which is correct but costs time.
- A late write from a child that outlived a parent killed on its own is covered
  by the in-process tests, not by a scenario.
- A write killed between creating its temporary file and renaming it leaves a
  `.state.json.<pid>.<random>.tmp` (or the same for another state file) beside
  the target. Nothing reads it, and nothing removes it automatically.
- The analyzer's own version is not part of any cache key, as before. Upgrading
  flashmap does not by itself redo analysis or verification.

## Integrating

The work was written on `claude/preparation-recovery`, from `bf2f615`
(`claude/ocean-layout-fix-2026-10-19`), and is combined with Playback Proof on
`codex/recovery-proof-integration-2026-10-22`. The recovery work itself changed
nothing in the app, playback, media, keys or trust configuration; Playback
Proof's app changes are described in [its results](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/results/playback-proof-2026-10-21/README.md).

- The integration review found two defects and fixed them in `1c6bea9`: verify's
  final byte comparison left out scene-hold images, so one rewritten after
  verification could still be published, and a ledger timestamp written as a huge
  JSON integer raised OverflowError instead of dropping its record. Both have
  regression tests and are among the guard mutations above.
- A work directory prepared before this change has no output hashes in its
  ledger. Its existing receipts are still checked and packaged as before, but
  the first `prepare` or `ingest` after this change redoes every step once.
  With the real analyzer that issues new maps with a new `created_utc` and
  signature, so do not re-prepare an approved work directory unless a new
  approval is intended.
- `eval/mutate_gate.py` keeps its 70 mutations. The one that mutated the old
  hash check in `pipeline/ingest.py` now mutates the ledger's check in
  `pipeline/state.py`; `results/mutation.json` was regenerated by the full gate
  on the integrated branch, with the result described in
  [RELEASE_READINESS.md](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/docs/RELEASE_READINESS.md).
- The key rotation steps in [SECURITY.md](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/docs/SECURITY.md) no longer depend on
  `--force`, and [pipeline/LOCAL_LIBRARY.md](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/pipeline/LOCAL_LIBRARY.md) says
  what to do after an interruption.
