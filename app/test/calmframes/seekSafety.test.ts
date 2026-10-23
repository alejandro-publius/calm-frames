/**
 * Every way of moving the playhead, and the one rule they all obey.
 *
 * The mock of @amazon-devices/react-native-w3cmedia has to be in place before
 * SafeMediaControlHandler is imported, because it extends a class from that
 * package.
 */

jest.mock('@amazon-devices/react-native-w3cmedia', () => {
  // The real base class carries these on its prototype, so the mock has to as
  // well: an instance field would shadow the subclass override and the tests
  // would be measuring the mock instead of our handler.
  const baseCalls: string[] = [];
  class KeplerMediaControlHandler {
    // The base class moves the playhead itself. If any override forgets to
    // stop that, this records it and the test says so.
    static baseCalls = baseCalls;
    async handlePlay() {baseCalls.push('handlePlay');}
    async handlePause() {baseCalls.push('handlePause');}
    async handleStop() {baseCalls.push('handleStop');}
    async handleTogglePlayPause() {baseCalls.push('handleTogglePlayPause');}
    async handleSeek() {
      baseCalls.push('handleSeek');
    }
    async handleSkipForward() {
      baseCalls.push('handleSkipForward');
    }
    async handleSkipBackward() {
      baseCalls.push('handleSkipBackward');
    }
    async handleFastForward() {
      baseCalls.push('handleFastForward');
    }
    async handleRewind() {
      baseCalls.push('handleRewind');
    }
    async handleStartOver() {
      baseCalls.push('handleStartOver');
    }
  }
  return { __esModule: true, KeplerMediaControlHandler };
});

import { ITimeValue } from '@amazon-devices/kepler-media-controls';
import { KeplerMediaControlHandler } from '@amazon-devices/react-native-w3cmedia';
import { buildCoverIntervals, CoverInterval } from '../../src/calmframes/coverSchedule';
import {
  SafeMediaControlHandler,
  timeValueToMs,
} from '../../src/calmframes/SafeMediaControlHandler';

test('remote toggle follows the current media paused flag after a recovered seek', async () => {
  const calls = (KeplerMediaControlHandler as unknown as {baseCalls: string[]}).baseCalls;
  calls.length = 0;
  let paused = true;
  const handler = new SafeMediaControlHandler({engine: {requestSeek: jest.fn()} as any,
    getCurrentMs: () => 26811, getPaused: () => paused, canControl: () => true});
  await handler.handleTogglePlayPause();
  expect(calls).toEqual(['handlePlay']);
  paused = false;
  await handler.handleTogglePlayPause();
  expect(calls).toEqual(['handlePlay', 'handlePause']);
});

test('blocked recovery cannot use the paused-state toggle override', async () => {
  const calls = (KeplerMediaControlHandler as unknown as {baseCalls: string[]}).baseCalls;
  calls.length = 0;
  const getPaused = jest.fn(() => true);
  const handler = new SafeMediaControlHandler({engine: {requestSeek: jest.fn()} as any,
    getCurrentMs: () => 0, getPaused, canControl: () => false});
  await handler.handleTogglePlayPause();
  expect(getPaused).not.toHaveBeenCalled();
  expect(calls).toEqual([]);
});
import {
  createSeekEngine,
  isPreviewAllowed,
  planSeek,
  SEEK_SOURCES,
  SeekPlan,
  SeekSource,
} from '../../src/calmframes/seekSafety';

const SEGMENTS = [
  { startMs: 10_000, endMs: 14_000 },
  { startMs: 40_000, endMs: 42_000, reason: 'red' as const },
];

function intervals(): CoverInterval[] {
  return buildCoverIntervals(SEGMENTS, { guardBandMs: 500, durationMs: 60_000 });
}

interface Harness {
  calls: string[];
  plans: SeekPlan[];
  covered: boolean;
  engine: ReturnType<typeof createSeekEngine>;
  currentMs: number;
}

function harness(): Harness {
  const state: Harness = {
    calls: [],
    plans: [],
    covered: false,
    currentMs: 0,
    engine: undefined as unknown as ReturnType<typeof createSeekEngine>,
  };
  state.engine = createSeekEngine({
    getIntervals: intervals,
    getDurationMs: () => 60_000,
    setCover: (covered, reason) => {
      state.covered = covered;
      state.calls.push(`cover:${covered ? 'on' : 'off'}:${reason.split(':')[0]}`);
    },
    seekTo: (targetMs) => {
      state.currentMs = targetMs;
      state.calls.push(`seek:${Math.round(targetMs)}`);
    },
    onPlan: (plan) => state.plans.push(plan),
  });
  return state;
}

