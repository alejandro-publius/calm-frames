/**
 * Every word Calm Frames puts on screen that is not about one particular
 * title, in one file.
 *
 * Three reasons it lives here rather than inside the screens:
 *
 * - the same state has to read the same way everywhere. A title that is still
 *   being checked says the same thing on the shelf, on its details page and in
 *   the parent area, because all three read this file;
 * - the wording about what this is and is not is fixed. SAFETY_NOTE carries
 *   the approved sentence word for word and a test fails if it drifts or if
 *   the words we never use turn up anywhere in the app;
 * - it can be read on its own. Copy written for a twelve year old and for a
 *   parent at the end of a long day is easier to judge as a list than as
 *   fragments spread through JSX.
 *
 * House style, checked in test/calmframes/copy.test.ts: short sentences, no
 * dashes of any kind, no exclamation marks, and every blocked state says what
 * happens to the picture rather than leaving it to be guessed.
 */

import { MapRejection } from './flashMap';
import { CheckedTitle } from './titleStatus';

/**
 * The approved sentence, word for word.
 *
 * docs/SAFETY.md and CLAUDE.md both fix this wording. It is never softened and
 * never shortened into something that sounds like a promise about what it
 * stops. docs/SAFETY.md names the two phrasings that are never used, and
 * test/calmframes/copy.test.ts searches every file in this folder for them.
 */
export const APPROVED_SAFETY_CLAUSE =
  'reduces exposure to flashing above published limits in the videos it plays; not a medical device.';

export const SAFETY_NOTE = `Calm Frames ${APPROVED_SAFETY_CLAUSE}`;

/**
 * How a state looks, not what it means.
 *
 * calm      nothing is wrong
 * waiting   a check has not finished, so there is nothing to see yet
 * blocked   the picture stays hidden and will not play in this state
 */
export type NoticeTone = 'calm' | 'waiting' | 'blocked';

export interface Notice {
  /** The big line. Six words or fewer wherever it can be. */
  title: string;
  /** The line under it. Says what happens next, in plain words. */
  detail: string;
  tone: NoticeTone;
}

/** Nothing has been checked yet, so the shelf is empty. */
export const NO_TITLES: Notice = {
  title: 'Nothing is ready to watch yet',
  detail:
    'Every title is checked all the way through before it can show up here. A grown up can see what is being checked in the parent area.',
  tone: 'waiting',
};

/**
 * The service that publishes checks cannot be reached.
 *
 * This is not an error a child has to solve, and it is not a reason to show
 * anything unchecked. The title that ships inside the app carries its own
 * signed check, so it keeps working with no network at all.
 */
export const BACKEND_UNREACHABLE: Notice = {
  title: 'We cannot reach the check service',
  detail:
    'The title that came with the app still plays, because its check travels with it. Anything new stays off the shelf until the service is back.',
  tone: 'waiting',
};

/** The backend is unreachable and there is not even a bundled title. */
export const BACKEND_UNREACHABLE_EMPTY: Notice = {
  title: 'We cannot reach the check service',
  detail:
    'Nothing can be shown until a checked title is on this device. Nothing plays here until it has been checked.',
  tone: 'waiting',
};

/** A title whose check has not finished. */
export const TITLE_PENDING: Notice = {
  title: 'Still being checked',
  detail:
    'This title is not ready. The picture stays hidden until the check is finished.',
  tone: 'waiting',
};

/** A title whose check was there and did not pass. */
export const TITLE_FAILED: Notice = {
  title: 'This title did not pass its check',
  detail: 'The picture stays hidden. Nothing plays until a check passes.',
  tone: 'blocked',
};

/** A title whose check is too old to trust. */
export const TITLE_STALE: Notice = {
  title: 'This check is too old',
  detail:
    'The picture stays hidden until the title is checked again. An old check may have been made with older limits.',
  tone: 'blocked',
};

/** The parent area, before a PIN exists. */
export const PIN_NOT_SET: Notice = {
  title: 'No PIN yet',
  detail: 'Set a four digit PIN so the settings stay where a child cannot change them.',
  tone: 'waiting',
};

/** The keypad, before anyone has typed anything. */
export const PIN_PROMPT: Notice = {
  title: 'Enter the PIN',
  detail: 'Enter the PIN to change settings.',
  tone: 'calm',
};

/**
 * The two ways a PIN entry goes wrong.
 *
 * The line underneath comes from parentGate, which counts the tries and the
 * lockout, so the numbers in it are the ones the gate is really using rather
 * than a second copy that could disagree.
 */
export const PIN_WRONG_TITLE = 'Try that again';
export const PIN_LOCKED_TITLE = 'Locked for a minute';

export const KID_HOME_TITLE = 'Ready to watch';
export const KID_HOME_SUBTITLE = 'Every title here has been checked all the way through.';
export const PARENT_AREA_TITLE = 'Parent area';

/** What the room settings can and cannot do, said the same way everywhere. */
export const ROOM_ONLY_ADDS =
  'A bigger television or a closer sofa can only add hidden parts. It never takes any away.';

/**
 * The first run explainer.
 *
 * Meant to be read in about twenty seconds. At 150 words a minute, a common
 * pace for reading a screen out loud, twenty seconds is about fifty words, and
 * test/calmframes/firstRun.test.tsx holds this to that budget. The safety
 * sentence is part of it, not a footnote under it.
 */
export const EXPLAINER_TARGET_SECONDS = 20;
export const EXPLAINER_WORDS_PER_MINUTE = 150;

export const EXPLAINER_TITLE = 'What Calm Frames hides, and why';
export const EXPLAINER_LINES: string[] = [
  'Calm Frames checks a whole title before it plays.',
  'Any part that goes over the published flash limits is hidden while the sound and the captions keep going.',
  'A card says what is coming, and what was hidden.',
  SAFETY_NOTE,
];

/** How long the explainer takes to read, in seconds, at the pace above. */
export function readingSeconds(
  lines: string[],
  wordsPerMinute: number = EXPLAINER_WORDS_PER_MINUTE,
): number {
  const words = lines
    .join(' ')
    .split(/\s+/)
    .filter((word) => word.length > 0).length;
  return (words / wordsPerMinute) * 60;
}

/**
 * The notice for a title that is not ready to play.
 *
 * Fail closed lives in one place: anything that is not verified gets a notice,
 * and the screens use the presence of a notice to decide whether a play
 * control exists at all. There is no fourth answer where the picture shows.
 */
export function noticeForTitle(entry: CheckedTitle): Notice | null {
  if (entry.status === 'verified') {
    return null;
  }
  const base = noticeForRejection(entry.rejection, entry.status === 'pending');
  // The reader's own wording for this rejection is more specific than the
  // general line, so it goes underneath rather than replacing it.
  return entry.reason && entry.reason !== base.detail
    ? { ...base, detail: `${base.detail} ${entry.reason}` }
    : base;
}

/**
 * Which notice a rejection gets.
 *
 * The status decides, not the rejection: a title can be blocked with no
 * rejection recorded at all, when the household's room is stricter than the
 * check that was run. A missing map is waiting rather than blocked, because
 * nothing is wrong with it yet.
 */
export function noticeForRejection(
  rejection: MapRejection | undefined,
  pending: boolean,
): Notice {
  if (rejection === 'stale') {
    return TITLE_STALE;
  }
  if (pending || rejection === 'missing') {
    return TITLE_PENDING;
  }
  return TITLE_FAILED;
}
