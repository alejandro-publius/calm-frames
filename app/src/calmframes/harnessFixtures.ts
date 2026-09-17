/**
 * What the measurement runs play, and where the cover leaves the screen alone.
 *
 * Phase 1.5, the layering test, plays a real title with captions available, so
 * that the recording shows whether the cover hides the hardware video layer
 * while captions stay readable above it and audio keeps going. It reuses the
 * sample's own catalog entry for Cosmos Laundromat, a Blender open movie with
 * a subtitle track, rather than inventing a URL.
 *
 * GATE 1, the timing harness, needs the two-minute marker clip that
 * calm-timing generates: twenty gentle gray-to-white steps, no flashing, with
 * a schedule saying exactly when each marker appears. That kit is not in the
 * repo yet, so the schedule below is a placeholder. It exercises the harness
 * end to end, and it cannot produce a GATE 1 number, because the title it
 * plays has no markers at these times. Every harness-start log line says which
 * schedule it used.
 */

import { TitleData } from '../types/TitleData';
import { ReferencePatch } from './CoverLayer';
import { FlashSegment } from './coverSchedule';
import { getClassics } from '../data/local/classics';

/**
 * The area the cover leaves visible so the camera can tell a running screen
 * from a frozen one. When calm-timing arrives, this has to match the patch its
 * marker clip draws, or the harness will cover the patch it is meant to read.
 */
export const REFERENCE_PATCH_1080P: ReferencePatch = {
  x: 48,
  y: 48,
  width: 96,
  height: 96,
};

/** True while the timing schedule is the placeholder rather than the kit's. */
export const TIMING_SCHEDULE_IS_PLACEHOLDER = true;

/**
 * A title with a subtitle track, for the layering test.
 *
 * The first Classics entry is Cosmos Laundromat over HLS with an English
 * subtitle track, which is what the layering test needs: moving picture,
 * captions and sound.
 */
export function getLayeringTestTitle(): TitleData {
  return getClassics()[0];
}

/**
 * A title that plays one URL, for measurement runs.
 *
 * The marker clip lives on the machine running the run, not in a catalog, so
 * the harness needs a title it can build on the spot.
 */
export function makeUrlTitle(uri: string, format = 'MP4'): TitleData {
  return {
    id: 'calm-frames-harness',
    title: 'Calm Frames measurement run',
    description: 'Timing markers for a measurement run. Not a catalog title.',
    mediaType: 'video',
    mediaSourceType: 'url',
    duration: 120,
    thumbnail: '',
    posterUrl: '',
    uri,
    categories: ['Measurement'],
    channelID: 'harness',
    rating: '',
    format,
    uhd: false,
    secure: false,
    rentAmount: '0',
  } as unknown as TitleData;
}

/**
 * Placeholder cover schedule, in milliseconds of media time.
 *
 * Twenty one-second hides, six seconds apart, starting at ten seconds. The
 * shape matches what the marker clip will ask for, so the scheduler, the
 * logging and the camera workflow can all be exercised now. Replace this with
 * the schedule calm-timing emits before running GATE 1.
 */
export function getTimingHarnessSegments(): FlashSegment[] {
  const segments: FlashSegment[] = [];
  for (let index = 0; index < 20; index += 1) {
    const startMs = 10_000 + index * 6_000;
    segments.push({
      startMs,
      endMs: startMs + 1_000,
      reason: 'general',
      label: `placeholder marker ${index + 1}`,
    });
  }
  return segments;
}
