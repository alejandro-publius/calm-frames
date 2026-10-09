/**
 * The shelf's first frame: the pictures on the posters.
 *
 * Everything here runs on the real bundled shelf, checked by the real reader,
 * because the claim is about what a household sees on the first screen and a
 * made-up title would prove nothing about that.
 */

import { render, screen } from '@testing-library/react-native';
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import {
  BENIGN_STORY_ID,
  benignStoryPoster,
} from '../../src/calmframes/benignStory';
import { BENIGN_STORY_PUBLIC_KEY } from '../../src/calmframes/benignStoryData';
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { shelfPoster } from '../../src/calmframes/shelf';
import { CheckedTitle } from '../../src/calmframes/titleStatus';
import { checkedShelf, SHELF_NOW } from './shelfFixtures';

const shelf = checkedShelf();
const harbor = shelf.find((entry) => entry.title.id === BENIGN_STORY_ID)!;
const others = shelf.filter((entry) => entry.title.id !== BENIGN_STORY_ID);

/** The first still the real verifier hands back for Harbor's WCAG map. */
function verifiedFirstStill(): string | undefined {
  const verdict = verifyFlashMap(harbor.title.maps?.wcag, {
    publicKeyBase64: BENIGN_STORY_PUBLIC_KEY,
    expectedSha256: harbor.title.sha256,
    nowMs: SHELF_NOW,
  });
  if (!verdict.ok) {
    throw new Error(`Harbor's map did not verify: ${verdict.reason}`);
  }
  return verdict.map.sceneHolds?.[0]?.imageDataUri;
}

describe('the pictures on the shelf', () => {
  it('starts from a shelf where every bundled title checked', () => {
    expect(harbor).toBeDefined();
    expect(others.length).toBeGreaterThanOrEqual(2);
    expect(shelf.map((entry) => entry.status)).toEqual(
      shelf.map(() => 'verified'),
    );
  });

  it("puts Harbor's own first signed still on its poster, uncropped and without a fade", () => {
    const still = verifiedFirstStill();
    expect(still).toMatch(/^data:image\/jpeg;base64,/);
    expect(shelfPoster(harbor)).toBe(still);

    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    const image = screen.getByTestId(`kid-home-poster-image-${BENIGN_STORY_ID}`);
    expect(image.props.source).toEqual({ uri: still });
    expect(image.props.resizeMode).toBe('contain');
    expect(image.props.fadeDuration).toBe(0);
  });

  /**
   * Seen to fail with benignStoryPoster checking only the status, so every
   * checked title got Harbor's still:
   *
   *     Expected: undefined
   *     Received: "data:image/jpeg;base64,/9j//gAPTGF2YzYz..."
   */
  it('lends no title a picture it does not carry', () => {
    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    for (const entry of others) {
      expect(shelfPoster(entry)).toBeUndefined();
      expect(
        screen.queryByTestId(`kid-home-poster-image-${entry.title.id}`),
      ).toBeNull();
    }
  });

  /**
   * One case per condition in benignStoryPoster. Each was seen to fail on
   * its own, with only that condition taken out, as a still where this test
   * expects none.
   */
  it.each<[string, CheckedTitle]>([
    ['a check that did not pass', { ...harbor, status: 'failed' }],
    [
      'a title that only borrows the id',
      { ...harbor, title: { ...harbor.title, uri: 'file:///pkg/other.mp4' } },
    ],
    ['a check that never read the WCAG map', { ...harbor, verifiedProfiles: ['broadcast'] }],
    [
      'a WCAG map that is not the compiled one',
      {
        ...harbor,
        title: {
          ...harbor.title,
          maps: { ...harbor.title.maps, wcag: `${harbor.title.maps?.wcag} ` },
        },
      },
    ],
  ])('gives no still to %s', (_name, entry) => {
    expect(benignStoryPoster(entry)).toBeUndefined();
  });

  /**
   * Seen to fail with the status check taken out of shelfPoster:
   *
   *     Expected: undefined
   *     Received: "https://example.invalid/poster.jpg"
   */
  it('shows a published poster only for a title that checked', () => {
    const published = {
      ...others[0],
      title: { ...others[0].title, posterUrl: 'https://example.invalid/poster.jpg' },
    };
    expect(shelfPoster(published)).toBe('https://example.invalid/poster.jpg');
    expect(shelfPoster({ ...published, status: 'pending' })).toBeUndefined();
  });
});
