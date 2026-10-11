#!/usr/bin/env python3
"""The mutation gate: break every safety guard on purpose and watch its test go red.

A green test proves nothing on its own. This file lists every safety property Calm
Frames claims, and for each one an edit to the code that guards it. The edit is applied,
the tests that should catch it are run, and the run has to go red for the right reason.
Anything that survives is named in results/mutation.json with why.

    python3 eval/mutate_gate.py              run the whole gate, write results/mutation.json
    python3 eval/mutate_gate.py --list       print the mutations and stop
    python3 eval/mutate_gate.py --lane app   one lane only
    python3 eval/mutate_gate.py --only cover-before-segment-app
    python3 eval/mutate_gate.py --check      run it and fail if the committed report disagrees

Six rules this harness follows, every one of them learned from a harness that lied:

1. Nothing is mutated in the working tree. flashmap and pipeline are copied into
   build/mutate/py and the app into build/mutate/app, and only the copy is edited. On this
   machine the analyzer runs as a subprocess of a long ingest and the app's tests run in
   another session, so an edit to the real tree, even for thirty seconds, could give
   somebody else a wrong answer. It also means no restore step can destroy anyone's work.

2. The mutated file has to be the file the runner loads. flashmap is installed into the
   virtual environment as an editable package, so `import flashmap` reaches the original
   source whatever the working directory is. Every mutation runs a canary first that
   resolves the module the way the test runner will and looks for the mutated text in it.
   A mutation that fails its canary is recorded as survived, never as killed.

3. Whole test files, never single test ids. A mutation was once recorded as surviving
   because the test that catches it lived in a different class in the same file than the
   one that was named. Selections here are files.

4. A red run is read, not counted. pytest exits non-zero for a collection error and jest
   exits non-zero for a TypeScript error, and neither is a test catching anything. A kill
   needs at least one named failing test and no collection or compile error. Anything else
   is recorded as "red for the wrong reason" and counted as a survivor.

5. The unmutated case is the negative control. Every distinct selection is run green before
   any mutation touches it, and the report says so.

6. Arguments are passed as arguments. Every command here is a list handed to subprocess,
   never a string split by a shell, because a shell loop that split a command string is how
   a mutation run silently tested the wrong file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / "build" / "mutate"
PY_LANE = BUILD / "py"
APP_LANE = BUILD / "app"
REPORT_PATH = REPO / "results" / "mutation.json"

PY = os.environ.get("CALM_MUTATE_PY") or str(REPO / ".venv" / "bin" / "python")
if not Path(PY).exists():
    PY = sys.executable

# Directories inside app/ that are shared rather than copied. node_modules is 800 MB and
# nothing in it is ever mutated, so it is linked. The rest are build output.
APP_LINKED = {
    "node_modules",
    "build",
    "coverage",
    "kepler-build",
    "bundle",
    "generated",
    "shaka-setup",
}

CANARY_TEST = "test/__mutation_canary.test.ts"

# The three values are written into the file as literals rather than read from the
# environment, and this is not a style choice. The first version read them from
# process.env, and the second mutation's canary was handed the FIRST mutation's needle:
# jest had cached the transformed canary, complete with the environment values baked in,
# because the file itself had not changed. A harness that reads its own inputs out of a
# cache is a harness that can say anything. Writing the values in makes the file different
# for every mutation, so there is nothing to reuse.
CANARY_SOURCE = """/* Written by eval/mutate_gate.py for one mutation and deleted after it. */
import * as fs from 'fs';

