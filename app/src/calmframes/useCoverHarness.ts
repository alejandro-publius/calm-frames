/**
 * Drives the cover, and records what it did.
 *
 * Two modes:
 *
 * - "layering" is the phase 1.5 check. It toggles a full-screen cover every
 *   five seconds over a playing title. What we are checking is whether the
 *   cover really hides the hardware video layer, whether captions stay
 *   readable above it and whether audio keeps going.
 *
 * - "timing" is the GATE 1 harness. It drives the cover from a schedule, on a
 *   wall clock re-synced to media time at every timeupdate, so the cover is
 *   on before the marker rather than after it.
 *
 * In both modes every transition is logged with media time and wall-clock time
 * so the camera recordings can be lined up against what the app believed.
 *
 * Fail safe while measuring: anything that makes the playhead uncertain, which
 * means seeking, buffering, stalling, pausing or the app going to the
 * background, puts the cover on and keeps it on until playback is confirmed
 * outside an interval again.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  CoverInterval,
  intervalAt,
  isCovered,
} from './coverSchedule';
import {
  createMediaClock,
  driftMs as clockDrift,
  estimate,
  MediaClock,
  setPlaybackRate,
  setRunning,
  sync,
} from './mediaClock';
import {
  beacon,
  getTimingSink,
  logTimingEvent,
  readPlaybackQuality,
  TimingEventKind,
} from './timingLog';

export type HarnessMode = 'off' | 'layering' | 'timing';

export interface CoverHarnessOptions {
  mode: HarnessMode;
  /** Timing mode: the intervals to cover, already widened and merged. */
  intervals?: CoverInterval[];
  /** Layering mode: how often to toggle, milliseconds. */
  toggleEveryMs?: number;
  /** How often the scheduler re-checks, milliseconds. */
  tickMs?: number;
  /** Set false when the app goes to the background. */
  foreground?: boolean;
  /** Which schedule this run used, recorded in the harness-start line. */
  scheduleLabel?: string;
  /**
   * True once the media element exists.
   *
   * The player is created after the screen mounts, so at mount the ref is
   * still null. Without this the harness would attach its listeners to
   * nothing and never try again, which is how a run produced no events at all
   * on the virtual device.
   */
  ready?: boolean;
}

export interface CoverHarnessState {
  covered: boolean;
  /** Estimated media time, milliseconds. */
  mediaTimeMs: number;
  /** Largest difference seen between the estimate and a reported position. */
  worstDriftMs: number;
  reason: string;
}

/** Minimal shape we need from the W3C media element. */
export interface MediaElementLike {
  currentTime?: number;
  playbackRate?: number;
  paused?: boolean;
  addEventListener?: (type: string, listener: () => void) => void;
  removeEventListener?: (type: string, listener: () => void) => void;
}

const MEDIA_EVENTS: TimingEventKind[] = [
  'timeupdate',
  'seeking',
  'seeked',
  'waiting',
  'stalled',
  'pause',
  'playing',
  'ratechange',
  'ended',
  'error',
];

/** Events after which the playhead is not trustworthy, so cover and hold. */
const UNCERTAIN_EVENTS = new Set<TimingEventKind>([
  'seeking',
  'waiting',
  'stalled',
  'pause',
  'error',
]);

export const DEFAULT_TOGGLE_MS = 5_000;
export const DEFAULT_TICK_MS = 50;

