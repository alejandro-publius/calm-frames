/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * One way to move the playhead.
 *
 * docs/BUILD_PROMPT.md 4.4: every way of moving the playhead goes through one
 * function, and the rule is
 *
 *     if a target lands inside an interval or its guard band, cover first,
 *     then seek, and keep the cover until playback is confirmed outside the
 *     interval.
 *
 * All playhead moves call `requestSeek`, including explicit recovery:
 *
 *   seek-bar          the focused seek bar (Vega does not let an app override
 *                     D-pad focus movement, so the bar takes focus and the
 *                     left and right keys move it)
 *   dpad-fast-forward and
 *   dpad-rewind       the transport keys on the remote
 *   trickplay         scrubbing with BIF previews, which come only from the
 *                     safe rendition
 *   media-control     Alexa and the remote's transport commands arriving
 *                     through Vega Media Controls
 *
 * Two things here are engineering numbers rather than thresholds from a spec,
 * and both only ever add cover:
 *
 * - `keyframeLookbackMs`. A seek decodes from the keyframe at or before the
 *   target, so a target just past the end of an interval can still show a
 *   frame from inside it. Anything within this much before the target counts
 *   as landing inside.
 * - `confirmOutsideMs`. After the seek, the cover comes off only once the
 *   player has reported a position this far outside the interval, so a report
 *   that arrives while the playhead is still settling cannot uncover it.
 */

import {
  CoverInterval,
  intervalAt,
  intervalForSeekTarget,
} from './coverSchedule';

export type SeekSource =
  | 'seek-bar'
  | 'dpad-fast-forward'
  | 'dpad-rewind'
  | 'trickplay'
  | 'media-control'
  | 'recovery';

export const SEEK_SOURCES: SeekSource[] = [
  'seek-bar',
  'dpad-fast-forward',
  'dpad-rewind',
  'trickplay',
  'media-control',
  'recovery',
];

/** A typical closed group of pictures is about two seconds. */
export const DEFAULT_KEYFRAME_LOOKBACK_MS = 2_000;
export const DEFAULT_CONFIRM_OUTSIDE_MS = 250;

export interface SeekPlan {
  source: SeekSource;
  /** Where the caller asked to go, before clamping. */
  requestedMs: number;
  /** Where the seek will actually go. */
  targetMs: number;
  /** True when the cover has to be on before the seek is issued. */
  coverFirst: boolean;
  /** The interval the target lands in or decodes from, when there is one. */
  interval?: CoverInterval;
  reason: string;
}

export interface SeekEngineOptions {
  keyframeLookbackMs?: number;
  confirmOutsideMs?: number;
}

export interface SeekEngineDeps {
  /** The merged cover schedule, read fresh on every call. */
  getIntervals: () => CoverInterval[];
  /** Media duration in milliseconds, when it is known. */
  getDurationMs?: () => number | undefined;
  /** Turn the cover on or off. The engine never touches the view directly. */
  setCover: (covered: boolean, reason: string) => void;
  /** Move the playhead. Called only after the cover is on, when it has to be. */
  seekTo: (targetMs: number) => void | Promise<void>;
  /** Optional: say what happened, for VoiceView. */
  announce?: (text: string) => void;
  /** Optional: record the decision. */
  onPlan?: (plan: SeekPlan) => void;
}

export interface SeekEngine {
  /** The one function. Every seek path calls this. */
  requestSeek: (source: SeekSource, targetMs: number) => Promise<SeekPlan>;
  /**
   * A position the player reported. Releases a held cover only once the
   * playhead is confirmed outside the interval that was seeked into.
   */
  notePlayback: (mediaTimeMs: number) => void;
  /** True while the cover is held because of a seek. */
  isHolding: () => boolean;
  /** The interval the cover is being held for, if any. */
  heldInterval: () => CoverInterval | undefined;
}

/**
 * Work out what a seek to this target means, without doing it.
 *
 * Exported on its own because the countdown card, the seek bar's preview and
 * the tests all want the decision without the side effects.
 */
