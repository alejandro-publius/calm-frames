/**
 * The shelf's first frame: the pictures and the words on the posters.
 *
 * Everything here runs on the real bundled shelf, checked by the real reader,
 * because the claim is about what a household sees on the first screen and a
 * made-up title would prove nothing about that.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import {
  BENIGN_STORY_ID,
  benignStoryPoster,
  benignStoryTitle,
} from '../../src/calmframes/benignStory';
import { BENIGN_STORY_PUBLIC_KEY } from '../../src/calmframes/benignStoryData';
import { CALM_COLORS } from '../../src/calmframes/calmStyles';
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { OFFLINE_TITLE_ID } from '../../src/calmframes/offlineTitle';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import {
  shelfLabel,
  shelfPoster,
  spokenShelfLabel,
} from '../../src/calmframes/shelf';
import { CatalogTitle, CheckedTitle } from '../../src/calmframes/titleStatus';
import { measureText, RenderedNode } from '../../src/calmframes/uiContrast';
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

  it("keeps signed playback stills separate from approved presentation artwork", () => {
    const still = verifiedFirstStill();
    expect(still).toMatch(/^data:image\/jpeg;base64,/);
    expect(shelfPoster(harbor)).toBe(still);

    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    const image = screen.getByTestId(`kid-home-poster-image-${BENIGN_STORY_ID}`);
    expect(image.props.source).toEqual(require('../../assets/image/tv/harbor.png'));
    expect(image.props.resizeMode).toBe('cover');
    expect(image.props.fadeDuration).toBe(0);
  });

  /**
   * Seen to fail with benignStoryPoster checking only the status, so every
   * checked title got Harbor's still:
   *
   *     Expected: undefined
   *     Received: "data:image/jpeg;base64,/9j//gAPTGF2YzYz..."
   */
  it('uses dedicated illustration assets for the known prepared story and test clip', () => {
    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    for (const entry of others) {
      expect(shelfPoster(entry)).toBeUndefined();
      expect(
        screen.queryByTestId(`kid-home-poster-image-${entry.title.id}`),
      ).toBeTruthy();
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

describe('the words on the shelf', () => {
  const preparedId = packagedLibrary.titles(DEFAULT_SETTINGS)[0].id;

  /** What one poster says, top to bottom, ending with its shield. */
  const posterWords = (id: string): unknown[] =>
    screen
      .getByTestId(`kid-home-poster-${id}`)
      .findAll((node) => (node.type as string) === 'Text')
      .map((node) => node.props.children);

  /**
   * Seen to fail with the full catalog title back on the first line and no
   * second line:
   *
   *     -   "Harbor story",
   *     -   "Benign demo, practice holds",
   *     +   "Harbor story (benign demo)",
   *         "Checked",
   */
  it('names each bundled title, and says what it is on the line under the name', () => {
    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    expect(posterWords(BENIGN_STORY_ID)).toEqual([
      'Harbor demo',
      'Scheduled scene holds',
    ]);
    expect(posterWords(preparedId)).toEqual([
      'Harbor',
      'Original story',
    ]);
    expect(posterWords(OFFLINE_TITLE_ID)).toEqual([
      'Calm gradient',
      'Playback test',
    ]);
    expect(
      screen.getByTestId(`kid-home-poster-${BENIGN_STORY_ID}`).props
        .accessibilityLabel,
    ).toBe('Harbor demo, Scheduled scene holds, checked');
  });

  /**
   * Seen to fail with Harbor's second line given to anything named Harbor
   * story, the shortcut this guards against:
   *
   *     Expected pattern: not /practice|demo/i
   *     Received string:      "Benign demo, practice holds"
   */
  it('keeps the two Harbors apart, and only the demo one says practice', () => {
    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    const [benignName, benignLine] = posterWords(BENIGN_STORY_ID);
    const [preparedName, preparedLine] = posterWords(preparedId);
    expect(benignName).toBe('Harbor demo');
    expect(preparedName).toBe('Harbor');
    expect(benignLine).toMatch(/scheduled scene holds/i);
    expect(preparedLine).not.toMatch(/practice|demo/i);
  });

  /**
   * Seen to fail with the capital dropped from the second line:
   *
   *     -   "qualifier": "Prepared locally",
   *     +   "qualifier": "prepared locally",
   */
  it.each([
    ['Harbor story (prepared locally)', 'Harbor story', 'Prepared locally'],
    ['Movie (2019) (extended)', 'Movie (2019)', 'Extended'],
    ['  Spaced   (  note  )  ', 'Spaced', 'Note'],
    ['Plain title', 'Plain title', undefined],
    ['(Untitled)', '(Untitled)', undefined],
    ['A (b) c', 'A (b) c', undefined],
  ])('reads %j as a name, and a second line only when it has one', (full, name, qualifier) => {
    const title: CatalogTitle = {
      id: 'any',
      title: full,
      uri: 'file:///pkg/any.mp4',
      sha256: 'a'.repeat(64),
    };
    expect(shelfLabel(title)).toEqual(qualifier ? { name, qualifier } : { name });
  });

  it("writes Harbor's own second line only for the bundled Harbor", () => {
    expect(shelfLabel(benignStoryTitle())).toEqual({
      name: 'Harbor story',
      qualifier: 'Benign demo, practice holds',
    });
    // Anything else with the same words is read like any catalog title.
    expect(
      shelfLabel({ ...benignStoryTitle(), uri: 'file:///pkg/other.mp4' }),
    ).toEqual({ name: 'Harbor story', qualifier: 'Benign demo' });
    expect(spokenShelfLabel({ name: 'Plain title' })).toBe('Plain title');
  });

  /**
   * The ten foot floors, on the resting card and on the focused one.
   *
   * tenFoot.test.tsx measures text on screens at rest, so a colour that holds
   * on the card and fails on the lighter focused fill would get past it. Seen
   * to fail with the second line painted VERIFIED, which does exactly that,
   * while tenFoot.test.tsx stayed green:
   *
   *     Expected: >= 4.5
   *     Received:    3.853900988791338
   */
  it('draws the second line at the ten foot floors, resting and focused', () => {
    const floors = { textSizeUnits: 32, textContrast: 4.5 };
    const secondLines = ['Scheduled scene holds', 'Original story', 'Playback test'];
    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    const measured = () =>
      measureText(screen.toJSON() as unknown as RenderedNode, { background: CALM_COLORS.BACKGROUND }).filter((line) => secondLines.includes(line.text)).slice(-3);

    const resting = measured();
    expect(resting.map((line) => line.text).sort()).toEqual([...secondLines].sort());
    for (const line of resting) {
      expect(line.background).toBe(CALM_COLORS.BACKGROUND);
      expect(line.fontSize).toBeGreaterThanOrEqual(floors.textSizeUnits);
      expect(line.contrast).toBeGreaterThanOrEqual(floors.textContrast);
    }

    fireEvent(screen.getByTestId(`kid-home-poster-${BENIGN_STORY_ID}`), 'focus');
    const focused = measured().find(
      (line) => line.text === 'Scheduled scene holds',
    );
    expect(focused?.background).toBe(CALM_COLORS.SURFACE_FOCUSED);
    expect(focused?.contrast).toBeGreaterThanOrEqual(floors.textContrast);
  });
});
