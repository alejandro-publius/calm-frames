/**
 * Timing log for the layering test and GATE 1.
 *
 * Amazon does not document how often `timeupdate` fires on Vega or how precise
 * `currentTime` is, so we measure it instead of assuming. Every line pairs
 * media time with wall-clock time, which is what lets the camera recordings be
 * lined up against what the app believed it was doing.
 *
 * Lines are printed with console.info, because release builds strip
 * console.log but keep info, and they carry a fixed prefix so the device log
 * can be filtered with:
 *
 *     vega device start-log-stream | grep CALM_TIMING
 */

export const TIMING_LOG_PREFIX = 'CALM_TIMING';

export type TimingEventKind =
  | 'harness-start'
  | 'harness-stop'
  | 'timeupdate'
  | 'seeking'
  | 'seeked'
  | 'waiting'
  | 'stalled'
  | 'pause'
  | 'playing'
  | 'ratechange'
  | 'ended'
  | 'error'
  | 'cover-on'
  | 'cover-off'
  | 'background'
  | 'foreground';

export interface PlaybackQualitySnapshot {
  droppedVideoFrames?: number;
  totalVideoFrames?: number;
  corruptedVideoFrames?: number;
}

export interface TimingEvent {
  kind: TimingEventKind;
  /** Wall clock, milliseconds since the epoch, taken as close to the event as possible. */
  wallClockMs: number;
  /** Media time in milliseconds, or null when there is no media element yet. */
  mediaTimeMs: number | null;
  covered: boolean;
  playbackRate?: number;
  /** Why the cover went on or off, for the cover events. */
  reason?: string;
  quality?: PlaybackQualitySnapshot;
  extra?: Record<string, string | number | boolean | null>;
}

/**
 * Read the frame counters the W3C media element exposes, if it has them.
 *
 * getVideoPlaybackQuality is optional in the W3C spec and we have not
 * confirmed it exists on Vega, so treat a missing function as normal rather
 * than an error.
 */
export function readPlaybackQuality(
  element: unknown,
): PlaybackQualitySnapshot | undefined {
  const candidate = element as
    | { getVideoPlaybackQuality?: () => PlaybackQualitySnapshot }
    | null
    | undefined;
  if (!candidate || typeof candidate.getVideoPlaybackQuality !== 'function') {
    return undefined;
  }
  try {
    const quality = candidate.getVideoPlaybackQuality();
    return {
      droppedVideoFrames: quality?.droppedVideoFrames,
      totalVideoFrames: quality?.totalVideoFrames,
      corruptedVideoFrames: quality?.corruptedVideoFrames,
    };
  } catch {
    return undefined;
  }
}

/** Format one event as a single line, so the log stays grep-friendly. */
export function formatTimingEvent(event: TimingEvent): string {
  return `${TIMING_LOG_PREFIX} ${JSON.stringify(event)}`;
}

export function logTimingEvent(event: TimingEvent): void {
  console.info(formatTimingEvent(event));
}
