/**
 * The shelf's first frame: the pictures and the words on the posters.
 *
 * Everything here runs on the real bundled shelf, checked by the real reader,
 * because the claim is about what a household sees on the first screen and a
 * made-up title would prove nothing about that.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
import { filmStill } from '../../src/calmframes/HomeHarborScene';
import { WORLD } from '../../src/calmframes/CoastalWorld';
import React from 'react';
import { Image } from 'react-native';
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
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import TitleArtwork from '../../src/calmframes/TitleArtwork';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { OFFLINE_TITLE_ID } from '../../src/calmframes/offlineTitle';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
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

    // Home is the coastal map now; its pictures are presentation artwork, never the signed still.
    render(<KidHomeScreen titles={shelf} onOpen={jest.fn()} />);
    expect(screen.getByTestId('coastal-world')).toBeTruthy();
    const images = screen.UNSAFE_getAllByType(Image);
    expect(images.length).toBeGreaterThan(0);
    for (const image of images) {
      expect(JSON.stringify(image.props.source)).not.toContain('data:image/jpeg');
      expect(image.props.resizeMode).toBe('cover');
      expect(image.props.fadeDuration).toBe(0);
    }
  });

  /**
   * Seen to fail with benignStoryPoster checking only the status, so every
   * checked title got Harbor's still:
   *
   *     Expected: undefined
   *     Received: "data:image/jpeg;base64,/9j//gAPTGF2YzYz..."
   */
  it('uses dedicated presentation artwork for each prepared title and test clip', () => {
    for (const entry of others) {
      expect(shelfPoster(entry)).toBeUndefined();
      const presentation = titlePresentation(entry.title);
      // A map destination's card shows its own photograph.
      if (presentation.menuArt) {
        expect(filmStill(presentation.menuArt)).toEqual(presentation.menuArt === 'forest'
          ? require('../../assets/image/tv/forest-creek.jpg') : presentation.menuArt === 'coastal'
            ? require('../../assets/image/tv/acadia-coast.png') : require('../../assets/image/tv/sea-otters-alaska.jpg'));
        continue;
      }
      const view = render(<TitleArtwork illustrated entry={entry} testID="art" />);
      expect(view.getByTestId('art').props.source).toEqual(entry.title.id === OFFLINE_TITLE_ID
        ? require('../../assets/image/tv/gradient.png')
        : entry.title.title.startsWith('Acadia coastal scenery') ? require('../../assets/image/tv/acadia-coast.png')
          : require('../../assets/image/tv/harbor-illustrated.png'));
      view.unmount();
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

  it('uses factual Harbor metadata and preserves Play and Details actions', () => {
    const prepared = shelf.find((entry) => entry.title.id === preparedId)!;
    const onOpen = jest.fn();
    const onPlay = jest.fn();
    const home = render(<KidHomeScreen titles={shelf} onOpen={onOpen} onPlay={onPlay} />);
    expect(screen.getByTestId('kid-home-title').props.children).toBe('Choose an island');
    expect(screen.queryByTestId('kid-home-meta')).toBeNull();
    expect(screen.queryByText('Picture holds on supported videos. Audio continues.')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-home-more-info'));
    expect(onOpen).toHaveBeenCalledWith(prepared);
    fireEvent.press(screen.getByTestId('kid-home-watch'));
    expect(onPlay).toHaveBeenCalledWith(prepared);
    home.unmount();

    render(<TitleDetailsScreen entry={prepared} onPlay={onPlay} />);
    expect(screen.queryByTestId('title-details-description')).toBeNull();
    expect(screen.getByTestId('title-details-meta').props.children).toBe('20 seconds');
    expect(screen.queryByText('Original story')).toBeNull();
  });

  it('retains the full practice-hold explanation when that demo leads the library', () => {
    const onPlay = jest.fn();
    render(<KidHomeScreen titles={[harbor]} onOpen={jest.fn()} onPlay={onPlay} />);
    fireEvent.press(screen.getByTestId('kid-home-learn'));
    expect(screen.getByText(/two simulated picture pauses/i)).toBeTruthy();
    fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
    expect(screen.getByTestId(`kid-home-poster-qualifier-${BENIGN_STORY_ID}`).props.children)
      .toMatch(/Demo/i);
    expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toMatch(/Watch demo/);
    fireEvent.press(screen.getByTestId('kid-home-watch'));
    expect(onPlay).toHaveBeenCalledWith(harbor);
  });

  it('keeps practice and playback diagnostics in optional help, with factual descriptions in details', () => {
    const open = jest.fn();
    render(<KidHomeScreen titles={shelf} onOpen={open} />);
    expect(screen.queryByText('Demo')).toBeNull();
    expect(screen.queryByText('Playback test')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-home-learn'));
    fireEvent.press(screen.getByTestId('picture-hold-demo-details'));
    expect(open).toHaveBeenCalledWith(harbor);
    fireEvent.press(screen.getByTestId('picture-hold-playback-check'));
    expect(open).toHaveBeenCalledWith(shelf.find(entry => entry.title.id === OFFLINE_TITLE_ID));
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
      qualifier: 'Picture pause demo',
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
    const secondLines = ['Demo', 'Playback check'];
    render(<KidHomeScreen titles={shelf.filter(entry => entry.title.id === BENIGN_STORY_ID || entry.title.id === OFFLINE_TITLE_ID)} onOpen={jest.fn()} />);
    const measured = () =>
      measureText(screen.toJSON() as unknown as RenderedNode, { background: WORLD.BACKGROUND }).filter((line) => secondLines.includes(line.text)).slice(-3);

    const resting = measured();
    expect(resting.map((line) => line.text).sort()).toEqual([...secondLines].sort());
    for (const line of resting) {
      // The cards stand on the coastal map, so they are its cream cards.
      expect(line.background).toBe(WORLD.SURFACE);
      expect(line.fontSize).toBeGreaterThanOrEqual(floors.textSizeUnits);
      expect(line.contrast).toBeGreaterThanOrEqual(floors.textContrast);
    }

    fireEvent(screen.getByTestId(`kid-home-poster-${BENIGN_STORY_ID}`), 'focus');
    const focused = measured().find(
      (line) => line.text === 'Demo',
    );
    expect(focused?.background).toBe(WORLD.SURFACE_FOCUSED);
    expect(focused?.contrast).toBeGreaterThanOrEqual(floors.textContrast);
  });
});
