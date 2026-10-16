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
  title: 'Nothing to watch yet',
  detail:
    'Checked videos appear here. A parent can review unavailable videos in Parents.',
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
  title: 'New videos are unavailable',
  detail:
    'You can still watch the videos on this television. Try again later for new ones.',
  tone: 'waiting',
};

/** The backend is unreachable and there is not even a bundled title. */
export const BACKEND_UNREACHABLE_EMPTY: Notice = {
  title: 'New videos are unavailable',
  detail:
    'There are no videos on this television yet. Try again later.',
  tone: 'waiting',
};

/** A title whose check has not finished. */
export const TITLE_PENDING: Notice = {
  title: 'Not ready to watch',
  detail:
    'This video is still being checked. The picture stays hidden for now.',
  tone: 'waiting',
};

/** A title whose check was there and did not pass. */
export const TITLE_FAILED: Notice = {
  title: 'This video is unavailable',
  detail: 'This version cannot play in Calm Frames. The picture stays hidden.',
  tone: 'blocked',
};

/** A title whose check is too old to trust. */
export const TITLE_STALE: Notice = {
  title: 'This video needs an update',
  detail:
    'The picture stays hidden until a newer version is available.',
  tone: 'blocked',
};

/** Parental controls, before a PIN exists. */
export const PIN_NOT_SET: Notice = {
  title: 'Set up a PIN to continue',
  detail:
    'A four digit PIN keeps parental controls where a child cannot change them.',
  tone: 'waiting',
};

/**
 * The keypad, before anyone has typed anything.
 *
 * The heading above it already says Parental controls, so the notice does not
 * say it again. The title is the one thing to do, and the detail says what the
 * PIN is for and where it stays.
 */
export const PIN_PROMPT: Notice = {
  title: 'Enter your PIN',
  detail:
    'Your PIN opens parental controls. It stays on this TV and is never sent anywhere.',
  tone: 'calm',
};

/**
 * The two ways a PIN entry goes wrong.
 *
 * The line underneath comes from parentGate, which counts the tries and the
 * lockout, so the numbers in it are the ones the gate is really using rather
 * than a second copy that could disagree. The titles name no number and no
 * time for the same reason: the gate's own line carries both.
 */
export const PIN_WRONG_TITLE = 'Try again';
export const PIN_LOCKED_TITLE = 'Locked for now';

/** A PIN attempt that could not be written down, so the gate stays shut. */
export const PIN_SAVE_FAILED: Notice = {
  title: 'Parental controls stay locked',
  detail: "The PIN attempt couldn't be saved. Try again.",
  tone: 'blocked',
};

/** What Home calls the way in. The page itself is headed Parental controls. */
export const PARENT_AREA_TITLE = 'Parental controls';
export const PARENTAL_CONTROLS_TITLE = 'Parental controls';
/** One line under the heading, saying what the page is for. */
export const PARENTAL_CONTROLS_LEAD =
  'Choose viewing settings for your family and see which scenes were hidden.';
/** While a change is being written to the household record. */
export const SAVING_CHANGES = 'Saving your changes…';

/** Button labels, the ones a television usually uses. Back is one word: the hardware key says the same. */
export const BACK_TO_LIBRARY_LABEL = 'Back';
export const SET_PIN_LABEL = 'Set up a PIN';
export const CREDITS_LABEL = 'Credits and licences';
export const ADD_KID_LABEL = 'Add a kid';

/**
 * The word at the edge of a chosen settings row.
 *
 * The same word the room chips use in their sentences and in their screen
 * reader labels, so a page has one word for one state.
 */
export const CHOSEN_WORD = 'Chosen';

/** What the room settings can and cannot do, said the same way everywhere. */
export const ROOM_ONLY_ADDS =
  'A larger TV or a closer seat can hide more of the video, never less.';

/**
 * The two rows of room chips, and which chip in each is the chosen one.
 *
 * The chips carried chosen as a fill colour and nothing else. That is a state
 * only a person who can tell two shades of teal apart can read, on a
 * television, from a sofa, which is the whole set of conditions this app was
 * built for. Their screen reader labels already said the word, so the one
 * reader who was told nothing was the one looking at the screen.
 *
 * The answer goes under the row rather than on the chosen chip, for the reason
 * the profile picker's does: a word that appears on one chip makes that chip
 * wider than it was a moment earlier and slides every chip after it along the
 * row, and a row of controls moving sideways is motion. Under the row the
 * geometry is fixed by construction and the answer gets to be a sentence.
 *
 * The rows are named here rather than in the JSX because both screens draw
 * them and a heading that only the first run says is a heading the parent area
 * cannot label its radio group with. The parent area draws them too now: two
 * unlabelled rows of numbers under one heading left a person working out which
 * row was inches and which was feet from the units on the chips.
 *
 * Each answer is the chip's own label and the state word, in that order, so a
 * person reads the sentence and then finds the chip that matches it without
 * translating anything. "Chosen" is the word the preset rows and every one of
 * these chips already used in their screen reader labels, so this adds no new
 * vocabulary to a screen that already has enough.
 */
export const TV_SIZE_TITLE = 'Television size';
export const SEAT_DISTANCE_TITLE = 'Viewing distance';

export function televisionChosen(inches: number): string {
  return `${Math.round(inches)} inch is chosen.`;
}

export function seatChosen(inches: number): string {
  const feet = Math.round(inches / 12);
  return `${feet} ${feet === 1 ? 'foot' : 'feet'} away is chosen.`;
}

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
export const STRICTNESS_TITLE = 'Viewing preset';
export const ROOM_TITLE = 'TV and seating';
export const HIDDEN_TITLE = 'Hidden scenes';
export const CHECKED_TITLES_TITLE = 'Videos';

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

