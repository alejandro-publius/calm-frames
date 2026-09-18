/**
 * Tests for the cover schedule.
 *
 * Every assertion here has been seen to fail: each rule was broken on purpose
 * in coverSchedule.ts and the suite went red before the file was restored.
 */
import {
  buildCoverIntervals,
  DEFAULT_GUARD_BAND_MS,
  intervalAt,
  intervalForSeekTarget,
  isCovered,
  MAX_RENDITION_START_OFFSET_MS,
  millisecondsUntilNextCover,
  nextIntervalAfter,
  totalCoveredMs,
} from '../../src/calmframes/coverSchedule';

describe('the rendition start offset', () => {
  /**
   * The safety property: a hide never lands late because of the offset.
   *
   * The map describes the source. The player plays the rendition, whose first
   * presentation timestamp a re-encode routinely renumbers to zero, so a
   * picture at source time S arrives at rendition time S minus the offset.
   *
   * "Late" here does not mean the flashing was missed. With an offset smaller
   * than the guard band the cover still lands before the picture does, just
   * with less room than the band promised. That is the whole point: the band
   * has to absorb the scheduler as well, and a cover was already measured
   * going on 86 ms after its marker with the JavaScript thread away for about
   * 335 ms of it (results/gate1_software_vvd.json). So the property is stated
   * as lead time, not as coverage, and the offset is not allowed to eat any
   * of the band.
   */
  const segments = [
    { startMs: 10_000, endMs: 12_000 },
    { startMs: 30_000, endMs: 30_400 },
    { startMs: 61_250, endMs: 63_000 },
  ];

  it.each([0, 3, 67, 120, MAX_RENDITION_START_OFFSET_MS])(
    'keeps the full guard band ahead of the picture at an offset of %i ms',
    (offsetMs) => {
      const intervals = buildCoverIntervals(segments, {
        guardBandMs: DEFAULT_GUARD_BAND_MS,
        renditionStartOffsetMs: offsetMs,
      });

      for (const segment of segments) {
        // Where the picture actually arrives for the viewer.
        const arrivesAtMs = segment.startMs - offsetMs;
        const covering = intervalAt(intervals, arrivesAtMs);
        expect(covering).toBeDefined();
        const leadMs = arrivesAtMs - covering!.startMs;
        expect(leadMs).toBeGreaterThanOrEqual(DEFAULT_GUARD_BAND_MS);
      }
    },
  );

  it('still covers the whole segment, not just its start', () => {
    const offsetMs = 140;
    const intervals = buildCoverIntervals(segments, {
      guardBandMs: DEFAULT_GUARD_BAND_MS,
      renditionStartOffsetMs: offsetMs,
    });
    for (const segment of segments) {
      expect(isCovered(intervals, segment.startMs - offsetMs)).toBe(true);
      expect(isCovered(intervals, segment.endMs - offsetMs)).toBe(true);
    }
  });

  it('refuses an offset further than verify would ever publish', () => {
    expect(() =>
      buildCoverIntervals(segments, {
        renditionStartOffsetMs: MAX_RENDITION_START_OFFSET_MS + 1,
      }),
    ).toThrow(/further than verify allows/);
  });

  it('refuses an offset that is not a number', () => {
    expect(() =>
      buildCoverIntervals(segments, { renditionStartOffsetMs: Number.NaN }),
    ).toThrow(/finite/);
  });

  it('treats a missing offset as zero rather than guessing', () => {
    const without = buildCoverIntervals(segments, {});
    const withZero = buildCoverIntervals(segments, {
      renditionStartOffsetMs: 0,
    });
    expect(without).toEqual(withZero);
  });
});

