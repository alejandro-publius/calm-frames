import {
  buildCoverIntervals,
  CoverInterval,
  FlashSegment,
  isCovered,
  nextIntervalAfter,
} from '../../src/calmframes/coverSchedule';
import {
  breakOwnsSelect,
  coveredWithBreak,
  expireGrace,
  MIN_BREAK_MS,
  NO_BREAK,
  OK_GRACE_MS,
  PictureBreakState,
  pictureBreakCopy,
  requestReturn,
  RETURN_CLEARANCE_MS,
  returnWait,
  settleBreak,
  startBreak,
  toggleBreak,
} from '../../src/calmframes/pictureBreak';

const HOLD: CoverInterval[] = [
  { startMs: 10_000, endMs: 12_000, sources: [] } as unknown as CoverInterval,
];

describe('the rules', () => {
  test('a break starts at once and starting again changes nothing', () => {
    const resting = startBreak(NO_BREAK, 1_000);
    expect(resting).toEqual({ resting: true, startedAtMs: 1_000, returnRequested: false });
    expect(startBreak(resting, 5_000)).toBe(resting);
  });

  test('Menu starts a break, then asks for the picture back, and asking twice changes nothing', () => {
    const resting = toggleBreak(NO_BREAK, 0);
    expect(resting.resting).toBe(true);
    const asked = toggleBreak(resting, 100);
    expect(asked.returnRequested).toBe(true);
    expect(toggleBreak(asked, 200)).toBe(asked);
    expect(requestReturn(asked)).toBe(asked);
    expect(requestReturn(NO_BREAK)).toBe(NO_BREAK);
  });

  test('the picture waits out the minimum break, then returns', () => {
    const asked = requestReturn(startBreak(NO_BREAK, 0));
    const early = settleBreak(asked, MIN_BREAK_MS - 1, 3_000, []);
    expect(early.resting).toBe(true);
    expect(early.waitingFor).toBe('minimum');
    expect(settleBreak(early, MIN_BREAK_MS - 1, 3_000, [])).toBe(early);
    expect(settleBreak(early, MIN_BREAK_MS, 3_000, [])).toEqual({ ...NO_BREAK, endedAtMs: MIN_BREAK_MS });
  });

  test('the picture never returns inside a scheduled hold', () => {
    const asked = requestReturn(startBreak(NO_BREAK, 0));
    const inside = settleBreak(asked, 5_000, 11_000, HOLD);
    expect(inside.resting).toBe(true);
    expect(inside.waitingFor).toBe('hold-now');
    expect(settleBreak(inside, 6_000, 12_000, HOLD)).toEqual({ ...NO_BREAK, endedAtMs: 6_000 });
  });

  test('the picture never returns less than the clearance before the next hold', () => {
    const asked = requestReturn(startBreak(NO_BREAK, 0));
    const before = 10_000 - RETURN_CLEARANCE_MS + 1;
    const soon = settleBreak(asked, 5_000, before, HOLD);
    expect(soon.waitingFor).toBe('hold-soon');
    expect(returnWait(asked, 5_000, 10_000 - RETURN_CLEARANCE_MS, HOLD)).toBeUndefined();
    expect(settleBreak(asked, 5_000, 10_000 - RETURN_CLEARANCE_MS, HOLD).resting).toBe(false);
  });

  test('OK stays with the break for a moment after the picture returns, then goes back', () => {
    const resting = startBreak(NO_BREAK, 0);
    expect(breakOwnsSelect(NO_BREAK)).toBe(false);
    expect(breakOwnsSelect(resting)).toBe(true);
    const ended = settleBreak(requestReturn(resting), 3_000, 3_000, []);
    expect(ended.resting).toBe(false);
    expect(breakOwnsSelect(ended)).toBe(true);
    expect(expireGrace(ended, 3_000 + OK_GRACE_MS - 1)).toBe(ended);
    expect(expireGrace(ended, 3_000 + OK_GRACE_MS)).toBe(NO_BREAK);
    expect(expireGrace(resting, 60_000)).toBe(resting);
    expect(startBreak(ended, 3_100)).toEqual({ resting: true, startedAtMs: 3_100, returnRequested: false });
  });

  test('a break that nobody asked to end never ends by itself', () => {
    const resting = startBreak(NO_BREAK, 0);
    expect(settleBreak(resting, 60_000, 30_000, [])).toBe(resting);
  });

  test('the break can only add cover', () => {
    const resting = startBreak(NO_BREAK, 0);
    for (const scheduleCovered of [false, true]) {
      for (const state of [NO_BREAK, resting]) {
        const covered = coveredWithBreak(scheduleCovered, state);
        if (scheduleCovered) expect(covered).toBe(true);
        if (state.resting) expect(covered).toBe(true);
      }
    }
    expect(coveredWithBreak(false, NO_BREAK)).toBe(false);
  });
});

