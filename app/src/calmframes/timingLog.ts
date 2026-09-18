/**
 * Timing log for the layering test and GATE 1.
 *
 * Amazon does not document how often `timeupdate` fires on Vega or how precise
 * `currentTime` is, so we measure it instead of assuming. Every line pairs
 * media time with wall-clock time, which is what lets the camera recordings be
 * lined up against what the app believed it was doing.
 *
 * Lines are printed with console.warn. Release builds strip console.log but
 * keep warn, and, more to the point, the device suppresses info level logs
 * under load: a run on the virtual device lost every info line to
 * "Log suppression ended at level [info]. [140] logs were suppressed". A
 * measurement whose evidence can be dropped by a log rate limiter is not a
 * measurement. They carry a fixed prefix so the device log can be filtered
 * with:
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

/**
 * Where events are sent, when a measurement run gives us somewhere to send
 * them.
 *
 * The device log cannot be trusted with this. On the virtual device every
 * console line from the app was dropped, with the device reporting
 * "Log suppression ended at level [info]. [140] logs were suppressed", and
 * nothing the app printed survived. So during a run the harness posts its
 * events straight to the machine running the run, and the log stays a
 * convenience rather than the evidence.
 *
 * Events are batched, because one request per timeupdate would change the
 * thing we are measuring.
 */
let sinkUrl: string | null = null;
let pending: TimingEvent[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * A one line beacon, used while bringing a device up.
 *
 * The device drops the app's console output, so when a run does not start
 * there is otherwise no way to tell whether the app's JavaScript ran at all.
 * Debug builds only.
 */
let beaconEnabled = true;

/**
 * Turn the beacon off.
 *
 * jest.setup.ts calls this, because a unit test has no business opening a
 * socket to the machine that ran it. Nothing else should.
 */
export function setBeaconEnabled(enabled: boolean): void {
  beaconEnabled = enabled;
}

export function beacon(where: string, detail: Record<string, unknown> = {}): void {
  if (!beaconEnabled) {
    return;
  }
  if (typeof __DEV__ === 'undefined' || !__DEV__) {
    return;
  }
  try {
    // The catch has to be on the promise, not just around the call. A
    // rejected fetch with no handler is an unhandled rejection, which is
    // noise on a device and a failed run under jest.
    void fetch('http://10.0.2.2:8000/beacon', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ where, at: Date.now(), ...detail }),
    }).catch(() => {
      // Nothing listening, which is the normal case.
    });
  } catch {
    // fetch itself missing, which is also fine.
  }
}

export function setTimingSink(url: string | null): void {
  sinkUrl = url;
  if (!url) {
    pending = [];
  }
}

export function getTimingSink(): string | null {
  return sinkUrl;
}

async function postBatch(batch: TimingEvent[], url: string): Promise<void> {
  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(batch),
    });
  } catch {
    // A run continues even if the collector is not listening. The events are
    // dropped rather than retried, so a slow collector cannot back up and
    // change the timing we are measuring.
  }
}

/** Send anything buffered now. Called on harness-stop and on a timer. */
export function flushTimingEvents(): void {
  if (flushTimer) {
    clearTimeout(flushTimer);
    flushTimer = null;
  }
  if (!sinkUrl || pending.length === 0) {
    return;
  }
  const batch = pending;
  pending = [];
  void postBatch(batch, sinkUrl).catch(() => {
    // postBatch already swallows its own errors; this is belt and braces so a
    // collector that vanishes mid run cannot produce an unhandled rejection.
  });
}

export function logTimingEvent(event: TimingEvent): void {
  console.warn(formatTimingEvent(event));
  if (!sinkUrl) {
    return;
  }
  pending.push(event);
  // Send at once for the events that bracket a run or change what is on
  // screen, and batch the rest.
  if (
    event.kind === 'harness-start' ||
    event.kind === 'harness-stop' ||
    event.kind === 'cover-on' ||
    event.kind === 'cover-off' ||
    pending.length >= 25
  ) {
    flushTimingEvents();
    return;
  }
  if (!flushTimer) {
    flushTimer = setTimeout(flushTimingEvents, 1000);
  }
}
