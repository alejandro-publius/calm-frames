/**
 * The chime before a hide, and the one property it has to keep.
 *
 *   a chime never sounds without a cover following it.
 *
 * Everything here is built to be able to see that fail. The cue is a state
 * machine, so a whole sitting can be scripted tick by tick and the machine
 * asked afterwards whether it kept its word: `unmatched` is the number of
 * times a chime sounded and the playhead then ran past the part it announced
 * with the picture never going dark. The detector is itself checked, by
 * driving a timeline that does leave a cue unmatched, so a green `unmatched`
 * of zero elsewhere means something.
 *
 * What "a cover following it" means when the playhead is seeked away is a
 * decision rather than an accident: the cue is discharged by the next time the
 * picture goes dark, whatever raised it, because every way of moving the
 * playhead in this app covers before it moves. docs/DECISIONS.md, 2026-09-18,
 * says why, and the scripted timeline below has a seek in it that is answered
 * the way seekSafety and useCoverHarness really answer one.
 *
 * Seen to fail, in an isolated copy of the app rather than in this tree,
 * because other lanes are working in it. `intervalToAnnounce` with its
 * `untilMs > 0` dropped, so that it announces a part that is near the playhead
 * rather than ahead of it, turned four tests red:
 *
 *   never announces a part the playhead has already gone by
 *     expect(received).toBe(expected), Expected: 0, Received: 1
 *     That one is `unmatched`: a chime sounded at 14,600 ms for a part that
 *     ended at 14,500 ms, and nothing covered after it.
 *   sounds a fixed time before the cover, and only then
 *     expect(received).toBeNull(), Received: {"endMs": 14500, "reason":
 *     "general", "sources": [{"endMs": 14000, "startMs": 10000}], "startMs":
 *     9500}
 *   over a whole sitting, with both parts played through
 *     expect(received).toBe(expected), Expected: 2, Received: 1
 *   when the second part is reached by seeking back into it
 *     expect(received).toBe(expected), Expected: 2, Received: 1
 *
 * That is the mutation eval/mutate_gate.py should carry for this property.
 */

import { render } from '@testing-library/react-native';
import React from 'react';
import {
  ChimeCueState,
  CHIME_LEAD_MS,
  CHIME_ON_BY_DEFAULT,
  emptyChimeCue,
  intervalToAnnounce,
  resetChimeCue,
  stepChimeCue,
} from '../../src/calmframes/chimeCue';
import {
  buildCoverIntervals,
  CoverInterval,
} from '../../src/calmframes/coverSchedule';
import { useChimeCue } from '../../src/calmframes/useChimeCue';

/** Two flagged parts, widened and merged the way the player would have them. */
const INTERVALS: CoverInterval[] = buildCoverIntervals(
  [
    { startMs: 10_000, endMs: 14_000 },
    { startMs: 40_000, endMs: 41_000 },
  ],
  { guardBandMs: 500, durationMs: 120_000 },
);

const FIRST = INTERVALS[0];

interface Tick {
  mediaTimeMs: number;
  covered?: boolean;
  verified?: boolean;
  enabled?: boolean;
}

interface RunResult {
  state: ChimeCueState;
  /** One entry per tick that sounded the chime, with the media time. */
  chimes: number[];
  /** The media time of every tick where the picture was dark. */
  darkAt: number[];
}

function run(ticks: Tick[], from: ChimeCueState = emptyChimeCue()): RunResult {
  let state = from;
  const chimes: number[] = [];
  const darkAt: number[] = [];
  for (const tick of ticks) {
    const covered = tick.covered ?? false;
    if (covered) {
      darkAt.push(tick.mediaTimeMs);
    }
    const stepped = stepChimeCue(state, {
      intervals: INTERVALS,
      mediaTimeMs: tick.mediaTimeMs,
      covered,
      verified: tick.verified ?? true,
      enabled: tick.enabled ?? true,
    });
    state = stepped.state;
    if (stepped.play) {
      chimes.push(tick.mediaTimeMs);
    }
  }
  return { state, chimes, darkAt };
}

/**
 * A sitting, played at the scheduler's own tick.
 *
 * The cover is on exactly while the playhead is inside an interval, which is
 * what useCoverHarness does when nothing goes wrong.
 */
function playThrough(fromMs: number, toMs: number, stepMs = 50): Tick[] {
  const ticks: Tick[] = [];
  for (let at = fromMs; at <= toMs; at += stepMs) {
    ticks.push({
      mediaTimeMs: at,
      covered: INTERVALS.some((one) => at >= one.startMs && at < one.endMs),
    });
  }
  return ticks;
}