describe('the wording', () => {
  const resting = startBreak(NO_BREAK, 0);

  test('it mentions captions only when the viewer has them on', () => {
    const on = pictureBreakCopy(resting, { captionsOn: true, paused: false });
    const off = pictureBreakCopy(resting, { captionsOn: false, paused: false });
    expect(on.detail).toBe('Sound and captions keep playing. Press OK to bring the picture back.');
    expect(off.detail).toBe('Sound keeps playing. Captions are off. Press OK to bring the picture back.');
    expect(off.detail).not.toMatch(/captions keep/);
    expect(on.announcement).toBe(`Picture break. ${on.detail}`);
    expect(on.returnLabel).toBe('Back to the picture');
  });

  test('a paused break does not claim sound is playing', () => {
    const paused = pictureBreakCopy(resting, { captionsOn: true, paused: true });
    expect(paused.detail).toMatch(/^Paused\./);
    expect(paused.detail).not.toMatch(/keep playing/);
  });

  test.each([
    ['minimum', 'The picture comes back in a moment.'],
    ['hold-now', 'The picture comes back when this hidden part ends.'],
    ['hold-soon', 'A hidden part is coming up. The picture comes back after it.'],
  ] as const)('a held-back return says why: %s', (waitingFor, detail) => {
    const state: PictureBreakState = { ...resting, returnRequested: true, waitingFor };
    expect(pictureBreakCopy(state, { captionsOn: true, paused: false }).detail).toBe(detail);
  });
});

// The remote, played against the schedule in 10 ms steps. Every check below is
// about what reaches the screen: the cover's changes of state.
const STEP_MS = 10;
const WINDOW_MS = 1_000;

interface Press { atMs: number; key: 'menu' | 'ok' }

interface Run {
  scheduleChanges: number[];
  screenChanges: number[];
  returns: { wallMs: number; mediaMs: number }[];
  scheduleCoveredButScreenClear: number;
  /** Ticks on which a requested return was held back by a hold. */
  heldByHoldTicks: number;
}

function simulate(
  intervals: CoverInterval[],
  presses: Press[],
  durationMs: number,
  mediaRate = 1,
): Run {
  const ticks = durationMs / STEP_MS;
  const scheduleChanges = new Array<number>(ticks).fill(0);
  const screenChanges = new Array<number>(ticks).fill(0);
  const returns: Run['returns'] = [];
  let scheduleCoveredButScreenClear = 0;
  let heldByHoldTicks = 0;
  let state: PictureBreakState = NO_BREAK;
  let lastSchedule = false;
  let lastScreen = false;
  const byTick = new Map<number, Press[]>();
  for (const press of presses) {
    const tick = Math.floor(press.atMs / STEP_MS);
    byTick.set(tick, [...(byTick.get(tick) ?? []), press]);
  }
  for (let tick = 0; tick < ticks; tick += 1) {
    const wallMs = tick * STEP_MS;
    const mediaMs = wallMs * mediaRate;
    const before = state.resting;
    for (const press of byTick.get(tick) ?? []) {
      state = press.key === 'menu'
        ? toggleBreak(state, wallMs)
        : requestReturn(state);
      state = settleBreak(state, wallMs, mediaMs, intervals);
    }
    state = settleBreak(state, wallMs, mediaMs, intervals);
    if (before && !state.resting) {
      returns.push({ wallMs, mediaMs });
    }
    if (state.waitingFor === 'hold-now' || state.waitingFor === 'hold-soon') {
      heldByHoldTicks += 1;
    }
    const schedule = isCovered(intervals, mediaMs);
    const screen = coveredWithBreak(schedule, state);
    if (schedule && !screen) {
      scheduleCoveredButScreenClear += 1;
    }
    if (tick > 0 && schedule !== lastSchedule) scheduleChanges[tick] = 1;
    if (tick > 0 && screen !== lastScreen) screenChanges[tick] = 1;
    lastSchedule = schedule;
    lastScreen = screen;
  }
  return { scheduleChanges, screenChanges, returns, scheduleCoveredButScreenClear, heldByHoldTicks };
}

function windowCounts(changes: number[]): number[] {
  const width = WINDOW_MS / STEP_MS;
  const prefix = [0];
  for (const change of changes) prefix.push(prefix[prefix.length - 1] + change);
  const counts: number[] = [];
  for (let start = 0; start < changes.length; start += 1) {
    const end = Math.min(changes.length, start + width);
    counts.push(prefix[end] - prefix[start]);
  }
  return counts;
}

