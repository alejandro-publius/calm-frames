/**
 * Cover schedule: when the picture must be hidden.
 *
 * This is the piece GATE 1 measures and the piece kid mode depends on, so it
 * is kept pure and free of React and of the media player. It answers three
 * questions from a flash map:
 *
 *   1. which spans of media time must be covered (segment plus guard band);
 *   2. whether a given media time falls inside one;
 *   3. how long until the next cover starts, so the countdown card and the
 *      cover itself can be scheduled ahead of time rather than reacted to.
 *
 * Times are milliseconds of media time unless a name says otherwise.
 *
 * Rules that must not drift (docs/BUILD_PROMPT.md phases 1.6 and 4.2):
 * - a guard band widens every interval on both sides, default 500 ms;
 * - overlapping intervals merge, so the cover never flickers off and on
 *   between two segments that nearly touch;
 * - every interval is at least minCoverMs long;
 * - a red segment is always opaque, and merging keeps that: if any part of a
 *   merged interval is red, the whole interval is red.
 */

/**
 * Why an interval is covered.
 *
 * `pattern` is the regular pattern rule, BT.1702-3 Guideline 2, and it is its
 * own class rather than a spelling of `red`. It has to be opaque like red, and
 * it is not a red flash: a title with a pattern and no red flashing should not
 * be recorded, coloured or reported as having red flashing.
 */
export type CoverReason = 'general' | 'red' | 'pattern';

export interface FlashSegment {
  /** Start of the flagged segment in media time, milliseconds. */
  startMs: number;
  /** End of the flagged segment in media time, milliseconds. */
  endMs: number;
  /**
   * WCAG's red rule keys on the red to total ratio, which dimming does not
   * change, so red segments are always covered opaque.
   */
  reason?: CoverReason;
  /** Optional label, used by the card that says what was hidden. */
  label?: string;
}

export interface CoverInterval {
  startMs: number;
  endMs: number;
  reason: CoverReason;
  /** The segments that produced this interval, before merging. */
  sources: FlashSegment[];
}

export interface CoverScheduleOptions {
  /** Cover this much before and after each segment. */
  guardBandMs?: number;
  /** Never cover for less than this, so the cover cannot flicker. */
  minCoverMs?: number;
  /** Total media duration, used to clamp the last interval. */
  durationMs?: number;
  /**
   * How far the rendition's timeline sits from the source's, milliseconds.
   *
   * The map always describes the source file, because that is what was
   * analyzed. The player plays the rendition, and a re-encode routinely
   * renumbers the first presentation timestamp to zero while leaving every
   * picture where it was. So a picture at source time S arrives at rendition
   * time S minus this offset, and a schedule that ignored it would put every
   * cover that much late.
   *
   * `pipeline/verify.py` measures it per preset and records it as
   * `rendition_start_offset_ms`. Passing it here is what stops it costing the
   * guard band anything.
   */
  renditionStartOffsetMs?: number;
}

export const DEFAULT_GUARD_BAND_MS = 500;
export const DEFAULT_MIN_COVER_MS = 400;

/**
 * The most the rendition's timeline may sit from the source's before this
 * refuses to build a schedule at all.
 *
 * `pipeline/verify.py` will not publish a title whose offset is larger than
 * this, so an offset above it means the map and the file disagree about
 * something. There is no safe schedule to build from that, and guessing would
 * put covers in the wrong places, so it throws and the caller's fail closed
 * path keeps the picture hidden. Kept in step with START_OFFSET_LIMIT_MS in
 * pipeline/verify.py.
 */
export const MAX_RENDITION_START_OFFSET_MS = 150;

/**
 * Turn flagged segments into the intervals the player must cover.
 *
 * Widens by the guard band, clamps to the media, enforces a minimum length,
 * then merges anything that overlaps or touches. Input order does not matter.
 */