it('jest loads the mutated file, not the original', () => {
  const specifier = %(specifier)s;
  const expected = %(expected)s;
  const needle = %(needle)s;
  const resolved = require.resolve(specifier);
  expect(resolved).toBe(expected);
  expect(fs.readFileSync(resolved, 'utf8')).toContain(needle);
});
"""


@dataclass(frozen=True)
class Mutation:
    """One edit, and the tests that have to notice it."""

    mid: str
    prop: str
    lane: str
    path: str
    old: str
    new: str
    tests: tuple[str, ...]
    why: str
    # Set when the mutant is known to be equivalent: the edit changes the code but cannot
    # change what the program does, so no test can catch it and none should be written to
    # pretend otherwise. It still counts as a survivor in the kill rate, because rounding a
    # number up for a good reason is still rounding it up. What it does not do is fail the
    # gate, and the reason has to be written here for a reader to check.
    equivalent: str = ""


@dataclass
class RunResult:
    command: list[str]
    returncode: int
    seconds: float
    stdout: str
    stderr: str
    failing: list[str] = field(default_factory=list)
    ran: int = 0
    broken: str = ""

    @property
    def is_a_kill(self) -> bool:
        return bool(self.failing) and not self.broken

    def tail(self, lines: int = 12) -> str:
        text = (self.stdout + self.stderr).strip().splitlines()
        return "\n".join(text[-lines:])


# --------------------------------------------------------------------- the mutations
#
# Each entry names the property from CLAUDE.md that it attacks. `old` must appear exactly
# once in the file, so a mutation cannot land somewhere it was not meant to.

MUTATIONS: list[Mutation] = [
    # ---------------------------------------------------------- cover before segment
    Mutation(
        mid="chime-only-before-a-cover",
        prop="a chime only ever sounds before a cover",
        lane="app",
        path="src/calmframes/chimeCue.ts",
        old="    if (untilMs > 0 && untilMs <= leadMs) {",
        new="    if (untilMs <= leadMs) {",
        tests=("test/calmframes/chimeCue.test.tsx",),
        why="the cue stops checking that the part is still ahead of the playhead, so a "
        "seek past a flagged part sounds a chime with nothing hidden after it",
    ),
    Mutation(
        mid="cover-before-segment-app",
        prop="cover before segment",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="      let startMs = segment.startMs - offsetMs - guardBandMs;",
        new="      let startMs = segment.startMs - offsetMs;",
        tests=("test/calmframes/coverSchedule.test.ts",),
        why="the guard band no longer runs ahead of the segment, so the cover arrives "
        "exactly when the flashing does",
    ),
    Mutation(
        mid="cover-before-segment-min-cover-grows-the-start",
        prop="cover before segment",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="      if (endMs - startMs < minCoverMs) {\n        endMs = startMs + minCoverMs;\n      }",
        new="      if (endMs - startMs < minCoverMs) {\n        startMs = endMs - minCoverMs;\n      }",
        tests=("test/calmframes/coverSchedule.test.ts",),
        why="a short segment reaches its minimum length by moving its start later, which "
        "is the one direction a cover may never move",
    ),
    Mutation(
        mid="cover-before-segment-pipeline",
        prop="cover before segment",
        lane="py",
        path="pipeline/hideplan.py",
        old="        start_ms = segment.start_ms - guard_band_ms",
        new="        start_ms = segment.start_ms",
        tests=("pipeline/tests/test_hideplan.py",),
        why="the hide plan the pipeline publishes loses its lead on every segment",
    ),
    Mutation(
        mid="cover-before-segment-flashmap",
        prop="cover before segment",
        lane="py",
        path="flashmap/src/flashmap/analyze.py",
        old="        start = max(0.0, pts_ms - window_ms)",
        new="        start = pts_ms",
        tests=("flashmap/tests/test_sidecar.py",),
        why="a segment starts where the window failed rather than where the window began, "
        "so the map itself understates the flashing",
    ),
    Mutation(
        mid="covers-merge-rather-than-blink",
        prop="cover before segment",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="    if (previous && interval.startMs <= previous.endMs) {",
        new="    if (previous && interval.startMs < previous.endMs) {",
        tests=("test/calmframes/coverSchedule.test.ts",),
        why="two intervals that touch exactly stop merging, so the cover blinks off for "
        "an instant between them",
    ),
    # ------------------------------------------------- cover held through stalls and seeks
    Mutation(
        mid="hold-through-stall",
        prop="cover held through stalls and seeks",
        lane="app",
        path="src/calmframes/useCoverHarness.ts",
        old="const UNCERTAIN_EVENTS = new Set<TimingEventKind>([\n  'seeking',\n  'waiting',\n  'stalled',\n  'pause',\n  'error',\n]);",
        new="const UNCERTAIN_EVENTS = new Set<TimingEventKind>([\n  'seeking',\n  'pause',\n  'error',\n]);",
        tests=("test/calmframes/coverHarness.test.tsx",),
        why="buffering and stalling stop making the playhead uncertain, so the estimate "
        "keeps running while the picture is frozen on a frame nobody checked",
    ),
    Mutation(
        mid="disrupted-scene-stills-stay-black-on-resume",
        prop="disrupted scene stills cannot flash on resume",
        lane="app",
        path="src/calmframes/useFlashGuard.ts",
        old="    !harness.uncertain &&\n    !seekHolding &&\n    !sceneIsLatchedBlack",
        new="    !harness.uncertain && !seekHolding",
        tests=("test/calmframes/sceneHoldPlayback.test.tsx",),
        why="waiting still turns the image black, but playing restores a bright "
        "still in the same interval, so repeated resume events can create flashes",
    ),
    Mutation(
        mid="hold-until-confirmed-outside",
        prop="cover held through stalls and seeks",
        lane="app",
        path="src/calmframes/useCoverHarness.ts",
        old="      if (!foreground || uncertainRef.current) {",
        new="      if (!foreground) {",
        tests=("test/calmframes/coverHarness.test.tsx",),
        why="the scheduler stops honouring the uncertain flag, so a held cover comes off "
        "on the next tick instead of waiting for playback to be confirmed",
    ),
    Mutation(
        mid="seek-covers-first",
        prop="cover held through stalls and seeks",
        lane="app",
        path="src/calmframes/seekSafety.ts",
        old="  const landing = intervalForSeekTarget(intervals, targetMs);\n  if (landing) {\n    return {\n      source,\n      requestedMs,\n      targetMs,\n      coverFirst: true,",
        new="  const landing = intervalForSeekTarget(intervals, targetMs);\n  if (landing) {\n    return {\n      source,\n      requestedMs,\n      targetMs,\n      coverFirst: false,",
        tests=("test/calmframes/seekSafety.test.ts",),
        why="a seek that lands inside a flagged interval no longer covers before it moves "
        "the playhead",
    ),
    Mutation(
        mid="seek-keyframe-lookback",
        prop="cover held through stalls and seeks",
        lane="app",
        path="src/calmframes/seekSafety.ts",
        old="      interval.endMs <= targetMs && targetMs - interval.endMs < lookbackMs,",
        new="      interval.endMs <= targetMs && targetMs - interval.endMs < 0,",
        tests=("test/calmframes/seekSafety.test.ts",),
        why="a seek just past an interval stops counting as landing inside it, so the "
        "decoder can put a frame from the flashing part on screen",
    ),
    Mutation(
        mid="seek-confirm-margin",
        prop="cover held through stalls and seeks",
        lane="app",
        path="src/calmframes/seekSafety.ts",
        old="      mediaTimeMs >= held.startMs - confirmOutsideMs &&\n      mediaTimeMs < held.endMs + confirmOutsideMs",
        new="      mediaTimeMs >= held.startMs &&\n      mediaTimeMs < held.endMs",
        tests=("test/calmframes/seekSafety.test.ts",),
        why="the cover comes off on the first report outside the interval, with no margin "
        "for a playhead that is still settling",
    ),
    Mutation(
        mid="background-hides-at-once",
        prop="cover held through stalls and seeks",
        lane="app",
        path="src/calmframes/useCoverHarness.ts",
        old="    if (mode === 'timing' && !foreground) {\n      applyCover(true, 'background', clockRef.current.anchorMediaMs);\n    }",
        new="    if (mode === 'timing' && false) {\n      applyCover(true, 'background', clockRef.current.anchorMediaMs);\n    }",
        tests=(
            "test/calmframes/coverHarness.test.tsx",
            "test/calmframes/useFlashGuard.test.tsx",
            "test/calmframes/mutationSurvivors.test.tsx",
        ),
        why="going to the background stops hiding the picture at once, and waits for the "
        "next scheduler tick instead",
        equivalent=(
            "the cover still goes on at once, by a second path. foreground is in the "
            "dependency list of the tick effect, and that effect calls tick() itself "
            "before setting its interval, so a change of foreground tears the effect "
            "down, builds it again and covers synchronously. The picture is hidden in "
            "the same commit either way and no test can see a difference. It was "
            "checked rather than assumed: coverHarness.test.tsx now has a test that "
            "flips foreground and advances no timers at all, and it stays green with "
            "this mutation applied and goes red when foreground is also taken out of "
            "that dependency list, which is the only way to actually remove the "
            "behaviour. Worth knowing that the redundancy is what makes this "
            "equivalent: drop foreground from those deps as a tidy-up and the guard on "
            "line 318 becomes load bearing again."
        ),
    ),
    # -------------------------------------------------------------- fail closed on maps
    Mutation(
        mid="fail-closed-missing",
        prop="fail closed on a map that is missing",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  if (text === null || text === undefined || text.length === 0) {\n    return reject('missing', 'no map was found for this title');\n  }",
        new=(
            "  if (text === null || text === undefined || text.length === 0) {\n"
            "    // MUTANT: trust a missing map as a checked, empty schedule.\n"
            "    return { ok: true, map: {\n"
            "      segments: [],\n"
            "      source: { path: '', sha256: options.expectedSha256, durationMs: null },\n"
            "      profileName: 'wcag', hiddenMs: 0, createdUtcMs: options.nowMs,\n"
            "      keyId: '', windows: [{ name: 'room', widthFraction: 0 }],\n"
            "    } };\n"
            "  }"
        ),
        tests=("test/calmframes/flashMap.test.ts", "test/calmframes/useFlashGuard.test.tsx"),
        why="missing map input returns a verified empty schedule without a signature "
        "or analysis, so playing confirmation can uncover the unchecked picture",
    ),
    Mutation(
        mid="fail-closed-stale",
        prop="fail closed on a map that is stale",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  if (options.nowMs - createdUtcMs > maxAgeMs) {",
        new="  if (false) {",
        tests=("test/calmframes/flashMap.test.ts", "test/calmframes/useFlashGuard.test.tsx"),
        why="a map made any number of years ago is accepted as a current check",
    ),
    Mutation(
        mid="fail-closed-unsigned",
        prop="fail closed on a map that is unsigned",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  const signature = asRecord(plain.signature);\n  if (!signature) {\n    return reject('unsigned', 'the map carries no signature');\n  }",
        new="  const signature = asRecord(plain.signature) ?? {};\n  if (false) {\n    return reject('unsigned', 'the map carries no signature');\n  }",
        tests=("test/calmframes/flashMap.test.ts",),
        why="a map with no signature block is read as if it had one",
        equivalent=(
            "the unsigned path is guarded three times over. With the first check gone, a map "
            "with no signature block reaches the algorithm check, where asString(undefined) "
            "is not 'ed25519', and is refused as 'unsigned' again. Only the diagnostic "
            "detail changes, and nothing user facing reads it: useFlashGuard shows "
            "rejectionMessage(reason). No test can tell the two apart, and writing one that "
            "pins the wording would be testing a log line."
        ),
    ),
    Mutation(
        mid="fail-closed-tampered",
        prop="fail closed on a map that was tampered with",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  if (!verifyEd25519(signatureBytes, signedBytes, publicKeyBytes)) {\n    return reject('bad-signature', 'the signature does not match the map');\n  }",
        new="  if (false) {\n    return reject('bad-signature', 'the signature does not match the map');\n  }",
        tests=("test/calmframes/flashMap.test.ts", "test/calmframes/useFlashGuard.test.tsx"),
        why="a segment can be removed from a signed map and the app will still play it",
    ),
    Mutation(
        mid="fail-closed-wrong-hash",
        prop="fail closed on a map bound to the wrong file",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  if (sha256.toLowerCase() !== options.expectedSha256.toLowerCase()) {",
        new="  if (false) {",
        tests=("test/calmframes/flashMap.test.ts",),
        why="a map made for another film answers for this one",
    ),
    Mutation(
        mid="fail-closed-unknown-key",
        prop="fail closed on a map signed by a key we do not hold",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  if (mapPublicKey !== options.publicKeyBase64) {",
        new="  if (false) {",
        tests=("test/calmframes/flashMap.test.ts",),
        why="the map's own key is trusted instead of the one the app ships, so anybody "
        "can sign a map for this app",
    ),
    Mutation(
        mid="fail-closed-wrong-version",
        prop="fail closed on a map in a version we do not read",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="  const version = asNumber(plain.version);\n  if (version !== SUPPORTED_MAP_VERSION) {",
        new="  const version = asNumber(plain.version);\n  if (false) {",
        tests=("test/calmframes/flashMap.test.ts",),
        why="a map in a format this build has never seen is read anyway",
    ),
    Mutation(
        mid="fail-closed-bad-segment-list",
        prop="fail closed on a map that cannot be read",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="    if (startMs === null || endMs === null || endMs <= startMs || startMs < 0) {\n      return null;\n    }",
        new="    if (startMs === null || endMs === null) {\n      continue;\n    }",
        tests=(
            "test/calmframes/flashMap.test.ts",
            "test/calmframes/mutationSurvivors.test.tsx",
        ),
        why="a segment with a negative or reversed time is skipped instead of refusing "
        "the whole map, so the part it described is never covered",
    ),
    Mutation(
        mid="fail-closed-guard-starts-hidden",
        prop="fail closed while a map is still being checked",
        lane="app",
        path="src/calmframes/useFlashGuard.ts",
        old="  const covered =\n    activeStatus !== 'verified' || !ready || harness.covered || seekHolding;",
        new="  const covered = harness.covered || seekHolding;",
        tests=("test/calmframes/useFlashGuard.test.tsx",),
        why="the picture is visible before any map has verified, which is the whole of "
        "fail closed",
    ),
    Mutation(
        mid="fail-closed-guard-keeps-going-on-rejection",
        prop="fail closed on a map the guard rejected",
        lane="app",
        path="src/calmframes/useFlashGuard.ts",
        old="        if (!verdict.ok) {\n          if (cancelled) {\n            return;\n          }\n          setStatus('blocked');",
        new="        if (!verdict.ok) {\n          if (cancelled) {\n            return;\n          }\n          setStatus('verified');",
        tests=("test/calmframes/useFlashGuard.test.tsx",),
        why="a rejected map leaves the title verified, so the picture plays uncovered",
    ),
    Mutation(
        mid="fail-closed-sidecar-unsigned-python",
        prop="fail closed on a map that is unsigned",
        lane="py",
        path="flashmap/src/flashmap/sidecar.py",
        old='        if require_signature:\n            problems.append("map is not signed")',
        new='        if False:\n            problems.append("map is not signed")',
        tests=("flashmap/tests/test_sidecar.py",),
        why="the analyzer's own reader stops refusing an unsigned map, so the pipeline "
        "would publish one",
    ),
    Mutation(
        mid="fail-closed-sidecar-wrong-hash-python",
        prop="fail closed on a map bound to the wrong file",
        lane="py",
        path="flashmap/src/flashmap/sidecar.py",
        old="                source_hash_matches = actual == expected_hash",
        new="                source_hash_matches = True",
        tests=("flashmap/tests/test_sidecar.py",),
        why="a map verifies against a file it was not made from",
    ),
    Mutation(
        mid="fail-closed-sidecar-signature-covers-body",
        prop="fail closed on a map that was tampered with",
        lane="py",
        path="flashmap/src/flashmap/sidecar.py",
        old='    payload = {key: value for key, value in document.items() if key != "signature"}',
        new='    payload = {"constant": 1}',
        tests=("flashmap/tests/test_sidecar.py",),
        why="the signature stops covering the segments, so they can be edited freely",
    ),
    Mutation(
        mid="fail-closed-sidecar-segment-list",
        prop="fail closed on a map that cannot be read",
        lane="py",
        path="flashmap/src/flashmap/sidecar.py",
        old='    problems.extend(_segment_problems(document.get("segments")))',
        new="    problems.extend([])",
        tests=("flashmap/tests/test_sidecar.py",),
        why="a signed map whose segments are strings, or not a list, or end before they "
        "start, verifies cleanly, so a studio is told its map is fine when no player will "
        "take it",
    ),
    Mutation(
        mid="fail-closed-sidecar-segment-ends-after-it-starts",
        prop="fail closed on a map that cannot be read",
        lane="py",
        path="flashmap/src/flashmap/sidecar.py",
        old='        if end <= start:\n            problems.append(f"segment {index} ends at {end} and starts at {start}")',
        new='        if False:\n            problems.append(f"segment {index} ends at {end} and starts at {start}")',
        tests=("flashmap/tests/test_sidecar.py",),
        why="the one segment check that costs coverage, a flash that ends before it starts, "
        "stops being made",
    ),
    Mutation(
        mid="verify-checks-the-source-hash",
        prop="fail closed on a map bound to the wrong file",
        lane="py",
        path="pipeline/verify.py",
        old='        "source_hash",\n        actual_sha == layout.sha256,',
        new='        "source_hash",\n        True,',
        tests=("pipeline/tests/test_verify.py",),
        why="verify stops noticing that the file on disk is not the file the title was "
        "built from",
    ),
    Mutation(
        mid="cached-artifacts-check-the-actual-output-bytes",
        prop="cached metadata and previews stay bound to their checked bytes",
        lane="py",
        path="pipeline/ingest.py",
        old="            if not check_output_bytes or (",
        new="            if True or not check_output_bytes or (",
        tests=("pipeline/tests/test_cached_artifacts.py",),
        why="an artifact changed at the same path is trusted from its old cache "
        "record instead of being regenerated before publication",
    ),
    Mutation(
        mid="cached-posters-are-recorded-as-outputs",
        prop="cached metadata and previews stay bound to their checked bytes",
        lane="py",
        path="pipeline/ingest.py",
        old="            poster_outputs.extend(poster.path for poster in posters)",
        new="            poster_outputs.extend([])",
        tests=("pipeline/tests/test_cached_artifacts.py",),
        why="poster JPEGs disappear from the ledger's output list, so a changed "
        "or missing poster can reuse a previously checked step",
    ),
    # ------------------------------------------------------- red segments always opaque
    Mutation(
        mid="red-survives-merging",
        prop="red segments always opaque",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="      if (interval.reason === 'red') {\n        previous.reason = 'red';\n      }",
        new="      if (false) {\n        previous.reason = 'red';\n      }",
        tests=("test/calmframes/coverSchedule.test.ts", "test/calmframes/household.test.ts"),
        why="a red segment merged into a general one loses its red reason, and a dim "
        "cover does not satisfy the red rule",
    ),
    Mutation(
        mid="red-is-the-default-reason",
        prop="red segments always opaque",
        lane="app",
        path="src/calmframes/flashMap.ts",
        old="    const reason: CoverReason =\n      reasonText === 'general'\n        ? 'general'\n        : reasonText === 'pattern'\n        ? 'pattern'\n        : 'red';",
        new="    const reason: CoverReason =\n      reasonText === 'red'\n        ? 'red'\n        : reasonText === 'pattern'\n        ? 'pattern'\n        : 'general';",
        tests=(
            "test/calmframes/flashMap.test.ts",
            "test/calmframes/mutationSurvivors.test.tsx",
        ),
        why="a reason this build has not seen is treated as general rather than red, so "
        "a future map's stricter category gets the weaker cover",
    ),
    Mutation(
        mid="red-is-never-dimmed-pipeline",
        prop="red segments always opaque",
        lane="py",
        path="pipeline/hideplan.py",
        old="    if interval.reason in (RED, PATTERN):\n        return OPAQUE\n    return DIM if allow_dim else OPAQUE",
        new="    if interval.reason == PATTERN:\n        return OPAQUE\n    return DIM if allow_dim else OPAQUE",
        tests=("pipeline/tests/test_hideplan.py",),
        why="the pipeline lets a red interval be dimmed",
    ),
    Mutation(
        mid="red-survives-merging-pipeline",
        prop="red segments always opaque",
        lane="py",
        path="pipeline/hideplan.py",
        old="            if interval.reason == RED:\n                previous.reason = RED",
        new="            if False:\n                previous.reason = RED",
        tests=("pipeline/tests/test_hideplan.py",),
        why="merging drops the red reason in the hide plan too",
    ),
    Mutation(
        mid="verify-red-always-opaque",
        prop="red segments always opaque",
        lane="py",
        path="pipeline/verify.py",
        old='            f"red_always_opaque:{preset}",\n            not red_dimmed,',
        new='            f"red_always_opaque:{preset}",\n            True,',
        tests=("pipeline/tests/test_verify.py",),
        why="verify stops blocking a plan that dims a red interval",
    ),
    # --------------------------------------------------- room rule never weaker than WCAG
    Mutation(
        mid="room-cannot-shorten-the-guard-band",
        prop="room rule never weaker than WCAG",
        lane="app",
        path="src/calmframes/household.ts",
        old="    guardBandMs: Math.max(DEFAULT_GUARD_BAND_MS, preset.guardBandMs),\n    minCoverMs: Math.max(DEFAULT_MIN_COVER_MS, preset.minCoverMs),",
        new="    guardBandMs: preset.guardBandMs,\n    minCoverMs: preset.minCoverMs,",
        tests=(
            "test/calmframes/household.test.ts",
            "test/calmframes/mutationSurvivors.test.tsx",
        ),
        why="a preset can set a guard band below the WCAG default, which is a household "
        "setting making the app weaker",
    ),
    Mutation(
        mid="room-keeps-the-wcag-map",
        prop="room rule never weaker than WCAG",
        lane="app",
        path="src/calmframes/household.ts",
        old="    mapProfiles: ['wcag', 'broadcast'],\n    guardBandMs: DEFAULT_GUARD_BAND_MS,",
        new="    mapProfiles: ['broadcast'],\n    guardBandMs: DEFAULT_GUARD_BAND_MS,",
        tests=("test/calmframes/household.test.ts",),
        why="the broadcast preset swaps the WCAG map out instead of adding to it",
    ),
    Mutation(
        mid="room-stricter-than-the-map-is-refused",
        prop="room rule never weaker than WCAG",
        lane="app",
        path="src/calmframes/household.ts",
        old="  if (map.windows.length === 0) {\n    return false;\n  }",
        new="  if (map.windows.length === 0) {\n    return true;\n  }",
        tests=("test/calmframes/household.test.ts", "test/calmframes/useFlashGuard.test.tsx"),
        why="a map that says nothing about its area windows is treated as answering for "
        "any room, however close the sofa is",
    ),
    Mutation(
        mid="room-window-is-added-not-swapped",
        prop="room rule never weaker than WCAG",
        lane="py",
        path="flashmap/src/flashmap/analyze.py",
        old="    if room is not None:\n        windows.append(",
        new="    if room is not None:\n        windows.clear()\n        windows.append(",
        tests=("flashmap/tests/test_room.py",),
        why="the room window replaces the WCAG one rather than being added to it, so a "
        "large room could produce a weaker analysis than WCAG asks for",
    ),
    # ----------------------------------------------- BIF and posters only from calm frames
    Mutation(
        mid="bif-frames-come-from-calm-moments",
        prop="BIF and posters only from calm frames",
        lane="py",
        path="pipeline/bif.py",
        old="        source_ms = snap_to_calm(intervals, slot_ms, duration_ms, margin_ms=margin_ms)",
        new="        source_ms = slot_ms",
        tests=("pipeline/tests/test_bif.py",),
        why="trickplay frames are taken from the slot time whatever is happening there, "
        "so scrubbing shows the flashing frame by frame",
    ),
    Mutation(
        mid="calm-margin-keeps-clear-of-the-edge",
        prop="BIF and posters only from calm frames",
        lane="py",
        path="pipeline/hideplan.py",
        old="        if interval.start_ms - margin_ms <= time_ms < interval.end_ms + margin_ms:",
        new="        if interval.start_ms <= time_ms < interval.end_ms:",
        tests=("pipeline/tests/test_hideplan.py", "pipeline/tests/test_bif.py"),
        why="the calm margin disappears, so a still may be taken from the moment just "
        "before a flash where it is already building",
    ),
    Mutation(
        mid="posters-snap-to-calm",
        prop="BIF and posters only from calm frames",
        lane="py",
        path="pipeline/posters.py",
        old="    if may_be_sampled(intervals, time_ms, duration_ms, margin_ms=margin_ms):\n        return time_ms",
        new="    return time_ms",
        tests=("pipeline/tests/test_stills.py", "pipeline/tests/test_bif.py"),
        why="a poster time is never moved off a flagged moment",
    ),
    Mutation(
        mid="verify-bif-calm",
        prop="BIF and posters only from calm frames",
        lane="py",
        path="pipeline/verify.py",
        old='                f"bif_calm:{preset}",\n                not bad and bool(frames),',
        new='                f"bif_calm:{preset}",\n                True,',
        tests=("pipeline/tests/test_verify.py",),
        why="verify stops blocking a title whose trickplay strip was cut from the "
        "flashing",
    ),
    Mutation(
        mid="verify-bif-from-safe-rendition",
        prop="BIF and posters only from calm frames",
        lane="py",
        path="pipeline/verify.py",
        old='            from_safe = manifest.get("from") == "safe_rendition"',
        new="            from_safe = True",
        tests=("pipeline/tests/test_verify.py",),
        why="trickplay frames cut from the original file rather than the covered "
        "rendition are accepted",
    ),
    # ------------------------------------------- verify blocks publishing on any violation
    Mutation(
        mid="verify-report-fails-on-any-check",
        prop="verify blocks publishing on any violation",
        lane="py",
        path="pipeline/verify.py",
        old="    @property\n    def passed(self) -> bool:\n        return bool(self.checks) and all(check.passed for check in self.checks)",
        new="    @property\n    def passed(self) -> bool:\n        return True",
        tests=("pipeline/tests/test_verify.py",),
        why="a report with failing checks says it passed, which is the single line that "
        "decides whether a title reaches kid mode",
    ),
    Mutation(
        mid="verify-writes-the-verdict-to-the-catalog",
        prop="verify blocks publishing on any violation",
        lane="py",
        path="pipeline/verify.py",
        old="    entry.verified = report.passed\n    entry.status = STATUS_VERIFIED if report.passed else STATUS_FAILED",
        new="    entry.verified = True\n    entry.status = STATUS_VERIFIED",
        tests=("pipeline/tests/test_verify.py",),
        why="the catalog marks a failed title verified, so kid mode lists it",
    ),
    Mutation(
        mid="verify-cover-proof-cannot-be-skipped",
        prop="verify blocks publishing on any violation",
        lane="py",
        path="pipeline/verify.py",
        old="            not plan.intervals or proven,",
        new="            True,",
        tests=("pipeline/tests/test_verify.py", "pipeline/tests/test_verify_pool.py"),
        why="a title with intervals to cover passes verify without the cover ever having "
        "been measured on the rendition, which is the hole that let fourteen titles with "
        "nothing to hide read exactly like seven whose cover was proven",
    ),
    Mutation(
        mid="verify-cover-is-actually-drawn",
        prop="verify blocks publishing on any violation",
        lane="py",
        path="pipeline/verify.py",
        old="COVER_PSNR_MIN_DB = 30.0",
        new="COVER_PSNR_MIN_DB = 0.0",
        tests=("pipeline/tests/test_verify.py",),
        why="a rendition that still shows the film under its cover passes the check that "
        "measures the cover against the still",
    ),
    Mutation(
        mid="verify-safe-rendition-is-clean",
        prop="verify blocks publishing on any violation",
        lane="py",
        path="pipeline/verify.py",
        old='                    f"safe_rendition_clean:{preset}",\n                    safe_map.is_clean,',
        new='                    f"safe_rendition_clean:{preset}",\n                    True,',
        tests=("pipeline/tests/test_verify.py",),
        why="a kid safe rendition with flashing left in it is published",
    ),
    # ---------------------------------------------------------- rendition start offset
    Mutation(
        mid="rendition-offset-limit-app",
        prop="rendition start offset",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="export const MAX_RENDITION_START_OFFSET_MS = 150;",
        new="export const MAX_RENDITION_START_OFFSET_MS = 100000;",
        tests=("test/calmframes/coverSchedule.test.ts", "test/calmframes/useFlashGuard.test.tsx"),
        why="the schedule accepts an offset verify would never publish, so it builds "
        "covers in the wrong places instead of refusing",
    ),
    Mutation(
        mid="rendition-offset-is-applied",
        prop="rendition start offset",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="      let endMs = segment.endMs - offsetMs + guardBandMs;",
        new="      let endMs = segment.endMs + guardBandMs;",
        tests=(
            "test/calmframes/coverSchedule.test.ts",
            "test/calmframes/mutationSurvivors.test.tsx",
        ),
        why="only one end of the interval moves onto the rendition's timeline, so the "
        "cover is the wrong length and ends late",
    ),
    Mutation(
        mid="rendition-offset-must-be-a-number",
        prop="rendition start offset",
        lane="app",
        path="src/calmframes/coverSchedule.ts",
        old="  if (!Number.isFinite(offsetMs)) {\n    throw new Error('renditionStartOffsetMs must be a finite number');\n  }",
        new="  if (false) {\n    throw new Error('renditionStartOffsetMs must be a finite number');\n  }",
        tests=("test/calmframes/coverSchedule.test.ts",),
        why="a NaN offset poisons every interval boundary instead of being refused",
    ),
    Mutation(
        mid="rendition-offset-fail-closed-path",
        prop="rendition start offset",
        lane="app",
        path="src/calmframes/useFlashGuard.ts",
        old="      } catch {\n        if (cancelled) {\n          return;\n        }\n        setStatus('blocked');\n        setCheckedInput(verificationInput);\n        setRejection('wrong-file');",
        new="      } catch {\n        if (cancelled) {\n          return;\n        }\n        built = [];\n        setStatus('verified');\n        setCheckedInput(verificationInput);\n        setRejection('wrong-file');",
        tests=("test/calmframes/useFlashGuard.test.tsx",),
        why="a schedule the app refused to build leaves the title playing with no "
        "intervals at all, which is the worst possible answer",
    ),
    Mutation(
        mid="rendition-offset-limit-pipeline",
        prop="rendition start offset",
        lane="py",
        path="pipeline/verify.py",
        old="START_OFFSET_LIMIT_MS = 150.0",
        new="START_OFFSET_LIMIT_MS = 150000.0",
        tests=("pipeline/tests/test_verify.py",),
        why="verify publishes a rendition whose timeline starts anywhere at all",
    ),
    Mutation(
        mid="rendition-offset-follows-a-narrow-guard-band",
        prop="rendition start offset",
        lane="py",
        path="pipeline/verify.py",
        old="            start_limit = min(START_OFFSET_LIMIT_MS, guard_band_ms)",
        new="            start_limit = START_OFFSET_LIMIT_MS",
        tests=("pipeline/tests/test_verify.py",),
        why="a household with a guard band narrower than the offset limit stops "
        "narrowing the limit with it, which is a setting making the check weaker",
    ),
    # -------------------------------------------- the property tests are not vacuous either
    #
    # These break the same guards again, but the tests that have to notice are the hypothesis
    # ones in eval/property_scheduler_test.py, driving the app copy's compiled TypeScript. A
    # property test that has never been seen to fail is worth no more than any other.
    Mutation(
        mid="property-cover-before-segment",
        prop="the property tests are not vacuous",
        lane="pyapp",
        path="src/calmframes/coverSchedule.ts",
        old="      let startMs = segment.startMs - offsetMs - guardBandMs;",
        new="      let startMs = segment.startMs - offsetMs;",
        tests=("eval/property_scheduler_test.py",),
        why="the guard band stops running ahead of the segment, which the hypothesis tests "
        "have to find at any guard band, minimum cover and rendition offset",
    ),
    Mutation(
        mid="property-red-survives-merging",
        prop="the property tests are not vacuous",
        lane="pyapp",
        path="src/calmframes/coverSchedule.ts",
        old="      if (interval.reason === 'red') {\n        previous.reason = 'red';\n      }",
        new="      if (false) {\n        previous.reason = 'red';\n      }",
        tests=("eval/property_scheduler_test.py",),
        why="merging drops the red reason, over random timelines rather than one fixture",
    ),
    Mutation(
        mid="property-intervals-never-touch",
        prop="the property tests are not vacuous",
        lane="pyapp",
        path="src/calmframes/coverSchedule.ts",
        old="    if (previous && interval.startMs <= previous.endMs) {",
        new="    if (previous && interval.startMs < previous.endMs) {",
        tests=("eval/property_scheduler_test.py",),
        why="two intervals that touch exactly stop merging, which no fixture in the jest "
        "suite happens to hit at every guard band",
    ),
    Mutation(
        mid="property-seek-covers-first",
        prop="the property tests are not vacuous",
        lane="pyapp",
        path="src/calmframes/seekSafety.ts",
        old="      interval.endMs <= targetMs && targetMs - interval.endMs < lookbackMs,",
        new="      interval.endMs <= targetMs && targetMs - interval.endMs < 0,",
        tests=("eval/property_scheduler_test.py",),
        why="the keyframe lookback disappears, at every gap the property test tries",
    ),
    Mutation(
        mid="property-clock-re-anchors",
        prop="the property tests are not vacuous",
        lane="pyapp",
        path="src/calmframes/mediaClock.ts",
        old="  const anchorMediaMs = estimate(clock, wallClockMs);\n  return { ...clock, running, anchorMediaMs, anchorWallMs: wallClockMs };",
        new="  return { ...clock, running };",
        tests=("eval/property_scheduler_test.py",),
        why="starting and stopping the clock stops re-anchoring it, so the estimate invents "
        "the media time a stall took",
    ),
    Mutation(
        mid="rendition-offset-is-recorded",
        prop="rendition start offset",
        lane="py",
        path="pipeline/verify.py",
        old='            measured["start_offset_ms"] = round(\n                ren["first_pts_ms"] - src["first_pts_ms"], 3\n            )',
        new='            measured["start_offset_ms"] = 0.0',
        tests=("pipeline/tests/test_verify.py",),
        why="the offset the player subtracts is reported as zero, so every live cover "
        "runs that far late",
    ),
    # ---- the Oct 2 to 10 guards: signed scene holds, the packaged library, the
    # demo key and the household record. Each was broken by hand and seen red
    # when it was written; this is the durable version of that.
    Mutation(
        mid="scene-still-belongs-to-a-covered-segment",
        prop="a scene hold still only ever stands over a segment of its own map",
        lane="app",
        path="src/calmframes/sceneHolds.ts",
        old="    if (\n      !segments.some(\n        (segment) => segment.startMs >= startMs && segment.endMs <= endMs,\n      ) ||\n      (frameMs !== null &&",
        new="    if (\n      (frameMs !== null &&",
        tests=("test/calmframes/sceneHolds.test.ts",),
        why="a signed still with no flagged segment inside its bounds is accepted, so a "
        "producer can put a picture over any moment of the film and call it a hold",
    ),
    Mutation(
        mid="demo-key-only-for-the-bundled-title",
        prop="the demo key unlocks one bundled title and nothing else",
        lane="app",
        path="src/calmframes/benignStory.ts",
        old="  return isBundledBenignStory(title) ? BENIGN_STORY_PUBLIC_KEY : fallback;",
        new="  return BENIGN_STORY_PUBLIC_KEY;",
        tests=("test/calmframes/benignStory.test.tsx",),
        why="any catalog entry is verified against the demo key, so a map signed with "
        "the demo's private key plays any title in kid mode",
    ),
    Mutation(
        mid="packaged-route-must-match-the-source-hash",
        prop="the packaged library accepts a route only for the exact source it compiled",
        lane="app",
        path="src/calmframes/packagedLibrary.ts",
        old="        expected.sha256 === guarded.sha256 && expected.durationMs === guarded.durationMs &&",
        new="        expected.durationMs === guarded.durationMs &&",
        tests=("test/calmframes/packagedLibrary.test.tsx",),
        why="a route naming a different source file with the same id and duration is "
        "accepted, and the compiled key then verifies a map for a file it was never "
        "compiled for",
    ),
    Mutation(
        mid="household-record-keeps-the-pin-rounds-bounded",
        prop="a stored household record cannot change how the PIN is hashed",
        lane="app",
        path="src/calmframes/householdStorage.ts",
        old="    record.rounds !== PIN_ROUNDS ||",
        new="    record.rounds < 1 ||",
        tests=("test/calmframes/householdStorage.test.ts",),
        why="a record carrying a rounds count of its own is accepted, so a tampered "
        "store can make every PIN check hash for as long as it likes, or not at all",
    ),
    Mutation(
        mid="scene-hold-bytes-reproduce-from-provenance",
        prop="verify refuses a scene hold image that does not reproduce from its stated frame",
        lane="py",
        path="pipeline/sceneholds.py",
        old='            if reproduced.read_bytes() != image.path.read_bytes():\n                raise PipelineError("scene hold bytes do not reproduce from their stated provenance")',
        new='            if False:\n                raise PipelineError("scene hold bytes do not reproduce from their stated provenance")',
        tests=("pipeline/tests/test_sceneholds.py",),
        why="an image that is not the frame it claims to be is signed and published, "
        "so the still a child sees is whatever the producer put there",
    ),
    Mutation(
        mid="cover-proof-reaches-the-end-of-a-span",
        prop="verify measures the cover at the first frame, the middle and the last frame of every covered span",
        lane="py",
        path="pipeline/verify.py",
        old="    return [start_s + frame_s, middle_s, end_s - frame_s]",
        new="    return [middle_s]",
        tests=("pipeline/tests/test_verify.py",),
        why="a cover drawn at the middle of a span and gone before its end passes a midpoint-only "
        "proof, which is the proof verify had until Oct 11, 2026",
    ),
]


# ------------------------------------------------------------------- lane preparation


def _copy_python_lane() -> None:
    PY_LANE.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", ".hypothesis", "*.egg-info", "*.pyc"
    )
    for name in ("flashmap", "pipeline"):
        target = PY_LANE / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(REPO / name, target, ignore=ignore, symlinks=False)


def _copy_app_lane() -> None:
    if APP_LANE.exists():
        # Unlink the shared directories first so rmtree cannot walk into node_modules.
        for name in APP_LINKED:
            link = APP_LANE / name
            if link.is_symlink():
                link.unlink()
        shutil.rmtree(APP_LANE)
    APP_LANE.mkdir(parents=True, exist_ok=True)
    source = REPO / "app"
    for entry in sorted(source.iterdir()):
        destination = APP_LANE / entry.name
        if entry.name in APP_LINKED:
            destination.symlink_to(entry.resolve())
        elif entry.is_dir():
            shutil.copytree(entry, destination, symlinks=False)
        else:
            shutil.copy2(entry, destination)


def prepare(lanes: set[str]) -> None:
    if "py" in lanes:
        _copy_python_lane()
    if lanes & {"app", "pyapp"}:
        _copy_app_lane()
    if "pyapp" in lanes:
        _PRISTINE["digest"] = compile_mutant_scheduler()


def lane_root(lane: str) -> Path:
    return PY_LANE if lane == "py" else APP_LANE


# The compiled scheduler as it is before any mutation, so a mutation that compiles to the
# same bytes can be caught and reported rather than counted.
_PRISTINE: dict[str, str] = {}


def compile_mutant_scheduler() -> str:
    """Compile the app copy's scheduler and return a hash of the JavaScript it produced."""
    code = (
        "import sys; sys.path.insert(0, 'eval');"
        "import property_runner as runner;"
        "runner.compile_scheduler(force=True);"
        "print(runner.compiled_digest())"
    )
    env = dict(os.environ)
    env["CALM_FRAMES_APP_DIR"] = str(APP_LANE)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [PY, "-c", code], cwd=REPO, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        raise SystemExit(
            "the app copy's scheduler would not compile, so the property tests cannot be "
            f"mutated:\n{(result.stdout + result.stderr)[-2000:]}"
        )
    return result.stdout.strip().splitlines()[-1]


