/**
 * The chime before a hide.
 *
 * A cover arriving with no warning is the one thing about this app that
 * startles people: the picture goes dark mid scene while the sound carries on.
 * So a soft chime sounds a fixed time before it, and the card that was already
 * counting down now has something to go with it for anyone not looking at the
 * screen.
 *
 * The property, and it is the whole module:
 *
 *   a chime never sounds without a cover following it.
 *
 * A chime that sounds and is followed by nothing teaches a household to ignore
 * it, and an ignored warning is worse than no warning, because the next one is
 * ignored too. So the cue is written as a state machine that can be stepped
 * over a scripted timeline and asked afterwards whether it kept its word, and
 * `unmatched` is the count of times it did not. It is always zero.
 * test/calmframes/chimeCue.test.tsx drives it over seeks, stalls and pauses,
 * and eval/mutate_gate.py has an entry that breaks the one line holding it up.
 *
 * What counts as "a cover following it", when the playhead can move in between
 *
 * The cue is discharged by the next time the picture goes dark, whatever
 * raised it: the interval the chime announced, or the fail safe cover that any
 * seek raises before the playhead moves. It does not have to be the announced
 * interval's own cover, and that is a decision rather than a shortcut
 * (docs/DECISIONS.md, 2026-09-18).
 *
 * Two reasons. Every way of moving the playhead in this app covers first:
 * `seekSafety.ts` covers before it seeks into an interval, and
 * `useCoverHarness.ts` treats `seeking` as an event after which the playhead
 * cannot be trusted, so the cover goes on at the start of every seek wherever
 * it lands and stays on until playback is confirmed outside an interval. A
 * person who hears the chime and then seeks still gets chime, then dark, which
 * is what the chime promised. And insisting on the announced interval would
 * make the app worse: after that seek it would either chime again over a cover
 * that is already on, which is a warning after the event, or mark the cue
 * broken and stay silent at the next interval.
 *
 * What the cue still refuses, and what the tests drive:
 *
 * - it never announces an interval that is not ahead of the playhead. A seek
 *   past a flagged part would otherwise chime with nothing to follow it;
 * - it never announces while the picture is already dark, because a chime
 *   after the cover is a warning about something that has happened;
 * - it never announces the same interval twice;
 * - it never announces anything at all before the map has verified, because
 *   there is no schedule then and so nothing to promise.
 */

import { CoverInterval } from './coverSchedule';

/**
 * How long before the cover the chime sounds, in media milliseconds.
 *
 * Two seconds, and the two numbers either side of it are what fix it. The
 * countdown card already appears at three seconds (`cards.ts`), so the chime
 * has to sit inside that or it would sound before there is anything on screen
 * to explain it. And the guard band is 500 ms, so anything under about a
 * second would land inside the widened interval rather than before it, and the
 * chime would be simultaneous with the dark rather than ahead of it.
 *
 * It is media time rather than wall clock time. The two are the same while the
 * playback rate is 1, and nothing in this app changes the rate: no remote key
 * reaches it and the app never sets it (docs/DECISIONS.md, the chaos run). A
 * player that did change it would want this converted the way
 * `millisecondsUntilNextCover` converts.
 */
export const CHIME_LEAD_MS = 2_000;

/** The chime is on unless a household turns it off. */
export const CHIME_ON_BY_DEFAULT = true;

export interface ChimeCueState {
  /**
   * The interval a chime has announced and not yet seen covered, or null.
   *
   * While this is set nothing else can be announced, so one outstanding
   * promise at a time.
   */
  awaitingStartMs: number | null;
  awaitingEndMs: number | null;
  /** Interval starts already announced, so each one sounds once. */
  announced: number[];
  /** How many cues have sounded. */
  played: number;
  /**
   * Cues the playhead ran past without the picture ever going dark.
   *
   * The property is that this is zero. It is counted rather than thrown so a
   * test can see the difference between a cue that was kept and one that was
   * not, and so a mutation to the code above shows up as a number rather than
   * as a crash somewhere else.
   */
  unmatched: number;
}

export interface ChimeCueInputs {
  /** The schedule, already widened and merged. */
  intervals: CoverInterval[];
  mediaTimeMs: number;
  /** True while the picture is hidden, for any reason at all. */
  covered: boolean;
  /** True only once the map has verified and there is a schedule. */
  verified: boolean;
  /** The household switch. */
  enabled: boolean;
  leadMs?: number;
}

export function emptyChimeCue(): ChimeCueState {
  return {
    awaitingStartMs: null,
    awaitingEndMs: null,
    announced: [],
    played: 0,
    unmatched: 0,
  };
}

/**
 * The interval a chime would be announcing now, or null.
 *
 * `untilMs > 0` is the line the whole property rests on: the interval has to
 * be ahead of the playhead, not merely near it. Without it a playhead sitting
 * just past a flagged part announces the part it has already gone by, and
 * nothing covers afterwards. That is the mutation in eval/mutate_gate.py.
 */
export function intervalToAnnounce(
  intervals: CoverInterval[],
  mediaTimeMs: number,
  leadMs: number = CHIME_LEAD_MS,
): CoverInterval | null {
  for (const interval of intervals) {
    const untilMs = interval.startMs - mediaTimeMs;
    if (untilMs > 0 && untilMs <= leadMs) {
      return interval;
    }
  }
  return null;
}

/**
 * One step of the cue.
 *
 * Pure: the same inputs give the same answer, and nothing here plays a sound.
 * The caller plays it when `play` comes back true, which is what lets the
 * whole property be checked over a scripted timeline with no player at all.
 */
export function stepChimeCue(
  state: ChimeCueState,
  inputs: ChimeCueInputs,
): { state: ChimeCueState; play: boolean } {
  const leadMs = inputs.leadMs ?? CHIME_LEAD_MS;
  let next = state;

  // The picture going dark is what discharges a cue, whatever raised it: the
  // interval that was announced, or the cover a seek or a stall put on. And
  // nothing is ever announced over a cover that is already on.
  if (inputs.covered) {
    if (next.awaitingStartMs !== null) {
      next = { ...next, awaitingStartMs: null, awaitingEndMs: null };
    }
    return { state: next, play: false };
  }

  // A cue whose interval the playhead has gone past with the picture never
  // having gone dark is the thing this module exists to make impossible.
  if (next.awaitingEndMs !== null && inputs.mediaTimeMs >= next.awaitingEndMs) {
    next = {
      ...next,
      awaitingStartMs: null,
      awaitingEndMs: null,
      unmatched: next.unmatched + 1,
    };
  }

  if (!inputs.enabled || !inputs.verified || next.awaitingStartMs !== null) {
    return { state: next, play: false };
  }

  const upcoming = intervalToAnnounce(inputs.intervals, inputs.mediaTimeMs, leadMs);
  if (!upcoming || next.announced.includes(upcoming.startMs)) {
    return { state: next, play: false };
  }

  return {
    state: {
      ...next,
      awaitingStartMs: upcoming.startMs,
      awaitingEndMs: upcoming.endMs,
      announced: [...next.announced, upcoming.startMs],
      played: next.played + 1,
    },
    play: true,
  };
}

/**
 * A new sitting.
 *
 * Which intervals have already been announced is the one thing that does not
 * survive a new title, because the same interval start in a different title is
 * a different part of a different film.
 */
export function resetChimeCue(state: ChimeCueState): ChimeCueState {
  return { ...emptyChimeCue(), played: state.played, unmatched: state.unmatched };
}
