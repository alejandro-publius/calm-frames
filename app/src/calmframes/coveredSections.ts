/**
 * The covered sections of a title, for the Details page.
 *
 * One still picture and one sentence that say, before the video starts, where
 * the player will cover it and for how long. The schedule is the player's own:
 * buildCoverIntervals under this household's cover options for this title, so
 * the guard bands, the clamp to the running time and the merging of overlaps
 * are exactly what playback will do. Nothing here reads the detector's raw
 * numbers, and nothing here can move the playhead: it is a picture of the
 * schedule, not a control.
 *
 * Four answers, so a missing fact is shown as missing rather than drawn:
 *
 *   unavailable   the title has not verified, or carries no segment list
 *   no-duration   the running time is unknown, so nothing can be clamped or drawn
 *   none          verified, with a running time, and nothing to cover
 *   ready         the merged, clamped sections and their total
 */

import { benignStorySettings, isBundledBenignStory } from './benignStory';
import { describeHiddenTotal, runtimeLabel } from './copy';
import {
  buildCoverIntervals,
  CoverInterval,
  FlashSegment,
  totalCoveredMs,
} from './coverSchedule';
import { coverOptionsFor, HouseholdSettings } from './household';
import { CheckedTitle } from './titleStatus';

export type CoveredSectionsResult =
  | { kind: 'unavailable'; text: string }
  | { kind: 'no-duration'; text: string }
  | { kind: 'none'; durationMs: number; text: string }
  | {
      kind: 'ready';
      durationMs: number;
      sections: CoverInterval[];
      /** The total of the merged sections, so an overlap is never counted twice. */
      coveredMs: number;
      text: string;
    };

export const COVERED_SECTIONS_UNAVAILABLE =
  'Scene information is unavailable.';
export const COVERED_SECTIONS_NO_DURATION =
  'The video length is unknown, so the scene timeline is unavailable.';
export const COVERED_SECTIONS_NONE = 'No flagged scenes.';

/**
 * The sentence under the strip.
 *
 * Running time is already shown above. A total shorter than a second is said
 * as one second rather than none. Audio belongs in the optional explanation.
 */
export function coveredSectionsLine(
  count: number,
  coveredMs: number,
  _durationMs: number,
  demo: boolean,
): string {
  const noun = demo ? 'simulated pause' : 'scene';
  const covered = describeHiddenTotal(Math.max(coveredMs, 1000));
  return `${count} ${noun}${count === 1 ? '' : 's'} · ${covered}`;
}

export function coveredSections(
  entry: CheckedTitle,
  settings: HouseholdSettings,
): CoveredSectionsResult {
  const segments: unknown = entry.segments;
  if (entry.status !== 'verified' || !Array.isArray(segments)) {
    return { kind: 'unavailable', text: COVERED_SECTIONS_UNAVAILABLE };
  }
  const durationMs = entry.title.durationMs;
  if (durationMs === undefined || runtimeLabel(durationMs) === null) {
    return { kind: 'no-duration', text: COVERED_SECTIONS_NO_DURATION };
  }
  const sections = buildCoverIntervals(segments as FlashSegment[], {
    ...coverOptionsFor(benignStorySettings(entry.title, settings)),
    durationMs,
    renditionStartOffsetMs: entry.title.renditionStartOffsetMs,
  });
  if (sections.length === 0) {
    return { kind: 'none', durationMs, text: COVERED_SECTIONS_NONE };
  }
  const coveredMs = totalCoveredMs(sections);
  return {
    kind: 'ready',
    durationMs,
    sections,
    coveredMs,
    text: coveredSectionsLine(
      sections.length,
      coveredMs,
      durationMs,
      isBundledBenignStory(entry.title),
    ),
  };
}