export function useCoverHarness(
  mediaRef: { current: MediaElementLike | null },
  options: CoverHarnessOptions,
): CoverHarnessState {
  const {
    mode,
    intervals = [],
    toggleEveryMs = DEFAULT_TOGGLE_MS,
    tickMs = DEFAULT_TICK_MS,
    foreground = true,
    scheduleLabel = 'none',
    ready = true,
  } = options;

  const [state, setState] = useState<CoverHarnessState>({
    covered: false,
    mediaTimeMs: 0,
    worstDriftMs: 0,
    reason: 'idle',
  });

  const clockRef = useRef<MediaClock>(createMediaClock(0, Date.now(), 1, false));
  const uncertainRef = useRef<boolean>(false);
  const coveredRef = useRef<boolean>(false);
  const worstDriftRef = useRef<number>(0);
  // The schedule is read through a ref so that a caller passing a fresh array
  // on every render does not restart the scheduler. It used to: the default
  // empty array was a new object each render, so the first cover caused a
  // re-render, which restarted the run clock, which turned the cover straight
  // back off.
  const intervalsRef = useRef<CoverInterval[]>(intervals);
  intervalsRef.current = intervals;
  const startedAtRef = useRef<number | null>(null);

  const applyCover = useCallback(
    (nextCovered: boolean, reason: string, mediaTimeMs: number) => {
      if (coveredRef.current === nextCovered) {
        return;
      }
      coveredRef.current = nextCovered;
      logTimingEvent({
        kind: nextCovered ? 'cover-on' : 'cover-off',
        wallClockMs: Date.now(),
        mediaTimeMs,
        covered: nextCovered,
        reason,
        playbackRate: clockRef.current.playbackRate,
        quality: readPlaybackQuality(mediaRef.current),
      });
      setState((previous) => ({
        ...previous,
        covered: nextCovered,
        mediaTimeMs,
        reason,
      }));
    },
    [mediaRef],
  );

  // Media events: keep the clock honest and log every one of them.
  useEffect(() => {
    if (mode === 'off') {
      return;
    }
    const element = mediaRef.current;
    beacon('harness.attach', {
      mode,
      ready,
      hasElement: Boolean(element),
      canListen: Boolean(element?.addEventListener),
      sink: getTimingSink(),
    });
    if (!element?.addEventListener) {
      return;
    }

    const listeners: Array<[string, () => void]> = [];

    const handle = (kind: TimingEventKind) => () => {
      const wallClockMs = Date.now();
      const reportedMs =
        typeof element.currentTime === 'number' ? element.currentTime * 1000 : null;

      if (reportedMs !== null) {
        const drift = clockDrift(clockRef.current, reportedMs, wallClockMs);
        if (Math.abs(drift) > Math.abs(worstDriftRef.current)) {
          worstDriftRef.current = drift;
        }
        clockRef.current = sync(clockRef.current, reportedMs, wallClockMs);
      }

      if (typeof element.playbackRate === 'number') {
        clockRef.current = setPlaybackRate(
          clockRef.current,
          element.playbackRate,
          wallClockMs,
        );
      }

      if (kind === 'playing' || kind === 'seeked' || kind === 'timeupdate') {
        clockRef.current = setRunning(clockRef.current, true, wallClockMs);
      }
      if (kind === 'pause' || kind === 'ended' || kind === 'stalled') {
        clockRef.current = setRunning(clockRef.current, false, wallClockMs);
      }

      if (UNCERTAIN_EVENTS.has(kind)) {
        uncertainRef.current = true;
        if (mode === 'timing') {
          applyCover(true, kind, reportedMs ?? clockRef.current.anchorMediaMs);
        }
      }
      if (kind === 'playing' || kind === 'seeked') {
        uncertainRef.current = false;
      }

      logTimingEvent({
        kind,
        wallClockMs,
        mediaTimeMs: reportedMs,
        covered: coveredRef.current,
        playbackRate: clockRef.current.playbackRate,
        quality: kind === 'timeupdate' ? readPlaybackQuality(element) : undefined,
        extra: { worstDriftMs: Math.round(worstDriftRef.current) },
      });
    };

    for (const kind of MEDIA_EVENTS) {
      const listener = handle(kind);
      listeners.push([kind, listener]);
      element.addEventListener?.(kind, listener);
    }

    logTimingEvent({
      kind: 'harness-start',
      wallClockMs: Date.now(),
      mediaTimeMs: null,
      covered: false,
      extra: {
        mode,
        intervals: intervals.length,
        toggleEveryMs,
        tickMs,
        scheduleLabel,
      },
    });

    return () => {
      for (const [kind, listener] of listeners) {
        element.removeEventListener?.(kind, listener);
      }
      logTimingEvent({
        kind: 'harness-stop',
        wallClockMs: Date.now(),
        mediaTimeMs: null,
        covered: coveredRef.current,
        extra: { mode },
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, mediaRef, applyCover, ready]);

  // A new mode is a new run, so the toggle clock starts again.
  useEffect(() => {
    startedAtRef.current = null;
  }, [mode]);

  // The app going to the background hides the picture at once.
  useEffect(() => {
    if (mode === 'timing' && !foreground) {
      applyCover(true, 'background', clockRef.current.anchorMediaMs);
    }
  }, [foreground, mode, applyCover]);

  // The scheduler itself.
  useEffect(() => {
    if (mode === 'off') {
      return;
    }

    if (startedAtRef.current === null) {
      startedAtRef.current = Date.now();
    }
    const startedAt = startedAtRef.current;

    const tick = () => {
      const wallClockMs = Date.now();
      const mediaTimeMs = estimate(clockRef.current, wallClockMs);

      if (mode === 'layering') {
        // Toggle on a wall clock, so the recording has a known cadence even if
        // the player never reports a position.
        const elapsed = wallClockMs - startedAt;
        const shouldCover =
          Math.floor(elapsed / toggleEveryMs) % 2 === 1;
        applyCover(shouldCover, 'layering-toggle', mediaTimeMs);
        return;
      }

      if (!foreground || uncertainRef.current) {
        applyCover(true, uncertainRef.current ? 'uncertain' : 'background', mediaTimeMs);
        return;
      }

      const covering = isCovered(intervalsRef.current, mediaTimeMs);
      const interval = intervalAt(intervalsRef.current, mediaTimeMs);
      applyCover(
        covering,
        covering ? `interval ${interval?.startMs}-${interval?.endMs}` : 'clear',
        mediaTimeMs,
      );
      setState((previous) =>
        previous.mediaTimeMs === mediaTimeMs
          ? previous
          : {
              ...previous,
              mediaTimeMs,
              worstDriftMs: worstDriftRef.current,
            },
      );
    };

    const handle = setInterval(tick, tickMs);
    tick();
    return () => clearInterval(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, toggleEveryMs, tickMs, foreground, applyCover]);

  return state;
}
