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
import { HideLogEntry } from './hideLog';
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
  title: 'We cannot look for new titles',
  detail:
    'The title that came with the app still plays, because its check is inside the app. Anything new stays off the shelf until this works again.',
  tone: 'waiting',
};

/** The backend is unreachable and there is not even a bundled title. */
export const BACKEND_UNREACHABLE_EMPTY: Notice = {
  title: 'We cannot look for new titles',
  detail:
    'There is nothing checked on this device yet, so there is nothing to watch. Nothing plays here until it has been checked.',
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
    'The picture stays hidden until the title is checked again. An old check may have been made using older limits.',
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
 * Family profiles.
 *
 * The shelf asks who is watching. The parent area asks whose settings are
 * being changed, which is a different question and reads as one. Both lists
 * put the household first, because what it is set to is the floor under every
 * profile.
 */
export const PROFILES_KID_TITLE = 'Who is watching';
export const PROFILES_PARENT_TITLE = 'Whose settings';
export const EVERYONE_LABEL = 'Everyone';

/**
 * The answer to the picker's question, as a sentence under the row.
 *
 * It used to be a word in brackets on the chosen chip, and that had two
 * problems. Brackets are a printing convention that reads as noise from a
 * sofa. And a word that only appears on one chip makes that chip wider than
 * the others, so choosing somebody moved every chip after them along the row.
 * A row of controls sliding sideways is motion, and kid mode has none.
 *
 * Off the chip, the chips never change size, and the answer gets room to be a
 * sentence rather than a fragment. The chip still carries the state for a
 * screen reader, in `chosenWord` below.
 */
export function whoIsWatching(name: string): string {
  return `${name} is watching.`;
}

export function whoseSettingsThese(name: string): string {
  return `These settings are for ${name}.`;
}

/** The state word a screen reader hears on the chosen chip, in each place. */
export const WATCHING_STATE_WORD = 'watching';
export const SETTINGS_STATE_WORD = 'showing';

/**
 * Section headings in the parent area, and whose they are.
 *
 * The heading for the record already said the name. The two above it did not,
 * so a parent who had scrolled past the picker was reading "How strict" with
 * no way to tell whether they were about to change the floor under every kid
 * or one kid's own setting. Those two are not the same thing and the screen
 * should never let them look the same. Every section says whose it is now.
 */
export const STRICTNESS_TITLE = 'How strict';
export const ROOM_TITLE = 'The room';
export const HIDDEN_TITLE = 'What was hidden';
export const CHECKED_TITLES_TITLE = 'Titles';

export function sectionFor(title: string, name: string | null): string {
  return name ? `${title} for ${name}` : title;
}

/** A second kid called Kid is two chips nobody can tell apart. */
export function nextKidName(base: string, taken: string[]): string {
  if (!taken.includes(base)) {
    return base;
  }
  let index = 2;
  while (taken.includes(`${base} ${index}`)) {
    index += 1;
  }
  return `${base} ${index}`;
}

/** The rule about profiles, said the same way as the one about rooms. */
export const PROFILE_ONLY_ADDS =
  'A profile can only add hidden parts to what Everyone is set to. It never takes any away.';

/** Four is the most, and the parent area says so before the button is gone. */
export const PROFILES_FULL = 'Four profiles is the most. Remove one to add another.';

/** The record, before anything has been hidden. */
export const NOTHING_HIDDEN_YET = 'Nothing has been hidden yet.';

/** One kid's record, before anything has been hidden for them. */
export function nothingHiddenFor(name: string): string {
  return `Nothing has been hidden for ${name} yet.`;
}

/**
 * How much was hidden, and whether the list under it is all of it.
 *
 * The screen draws the twenty most recent lines and keeps two hundred. It used
 * to say "43 parts" and then show twenty lines without mentioning it, which is
 * the one thing this record cannot afford to do: it is the only evidence a
 * household gets that the thing they set up is working, so it says where the
 * list stops.
 *
 * Long totals are read as minutes. "312 seconds in all" is arithmetic a tired
 * parent has to do in their head.
 */
export function hiddenSummary(count: number, totalMs: number, shown: number): string {
  const parts = `${count} part${count === 1 ? '' : 's'}`;
  const line = `${parts}, ${describeHiddenTotal(totalMs)} in all.`;
  return shown < count ? `${line} The ${shown} most recent are below.` : line;
}

function plural(value: number, word: string): string {
  return `${value} ${word}${value === 1 ? '' : 's'}`;
}

export function describeHiddenTotal(totalMs: number): string {
  const seconds = Math.round(totalMs / 1000);
  if (seconds < 60) {
    return plural(seconds, 'second');
  }
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest === 0
    ? plural(minutes, 'minute')
    : `${plural(minutes, 'minute')} ${plural(rest, 'second')}`;
}

const WEEKDAYS = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

/** The local day an entry belongs to, as a key the screen can group on. */
export function hideDayKey(atMs: number): string {
  const when = new Date(atMs);
  const month = when.getMonth() + 1;
  const day = when.getDate();
  return `${when.getFullYear()}-${month < 10 ? `0${month}` : month}-${
    day < 10 ? `0${day}` : day
  }`;
}

/**
 * The heading over one day of the record.
 *
 * A line in the record says the time and nothing else, so two hundred entries
 * read as one undated pile: "19:30 hid 4 seconds" could be tonight or last
 * week. The day belongs above the lines rather than repeated on every one of
 * them, which is also how a person would write the list out by hand.
 *
 * The names are spelled out here rather than taken from the platform, because
 * the parent area is measured in tests and a date that changes with the locale
 * data on the machine is a date no test can hold.
 */
export function hideDayHeading(atMs: number, nowMs: number): string {
  const key = hideDayKey(atMs);
  if (key === hideDayKey(nowMs)) {
    return 'Today';
  }
  const yesterday = new Date(nowMs);
  yesterday.setDate(yesterday.getDate() - 1);
  if (key === hideDayKey(yesterday.getTime())) {
    return 'Yesterday';
  }
  const when = new Date(atMs);
  return `${WEEKDAYS[when.getDay()]} ${when.getDate()} ${MONTHS[when.getMonth()]}`;
}

/** One day of the record, newest day first, newest line first inside it. */
export interface HideDay {
  key: string;
  heading: string;
  /** The index each line has in the whole list, so a line keeps its place. */
  lines: Array<{ index: number; entry: HideLogEntry }>;
}

export function hidesByDay(entries: HideLogEntry[], nowMs: number): HideDay[] {
  const days: HideDay[] = [];
  entries.forEach((entry, index) => {
    const key = hideDayKey(entry.atMs);
    const last = days[days.length - 1];
    if (last && last.key === key) {
      last.lines.push({ index, entry });
      return;
    }
    days.push({
      key,
      heading: hideDayHeading(entry.atMs, nowMs),
      lines: [{ index, entry }],
    });
  });
  return days;
}

/**
 * The chime before a hide.
 *
 * The label says what the sound does, not what the feature is called, and it
 * carries its own state so a parent reading it from the sofa does not have to
 * work out whether a highlighted row means on or off. The note underneath says
 * the thing that matters most about the switch: turning it off changes nothing
 * about what is hidden.
 */
export const CHIME_SECTION_TITLE = 'Sound before a hide';
export const CHIME_ON_LABEL = 'A soft chime plays first: on';
export const CHIME_OFF_LABEL = 'A soft chime plays first: off';
export const CHIME_NOTE =
  'The chime sounds a couple of seconds before the picture goes dark, so nobody is taken by surprise. Turning it off changes nothing about what is hidden.';

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