/** The rule about kids' settings, said the same way as the one about rooms. */
export const PROFILE_ONLY_ADDS =
  "A kid's settings can hide more than Everyone's settings, never less.";

/** Four is the most, and the page says so before the button is gone. */
export const PROFILES_FULL = 'Up to four kids can be added. Remove one to add another.';

/**
 * The question before a kid is removed.
 *
 * Removing a kid took one press and took two things with it: that kid's own
 * preset and room, and their record of what was hidden, which is the only
 * evidence a household ever gets that any of this works. Neither comes back,
 * and the button sat one press away from the picker where a parent goes to
 * switch between kids.
 *
 * It asks in the app's own notice block rather than in a dialog. CLAUDE.md
 * rules out anything that blocks events on Vega, and a browser modal is not a
 * thing this app has: there is no browser, and `Alert` would be a second style
 * of asking on a screen that already has one.
 *
 * The wording follows the same shape as every other question worth asking:
 * name the thing rather than saying "are you sure", say what goes, say what
 * does not, and put the action in both button labels rather than leaving a
 * person to work out which way round OK means. The safe answer is first in the
 * row and takes focus, because a parent who pressed Remove by mistake should
 * be one press from undoing that mistake rather than one press from finishing
 * it.
 *
 * The tone is calm on purpose. Nothing is wrong yet, and nothing here is
 * blocked or waiting, which is what the other two tones mean. Colour carries
 * none of this: the words do all of it, which is the rule everywhere else in
 * this app and the reason this defect was worth fixing in the first place.
 */
export function removeKidPrompt(name: string): Notice {
  return {
    title: `Remove ${name}?`,
    detail: `${name}'s settings and ${name}'s record of what was hidden will be removed. Everyone else stays as they are, and this cannot be undone.`,
    tone: 'calm',
  };
}

/** Both answers say what they do. Neither of them says OK. */
export function removeKidLabel(name: string): string {
  return `Remove ${name}`;
}

export function keepKidLabel(name: string): string {
  return `Keep ${name}`;
}

/** The record, before anything has been hidden. */
export const NOTHING_HIDDEN_YET = 'No scenes hidden yet.';

/** One kid's record, before anything has been hidden for them. */
export function nothingHiddenFor(name: string): string {
  return `No scenes hidden for ${name} yet.`;
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
  const parts = `${count} scene${count === 1 ? '' : 's'} hidden`;
  const line = `${parts}, ${describeHiddenTotal(totalMs)} in total.`;
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
 * It is one settings row: a plain label, the state word at the row's edge, and
 * a helper line under the label saying the thing that matters most about the
 * switch, which is that turning it off changes nothing about what is hidden.
 * The state is a word rather than a highlight, so a parent reading it from the
 * sofa does not have to work out which way round a colour means.
 */
export const CHIME_SECTION_TITLE = 'Sound';
export const CHIME_ROW_TITLE = 'Warning chime';
export const CHIME_ON_LABEL = 'On';
export const CHIME_OFF_LABEL = 'Off';
export const CHIME_NOTE =
  'A soft chime plays before a scene is hidden. Turning it off does not change which scenes are hidden.';

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

export const EXPLAINER_TITLE = 'How Calm Frames works';
export const EXPLAINER_LINES: string[] = [
  'Calm Frames checks every video for flashing before it plays.',
  'Flashing scenes are covered while the sound continues. Captions continue when a video has them.',
  'Some flashing may go undetected.',
  SAFETY_NOTE,
];

/**
 * What Calm Frames does, in one line, said the same way on Home's How it
 * works page and on a title's More info page.
 *
 * "Covered", not "replaced by a still picture". The still is drawn only when
 * a title's signed map carries a scene hold for that interval, and the
 * prepared Acadia maps carry none, so its covers are plain black. Captions
 * are promised only for a title that ships them, for the same reason: Acadia
 * has none, the Harbor demo has one track.
 */
export const PURPOSE_LINE =
  'Watch selected videos with flashing scenes covered while the sound continues.';
/** Home's one line under the title: the benefit, without a promise about tracks. */
export const HOME_BENEFIT_LINE = 'Watch prepared videos with flashing scenes covered.';

/**
 * A running time as a person would say it: "37 seconds", "2 minutes 5 seconds".
 * Home and Details read the same helper so the two never disagree.
 */
export function runtimeLabel(durationMs: number | undefined): string | null {
  if (durationMs === undefined || !(durationMs > 0)) {
    return null;
  }
  return describeHiddenTotal(durationMs);
}
export const CAPTIONS_CONTINUE_LINE =
  'When a video has captions, the captions continue too.';
export const CHECKED_BEFORE_ADDED_LINE = 'Every video is checked before it is added.';
export const ONLY_IN_CALM_FRAMES_LINE =
  'This only works with videos in Calm Frames, not other apps or live TV.';

/**
 * The More info line about one title's own covers, built from what the
 * title carries: how many covered parts its schedule has and whether it
 * ships captions. It never names a still picture, because the schedule does
 * not say whether a still exists for each part.
 */
export function coverLine(count: number, hasCaptions: boolean): string {
  const parts =
    count === 1
      ? 'One brief part of this video is covered.'
      : 'Brief parts of this video are covered.';
  return `${parts} The sound continues.${hasCaptions ? ' Captions continue too.' : ''}`;
}

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
    ? { ...base, detail: /picture stays hidden/i.test(entry.reason)
        ? entry.reason : `${entry.reason} The picture stays hidden.` }
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
