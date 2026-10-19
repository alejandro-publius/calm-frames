/**
 * The words, checked as words.
 *
 * Two things are being protected here.
 *
 * The first is the sentence about what this is and is not. docs/SAFETY.md
 * fixes it word for word, and the app says it in the first run and in the
 * parent area. A test that only checked it was "about right" would let it
 * drift into a promise, so this one checks the sentence itself and then
 * searches every Calm Frames source file for the two phrasings we never use.
 *
 * The second is house style. Short sentences, no dashes of any kind, and every
 * state that stops something says what happens to the picture. A person
 * reading these for the first time is a parent at the end of a long day or a
 * twelve year old who wants to watch something.
 */

import fs from 'fs';
import path from 'path';
import { cardAt } from '../../src/calmframes/cards';
import {
  APPROVED_SAFETY_CLAUSE,
  BACKEND_UNREACHABLE,
  BACKEND_UNREACHABLE_EMPTY,
  CAPTIONS_CONTINUE_LINE,
  CHECKED_BEFORE_ADDED_LINE,
  coverLine,
  describeHiddenTotal,
  DETECTION_LIMITS_LINE,
  EVERYONE_LABEL,
  EXPLAINER_LINES,
  EXPLAINER_TARGET_SECONDS,
  EXPLAINER_WORDS_PER_MINUTE,
  HIDDEN_TITLE,
  hiddenSummary,
  hideDayHeading,
  keepKidLabel,
  nextKidName,
  Notice,
  noticeForTitle,
  nothingHiddenFor,
  NOTHING_HIDDEN_YET,
  NO_TITLES,
  ONLY_IN_CALM_FRAMES_LINE,
  PIN_NOT_SET,
  PIN_PROMPT,
  PROFILE_ONLY_ADDS,
  PURPOSE_LINE,
  readingSeconds,
  removeKidLabel,
  removeKidPrompt,
  ROOM_ONLY_ADDS,
  ROOM_TITLE,
  SAFETY_NOTE,
  seatChosen,
  SEAT_DISTANCE_TITLE,
  sectionFor,
  STRICTNESS_TITLE,
  televisionChosen,
  TV_SIZE_TITLE,
  TITLE_FAILED,
  TITLE_PENDING,
  TITLE_STALE,
  whoIsWatching,
  whoseSettingsThese,
} from '../../src/calmframes/copy';
import { CheckedTitle } from '../../src/calmframes/titleStatus';

const SOURCE_DIR = path.join(__dirname, '..', '..', 'src', 'calmframes');

const ALL_NOTICES: Notice[] = [
  NO_TITLES,
  BACKEND_UNREACHABLE,
  BACKEND_UNREACHABLE_EMPTY,
  TITLE_PENDING,
  TITLE_FAILED,
  TITLE_STALE,
  PIN_NOT_SET,
  PIN_PROMPT,
];

function entry(overrides: Partial<CheckedTitle>): CheckedTitle {
  return {
    title: {
      id: 'one',
      title: 'One',
      uri: 'https://example.invalid/one.m3u8',
      sha256: 'a'.repeat(64),
    },
    status: 'verified',
    segments: [],
    hiddenMs: 0,
    verifiedProfiles: ['wcag'],
    ...overrides,
  };
}

describe('the sentence about what this is', () => {
  it('is the approved one, word for word', () => {
    expect(APPROVED_SAFETY_CLAUSE).toBe(
      'reduces exposure to flashing above published limits in the videos it plays; not a medical device.',
    );
    expect(SAFETY_NOTE).toBe(`Calm Frames ${APPROVED_SAFETY_CLAUSE}`);
  });

  it('is what the first run shows', () => {
    expect(EXPLAINER_LINES).toContain(SAFETY_NOTE);
  });

  it('never turns into a promise anywhere in the app', () => {
    const banned = [/prevents? seizures/i, /seizure[- ]proof/i, /stops? seizures/i];
    // Every file, in every folder: on Oct 18 an integration/ folder made this
    // read a directory and throw, and the guard stopped checking anything.
    const names = (fs.readdirSync(SOURCE_DIR, { recursive: true }) as string[])
      .filter((name) => fs.statSync(path.join(SOURCE_DIR, name)).isFile());
    expect(names.some((name) => name.startsWith(`integration${path.sep}`))).toBe(true);
    for (const name of names) {
      const text = fs.readFileSync(path.join(SOURCE_DIR, name), 'utf8');
      for (const phrase of banned) {
        expect(`${name}: ${phrase.source} ${phrase.test(text)}`).toBe(
          `${name}: ${phrase.source} false`,
        );
      }
    }
  });
});

