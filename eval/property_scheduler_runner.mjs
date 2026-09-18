/**
 * The node half of the scheduler property tests.
 *
 * hypothesis, in eval/property_scheduler_test.py and eval/property_drift_test.py, invents
 * timelines, seeks, rate changes and stalls. This process replays each one against the app's
 * real scheduler and prints what happened, one JSON line in, one JSON line out. It stays alive
 * for the whole session, so a few hundred examples cost a few hundred milliseconds rather than
 * a few hundred node startups.
 *
 *     node eval/property_scheduler_runner.mjs --js build/property/js
 *
 * `--js` points at the compiled TypeScript. `make properties` compiles it with the app's own
 * tsc, from app/src/calmframes, so what runs here is the code that ships and not a copy of it.
 *
 * Jobs:
 *   schedule     build the cover intervals for a set of segments
 *   covered      ask isCovered for a list of media times
 *   plans        ask planSeek about a list of seek targets
 *   seekRun      drive the real seek engine through a script of seeks and positions
 *   scheduleRun  drive the real media clock and the real schedule through a timeline
 *
 * scheduleRun is the only job with glue in it. The clock arithmetic, the schedule and the
 * covering decision are all the app's; what this file adds is the loop that useCoverHarness
 * writes in React: tick every tickMs, re-anchor on every position report, and hold the cover
 * whenever an event has made the playhead uncertain. The loop is a model of the hook. The
 * hook itself is covered by app/test/calmframes/coverHarness.test.tsx and by the mutation
 * gate, and this file never claims otherwise.
 */

import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const jsIndex = process.argv.indexOf('--js');
if (jsIndex === -1 || !process.argv[jsIndex + 1]) {
  console.error('usage: node property_scheduler_runner.mjs --js <compiled dir>');
  process.exit(2);
}
const jsDir = resolve(process.argv[jsIndex + 1]);

const load = async (name) =>
  import(pathToFileURL(resolve(jsDir, `${name}.js`)).href);

const { buildCoverIntervals, isCovered, intervalAt, millisecondsUntilNextCover } =
  await load('coverSchedule');
const { planSeek, createSeekEngine } = await load('seekSafety');
const { verifyFlashMap } = await load('flashMap');
const { createMediaClock, estimate, setPlaybackRate, setRunning, sync } =
  await load('mediaClock');

function schedule(job) {
  return { intervals: buildCoverIntervals(job.segments, job.options ?? {}) };
}

function covered(job) {
  const intervals = buildCoverIntervals(job.segments, job.options ?? {});
  return {
    intervals,
    covered: job.times.map((time) => isCovered(intervals, time)),
    reasons: job.times.map((time) => intervalAt(intervals, time)?.reason ?? null),
    waits: job.times.map((time) =>
      millisecondsUntilNextCover(intervals, time, job.playbackRate ?? 1) ?? null,
    ),
  };
}

function plans(job) {
  const intervals = buildCoverIntervals(job.segments, job.options ?? {});
  return {
    intervals,
    plans: job.targets.map((target) =>
      planSeek(job.source ?? 'seek-bar', target, intervals, job.seekOptions ?? {}),
    ),
  };
}

function seekRun(job) {
  const intervals = buildCoverIntervals(job.segments, job.options ?? {});
  const calls = [];
  let coverOn = false;
  let position = job.startMs ?? 0;
  const engine = createSeekEngine(
    {
      getIntervals: () => intervals,
      getDurationMs: () => job.options?.durationMs,
      setCover: (on, reason) => {
        coverOn = on;
        calls.push({ at: position, on, reason });
      },
      seekTo: (target) => {
        position = target;
      },
    },
    job.seekOptions ?? {},
  );

  const steps = [];
  for (const step of job.script) {
    if (step.kind === 'seek') {
      // requestSeek is async only because seekTo may be; nothing here awaits a real player.
      engine.requestSeek(step.source ?? 'seek-bar', step.targetMs);
    } else if (step.kind === 'report') {
      position = step.mediaTimeMs;
      engine.notePlayback(step.mediaTimeMs);
    }
    steps.push({
      kind: step.kind,
      position,
      coverOn,
      holding: engine.isHolding(),
      heldStart: engine.heldInterval()?.startMs ?? null,
      heldEnd: engine.heldInterval()?.endMs ?? null,
      insideNow: isCovered(intervals, position),
    });
  }
  return { intervals, calls, steps };
}

