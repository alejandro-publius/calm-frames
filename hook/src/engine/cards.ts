/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * What the card says, and when.
 *
 * docs/BUILD_PROMPT.md 4.2 and 4.3:
 *
 *   5 seconds before an interval: "Flashing part coming up", with a Skip
 *   button that has D-pad focus.
 *   During the interval: the cover, while sound and captions keep going.
 *   After it: one line, such as "Hid 4 seconds of flashing. Sound and captions
 *   kept playing."
 *   A map that did not verify: the picture stays hidden and a card says the
 *   title is not checked yet.
 *   A map still being checked: the picture stays hidden and a card says the
 *   check is under way. That is not a refusal, so it is not the same card.
 *
 * This module is the whole decision, as one pure function of the schedule and
 * the playhead. Keeping it pure is what lets the wording, the timing and the
 * announcements be tested without a player, a screen or a clock.
 */

import { CoverInterval, intervalAt, nextIntervalAfter } from './coverSchedule';
import { MapRejection, rejectionMessage } from './flashMap';

export type CardKind =
  | 'none'
  | 'checking'
  | 'countdown'
  | 'covering'
  | 'after'
  | 'unverified';

export interface Card {
  kind: CardKind;
  /** The big line. */
  title: string;
  /** The small line under it, when there is one. */
  detail?: string;
  /** What VoiceView says. Empty for the no-card case. */
  announcement: string;
  /** Countdown only: whole seconds left before the cover comes on. */
  secondsLeft?: number;
  /** Countdown only: where a Skip press should land. */
  skipToMs?: number;
  /** The interval this card is about. */
  interval?: CoverInterval;
}

/** The card comes up five seconds before the cover does. */
export const COUNTDOWN_LEAD_MS = 5_000;
/** The card that says what was hidden stays this long. */
export const AFTER_CARD_MS = 5_000;
/** Skip lands this far past the end of the interval, clear of its last frame. */
export const SKIP_MARGIN_MS = 100;

export const NO_CARD: Card = { kind: 'none', title: '', announcement: '' };

/**
 * The card while the map is still being checked.
 *
 * Nothing has gone wrong yet, so this is not the "Not checked yet" card a
 * refused map gets. The picture is hidden either way: the guard starts
 * covered and only a verified map uncovers it, whatever the card says. There
 * is nothing coming up to skip, so there is no Skip button.
 */
export const CHECKING_CARD: Card = {
  kind: 'checking',
  title: 'Checking this title',
  detail: 'The picture stays hidden until the check passes.',
  announcement:
    'Checking this title. The picture stays hidden until the check passes.',
};

function secondsWord(milliseconds: number): string {
  const seconds = Math.max(1, Math.round(milliseconds / 1000));
  return `${seconds} second${seconds === 1 ? '' : 's'}`;
}

export interface CardOptions {
  /** Set when the map did not verify. The picture stays hidden either way. */
  rejection?: MapRejection | null;
  /**
   * Wording that fits the case better than the general one.
   *
   * A room that is stricter than the check is not a broken map, so the card
   * says that instead of "could not be read".
   */
  blockedDetail?: string;
  countdownLeadMs?: number;
  afterCardMs?: number;
}

/**
 * The card for this moment.
 *
 * Priority, highest first: a map we could not trust, then the cover itself,
 * then the next one coming, then what was just hidden. The countdown beats the
 * card about the part that just ended, because what is about to happen is what
 * a child needs to know.
 */
export function cardAt(
  intervals: CoverInterval[],
  mediaTimeMs: number,
  options: CardOptions = {},
): Card {
  if (options.rejection) {
    const detail = options.blockedDetail ?? rejectionMessage(options.rejection);
    return {
      kind: 'unverified',
      title: 'Not checked yet',
      detail,
      announcement: `Not checked yet. ${detail}`,
    };
  }

  const leadMs = options.countdownLeadMs ?? COUNTDOWN_LEAD_MS;
  const afterMs = options.afterCardMs ?? AFTER_CARD_MS;

  const inside = intervalAt(intervals, mediaTimeMs);
  if (inside) {
    return {
      kind: 'covering',
      title: 'Hiding a flashing part',
      detail: 'Sound and captions keep playing.',
      announcement: 'Hiding a flashing part. Sound and captions keep playing.',
      interval: inside,
    };
  }

  const next = nextIntervalAfter(intervals, mediaTimeMs);
  if (next && next.startMs - mediaTimeMs <= leadMs) {
    const remainingMs = next.startMs - mediaTimeMs;
    const secondsLeft = Math.max(0, Math.ceil(remainingMs / 1000));
    return {
      kind: 'countdown',
      title: 'Flashing part coming up',
      detail: `In ${secondsLeft} second${secondsLeft === 1 ? '' : 's'}. Press Skip to jump past it.`,
      announcement: `Flashing part coming up in ${secondsLeft} second${
        secondsLeft === 1 ? '' : 's'
      }. Press Skip to jump past it.`,
      secondsLeft,
      skipToMs: next.endMs + SKIP_MARGIN_MS,
      interval: next,
    };
  }

  // Nothing ahead, so say what just went by, for a few seconds.
  let justEnded: CoverInterval | undefined;
  for (const interval of intervals) {
    if (interval.endMs <= mediaTimeMs && mediaTimeMs - interval.endMs < afterMs) {
      justEnded = interval;
    }
  }
  if (justEnded) {
    const hidden = secondsWord(justEnded.endMs - justEnded.startMs);
    return {
      kind: 'after',
      title: `Hid ${hidden} of flashing`,
      detail: 'Sound and captions kept playing.',
      announcement: `Hid ${hidden} of flashing. Sound and captions kept playing.`,
      interval: justEnded,
    };
  }

  return NO_CARD;
}

/**
 * True when this card replaces the one on screen.
 *
 * Cards are announced once each. Without this the countdown would re-announce
 * every tick as the seconds changed, which is noise in a screen reader.
 */
export function cardChanged(previous: Card, next: Card): boolean {
  if (previous.kind !== next.kind) {
    return true;
  }
  if (previous.interval?.startMs !== next.interval?.startMs) {
    return true;
  }
  return false;
}