describe('when a chime is due', () => {
  it('sounds a fixed time before the cover, and only then', () => {
    expect(intervalToAnnounce(INTERVALS, FIRST.startMs - CHIME_LEAD_MS - 1)).toBeNull();
    expect(intervalToAnnounce(INTERVALS, FIRST.startMs - CHIME_LEAD_MS)).toBe(FIRST);
    expect(intervalToAnnounce(INTERVALS, FIRST.startMs - 1)).toBe(FIRST);
    // At the cover itself there is nothing left to announce.
    expect(intervalToAnnounce(INTERVALS, FIRST.startMs)).toBeNull();
  });

  it('never announces a part the playhead has already gone by', () => {
    // A kid seeks past a flagged part. Nothing is coming, so nothing sounds.
    const after = run([
      { mediaTimeMs: FIRST.endMs + 100 },
      { mediaTimeMs: FIRST.endMs + 200 },
      { mediaTimeMs: FIRST.endMs + 300 },
    ]);
    // The property first: a chime sounded here would have nothing to follow
    // it, and that is what unmatched counts.
    expect(after.state.unmatched).toBe(0);
    expect(after.state.played).toBe(0);
    expect(after.chimes).toEqual([]);
    for (const at of [FIRST.endMs, FIRST.endMs + 1_000, FIRST.startMs + 1]) {
      expect(intervalToAnnounce(INTERVALS, at)).not.toBe(FIRST);
    }
  });

  it('sounds once per part, however many ticks are inside the lead', () => {
    const result = run(playThrough(0, 20_000));
    expect(result.chimes).toHaveLength(1);
    expect(result.chimes[0]).toBeGreaterThanOrEqual(FIRST.startMs - CHIME_LEAD_MS);
    expect(result.chimes[0]).toBeLessThan(FIRST.startMs);
    expect(result.state.played).toBe(1);
  });

  it('stays silent while the picture is already dark', () => {
    // A chime after the cover is a warning about something that has happened.
    const result = run(
      playThrough(FIRST.startMs, FIRST.endMs - 50).map((tick) => ({
        ...tick,
        covered: true,
      })),
    );
    expect(result.chimes).toEqual([]);
  });

  it('stays silent until the map has verified', () => {
    const ticks = playThrough(0, 20_000).map((tick) => ({ ...tick, verified: false }));
    expect(run(ticks).chimes).toEqual([]);
  });

  it('stays silent when the household has turned it off', () => {
    const ticks = playThrough(0, 20_000).map((tick) => ({ ...tick, enabled: false }));
    expect(run(ticks).chimes).toEqual([]);
    // And the switch is on to begin with.
    expect(CHIME_ON_BY_DEFAULT).toBe(true);
  });

  it('forgets what it announced when a new title starts', () => {
    const first = run(playThrough(0, 20_000));
    expect(first.state.announced).toContain(FIRST.startMs);
    const fresh = resetChimeCue(first.state);
    expect(fresh.announced).toEqual([]);
    expect(fresh.awaitingStartMs).toBeNull();
    // The counts carry, because they are what a run is measured by.
    expect(fresh.played).toBe(first.state.played);
  });
});