export function buildCoverIntervals(
  segments: FlashSegment[],
  options: CoverScheduleOptions = {},
): CoverInterval[] {
  const guardBandMs = options.guardBandMs ?? DEFAULT_GUARD_BAND_MS;
  const minCoverMs = options.minCoverMs ?? DEFAULT_MIN_COVER_MS;
  const durationMs = options.durationMs;

  if (guardBandMs < 0) {
    throw new Error('guardBandMs cannot be negative');
  }

  const offsetMs = options.renditionStartOffsetMs ?? 0;
  if (!Number.isFinite(offsetMs)) {
    throw new Error('renditionStartOffsetMs must be a finite number');
  }
  if (Math.abs(offsetMs) > MAX_RENDITION_START_OFFSET_MS) {
    throw new Error(
      `renditionStartOffsetMs of ${offsetMs} ms is further than verify allows ` +
        `(${MAX_RENDITION_START_OFFSET_MS} ms), so the map and the file disagree`,
    );
  }

  const widened: CoverInterval[] = segments
    .filter((segment) => segment.endMs > segment.startMs)
    .map((segment) => {
      // Move the segment onto the rendition's timeline before widening, so the
      // guard band is measured from where the picture actually arrives rather
      // than from where the source had it. Both ends shift together, so the
      // span is unchanged.
      let startMs = segment.startMs - offsetMs - guardBandMs;
      let endMs = segment.endMs - offsetMs + guardBandMs;

      // Enforce the minimum length by growing the end, then the start, so a
      // cover never starts later than the guard band promised.
      if (endMs - startMs < minCoverMs) {
        endMs = startMs + minCoverMs;
      }
      if (startMs < 0) {
        startMs = 0;
      }
      if (durationMs !== undefined && endMs > durationMs) {
        endMs = durationMs;
      }

      return {
        startMs,
        endMs,
        reason: segment.reason ?? 'general',
        sources: [segment],
      };
    })
    .filter((interval) => interval.endMs > interval.startMs)
    .sort((a, b) => a.startMs - b.startMs);

  const merged: CoverInterval[] = [];
  for (const interval of widened) {
    const previous = merged[merged.length - 1];
    if (previous && interval.startMs <= previous.endMs) {
      previous.endMs = Math.max(previous.endMs, interval.endMs);
      // Any red part makes the whole merged interval red, because a dim cover
      // would not satisfy the red rule for that part.
      // Strength wins when two intervals merge, and red is the strongest. A
      // pattern merged with a general flash stays a pattern, so the merged
      // interval keeps the opaque cover the pattern needs.
      if (interval.reason === 'red') {
        previous.reason = 'red';
      } else if (interval.reason === 'pattern' && previous.reason !== 'red') {
        previous.reason = 'pattern';
      }
      previous.sources.push(...interval.sources);
      continue;
    }
    merged.push({ ...interval, sources: [...interval.sources] });
  }

  return merged;
}

/** The interval covering this media time, or undefined if the picture is safe. */
export function intervalAt(
  intervals: CoverInterval[],
  mediaTimeMs: number,
): CoverInterval | undefined {
  return intervals.find(
    (interval) => mediaTimeMs >= interval.startMs && mediaTimeMs < interval.endMs,
  );
}

export function isCovered(
  intervals: CoverInterval[],
  mediaTimeMs: number,
): boolean {
  return intervalAt(intervals, mediaTimeMs) !== undefined;
}

/** The first interval that starts at or after this media time. */
export function nextIntervalAfter(
  intervals: CoverInterval[],
  mediaTimeMs: number,
): CoverInterval | undefined {
  return intervals.find((interval) => interval.startMs >= mediaTimeMs);
}

/**
 * How long until the cover must be on, in wall-clock milliseconds.
 *
 * Media time and wall-clock time only run at the same rate when the playback
 * rate is 1, so the scheduler converts. Returns undefined when nothing is
 * scheduled ahead, and 0 when the cover is due now.
 */
export function millisecondsUntilNextCover(
  intervals: CoverInterval[],
  mediaTimeMs: number,
  playbackRate = 1,
): number | undefined {
  if (isCovered(intervals, mediaTimeMs)) {
    return 0;
  }
  const next = nextIntervalAfter(intervals, mediaTimeMs);
  if (!next) {
    return undefined;
  }
  if (playbackRate <= 0) {
    // Paused or stalled media never reaches the interval on its own.
    return undefined;
  }
  return Math.max(0, (next.startMs - mediaTimeMs) / playbackRate);
}

/**
 * Where a seek should be treated as landing.
 *
 * Seeking into an interval, or into its guard band, must cover first and only
 * then move the playhead, so this returns the interval a target lands in.
 */
export function intervalForSeekTarget(
  intervals: CoverInterval[],
  targetMs: number,
): CoverInterval | undefined {
  return intervalAt(intervals, targetMs);
}

/** Total covered milliseconds, for the card that says what was hidden. */
export function totalCoveredMs(intervals: CoverInterval[]): number {
  return intervals.reduce(
    (total, interval) => total + (interval.endMs - interval.startMs),
    0,
  );
}