describe('the cover schedule this all runs against', () => {
  it('widens by the guard band, so the first interval is 9500 to 14500', () => {
    expect(intervals().map((one) => [one.startMs, one.endMs])).toEqual([
      [9_500, 14_500],
      [39_500, 42_500],
    ]);
    expect(intervals()[1].reason).toBe('red');
  });
});

describe('planSeek', () => {
  it('covers first for a target inside an interval', () => {
    const plan = planSeek('seek-bar', 12_000, intervals());
    expect(plan.coverFirst).toBe(true);
    expect(plan.interval?.startMs).toBe(9_500);
  });

  it('covers first for a target inside the guard band, not only the segment', () => {
    // 9800 is before the flagged segment starts at 10000. The guard band is
    // what makes it a cover.
    const plan = planSeek('seek-bar', 9_800, intervals());
    expect(plan.coverFirst).toBe(true);
  });

  it('covers first for a target just after an interval, which decodes from inside it', () => {
    const plan = planSeek('dpad-rewind', 15_000, intervals());
    expect(plan.coverFirst).toBe(true);
    expect(plan.reason).toMatch(/decodes from inside/);
  });

  it('leaves a clear target alone', () => {
    const plan = planSeek('seek-bar', 30_000, intervals());
    expect(plan.coverFirst).toBe(false);
    expect(plan.interval).toBeUndefined();
  });

  it('clamps a target to the media', () => {
    expect(planSeek('seek-bar', -5_000, intervals(), { durationMs: 60_000 }).targetMs).toBe(0);
    expect(planSeek('seek-bar', 99_000, intervals(), { durationMs: 60_000 }).targetMs).toBe(
      60_000,
    );
    expect(planSeek('seek-bar', Number.NaN, intervals()).targetMs).toBe(0);
  });
});

describe('the one function, from each source', () => {
  it.each(SEEK_SOURCES)('%s covers before it seeks', async (source: SeekSource) => {
    const state = harness();
    await state.engine.requestSeek(source, 12_000);
    expect(state.calls).toEqual([`cover:on:seek ${source}`, 'seek:12000']);
    expect(state.calls.indexOf(`cover:on:seek ${source}`)).toBeLessThan(
      state.calls.indexOf('seek:12000'),
    );
    expect(state.engine.isHolding()).toBe(true);
    expect(state.plans[0].source).toBe(source);
  });

  it.each(SEEK_SOURCES)('%s does not cover a clear target', async (source: SeekSource) => {
    const state = harness();
    await state.engine.requestSeek(source, 30_000);
    expect(state.calls).toEqual(['seek:30000']);
    expect(state.engine.isHolding()).toBe(false);
  });
});

describe('holding the cover until playback is confirmed outside', () => {
  it('keeps the cover on while reports still land inside', async () => {
    const state = harness();
    await state.engine.requestSeek('seek-bar', 12_000);
    for (const reported of [9_600, 12_000, 14_400, 14_600]) {
      state.engine.notePlayback(reported);
      expect(state.covered).toBe(true);
    }
    // 14500 is the end, and the confirmation margin is 250 ms, so 14600 is
    // still not enough. 14800 is.
    state.engine.notePlayback(14_800);
    expect(state.covered).toBe(false);
    expect(state.engine.isHolding()).toBe(false);
  });

  it('does not uncover when the playhead left one interval into another', async () => {
    const state = harness();
    await state.engine.requestSeek('media-control', 12_000);
    state.engine.notePlayback(40_000);
    expect(state.covered).toBe(true);
    expect(state.calls).not.toContain('cover:off:seek confirmed outside the interval');
  });

  it('ignores a position that is not a number', async () => {
    const state = harness();
    await state.engine.requestSeek('seek-bar', 12_000);
    state.engine.notePlayback(Number.NaN);
    expect(state.covered).toBe(true);
  });

  it('never leaves the picture showing inside an interval, over many targets', async () => {
    // A blunt sweep: every 100 ms from before the media to past its end.
    for (let target = -2_000; target <= 62_000; target += 100) {
      const state = harness();
      await state.engine.requestSeek('trickplay', target);
      const landed = state.currentMs;
      const inside = intervals().some(
        (one) => landed >= one.startMs && landed < one.endMs,
      );
      if (inside) {
        expect(state.covered).toBe(true);
      }
    }
  });
});