# ------------------------------------------------------------------------ running tests


def _python_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(PY_LANE), str(PY_LANE / "flashmap" / "src")]
    )
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTEST_ADDOPTS", None)
    if extra:
        env.update(extra)
    return env


_PYTEST_COUNT = re.compile(r"(\d+) (passed|failed|error|errors|skipped|deselected|xfailed|xpassed)")


def _read_pytest(result: RunResult) -> None:
    """Say what a pytest run actually did, rather than trusting its exit code."""
    text = result.stdout + "\n" + result.stderr
    result.failing = [
        line.split(" ", 1)[1].strip()
        for line in text.splitlines()
        if line.startswith("FAILED ")
    ]
    counts = {}
    for match in _PYTEST_COUNT.finditer(text):
        counts[match.group(2)] = int(match.group(1))
    result.ran = counts.get("passed", 0) + counts.get("failed", 0)
    if "error during collection" in text or "errors during collection" in text:
        result.broken = "pytest could not collect the tests"
    elif counts.get("error") or counts.get("errors"):
        result.broken = "pytest reported an error rather than a failing test"
    elif result.ran == 0:
        result.broken = "no test ran at all"
    elif result.returncode != 0 and not result.failing:
        result.broken = "pytest went red without naming a failing test"


_JEST_TESTS = re.compile(r"^Tests:\s+(?P<body>.*)$", re.MULTILINE)
_JEST_SUITES = re.compile(r"^Test Suites:\s+(?P<body>.*)$", re.MULTILINE)


