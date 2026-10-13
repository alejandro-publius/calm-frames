/**
 * The player's three answers, and the one that matters.
 *
 * An unguarded player is the failure this project exists to prevent, so the
 * decision is not left to whoever navigated. Every case here was seen to fail:
 * make playbackAccess return "guarded" for an empty object, or make
 * mustStayHidden return false, and these go red.
 */

import { UNGUARDED_CARD, mustStayHidden, playbackAccess } from '../../src/calmframes/playerAccess';

describe('what the player is allowed to show', () => {
  it('runs the guard for a title that arrived with its map', () => {
    expect(
      playbackAccess({
        guarded: { sha256: 'a'.repeat(64), maps: { wcag: '{"version":1}' } },
      }),
    ).toBe('guarded');
    expect(
      playbackAccess({
        guarded: {
          sha256: 'a'.repeat(64),
          mapUrls: { wcag: 'https://example.invalid/map.json' },
        },
      }),
    ).toBe('guarded');
  });

  it('refuses guarded parameters that carry no map', () => {
    // An empty object would otherwise turn the guard off while reading like it
    // was on, which is the worst of the three answers.
    expect(playbackAccess({ guarded: {} })).toBe('unguarded');
    expect(playbackAccess({ guarded: { sha256: 'a'.repeat(64) } })).toBe('unguarded');
    expect(playbackAccess({ guarded: { sha256: '', maps: { wcag: '{}' } } })).toBe(
      'unguarded',
    );
    expect(
      playbackAccess({ guarded: { sha256: 'a'.repeat(64), maps: { wcag: null } } }),
    ).toBe('unguarded');
  });

  it('lets a measurement run play with the harness in charge', () => {
    expect(playbackAccess({ coverTest: 'timing' })).toBe('harness');
    expect(playbackAccess({ coverTest: 'layering' })).toBe('harness');
    expect(playbackAccess({ coverTest: 'off' })).toBe('unguarded');
  });

  it('prefers the guard when a run somehow carries a map as well', () => {
    expect(
      playbackAccess({
        guarded: { sha256: 'a'.repeat(64), maps: { wcag: '{}' } },
        coverTest: 'timing',
      }),
    ).toBe('guarded');
  });

  it('answers unguarded for nothing at all', () => {
    expect(playbackAccess({})).toBe('unguarded');
    expect(playbackAccess({ guarded: null, coverTest: null })).toBe('unguarded');
  });

  it('hides the picture for the unguarded answer and only that one', () => {
    expect(mustStayHidden('unguarded')).toBe(true);
    expect(mustStayHidden('guarded')).toBe(false);
    expect(mustStayHidden('harness')).toBe(false);
  });

  it('says why, in the same words as every other blocked state', () => {
    expect(UNGUARDED_CARD.kind).toBe('unverified');
    expect(UNGUARDED_CARD.title).toBe('This title is unavailable');
    expect(UNGUARDED_CARD.detail).toMatch(/picture stays hidden/);
    expect(UNGUARDED_CARD.announcement).toMatch(/This title is unavailable/);
  });
});