describe('trickplay previews', () => {
  it('allows a preview from the safe rendition anywhere', () => {
    expect(isPreviewAllowed(intervals(), 12_000, true)).toBe(true);
  });

  it('refuses a preview inside an interval when the source is not the safe rendition', () => {
    expect(isPreviewAllowed(intervals(), 12_000, false)).toBe(false);
    expect(isPreviewAllowed(intervals(), 30_000, false)).toBe(true);
  });
});

describe('SafeMediaControlHandler', () => {
  const seconds = (value: number): ITimeValue => ({
    seconds: Math.floor(value),
    nanoseconds: Math.round((value - Math.floor(value)) * 1e9),
  });

  function makeHandler() {
    const state = harness();
    const handler = new SafeMediaControlHandler({
      engine: state.engine,
      getCurrentMs: () => state.currentMs,
      stepMs: 10_000,
    });
    return { state, handler };
  }

  it('turns a time value into milliseconds', () => {
    expect(timeValueToMs({ seconds: 12, nanoseconds: 500_000_000 })).toBe(12_500);
    expect(timeValueToMs(undefined)).toBe(0);
    expect(
      timeValueToMs({ seconds: Number.NaN, nanoseconds: 0 } as ITimeValue),
    ).toBe(0);
  });

  it('covers first on a spoken seek into a flagged part', async () => {
    const { state, handler } = makeHandler();
    await handler.handleSeek(seconds(12));
    expect(state.calls).toEqual(['cover:on:seek media-control', 'seek:12000']);
  });

  it('covers first on skip forward that lands inside', async () => {
    const { state, handler } = makeHandler();
    state.currentMs = 5_000;
    await handler.handleSkipForward(seconds(6));
    expect(state.calls[0]).toMatch(/^cover:on/);
    expect(state.currentMs).toBe(11_000);
  });

  it('covers first on skip backward that lands inside', async () => {
    const { state, handler } = makeHandler();
    state.currentMs = 20_000;
    await handler.handleSkipBackward(seconds(8));
    expect(state.calls[0]).toMatch(/^cover:on/);
    expect(state.currentMs).toBe(12_000);
  });

  it('covers first on fast forward and rewind that land inside', async () => {
    const forward = makeHandler();
    forward.state.currentMs = 5_000;
    await forward.handler.handleFastForward();
    expect(forward.state.calls[0]).toMatch(/^cover:on/);

    const back = makeHandler();
    back.state.currentMs = 20_000;
    await back.handler.handleRewind();
    // 20000 back 10000 is 10000, inside the first interval.
    expect(back.state.calls[0]).toMatch(/^cover:on/);
  });

  it('sends start over through the same funnel', async () => {
    const { state, handler } = makeHandler();
    state.currentMs = 30_000;
    await handler.handleStartOver();
    expect(state.plans).toHaveLength(1);
    expect(state.plans[0]).toMatchObject({ source: 'media-control', targetMs: 0 });
    expect(state.currentMs).toBe(0);
  });

  it('never lets the base class move the playhead', async () => {
    const { state, handler } = makeHandler();
    await handler.handleSeek(seconds(12));
    await handler.handleSkipForward(seconds(1));
    await handler.handleSkipBackward(seconds(1));
    await handler.handleFastForward();
    await handler.handleRewind();
    await handler.handleStartOver();
    // Six commands, six plans, and every one of them went through the engine.
    expect(state.plans).toHaveLength(6);
    for (const plan of state.plans) {
      expect(plan.source).toBe('media-control');
    }
    // And not one of them reached the base class, which would have moved the
    // playhead with no cover.
    expect(
      (KeplerMediaControlHandler as unknown as { baseCalls: string[] }).baseCalls,
    ).toEqual([]);
  });
});

it('recovery/stale-session transport gating prevents seeks and playback; Pause cancels the attempt', async () => {
  const engine = {requestSeek: jest.fn()} as unknown as ReturnType<typeof createSeekEngine>;
  const pause = jest.fn();
  const handler = new SafeMediaControlHandler({engine, getCurrentMs: () => 0, canControl: () => false, onBlockedPause: pause});
  const calls = (KeplerMediaControlHandler as unknown as {baseCalls: string[]}).baseCalls; calls.length = 0;
  await handler.handlePlay(); await handler.handleTogglePlayPause(); await handler.handleStartOver();
  await handler.handlePause(); await handler.handleStop();
  expect(engine.requestSeek).not.toHaveBeenCalled(); expect(calls).toEqual([]); expect(pause).toHaveBeenCalledTimes(2);
});
