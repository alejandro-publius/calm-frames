/**
 * Tests for the media clock.
 *
 * Every assertion here was seen to fail: each rule was broken on purpose in
 * mediaClock.ts and the suite went red before the file was restored.
 */
import {
  createMediaClock,
  driftMs,
  estimate,
  setPlaybackRate,
  setRunning,
  sync,
} from '../../src/calmframes/mediaClock';

describe('estimate', () => {
  it('holds position while the clock is stopped', () => {
    const clock = createMediaClock(5_000, 1_000, 1, false);
    expect(estimate(clock, 9_000)).toBe(5_000);
  });

  it('advances with the wall clock while running', () => {
    const clock = createMediaClock(5_000, 1_000, 1, true);
    expect(estimate(clock, 3_000)).toBe(7_000);
  });

  it('advances twice as fast at double speed', () => {
    const clock = createMediaClock(5_000, 1_000, 2, true);
    expect(estimate(clock, 3_000)).toBe(9_000);
  });

  it('advances half as fast at half speed', () => {
    const clock = createMediaClock(5_000, 1_000, 0.5, true);
    expect(estimate(clock, 3_000)).toBe(6_000);
  });

  it('never runs backwards when the wall clock jumps back', () => {
    const clock = createMediaClock(5_000, 10_000, 1, true);
    expect(estimate(clock, 9_000)).toBe(5_000);
  });
});

describe('sync', () => {
  it('re-anchors to the position the player reported', () => {
    let clock = createMediaClock(5_000, 1_000, 1, true);
    clock = sync(clock, 4_800, 2_000);
    expect(estimate(clock, 2_000)).toBe(4_800);
  });
});

describe('setRunning', () => {
  it('keeps the position reached so far when pausing', () => {
    let clock = createMediaClock(5_000, 1_000, 1, true);
    clock = setRunning(clock, false, 3_000);
    expect(estimate(clock, 60_000)).toBe(7_000);
  });

  it('starts counting from the paused position when resuming', () => {
    let clock = createMediaClock(7_000, 3_000, 1, false);
    clock = setRunning(clock, true, 20_000);
    expect(estimate(clock, 21_000)).toBe(8_000);
  });
});

describe('setPlaybackRate', () => {
  it('does not lose the media time already played', () => {
    let clock = createMediaClock(5_000, 1_000, 1, true);
    clock = setPlaybackRate(clock, 2, 3_000);
    // 2 seconds played at 1x, then 1 second at 2x.
    expect(estimate(clock, 4_000)).toBe(9_000);
  });
});

describe('driftMs', () => {
  it('is zero when the estimate matches the player', () => {
    const clock = createMediaClock(5_000, 1_000, 1, true);
    expect(driftMs(clock, 7_000, 3_000)).toBe(0);
  });

  it('is positive when the estimate has run ahead of the player', () => {
    const clock = createMediaClock(5_000, 1_000, 1, true);
    expect(driftMs(clock, 6_800, 3_000)).toBe(200);
  });

  it('is negative when the estimate is behind the player', () => {
    const clock = createMediaClock(5_000, 1_000, 1, true);
    expect(driftMs(clock, 7_200, 3_000)).toBe(-200);
  });
});
