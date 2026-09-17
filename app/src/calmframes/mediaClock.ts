/**
 * Media clock: where the playhead is between timeupdate events.
 *
 * The cover has to be fully on before a flagged segment starts, and reacting
 * to `timeupdate` alone is too slow: it fires a few times a second at best, so
 * waiting for it would put the cover on late by up to that interval. Instead
 * the scheduler runs on a wall clock and re-syncs to media time whenever the
 * player tells us where it is.
 *
 * This module holds only the arithmetic, so it can be tested without a player:
 *
 *     sync(clock, mediaTimeMs, wallClockMs)   the player reported a position
 *     estimate(clock, wallClockMs)            where the playhead is now
 *
 * A paused or stalled clock does not advance. A playback rate of 2 advances
 * media time twice as fast as the wall clock.
 */

export interface MediaClock {
  /** Media time at the last sync, milliseconds. */
  anchorMediaMs: number;
  /** Wall clock at the last sync, milliseconds. */
  anchorWallMs: number;
  playbackRate: number;
  running: boolean;
}

export function createMediaClock(
  mediaTimeMs = 0,
  wallClockMs = 0,
  playbackRate = 1,
  running = false,
): MediaClock {
  return {
    anchorMediaMs: mediaTimeMs,
    anchorWallMs: wallClockMs,
    playbackRate,
    running,
  };
}

/** Record a position the player reported. */
export function sync(
  clock: MediaClock,
  mediaTimeMs: number,
  wallClockMs: number,
): MediaClock {
  return { ...clock, anchorMediaMs: mediaTimeMs, anchorWallMs: wallClockMs };
}

/** Start or stop the clock, re-anchoring so no media time is invented. */
export function setRunning(
  clock: MediaClock,
  running: boolean,
  wallClockMs: number,
): MediaClock {
  const anchorMediaMs = estimate(clock, wallClockMs);
  return { ...clock, running, anchorMediaMs, anchorWallMs: wallClockMs };
}

export function setPlaybackRate(
  clock: MediaClock,
  playbackRate: number,
  wallClockMs: number,
): MediaClock {
  const anchorMediaMs = estimate(clock, wallClockMs);
  return { ...clock, playbackRate, anchorMediaMs, anchorWallMs: wallClockMs };
}

/**
 * Estimated media time now.
 *
 * A stopped clock holds its position. A running clock advances by the elapsed
 * wall-clock time times the playback rate. The estimate never runs backwards
 * from the anchor, because a wall clock that jumps backwards would otherwise
 * uncover the picture.
 */
export function estimate(clock: MediaClock, wallClockMs: number): number {
  if (!clock.running) {
    return clock.anchorMediaMs;
  }
  const elapsed = Math.max(0, wallClockMs - clock.anchorWallMs);
  return clock.anchorMediaMs + elapsed * clock.playbackRate;
}

/**
 * How far the estimate was off when the player reported a real position.
 *
 * GATE 1 reports this as drift: it is the error the cover schedule inherits
 * from running ahead of the player, and it is what grows over a long title if
 * the wall clock and the media clock disagree.
 */
export function driftMs(
  clock: MediaClock,
  reportedMediaMs: number,
  wallClockMs: number,
): number {
  return estimate(clock, wallClockMs) - reportedMediaMs;
}