/**
 * Play a whole timeline and ask, at every tick, whether the picture was hidden.
 *
 * One simulator, one truth. The test describes what the PLAYER does, in phases, and this
 * function derives both where the playhead really is and what the app gets to see: position
 * reports every reportEveryMs, and the events a player fires when it stalls, pauses or seeks.
 * Deriving the app's view from the truth is the point. Two separate models would agree with
 * each other and prove nothing, which is the mistake docs/GATES.md records.
 *
 * `driftFactor` is how much faster the player's media time runs than the app assumes. 1.005
 * is half a percent fast, which is the clock drift case in eval/property_drift_test.py.
 *
 * Phases are {untilWallMs, kind, rate}. kind is "play", "stall" or "pause". A seek is
 * {atWallMs, toMediaMs} in `seeks`.
 *
 * The loop itself is the one useCoverHarness writes in React: tick every tickMs, re-anchor on
 * every report, hold the cover while an event has made the playhead uncertain. The clock, the
 * schedule and the covering decision are the app's own code. This loop is a model of the
 * hook, and the hook is covered by app/test/calmframes/coverHarness.test.tsx and by the
 * mutation gate.
 */
function scheduleRun(job) {
  const intervals = buildCoverIntervals(job.segments, job.options ?? {});
  const tickMs = job.tickMs ?? 50;
  const reportEveryMs = job.reportEveryMs ?? 400;
  const driftFactor = job.driftFactor ?? 1;
  const phases = job.phases ?? [{ untilWallMs: job.endWallMs ?? 0, kind: 'play', rate: 1 }];
  const seeks = [...(job.seeks ?? [])].sort((a, b) => a.atWallMs - b.atWallMs);
  const endWallMs = job.endWallMs ?? phases[phases.length - 1].untilWallMs;

  // The flagged spans as they arrive in the rendition the player is showing. The guard band
  // is not part of them: the theorem this job exists to check is that a real playhead inside
  // a flagged span is covered whenever the estimate is wrong by no more than the guard band,
  // and the band is exactly the room that theorem needs.
  const offsetMs = job.options?.renditionStartOffsetMs ?? 0;
  const flagged = job.segments
    .filter((segment) => segment.endMs > segment.startMs)
    .map((segment) => [segment.startMs - offsetMs, segment.endMs - offsetMs]);
  const insideFlagged = (time) =>
    flagged.some(([start, end]) => time >= start && time < end);

  let clock = createMediaClock(0, 0, 1, false);
  let uncertain = false;
  let coverOn = true;

  const corrections = [];
  const resyncSample = [];
  const uncoveredAt = [];
  let ticks = 0;
  let ticksInsideFlagged = 0;
  let reports = 0;
  let worstEstimateError = 0;
  let worstErrorInsideFlagged = 0;

  // Where the player really is. Nothing else may write to it.
  let realMediaMs = job.startMediaMs ?? 0;
  let phaseIndex = 0;
  let seekIndex = 0;
  let nextReportWall = 0;
  let lastRateSeen = null;
  let playing = false;

  /**
   * The player says where it is.
   *
   * `atWall` is when it says so and `realAt` is where it really was at that moment. A report
   * is delivered at its own time rather than at the next tick, because a timeupdate listener
   * runs when the event fires. Rounding reports up to the tick would have quantised the
   * correction to a multiple of the tick and made the drift look larger than it is.
   */
  const report = (atWall, realAt) => {
    reports += 1;
    const correction = realAt - estimate(clock, atWall);
    corrections.push(Number(correction.toFixed(6)));
    if (resyncSample.length < 6) {
      resyncSample.push({
        wallMs: atWall,
        reportedMs: realAt,
        estimateMs: estimate(clock, atWall),
        correctionMs: correction,
      });
    }
    clock = sync(clock, realAt, atWall);
    clock = setRunning(clock, true, atWall);
    uncertain = false;
  };

  for (let wall = 0; wall <= endWallMs; wall += tickMs) {
    while (phaseIndex < phases.length - 1 && wall > phases[phaseIndex].untilWallMs) {
      phaseIndex += 1;
    }
    const phase = phases[phaseIndex];
    const phaseRate = phase.kind === 'play' ? (phase.rate ?? 1) : 0;

    // What the player does at this moment, and what it tells the app about it.
    if (phase.kind === 'play' && !playing) {
      playing = true;
      clock = setRunning(clock, true, wall);
      uncertain = false;
    } else if (phase.kind !== 'play' && playing) {
      playing = false;
      // stalled and pause both stop the clock and make the playhead uncertain.
      clock = setRunning(clock, false, wall);
      uncertain = true;
      coverOn = true;
    }
    if (phase.kind === 'play' && lastRateSeen !== phaseRate) {
      lastRateSeen = phaseRate;
      clock = setPlaybackRate(clock, phaseRate, wall);
    }

    while (seekIndex < seeks.length && seeks[seekIndex].atWallMs <= wall) {
      // seeking: the playhead is not trustworthy, so cover and hold.
      uncertain = true;
      coverOn = true;
      realMediaMs = seeks[seekIndex].toMediaMs;
      // seeked, then the position report that follows it.
      clock = setRunning(clock, true, wall);
      report(wall, realMediaMs);
      nextReportWall = wall + reportEveryMs;
      seekIndex += 1;
    }

    // Reports due since the last tick, each delivered at its own time. Where the player was
    // then is this tick's position wound back at the rate it has been running at.
    //
    // A stalled or paused player fires no timeupdate, so none is invented here. It matters:
    // a report during a stall would set the clock running again, and the estimate would then
    // advance through a stall the player was sitting still in.
    while (nextReportWall <= wall) {
      if (phase.kind === 'play') {
        const realThen = realMediaMs - (wall - nextReportWall) * phaseRate * driftFactor;
        report(nextReportWall, realThen);
      }
      nextReportWall += reportEveryMs;
    }

    const mediaTimeMs = estimate(clock, wall);
    coverOn = uncertain ? true : isCovered(intervals, mediaTimeMs);
    ticks += 1;

    const error = mediaTimeMs - realMediaMs;
    if (Math.abs(error) > Math.abs(worstEstimateError)) {
      worstEstimateError = error;
    }
    if (insideFlagged(realMediaMs)) {
      ticksInsideFlagged += 1;
      if (Math.abs(error) > Math.abs(worstErrorInsideFlagged)) {
        worstErrorInsideFlagged = error;
      }
      if (!coverOn && uncoveredAt.length < 50) {
        uncoveredAt.push({ wallMs: wall, realMs: realMediaMs, estimateMs: mediaTimeMs, errorMs: error });
      }
    }

    // Advance the real playhead to the next tick. The drift factor is the player's clock
    // running faster than the app assumes it does.
    realMediaMs += tickMs * phaseRate * driftFactor;
  }

  return {
    intervals,
    ticks,
    ticksInsideFlagged,
    reports,
    corrections,
    resyncSample,
    uncoveredAt,
    worstEstimateErrorMs: worstEstimateError,
    worstErrorInsideFlaggedMs: worstErrorInsideFlagged,
    finalRealMediaMs: realMediaMs,
    finalEstimateMs: estimate(clock, endWallMs),
  };
}