describe('a chime is never left without a cover', () => {
  it('over a whole sitting, with both parts played through', () => {
    const result = run(playThrough(0, 50_000));
    expect(result.state.played).toBe(2);
    expect(result.state.unmatched).toBe(0);
    // Every chime is followed by the picture going dark, in that order.
    for (const chimedAt of result.chimes) {
      expect(result.darkAt.some((at) => at > chimedAt)).toBe(true);
    }
  });

  it('when a seek takes the playhead away in between', () => {
    // The seek is answered the way the real player answers one: seekSafety
    // covers before it moves, and useCoverHarness treats seeking as uncertain,
    // so the picture is dark from the moment the seek starts until playback is
    // confirmed outside an interval.
    const ticks: Tick[] = [
      ...playThrough(8_000, 9_400),
      { mediaTimeMs: 9_400, covered: true },
      { mediaTimeMs: 30_000, covered: true },
      { mediaTimeMs: 30_050, covered: true },
      ...playThrough(30_100, 32_000),
    ];
    const result = run(ticks);
    expect(result.state.played).toBe(1);
    expect(result.state.unmatched).toBe(0);
    expect(result.state.awaitingStartMs).toBeNull();
  });

  it('when a stall holds the playhead still after the chime', () => {
    const ticks: Tick[] = [
      ...playThrough(8_000, 9_400),
      // Buffering: the harness covers and the playhead does not move.
      ...Array.from({ length: 20 }, () => ({ mediaTimeMs: 9_400, covered: true })),
      ...playThrough(9_450, 15_000),
    ];
    const result = run(ticks);
    expect(result.state.played).toBe(1);
    expect(result.state.unmatched).toBe(0);
  });

  it('when the second part is reached by seeking back into it', () => {
    const ticks: Tick[] = [
      ...playThrough(0, 15_000),
      { mediaTimeMs: 15_000, covered: true },
      { mediaTimeMs: 38_500, covered: true },
      ...playThrough(38_600, 42_000),
    ];
    const result = run(ticks);
    expect(result.state.played).toBe(2);
    expect(result.state.unmatched).toBe(0);
  });

  it('and the detector that says so can itself go red', () => {
    // If the cue ever announced a part and the playhead then ran past it with
    // the picture never going dark, this is what it would look like. Driving
    // it by hand proves the zero in the tests above is a measurement and not a
    // constant.
    const armed: ChimeCueState = {
      ...emptyChimeCue(),
      awaitingStartMs: FIRST.startMs,
      awaitingEndMs: FIRST.endMs,
      announced: [FIRST.startMs],
      played: 1,
    };
    const result = run([{ mediaTimeMs: FIRST.endMs + 50 }], armed);
    expect(result.state.unmatched).toBe(1);
    expect(result.state.awaitingStartMs).toBeNull();
  });
});

describe('the hook that drives it', () => {
  const Harness = ({
    mediaTimeMs,
    covered,
    verified = true,
    enabled = true,
    playChime,
  }: {
    mediaTimeMs: number;
    covered: boolean;
    verified?: boolean;
    enabled?: boolean;
    playChime: () => void;
  }) => {
    useChimeCue({
      intervals: INTERVALS,
      mediaTimeMs,
      covered,
      verified,
      enabled,
      playChime,
      titleId: 'one',
    });
    return null;
  };

  it('plays the sound once, a couple of seconds before the cover', () => {
    const playChime = jest.fn();
    const { rerender } = render(
      <Harness mediaTimeMs={5_000} covered={false} playChime={playChime} />,
    );
    expect(playChime).not.toHaveBeenCalled();

    rerender(<Harness mediaTimeMs={8_000} covered={false} playChime={playChime} />);
    expect(playChime).toHaveBeenCalledTimes(1);

    // Still inside the lead: it does not sound again.
    rerender(<Harness mediaTimeMs={9_000} covered={false} playChime={playChime} />);
    expect(playChime).toHaveBeenCalledTimes(1);

    // And the cover arrives.
    rerender(<Harness mediaTimeMs={9_600} covered playChime={playChime} />);
    expect(playChime).toHaveBeenCalledTimes(1);
  });

  it('plays nothing at all when the household has switched it off', () => {
    const playChime = jest.fn();
    const { rerender } = render(
      <Harness
        mediaTimeMs={5_000}
        covered={false}
        enabled={false}
        playChime={playChime}
      />,
    );
    rerender(
      <Harness
        mediaTimeMs={8_000}
        covered={false}
        enabled={false}
        playChime={playChime}
      />,
    );
    rerender(
      <Harness
        mediaTimeMs={9_000}
        covered={false}
        enabled={false}
        playChime={playChime}
      />,
    );
    expect(playChime).not.toHaveBeenCalled();
  });

  it('plays nothing while the title is still being checked', () => {
    const playChime = jest.fn();
    const { rerender } = render(
      <Harness
        mediaTimeMs={5_000}
        covered
        verified={false}
        playChime={playChime}
      />,
    );
    rerender(
      <Harness
        mediaTimeMs={8_000}
        covered
        verified={false}
        playChime={playChime}
      />,
    );
    expect(playChime).not.toHaveBeenCalled();
  });

  it('makes no sound of its own when nobody hands it one', () => {
    // The default is silence rather than a reach for an audio API that is not
    // there. The cue still runs, so the parent area's switch and the timing
    // are testable without a device.
    const { rerender } = render(
      <Harness mediaTimeMs={5_000} covered={false} playChime={undefined as never} />,
    );
    expect(() =>
      rerender(
        <Harness mediaTimeMs={8_000} covered={false} playChime={undefined as never} />,
      ),
    ).not.toThrow();
  });
});