describe('buildCoverIntervals', () => {
  it('widens a segment by the guard band on both sides', () => {
    const [interval] = buildCoverIntervals([{ startMs: 10_000, endMs: 12_000 }], {
      guardBandMs: 500,
    });
    expect(interval.startMs).toBe(9_500);
    expect(interval.endMs).toBe(12_500);
  });

  it('uses a 500 ms guard band by default', () => {
    const [interval] = buildCoverIntervals([{ startMs: 5_000, endMs: 6_000 }]);
    expect(DEFAULT_GUARD_BAND_MS).toBe(500);
    expect(interval.startMs).toBe(4_500);
    expect(interval.endMs).toBe(6_500);
  });

  it('merges intervals that overlap once the guard band is applied', () => {
    const intervals = buildCoverIntervals(
      [
        { startMs: 1_000, endMs: 2_000 },
        { startMs: 2_400, endMs: 3_000 },
      ],
      { guardBandMs: 500 },
    );
    expect(intervals).toHaveLength(1);
    expect(intervals[0].startMs).toBe(500);
    expect(intervals[0].endMs).toBe(3_500);
    expect(intervals[0].sources).toHaveLength(2);
  });

  it('merges intervals that touch exactly, so the cover cannot blink off', () => {
    // With a 500 ms guard band the first interval ends at 1500 and the second
    // starts at 1500. Treating that as a gap would lift the cover for a frame
    // between two hidden parts.
    const intervals = buildCoverIntervals(
      [
        { startMs: 0, endMs: 1_000 },
        { startMs: 2_000, endMs: 3_000 },
      ],
      { guardBandMs: 500 },
    );
    expect(intervals).toHaveLength(1);
    expect(intervals[0].startMs).toBe(0);
    expect(intervals[0].endMs).toBe(3_500);
  });

  it('keeps separate intervals that do not touch', () => {
    const intervals = buildCoverIntervals(
      [
        { startMs: 1_000, endMs: 2_000 },
        { startMs: 10_000, endMs: 11_000 },
      ],
      { guardBandMs: 500 },
    );
    expect(intervals).toHaveLength(2);
  });

  it('sorts segments given out of order', () => {
    const intervals = buildCoverIntervals(
      [
        { startMs: 10_000, endMs: 11_000 },
        { startMs: 1_000, endMs: 2_000 },
      ],
      { guardBandMs: 0 },
    );
    expect(intervals.map((i) => i.startMs)).toEqual([1_000, 10_000]);
  });

  it('makes a merged interval red when any part of it is red', () => {
    const [interval] = buildCoverIntervals(
      [
        { startMs: 1_000, endMs: 2_000, reason: 'general' },
        { startMs: 2_200, endMs: 2_600, reason: 'red' },
      ],
      { guardBandMs: 500 },
    );
    expect(interval.reason).toBe('red');
  });

  it('enforces a minimum cover length so the cover cannot flicker', () => {
    const [interval] = buildCoverIntervals([{ startMs: 1_000, endMs: 1_040 }], {
      guardBandMs: 0,
      minCoverMs: 400,
    });
    expect(interval.endMs - interval.startMs).toBeGreaterThanOrEqual(400);
  });

  it('never starts a cover later than the guard band promised', () => {
    const [interval] = buildCoverIntervals([{ startMs: 1_000, endMs: 1_040 }], {
      guardBandMs: 500,
      minCoverMs: 5_000,
    });
    // Growing to the minimum length must not push the start later.
    expect(interval.startMs).toBe(500);
  });

  it('clamps to the start of the media', () => {
    const [interval] = buildCoverIntervals([{ startMs: 100, endMs: 600 }], {
      guardBandMs: 500,
    });
    expect(interval.startMs).toBe(0);
  });

  it('clamps to the end of the media when a duration is given', () => {
    const [interval] = buildCoverIntervals([{ startMs: 9_000, endMs: 9_800 }], {
      guardBandMs: 500,
      durationMs: 10_000,
    });
    expect(interval.endMs).toBe(10_000);
  });

  it('ignores empty or reversed segments', () => {
    expect(
      buildCoverIntervals([
        { startMs: 5_000, endMs: 5_000 },
        { startMs: 8_000, endMs: 7_000 },
      ]),
    ).toEqual([]);
  });

  it('refuses a negative guard band', () => {
    expect(() =>
      buildCoverIntervals([{ startMs: 1_000, endMs: 2_000 }], {
        guardBandMs: -100,
      }),
    ).toThrow();
  });
});