/**
 * Read a map the way the app does, and say what the picture would do.
 *
 * eval/fuzz_maps_test.py feeds this malformed, oversized, back to front and outright hostile
 * maps. Fail closed means one of two answers and never a third: the map is refused and the
 * picture stays hidden, or the map is accepted and everything it flags is hidden. An
 * exception is not one of the two, so it comes back as ok:false and is recorded as a finding.
 */
function verify(job) {
  const verdict = verifyFlashMap(job.text, {
    publicKeyBase64: job.publicKeyBase64,
    expectedSha256: job.expectedSha256,
    nowMs: job.nowMs ?? 0,
    maxAgeMs: job.maxAgeMs,
  });
  if (!verdict.ok) {
    return { verdict: 'rejected', reason: verdict.reason, detail: verdict.detail };
  }
  let intervals = null;
  let scheduleError = null;
  try {
    intervals = buildCoverIntervals(verdict.map.segments, job.options ?? {});
  } catch (error) {
    scheduleError = String(error && error.message ? error.message : error);
  }
  const segments = verdict.map.segments;
  // Was every flagged moment hidden? Sampled at the ends and the middle of each segment,
  // which is where an off by one in the schedule shows up.
  const missed = [];
  if (intervals) {
    for (const segment of segments) {
      for (const time of [
        segment.startMs,
        (segment.startMs + segment.endMs) / 2,
        segment.endMs - 1,
      ]) {
        if (!isCovered(intervals, time)) {
          missed.push(time);
        }
      }
    }
  }
  return {
    verdict: 'accepted',
    segmentCount: segments.length,
    reasons: [...new Set(segments.map((segment) => segment.reason))],
    intervalCount: intervals ? intervals.length : null,
    scheduleError,
    missed: missed.slice(0, 10),
    sha256: verdict.map.source.sha256,
    profileName: verdict.map.profileName,
    windowCount: verdict.map.windows.length,
  };
}

const JOBS = { schedule, covered, plans, seekRun, scheduleRun, verify };

const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of lines) {
  if (!line.trim()) {
    continue;
  }
  let out;
  try {
    const job = JSON.parse(line);
    const handler = JOBS[job.job];
    if (!handler) {
      out = { ok: false, error: `no job called ${job.job}` };
    } else {
      out = { ok: true, ...handler(job) };
    }
  } catch (error) {
    out = { ok: false, error: String(error && error.message ? error.message : error) };
  }
  process.stdout.write(JSON.stringify(out) + '\n');
}