describe('house style', () => {
  it('uses no dash of any kind in anything a person reads', () => {
    const lines = [
      ...ALL_NOTICES.flatMap((notice) => [notice.title, notice.detail]),
      ...EXPLAINER_LINES,
      ROOM_ONLY_ADDS,
      PROFILE_ONLY_ADDS,
      // The parent area's own words, which used to be literals in the JSX and
      // so were never read by this check at all.
      NOTHING_HIDDEN_YET,
      nothingHiddenFor('Robin'),
      whoIsWatching('Robin'),
      whoseSettingsThese(EVERYONE_LABEL),
      hiddenSummary(25, 100_000, 20),
      sectionFor(STRICTNESS_TITLE, 'Robin'),
      sectionFor(ROOM_TITLE, 'Robin'),
      sectionFor(HIDDEN_TITLE, 'Robin'),
      hideDayHeading(new Date(2026, 8, 17).getTime(), new Date(2026, 8, 20).getTime()),
      // The room chips' answers and the question before a kid is removed.
      TV_SIZE_TITLE,
      SEAT_DISTANCE_TITLE,
      televisionChosen(85),
      seatChosen(48),
      removeKidPrompt('Robin').title,
      removeKidPrompt('Robin').detail,
      removeKidLabel('Robin'),
      keepKidLabel('Robin'),
      // What the app says it does, on How it works and More info.
      PURPOSE_LINE,
      CAPTIONS_CONTINUE_LINE,
      CHECKED_BEFORE_ADDED_LINE,
      ONLY_IN_CALM_FRAMES_LINE,
      DETECTION_LIMITS_LINE,
      coverLine(1, false),
      coverLine(3, true),
    ];
    for (const line of lines) {
      expect(`${line} has em dash: ${line.includes('—')}`).toBe(
        `${line} has em dash: false`,
      );
      expect(`${line} has en dash: ${line.includes('–')}`).toBe(
        `${line} has en dash: false`,
      );
    }
  });

  it('ends every line it shows, and shouts at nobody', () => {
    for (const notice of ALL_NOTICES) {
      expect(notice.detail.endsWith('.')).toBe(true);
      expect(notice.title).not.toContain('!');
      expect(notice.detail).not.toContain('!');
      // A title a person can take in at a glance from the sofa.
      expect(notice.title.split(' ').length).toBeLessThanOrEqual(7);
    }
  });

  it('says what happens to the picture whenever something is stopped', () => {
    for (const notice of [TITLE_PENDING, TITLE_FAILED, TITLE_STALE]) {
      expect(notice.detail).toMatch(/picture stays hidden|Nothing plays/);
    }
  });

  it('says the same thing on the card over the video as on the page', () => {
    // The card the player shows over a title that did not verify and the
    // notice its page shows are written in different files. They are read by
    // the same person minutes apart, so they say the same thing.
    const card = cardAt([], 0, { rejection: 'missing' });
    expect(card.detail).toMatch(/picture stays hidden/);
    expect(TITLE_PENDING.detail).toMatch(/picture stays hidden/);
  });
});

