/**
 * What the player's words say about sound, captions and pausing.
 *
 * Every status statement has to agree with the state it describes. A paused
 * player plays nothing, so its card must not say the sound continues; a route
 * with no map has told the player nothing about tracks, so its card promises
 * neither sound nor captions; the covering and after cards promise the sound
 * only, because the card knows nothing about a title's caption tracks.
 *
 * Seen to fail, Oct 16 2026: with the old paused line restored ("Sound
 * resumes when you press Play.") the first test reported the forbidden words.
 */
import { cardAt, COUNTDOWN_LEAD_MS } from '../../src/calmframes/cards';
import { CoverInterval } from '../../src/calmframes/coverSchedule';
import { UNGUARDED_CARD } from '../../src/calmframes/playerAccess';
import { pausedCard } from '../../src/calmframes/usePlaybackPresentation';

const interval: CoverInterval = {
  startMs: 10_000, endMs: 14_000, reason: 'general',
  sources: [{ startMs: 10_000, endMs: 14_000, reason: 'general' }],
};

const forbidden = /captions|sound continues|sound resumes|keep playing|kept playing/i;

describe('while paused', () => {
  it('the covering card says paused and what Play does, and nothing about sound', () => {
    const card = pausedCard(cardAt([interval], 11_000), true);
    expect(card.kind).toBe('covering');
    expect(card.detail).toBe('Paused. The picture stays hidden. Press Play to continue.');
    expect(card.announcement).toBe('Flashing hidden. Paused. The picture stays hidden. Press Play to continue.');
    expect(card.detail).not.toMatch(forbidden);
    expect(card.announcement).not.toMatch(forbidden);
  });

  it('the countdown card says how long remains and keeps Skip', () => {
    const card = pausedCard(cardAt([interval], 10_000 - COUNTDOWN_LEAD_MS + 1_500), true);
    expect(card.kind).toBe('countdown');
    expect(card.detail).toMatch(/^Paused, \d+ seconds before the flashing\. Press Play to continue, or Skip to jump past it\.$/);
    expect(card.announcement.startsWith('Flashing coming up. Paused, ')).toBe(true);
    expect(card.detail).not.toMatch(forbidden);
    expect(card.skipToMs).toBeDefined();
  });

  it('a card that is not about a cover is left alone, and so is a playing card', () => {
    const after = cardAt([interval], 14_500);
    expect(pausedCard(after, true)).toBe(after);
    const playing = cardAt([interval], 11_000);
    expect(pausedCard(playing, false)).toBe(playing);
  });
});

describe('while playing', () => {
  it('the covering and after cards promise the sound only', () => {
    expect(cardAt([interval], 11_000).detail).toBe('Sound continues while this scene is hidden.');
    expect(cardAt([interval], 14_500).detail).toBe('Sound continued.');
    expect(cardAt([interval], 11_000).announcement).not.toMatch(/captions/i);
    expect(cardAt([interval], 14_500).announcement).not.toMatch(/captions/i);
  });
});

describe('with nothing to check', () => {
  it('the unavailable card says the picture stays hidden and what to do, once', () => {
    expect(UNGUARDED_CARD.kind).toBe('unverified');
    expect(UNGUARDED_CARD.title).toBe('This video is unavailable');
    expect(UNGUARDED_CARD.detail).toBe('The picture stays hidden. Go back to the library.');
    expect(UNGUARDED_CARD.announcement).toBe('This video is unavailable. The picture stays hidden. Go back to the library.');
    expect(UNGUARDED_CARD.announcement.match(/This video is unavailable/g)).toHaveLength(1);
    expect(UNGUARDED_CARD.detail).not.toMatch(forbidden);
  });
});