export function planSeek(
  source: SeekSource,
  requestedMs: number,
  intervals: CoverInterval[],
  options: SeekEngineOptions & { durationMs?: number } = {},
): SeekPlan {
  const lookbackMs = options.keyframeLookbackMs ?? DEFAULT_KEYFRAME_LOOKBACK_MS;
  const durationMs = options.durationMs;

  let targetMs = Number.isFinite(requestedMs) ? requestedMs : 0;
  if (targetMs < 0) {
    targetMs = 0;
  }
  if (durationMs !== undefined && targetMs > durationMs) {
    targetMs = durationMs;
  }

  const landing = intervalForSeekTarget(intervals, targetMs);
  if (landing) {
    return {
      source,
      requestedMs,
      targetMs,
      coverFirst: true,
      interval: landing,
      reason: `target ${Math.round(targetMs)} is inside ${landing.startMs}-${
        landing.endMs
      }`,
    };
  }

  // A seek decodes from the keyframe at or before the target, so an interval
  // that ended a moment before the target can still be on screen.
  const decodesFrom = intervals.find(
    (interval) =>
      interval.endMs <= targetMs && targetMs - interval.endMs < lookbackMs,
  );
  if (decodesFrom) {
    return {
      source,
      requestedMs,
      targetMs,
      coverFirst: true,
      interval: decodesFrom,
      reason: `target ${Math.round(targetMs)} decodes from inside ${
        decodesFrom.startMs
      }-${decodesFrom.endMs}`,
    };
  }

  return {
    source,
    requestedMs,
    targetMs,
    coverFirst: false,
    reason: `target ${Math.round(targetMs)} is clear`,
  };
}

/** Wording for the announcement a seek makes, or null when it says nothing. */
export function seekAnnouncement(plan: SeekPlan): string | null {
  if (!plan.coverFirst || !plan.interval) {
    return null;
  }
  return 'Moved into a flashing part. The picture is hidden until it is over.';
}

export function createSeekEngine(
  deps: SeekEngineDeps,
  options: SeekEngineOptions = {},
): SeekEngine {
  const confirmOutsideMs =
    options.confirmOutsideMs ?? DEFAULT_CONFIRM_OUTSIDE_MS;
  let held: CoverInterval | undefined;

  const requestSeek = async (
    source: SeekSource,
    requestedMs: number,
  ): Promise<SeekPlan> => {
    const intervals = deps.getIntervals();
    const plan = planSeek(source, requestedMs, intervals, {
      ...options,
      durationMs: deps.getDurationMs?.(),
    });
    deps.onPlan?.(plan);

    if (plan.coverFirst && plan.interval) {
      // Cover, then seek. Never the other way round: the first frame after a
      // seek can be on screen before any event tells us the seek happened.
      held = plan.interval;
      deps.setCover(true, `seek ${source}: ${plan.reason}`);
      const text = seekAnnouncement(plan);
      if (text) {
        deps.announce?.(text);
      }
    }

    await deps.seekTo(plan.targetMs);
    return plan;
  };

  const notePlayback = (mediaTimeMs: number): void => {
    if (!held) {
      return;
    }
    if (!Number.isFinite(mediaTimeMs)) {
      return;
    }
    // Still inside, or not yet clear of it by the confirmation margin.
    if (
      mediaTimeMs >= held.startMs - confirmOutsideMs &&
      mediaTimeMs < held.endMs + confirmOutsideMs
    ) {
      return;
    }
    // Outside the interval we were holding for. It may still be inside another
    // one, in which case the schedule keeps the cover on by itself.
    const nowInside = intervalAt(deps.getIntervals(), mediaTimeMs);
    held = undefined;
    if (!nowInside) {
      deps.setCover(false, 'seek confirmed outside the interval');
    }
  };

  return {
    requestSeek,
    notePlayback,
    isHolding: () => held !== undefined,
    heldInterval: () => held,
  };
}

/**
 * Whether a trickplay preview may be drawn for this position.
 *
 * BIF frames are generated from the safe rendition, where flagged parts are
 * already replaced by a still, so a preview from that source is safe anywhere.
 * A BIF file from anywhere else is not, so previews inside an interval are
 * refused rather than guessed at.
 */
export function isPreviewAllowed(
  intervals: CoverInterval[],
  mediaTimeMs: number,
  bifFromSafeRendition: boolean,
): boolean {
  if (bifFromSafeRendition) {
    return true;
  }
  return intervalAt(intervals, mediaTimeMs) === undefined;
}