def _jest_counts(body: str) -> dict[str, int]:
    return {
        word: int(number)
        for number, word in re.findall(r"(\d+) (\w+)", body)
    }


def _read_jest(result: RunResult) -> None:
    """Same idea for jest. A TypeScript error also exits non-zero and catches nothing."""
    text = result.stdout + "\n" + result.stderr
    result.failing = [
        line.strip().lstrip("● ").strip()
        for line in text.splitlines()
        if line.strip().startswith("●") and "Console" not in line
    ]
    tests = _JEST_TESTS.search(text)
    suites = _JEST_SUITES.search(text)
    counts = _jest_counts(tests.group("body")) if tests else {}
    suite_counts = _jest_counts(suites.group("body")) if suites else {}
    result.ran = counts.get("passed", 0) + counts.get("failed", 0)
    failed_tests = counts.get("failed", 0)
    if not tests or result.ran == 0:
        result.broken = "jest ran no test, so the suite did not compile or did not load"
    elif failed_tests == 0 and suite_counts.get("failed", 0):
        result.broken = "a jest suite failed without a failing test, which is a compile error"
    elif failed_tests == 0 and result.returncode != 0:
        result.broken = "jest went red without a failing test"
    if failed_tests and not result.failing:
        # Keep the evidence honest even if the bullet lines were not printed.
        result.failing = [f"{failed_tests} failing test(s), see the tail"]