describe('the record in the parent area', () => {
  it('counts one part as one part, and reads long totals as minutes', () => {
    expect(hiddenSummary(1, 4_000, 1)).toBe('1 scene hidden, 4 seconds in total.');
    // One second used to read "1 seconds".
    expect(describeHiddenTotal(1_000)).toBe('1 second');
    expect(describeHiddenTotal(59_000)).toBe('59 seconds');
    expect(describeHiddenTotal(120_000)).toBe('2 minutes');
    // 312 seconds in all is arithmetic a tired parent should not have to do.
    expect(describeHiddenTotal(312_000)).toBe('5 minutes 12 seconds');
  });

  it('says where the list stops, and stays quiet when it does not stop', () => {
    expect(hiddenSummary(25, 100_000, 20)).toBe(
      '25 scenes hidden, 1 minute 40 seconds in total. The 20 most recent are below.',
    );
    expect(hiddenSummary(3, 12_000, 3)).toBe('3 scenes hidden, 12 seconds in total.');
  });

  it('names the day rather than leaving a bare time to be guessed at', () => {
    const now = new Date(2026, 8, 17, 21, 0).getTime();
    expect(hideDayHeading(new Date(2026, 8, 17, 19, 30).getTime(), now)).toBe('Today');
    expect(hideDayHeading(new Date(2026, 8, 16, 19, 30).getTime(), now)).toBe(
      'Yesterday',
    );
    expect(hideDayHeading(new Date(2026, 8, 11, 19, 30).getTime(), now)).toBe(
      'Friday 11 September',
    );
    // The first of a month is not yesterday just because the number is lower.
    expect(hideDayHeading(new Date(2026, 8, 1, 19, 30).getTime(), now)).toBe(
      'Tuesday 1 September',
    );
  });

  it('says the same thing whether the record is one kid or the household', () => {
    expect(NOTHING_HIDDEN_YET).toBe('No scenes hidden yet.');
    expect(nothingHiddenFor('Robin')).toBe('No scenes hidden for Robin yet.');
  });
});

describe('the room chips, in words', () => {
  /**
   * Seen to fail with the plural dropped from `seatChosen`:
   *
   *     Expected: "8 feet away is chosen."
   *     Received: "8 foot away is chosen."
   */
  it('names the chip rather than describing it in other words', () => {
    // Whatever the sentence says is on a chip in the row above it, spelled the
    // same way, so nobody has to translate one into the other from a sofa.
    expect(televisionChosen(55)).toBe('55 inch is chosen.');
    expect(seatChosen(96)).toBe('8 feet away is chosen.');
    expect(seatChosen(48)).toBe('4 feet away is chosen.');
    // One foot would read "1 feet". No choice in the list is that close, and
    // the rule costs nothing.
    expect(seatChosen(12)).toBe('1 foot away is chosen.');
  });

  it('gives both rows a name, because two rows of numbers are not one row', () => {
    expect(TV_SIZE_TITLE).toBe('Television size');
    expect(SEAT_DISTANCE_TITLE).toBe('Viewing distance');
  });
});

describe('the question before a kid is removed', () => {
  /**
   * Naming the kid, saying what goes, and putting the action in both labels.
   *
   * "Are you sure?" with OK and Cancel asks a person to remember what they
   * pressed and to work out which button means which. This one says the name
   * in the question and in both answers.
   *
   * Seen to fail with the title back to a bare 'Are you sure?':
   *
   *     Expected: "Remove Robin?"
   *     Received: "Are you sure?"
   */
  it('names the kid, says what goes, and says it cannot be undone', () => {
    const prompt = removeKidPrompt('Robin');
    expect(prompt.title).toBe('Remove Robin?');
    expect(prompt.detail).toContain('Robin');
    expect(prompt.detail).toContain('record of what was hidden');
    expect(prompt.detail).toContain('cannot be undone');
    expect(prompt.detail.endsWith('.')).toBe(true);
    // A title a person takes in at a glance, like every other one.
    expect(prompt.title.split(' ').length).toBeLessThanOrEqual(7);
    // Nothing is wrong yet and nothing is blocked, so it is not dressed as an
    // error. The words carry all of this, which is the rule everywhere else.
    expect(prompt.tone).toBe('calm');
  });

  it('puts the action in both answers, and OK in neither', () => {
    expect(removeKidLabel('Robin')).toBe('Remove Robin');
    expect(keepKidLabel('Robin')).toBe('Keep Robin');
    for (const label of [removeKidLabel('Robin'), keepKidLabel('Robin')]) {
      expect(label).not.toMatch(/^(OK|Okay|Yes|No|Cancel)$/i);
    }
  });
});

