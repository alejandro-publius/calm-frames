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
  EXPLAINER_LINES,
  EXPLAINER_TARGET_SECONDS,
  EXPLAINER_WORDS_PER_MINUTE,
  Notice,
  noticeForTitle,
  NO_TITLES,
  PIN_NOT_SET,
  PIN_PROMPT,
  readingSeconds,
  ROOM_ONLY_ADDS,
  SAFETY_NOTE,
  TITLE_FAILED,
  TITLE_PENDING,
  TITLE_STALE,
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
    for (const name of fs.readdirSync(SOURCE_DIR)) {
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

  it('keeps the wording from the reader underneath the general line', () => {
    const notice = noticeForTitle(
      entry({
        status: 'failed',
        rejection: 'wrong-file',
        reason: 'The check for this title belongs to a different file.',
      }),
    );
    expect(notice?.detail).toContain(TITLE_FAILED.detail);
    expect(notice?.detail).toContain('belongs to a different file');
  });
});