/** A small deterministic generator, so a failure names its seed. */
function generator(seed: number): () => number {
  // Park and Miller's minimal standard generator; every product stays an
  // exact integer below 2 ** 53.
  const modulus = 2_147_483_647;
  let value = seed % modulus || 1;
  return () => {
    value = (value * 16_807) % modulus;
    return value / modulus;
  };
}

function randomSchedule(random: () => number, durationMs: number): CoverInterval[] {
  const segments: FlashSegment[] = [];
  const count = 1 + Math.floor(random() * 8);
  for (let index = 0; index < count; index += 1) {
    const startMs = Math.floor(random() * (durationMs - 500));
    segments.push({
      startMs,
      endMs: startMs + 50 + Math.floor(random() * 3_000),
      reason: 'general',
    });
  }
  return buildCoverIntervals(segments, { durationMs });
}

function randomPresses(random: () => number, durationMs: number): Press[] {
  const presses: Press[] = [];
  let atMs = 0;
  // Bursts of mashing between pauses, the way an anxious press looks.
  while (atMs < durationMs) {
    const mash = random() < 0.4;
    atMs += mash ? 10 + Math.floor(random() * 60) : Math.floor(random() * 2_500);
    presses.push({ atMs, key: random() < 0.7 ? 'menu' : 'ok' });
  }
  return presses.filter((press) => press.atMs < durationMs);
}

const SEEDS = Array.from({ length: 60 }, (_, index) => index + 1);
const DURATION_MS = 30_000;

describe('the remote cannot make the screen flash', () => {
  test('mashing Menu with nothing scheduled changes the cover at most twice in any second', () => {
    const presses = Array.from({ length: DURATION_MS / 20 }, (_, index) => ({
      atMs: index * 20,
      key: 'menu' as const,
    }));
    const run = simulate([], presses, DURATION_MS);
    expect(Math.max(...windowCounts(run.screenChanges))).toBeLessThanOrEqual(2);
    expect(run.returns.length).toBeGreaterThan(0);
  });

  test('mashing while paused is held to the same bound by the wall clock', () => {
    const presses = Array.from({ length: DURATION_MS / 30 }, (_, index) => ({
      atMs: index * 30,
      key: (index % 3 === 0 ? 'ok' : 'menu') as Press['key'],
    }));
    const run = simulate([], presses, DURATION_MS, 0);
    expect(Math.max(...windowCounts(run.screenChanges))).toBeLessThanOrEqual(2);
  });

  test.each(SEEDS)('seed %i: presses add at most two cover changes to any second of the schedule', (seed) => {
    const random = generator(seed);
    const intervals = randomSchedule(random, DURATION_MS);
    const run = simulate(intervals, randomPresses(random, DURATION_MS), DURATION_MS);
    const screen = windowCounts(run.screenChanges);
    const schedule = windowCounts(run.scheduleChanges);
    const excess = screen.map((count, index) => count - schedule[index]);
    expect(Math.max(...excess)).toBeLessThanOrEqual(2);
    expect(run.scheduleCoveredButScreenClear).toBe(0);
  });

  test.each(SEEDS)('seed %i: a return never lands inside a hold or within the clearance before one', (seed) => {
    const random = generator(seed);
    const intervals = randomSchedule(random, DURATION_MS);
    const run = simulate(intervals, randomPresses(random, DURATION_MS), DURATION_MS);
    for (const { mediaMs } of run.returns) {
      expect(isCovered(intervals, mediaMs)).toBe(false);
      const next = nextIntervalAfter(intervals, mediaMs);
      if (next) {
        // The promise in docs/WORKING_BACKWARDS.md, written out so that
        // weakening the constant cannot weaken the test with it.
        expect(next.startMs - mediaMs).toBeGreaterThanOrEqual(2_000);
      }
    }
  });

  test('the generated runs exercise returns held back by holds, not only easy ones', () => {
    let returns = 0;
    let runsHeldByHolds = 0;
    for (const seed of SEEDS) {
      const random = generator(seed);
      const intervals = randomSchedule(random, DURATION_MS);
      expect(intervals.length).toBeGreaterThan(0);
      const run = simulate(intervals, randomPresses(random, DURATION_MS), DURATION_MS);
      returns += run.returns.length;
      if (run.heldByHoldTicks > 0) runsHeldByHolds += 1;
    }
    expect(returns).toBeGreaterThan(100);
    expect(runsHeldByHolds).toBeGreaterThan(10);
  });
});