describe('naming a new kid', () => {
  it('reaches for the plain name first, then a number nobody has', () => {
    expect(nextKidName('Kid', ['Robin'])).toBe('Kid');
    expect(nextKidName('Kid', ['Kid'])).toBe('Kid 2');
    expect(nextKidName('Kid', ['Kid', 'Kid 2'])).toBe('Kid 3');
    // A gap is filled rather than skipped past.
    expect(nextKidName('Kid', ['Kid', 'Kid 3'])).toBe('Kid 2');
  });
});

describe('what the app says it does', () => {
  /**
   * The covers are black unless a signed scene hold exists for the interval,
   * and the prepared Acadia maps carry none, so neither line may promise a
   * still picture. Captions are promised only where a title ships them.
   */
  it('says covered, never a still picture, and promises nothing it cannot keep', () => {
    for (const line of [PURPOSE_LINE, CAPTIONS_CONTINUE_LINE, ...EXPLAINER_LINES, coverLine(2, false)]) {
      expect(line).not.toMatch(/still picture|safe|guaranteed|nothing flagged|never holds/i);
      expect(line.endsWith('.')).toBe(true);
    }
    expect(PURPOSE_LINE).toMatch(/covered/);
    expect(PURPOSE_LINE).toMatch(/sound continues/);
  });

  it('says plainly which videos it works with, and names what it does not cover', () => {
    expect(PURPOSE_LINE).toMatch(/^Flashing scenes are covered/);
    expect(ONLY_IN_CALM_FRAMES_LINE).toBe(
      'Calm Frames works only with prepared videos in this app, not other apps or live TV.',
    );
  });

  it('names captions only for a title that has them', () => {
    expect(coverLine(3, false)).toBe('Flagged scenes are covered. Original audio is kept when the video has sound.');
    expect(coverLine(3, true)).toBe('Flagged scenes are covered. Original audio is kept when the video has sound. Captions continue too.');
    expect(coverLine(1, false)).toBe('The flagged scene is covered. Original audio is kept when the video has sound.');
  });
});

describe('the explainer', () => {
  it('is about twenty seconds of reading', () => {
    const seconds = readingSeconds(EXPLAINER_LINES, EXPLAINER_WORDS_PER_MINUTE);
    // Twenty seconds is the target. Anything from fifteen to twenty five still
    // reads as a short explanation rather than a wall of text or a slogan.
    expect(seconds).toBeGreaterThanOrEqual(EXPLAINER_TARGET_SECONDS - 5);
    expect(seconds).toBeLessThanOrEqual(EXPLAINER_TARGET_SECONDS + 5);
  });

  it('counts words, not characters', () => {
    expect(readingSeconds(['one two three'], 180)).toBeCloseTo(1, 5);
    expect(readingSeconds([''], 180)).toBe(0);
  });
});

describe('which notice a title gets', () => {
  it('gives a verified title none at all', () => {
    expect(noticeForTitle(entry({ status: 'verified' }))).toBeNull();
  });

  it('separates waiting from blocked', () => {
    expect(noticeForTitle(entry({ status: 'pending', rejection: 'missing' }))?.tone).toBe(
      'waiting',
    );
    expect(
      noticeForTitle(entry({ status: 'failed', rejection: 'bad-signature' }))?.tone,
    ).toBe('blocked');
    expect(noticeForTitle(entry({ status: 'failed', rejection: 'stale' }))?.title).toBe(
      TITLE_STALE.title,
    );
  });

  it('blocks a title with no rejection recorded, rather than calling it waiting', () => {
    // The room being stricter than the check is a real block with no rejection
    // of its own, and treating it as waiting would be the wrong way round.
    const notice = noticeForTitle(entry({ status: 'failed' }));
    expect(notice?.tone).toBe('blocked');
  });

  it('explains a refusal once, without repeating the general status', () => {
    const notice = noticeForTitle(
      entry({
        status: 'failed',
        rejection: 'wrong-file',
        reason: 'The check for flashing belongs to a different version of this video.',
      }),
    );
    expect(notice?.title).toBe(TITLE_FAILED.title);
    expect(notice?.detail).toBe('The check for flashing belongs to a different version of this video. The picture stays hidden.');
  });
});