def run_tests(lane: str, tests: tuple[str, ...], env_extra: dict[str, str] | None = None) -> RunResult:
    root = lane_root(lane)
    if lane == "pyapp":
        # Python property tests, driving the app copy's TypeScript through node. Run from the
        # repository, not the copy, because the tests themselves are not what is mutated.
        root = REPO
        command = [
            PY, "-m", "pytest", "-q", "-rf", "-x", "--no-header",
            "-p", "no:cacheprovider", *tests,
        ]
        env = dict(os.environ)
        env["CALM_FRAMES_APP_DIR"] = str(APP_LANE)
        env["CALM_FRAMES_REQUIRE_NODE"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.pop("PYTEST_ADDOPTS", None)
        if env_extra:
            env.update(env_extra)
    elif lane == "py":
        command = [
            PY, "-m", "pytest", "-q", "-rf", "-x", "--no-header",
            "-p", "no:cacheprovider", *tests,
        ]
        env = _python_env(env_extra)
    else:
        command = [
            "npx", "jest", "--ci", "--colors=false", "--coverage=false", "--watchman=false",
            "--runInBand", "--silent", *tests,
        ]
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
    started = time.time()
    proc = subprocess.run(
        command, cwd=root, capture_output=True, text=True, env=env
    )
    result = RunResult(
        command=command,
        returncode=proc.returncode,
        seconds=round(time.time() - started, 1),
        stdout=proc.stdout[-20000:],
        stderr=proc.stderr[-20000:],
    )
    if lane in ("py", "pyapp"):
        _read_pytest(result)
    else:
        _read_jest(result)
    return result


# ----------------------------------------------------------------------------- canary


def canary(mutation: Mutation, needle: str) -> tuple[bool, str]:
    """Prove the runner loads the mutated file, not the original one."""
    root = lane_root(mutation.lane)
    target = (root / mutation.path).resolve()

    if mutation.lane == "pyapp":
        # The property tests reach the app through compiled JavaScript, so the proof has to be
        # that the compile changed. A mutation that compiles to the same bytes never reached
        # the code that answers, whatever the source file now says.
        if needle not in target.read_text():
            return False, "the mutated text is not in the app copy"
        digest = compile_mutant_scheduler()
        if digest == _PRISTINE.get("digest"):
            return False, (
                "the compiled scheduler is byte for byte what it was before the mutation, "
                "so the mutation never reached the code the property tests run"
            )
        return True, ""

    if mutation.lane == "py":
        if mutation.path.startswith("flashmap/"):
            module = "flashmap." + Path(mutation.path).stem
        else:
            module = "pipeline." + Path(mutation.path).stem
        code = (
            "import importlib, pathlib, sys\n"
            f"module = importlib.import_module({module!r})\n"
            "loaded = pathlib.Path(module.__file__).resolve()\n"
            f"expected = pathlib.Path({str(target)!r}).resolve()\n"
            "if loaded != expected:\n"
            "    print('loaded ' + str(loaded), file=sys.stderr); sys.exit(3)\n"
            f"if {needle!r} not in loaded.read_text():\n"
            "    print('needle missing', file=sys.stderr); sys.exit(4)\n"
        )
        proc = subprocess.run(
            [PY, "-c", code], cwd=PY_LANE, capture_output=True, text=True,
            env=_python_env(),
        )
        if proc.returncode == 0:
            return True, ""
        return False, (proc.stderr or proc.stdout).strip()[-400:]

    # The app lane asks jest itself, because jest's resolver is the one that matters.
    specifier = "../" + mutation.path.rsplit(".", 1)[0]
    canary_path = APP_LANE / CANARY_TEST
    canary_path.write_text(
        CANARY_SOURCE
        % {
            "specifier": json.dumps(specifier),
            "expected": json.dumps(str(target)),
            "needle": json.dumps(needle),
        }
    )
    try:
        result = run_tests("app", (CANARY_TEST,))
    finally:
        canary_path.unlink(missing_ok=True)
    if result.returncode == 0:
        return True, ""
    return False, result.tail(8)


def needle_for(mutation: Mutation) -> str:
    for line in mutation.new.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    raise ValueError(f"{mutation.mid}: the replacement is empty")


# ------------------------------------------------------------------------------ the run


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_and_run(mutation: Mutation) -> dict:
    root = lane_root(mutation.lane)
    path = root / mutation.path
    record: dict = {
        "id": mutation.mid,
        "property": mutation.prop,
        "lane": mutation.lane,
        "file": mutation.path,
        "breaks": mutation.why,
        "tests": list(mutation.tests),
        "killed": False,
        "evidence": "",
        "survived_because": "",
        "seconds": 0.0,
    }
    if mutation.equivalent:
        record["equivalent"] = mutation.equivalent

    if not path.exists():
        record["survived_because"] = f"there is no {mutation.path} in the copy"
        return record

    original = path.read_text()
    if original.count(mutation.old) != 1:
        record["survived_because"] = (
            f"the text to mutate appears {original.count(mutation.old)} times in "
            f"{mutation.path}, and a mutation needs exactly one"
        )
        return record

    # Backed up by copy, never by git. `git checkout -- <path>` restores from the index
    # and would throw away anything unstaged, which on a shared checkout means somebody
    # else's work.
    backup = path.with_suffix(path.suffix + ".mutation-backup")
    shutil.copy2(path, backup)
    before = digest(path)
    try:
        path.write_text(original.replace(mutation.old, mutation.new))
        if digest(path) == before:
            record["survived_because"] = "the file on disk did not change"
            return record

        needle = needle_for(mutation)
        loaded, detail = canary(mutation, needle)
        if not loaded:
            record["survived_because"] = f"the mutated file is not the one loaded: {detail}"
            return record

        result = run_tests(mutation.lane, mutation.tests)
        record["seconds"] = result.seconds
        if result.is_a_kill:
            record["killed"] = True
            record["evidence"] = "; ".join(result.failing[:3])
            record["tests_run"] = result.ran
        elif result.broken:
            record["survived_because"] = (
                f"the run went red for the wrong reason: {result.broken}. "
                f"Tail: {result.tail(6)}"
            )
        else:
            record["survived_because"] = (
                f"every test passed with the guard broken ({result.ran} ran)"
            )
            record["tests_run"] = result.ran
    finally:
        shutil.copy2(backup, path)
        backup.unlink()
        if digest(path) != before:
            raise SystemExit(f"{mutation.mid}: the file was not restored, stopping")
    return record


def negative_control(selected: list[Mutation]) -> tuple[list[dict], bool]:
    """Run every selection unmutated first. A red baseline makes every kill meaningless."""
    seen: dict[tuple[str, tuple[str, ...]], None] = {}
    for mutation in selected:
        seen.setdefault((mutation.lane, mutation.tests), None)
    records: list[dict] = []
    green = True
    for lane, tests in seen:
        result = run_tests(lane, tests)
        passed = result.returncode == 0 and not result.failing
        green = green and passed
        records.append(
            {
                "lane": lane,
                "tests": list(tests),
                "green": passed,
                "tests_run": result.ran,
                "seconds": result.seconds,
                "detail": "" if passed else result.tail(8),
            }
        )
        print(
            f"  control {'green' if passed else 'RED  '} "
            f"{lane:4s} {' '.join(tests)} ({result.ran} tests, {result.seconds}s)"
        )
    return records, green


def floor_to(value: float, places: int) -> float:
    scale = 10**places
    return math.floor(value * scale) / scale


def build_report(
    records: list[dict], controls: list[dict], control_green: bool,
    *, controls_performed: bool = True,
) -> dict:
    killed = [record for record in records if record["killed"]]
    survived = [record for record in records if not record["killed"]]
    unexpected = [record for record in survived if "equivalent" not in record]
    claimed_equivalent_but_killed = [
        record for record in killed if "equivalent" in record
    ]
    total = len(records)
    rate = floor_to(len(killed) / total, 4) if total else 0.0
    by_property: dict[str, dict] = {}
    for record in records:
        entry = by_property.setdefault(
            record["property"], {"mutations": 0, "killed": 0, "survivors": []}
        )
        entry["mutations"] += 1
        if record["killed"]:
            entry["killed"] += 1
        else:
            entry["survivors"].append(record["id"])
    return {
        "statement": (
            "Every safety property Calm Frames claims has a mutation that breaks the code "
            "guarding it. The kill rate below is killed divided by attempted, rounded down, "
            "over the mutations in eval/mutate_gate.py only. It is not a whole-codebase "
            "mutation score and it does not stand in for one."
        ),
        "tool": "eval/mutate_gate.py",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "how_a_kill_is_counted": (
            "The tests that guard the mutated line are run as whole files. A kill needs at "
            "least one named failing test and no collection or compile error, because both "
            "of those also exit non-zero and neither is a test catching anything."
        ),
        "negative_control": {
            "description": (
                "every selection run unmutated before any mutation was applied"
                if controls_performed
                else "skipped by --skip-control; no green baseline was established"
            ),
            "performed": controls_performed,
            "all_green": control_green and controls_performed,
            "selections": controls,
        },
        "totals": {
            "mutations": total,
            "killed": len(killed),
            "survived": len(survived),
            "survived_and_not_equivalent": len(unexpected),
            "kill_rate": rate,
            "kill_rate_percent": floor_to(rate * 100, 2),
            "as_a_fraction": f"{len(killed)}/{total}",
        },
        "equivalent_mutants_that_were_killed_after_all": [
            record["id"] for record in claimed_equivalent_but_killed
        ],
        "properties": by_property,
        "survivors": survived,
        "mutations": records,
    }


def compare_with_committed(report: dict, committed: dict | None = None) -> int:
    """Fail when this run disagrees with the report in the repository."""
    if committed is None:
        if not REPORT_PATH.exists():
            print(f"no committed report at {REPORT_PATH}", file=sys.stderr)
            return 1
        committed = json.loads(REPORT_PATH.read_text())
    problems = []
    if committed["totals"]["mutations"] != report["totals"]["mutations"]:
        problems.append(
            f"the committed report has {committed['totals']['mutations']} mutations, "
            f"this run had {report['totals']['mutations']}"
        )
    if report["totals"]["kill_rate"] < committed["totals"]["kill_rate"]:
        problems.append(
            f"the kill rate fell from {committed['totals']['kill_rate']} to "
            f"{report['totals']['kill_rate']}"
        )
    was = {record["id"] for record in committed["survivors"]}
    now = {record["id"] for record in report["survivors"]}
    for mid in sorted(now - was):
        problems.append(f"{mid} survived and the committed report does not say it would")
    for mid in sorted(was - now):
        print(f"mutation gate: {mid} used to survive and is now killed. Update the report.")
    for problem in problems:
        print(f"mutation gate: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lane", choices=["py", "app", "pyapp"], help="run one lane only"
    )
    parser.add_argument("--only", action="append", default=[], help="run these ids only")
    parser.add_argument("--property", action="append", default=[], help="run these properties only")
    parser.add_argument("--list", action="store_true", help="print the mutations and stop")
    parser.add_argument("--check", action="store_true", help="fail if the committed report disagrees")
    parser.add_argument(
        "--out", default=str(REPORT_PATH),
        help="report output; --check writes only to a path other than its committed baseline",
    )
    parser.add_argument(
        "--skip-control", action="store_true",
        help="skip the unmutated runs, for a quick look only",
    )
    args = parser.parse_args(argv)
    if args.check and args.skip_control:
        print("--check requires negative controls; --skip-control is for quick looks only", file=sys.stderr)
        return 2

    selected = [
        mutation
        for mutation in MUTATIONS
        if (not args.lane or mutation.lane == args.lane)
        and (not args.only or mutation.mid in args.only)
        and (not args.property or mutation.prop in args.property)
    ]
    if not selected:
        print("no mutation matched", file=sys.stderr)
        return 2

    if args.list:
        width = max(len(m.mid) for m in selected)
        for mutation in selected:
            print(f"{mutation.lane:4s} {mutation.mid:{width}s}  {mutation.prop}")
        print(f"\n{len(selected)} mutation(s)")
        return 0

    ids = [mutation.mid for mutation in selected]
    if len(set(ids)) != len(ids):
        print("two mutations share an id", file=sys.stderr)
        return 2

    # Preserve the baseline before any work starts. In check mode, the measured
    # report must never replace the document it is compared against, including
    # when --out names that document explicitly or through a path alias.
    committed = None
    if args.check:
        try:
            committed = json.loads(REPORT_PATH.read_text())
        except (OSError, json.JSONDecodeError) as error:
            print(f"cannot read committed report at {REPORT_PATH}: {error}", file=sys.stderr)
            return 1

    lanes = {mutation.lane for mutation in selected}
    print(f"copying {', '.join(sorted(lanes))} into {BUILD}")
    prepare(lanes)

    controls: list[dict] = []
    control_green = not args.skip_control
    if not args.skip_control:
        print("\nnegative control, nothing mutated:")
        controls, control_green = negative_control(selected)
        if not control_green:
            print(
                "\nBASELINE IS ALREADY RED. Every kill below would be meaningless, stopping.",
                file=sys.stderr,
            )
            return 2

    print(f"\n{len(selected)} mutation(s):")
    records: list[dict] = []
    for index, mutation in enumerate(selected, start=1):
        record = apply_and_run(mutation)
        records.append(record)
        mark = "killed  " if record["killed"] else "SURVIVED"
        print(f"  [{index:2d}/{len(selected)}] {mark} {mutation.mid} ({record['seconds']}s)")
        if not record["killed"]:
            print(f"            because: {record['survived_because']}")

    report = build_report(
        records, controls, control_green, controls_performed=not args.skip_control,
    )
    out = Path(args.out)
    comparison_status = compare_with_committed(report, committed) if args.check else 0
    same_as_baseline = out.resolve() == REPORT_PATH.resolve()
    if args.check and out.exists() and REPORT_PATH.exists():
        same_as_baseline = same_as_baseline or out.samefile(REPORT_PATH)
    writes_report = not args.check or not same_as_baseline
    if writes_report:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")

    totals = report["totals"]
    destination = f"written to {out}" if writes_report else f"compared with {REPORT_PATH}"
    print(
        f"\nkill rate {totals['as_a_fraction']} = {totals['kill_rate']} "
        f"({totals['kill_rate_percent']}%), {destination}"
    )
    if report["survivors"]:
        print(f"\n{len(report['survivors'])} survivor(s):")
        for record in report["survivors"]:
            mark = "equivalent, " if "equivalent" in record else ""
            print(f"  {record['id']}: {mark}{record['survived_because']}")
            if "equivalent" in record:
                print(f"            {record['equivalent']}")
    for mid in report["equivalent_mutants_that_were_killed_after_all"]:
        print(f"\n{mid} was called equivalent and a test caught it. Remove that claim.")

    if args.check:
        return 1 if comparison_status or totals["survived_and_not_equivalent"] else 0
    return 0 if not report["totals"]["survived_and_not_equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
