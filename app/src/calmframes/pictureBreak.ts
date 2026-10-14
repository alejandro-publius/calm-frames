/**
 * The picture break: a viewer hides the picture on demand while sound and
 * captions carry on, then asks for it back.
 *
 * The signed schedule only covers what the map flagged, and detection can miss
 * flashing. This is the family's own control for every other moment. It never
 * moves the playhead, never pauses, never touches the caption track and never
 * writes exposure history. It can only add cover: the screen is covered
 * whenever the schedule alone would cover it (coveredWithBreak).
 *
 * Two rules keep the remote from becoming a source of flashing itself. The
 * three-flashes rule they stay under is quoted in flashmap/docs/SPEC_SOURCES.md
 * section 1; neither number below is a threshold taken from it.
 *
 * - A break lasts at least MIN_BREAK_MS of wall-clock time before the picture
 *   may return. Hiding is never delayed. So viewer presses can change the
 *   cover at most twice in any window shorter than MIN_BREAK_MS: one return
 *   and one new break.
 * - The picture never returns inside a scheduled hold or less than
 *   RETURN_CLEARANCE_MS of media time before the next one. Otherwise a return
 *   could show the picture for a moment and cover it again, which is a flash
 *   the viewer caused by asking for the picture back.
 *
 * A request that arrives while either rule holds the picture back is kept, and
 * the picture returns by itself once both allow it. This module is pure, so
 * every rule is tested without a player, a screen or a clock.
 */

import { CoverInterval, intervalAt, nextIntervalAfter } from './coverSchedule';

/** The shortest break, in wall-clock milliseconds. */
export const MIN_BREAK_MS = 2_000;
/** The least picture time before a scheduled hold, in media milliseconds. */
export const RETURN_CLEARANCE_MS = 2_000;
/**
 * How long OK stays the break's after the picture returns. Without it, a child
 * pressing OK twice to get the picture back pauses the film on the second
 * press, because OK on a clear picture means pause.
 */
export const OK_GRACE_MS = 1_000;

/** Why a requested return is still waiting. */
export type ReturnWait = 'minimum' | 'hold-now' | 'hold-soon';

export interface PictureBreakState {
  resting: boolean;
  /** Wall-clock time the current break began. */
  startedAtMs: number;
  /** The viewer has asked for the picture back. */
  returnRequested: boolean;
  /** Set while a requested return is held back, and why. */
  waitingFor?: ReturnWait;
  /** Wall-clock time the last break ended, kept until OK_GRACE_MS has run. */
  endedAtMs?: number;
}

export const NO_BREAK: PictureBreakState = {
  resting: false,
  startedAtMs: 0,
  returnRequested: false,
};

/** Hide the picture now. A break already running is left as it is. */
export function startBreak(
  state: PictureBreakState,
  nowMs: number,
): PictureBreakState {
  if (state.resting) {
    return state;
  }
  return { resting: true, startedAtMs: nowMs, returnRequested: false };
}

/** Ask for the picture back. Asking again changes nothing. */
export function requestReturn(state: PictureBreakState): PictureBreakState {
  if (!state.resting || state.returnRequested) {
    return state;
  }
  return { ...state, returnRequested: true };
}

/** The Menu key: start a break, or ask for the picture back. */
export function toggleBreak(
  state: PictureBreakState,
  nowMs: number,
): PictureBreakState {
  return state.resting ? requestReturn(state) : startBreak(state, nowMs);
}

/** What still holds the picture back, or undefined when it may return. */
export function returnWait(
  state: PictureBreakState,
  nowMs: number,
  mediaTimeMs: number,
  intervals: CoverInterval[],
): ReturnWait | undefined {
  if (nowMs - state.startedAtMs < MIN_BREAK_MS) {
    return 'minimum';
  }
  if (intervalAt(intervals, mediaTimeMs)) {
    return 'hold-now';
  }
  const next = nextIntervalAfter(intervals, mediaTimeMs);
  if (next && next.startMs - mediaTimeMs < RETURN_CLEARANCE_MS) {
    return 'hold-soon';
  }
  return undefined;
}

/**
 * Apply a pending return if the rules allow it now.
 *
 * Returns the same object when nothing changed, so a caller can hand the
 * result straight to React state without causing a render.
 */
export function settleBreak(
  state: PictureBreakState,
  nowMs: number,
  mediaTimeMs: number,
  intervals: CoverInterval[],
): PictureBreakState {
  if (!state.resting || !state.returnRequested) {
    return state;
  }
  const wait = returnWait(state, nowMs, mediaTimeMs, intervals);
  if (wait === undefined) {
    return { ...NO_BREAK, endedAtMs: nowMs };
  }
  return wait === state.waitingFor ? state : { ...state, waitingFor: wait };
}

/** OK belongs to the break while it runs and for OK_GRACE_MS after it ends. */
export function breakOwnsSelect(state: PictureBreakState): boolean {
  return state.resting || state.endedAtMs !== undefined;
}

/** Hand OK back to the player once the grace after a return has run. */
export function expireGrace(
  state: PictureBreakState,
  nowMs: number,
): PictureBreakState {
  if (
    state.resting ||
    state.endedAtMs === undefined ||
    nowMs - state.endedAtMs < OK_GRACE_MS
  ) {
    return state;
  }
  return NO_BREAK;
}

/** The break can only add cover to what the schedule already covers. */
export function coveredWithBreak(
  scheduleCovered: boolean,
  state: PictureBreakState,
): boolean {
  return scheduleCovered || state.resting;
}

export interface PictureBreakCopy {
  title: string;
  detail: string;
  announcement: string;
  returnLabel: string;
}

export interface PictureBreakCopyContext {
  /** The viewer's own caption choice, which the break never changes. */
  captionsOn: boolean;
  paused: boolean;
}

/** Proposed wording. UI copy is owned by the design pass, so it lives here alone. */
export function pictureBreakCopy(
  state: PictureBreakState,
  context: PictureBreakCopyContext,
): PictureBreakCopy {
  const title = 'Picture break';
  let detail: string;
  if (state.returnRequested && state.waitingFor === 'hold-now') {
    detail = 'The picture comes back when this hidden part ends.';
  } else if (state.returnRequested && state.waitingFor === 'hold-soon') {
    detail = 'A hidden part is coming up. The picture comes back after it.';
  } else if (state.returnRequested) {
    detail = 'The picture comes back in a moment.';
  } else if (context.paused) {
    detail = 'Paused. Press Play to keep listening, or OK to bring the picture back.';
  } else if (context.captionsOn) {
    detail = 'Sound and captions keep playing. Press OK to bring the picture back.';
  } else {
    detail = 'Sound keeps playing. Captions are off. Press OK to bring the picture back.';
  }
  return {
    title,
    detail,
    announcement: `${title}. ${detail}`,
    returnLabel: 'Back to the picture',
  };
}