describe('isCovered', () => {
  const intervals = buildCoverIntervals([{ startMs: 10_000, endMs: 12_000 }], {
    guardBandMs: 500,
  });

  it('covers the guard band before the flashing starts', () => {
    expect(isCovered(intervals, 9_600)).toBe(true);
  });

  it('covers the flagged segment itself', () => {
    expect(isCovered(intervals, 11_000)).toBe(true);
  });

  it('covers the guard band after the flashing ends', () => {
    expect(isCovered(intervals, 12_400)).toBe(true);
  });

  it('leaves the picture alone outside the interval', () => {
    expect(isCovered(intervals, 9_400)).toBe(false);
    expect(isCovered(intervals, 12_600)).toBe(false);
  });

  it('treats the interval as half open, so the cover lifts at the end', () => {
    expect(isCovered(intervals, 12_500)).toBe(false);
  });

  it('returns the interval that covers a time', () => {
    expect(intervalAt(intervals, 11_000)?.endMs).toBe(12_500);
    expect(intervalAt(intervals, 1_000)).toBeUndefined();
  });
});

describe('millisecondsUntilNextCover', () => {
  const intervals = buildCoverIntervals([{ startMs: 10_000, endMs: 12_000 }], {
    guardBandMs: 500,
  });

  it('counts down in wall-clock time at normal speed', () => {
    expect(millisecondsUntilNextCover(intervals, 8_000, 1)).toBe(1_500);
  });

  it('halves the wall-clock wait at double speed', () => {
    expect(millisecondsUntilNextCover(intervals, 8_000, 2)).toBe(750);
  });

  it('doubles the wall-clock wait at half speed', () => {
    expect(millisecondsUntilNextCover(intervals, 8_000, 0.5)).toBe(3_000);
  });

  it('says cover now when the time is already inside an interval', () => {
    expect(millisecondsUntilNextCover(intervals, 11_000, 1)).toBe(0);
  });

  it('returns undefined when playback is paused', () => {
    expect(millisecondsUntilNextCover(intervals, 8_000, 0)).toBeUndefined();
  });

  it('returns undefined when nothing is scheduled ahead', () => {
    expect(millisecondsUntilNextCover(intervals, 20_000, 1)).toBeUndefined();
  });

  it('finds the next interval after a time', () => {
    expect(nextIntervalAfter(intervals, 0)?.startMs).toBe(9_500);
    expect(nextIntervalAfter(intervals, 20_000)).toBeUndefined();
  });
});

describe('seek safety', () => {
  const intervals = buildCoverIntervals(
    [{ startMs: 10_000, endMs: 12_000, reason: 'red' }],
    { guardBandMs: 500 },
  );

  it('flags a seek target inside the flagged segment', () => {
    expect(intervalForSeekTarget(intervals, 11_000)).toBeDefined();
  });

  it('flags a seek target inside the guard band', () => {
    expect(intervalForSeekTarget(intervals, 9_700)).toBeDefined();
  });

  it('allows a seek target outside any interval', () => {
    expect(intervalForSeekTarget(intervals, 3_000)).toBeUndefined();
  });
});

describe('totalCoveredMs', () => {
  it('adds up what was hidden', () => {
    const intervals = buildCoverIntervals(
      [
        { startMs: 1_000, endMs: 2_000 },
        { startMs: 10_000, endMs: 11_000 },
      ],
      { guardBandMs: 500 },
    );
    expect(totalCoveredMs(intervals)).toBe(4_000);
  });
});
