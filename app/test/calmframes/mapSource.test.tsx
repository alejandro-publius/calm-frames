/**
 * Where a map comes from, and what the shelf does with each answer.
 *
 * `lookupMap` has been right since it was written and nothing called it, so
 * the registry was a feature the app had rather than a feature the app used.
 * These tests drive the real shelf: the catalog goes through mapSource.ts, the
 * index is the signed fixture under `fixtures/registry`, and what comes back
 * goes on to `checkTitle` and to the player exactly as it does on a device.
 *
 * The fixtures are described at the top of mapRegistry.test.ts. They are a
 * real signed index and the real maps it names, built by
 * `pipeline/tests/make_registry_fixture.py`, and there is no private key in
 * this repository. `registry_swapped_map.json` is a sham and its name says so.
 *
 * The three paths, and the mutation that was watched go red for each, are
 * quoted on the tests themselves.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import {
  fallsThroughToLocalMap,
  resolveCatalog,
  resolveMaps,
  withoutRegistry,
} from '../../src/calmframes/mapSource';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import {
  OFFLINE_PUBLIC_KEY_BASE64,
  OFFLINE_TITLE_ID,
} from '../../src/calmframes/offlineTitle';
import { CatalogTitle } from '../../src/calmframes/titleStatus';
import { Screens } from '../../src/components/navigation/types';
import KidModeScreen, { defaultCatalog } from '../../src/screens/KidModeScreen';

const FIXTURES = path.join(__dirname, 'fixtures');
const REGISTRY_DIR = path.join(FIXTURES, 'registry');
const BASE_URL = 'https://maps.example/calm-frames/';
const REGISTRY_URL = `${BASE_URL}registry.json`;
const BURSTS_MAP_URL = `${BASE_URL}maps/bursts.wcag.json`;

/** The public half of the fixture key. The private half is in nobody's tree. */
const KEY = '/brschmFHfvmbulBzPdh2EzwlSOUvAcvXF3X5bNAtJY=';

const registryText = fs.readFileSync(
  path.join(REGISTRY_DIR, 'registry.json'),
  'utf8',
);
const burstsMapText = fs.readFileSync(
  path.join(REGISTRY_DIR, 'maps', 'bursts.wcag.json'),
  'utf8',
);
const swappedMapText = fs.readFileSync(
  path.join(FIXTURES, 'registry_swapped_map.json'),
  'utf8',
);

const BURSTS_SHA256 =
  '94b63ee75c9873c23df210c82f0e65319b492666fed5383ce647754f46460c5e';
const REGISTRY_MADE_AT = Date.parse(JSON.parse(registryText).created_utc);
const NOW = REGISTRY_MADE_AT + 1_000;
const OFFLINE_NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;

/** A catalog entry for the file the index lists, carrying no map of its own. */
function burstsTitle(maps: CatalogTitle['maps'] = {}): CatalogTitle {
  return {
    id: 'bursts',
    title: 'Test pattern',
    uri: 'https://example.invalid/bursts.mp4',
    sha256: BURSTS_SHA256,
    maps,
    durationMs: 30_000,
  };
}

/** Everything the fixture directory would serve, by URL. */
function served(overrides: Record<string, string | null> = {}) {
  return async (url: string): Promise<string | null> => {
    if (Object.prototype.hasOwnProperty.call(overrides, url)) {
      return overrides[url];
    }
    if (!url.startsWith(BASE_URL)) {
      return null;
    }
    const file = path.join(REGISTRY_DIR, url.slice(BASE_URL.length));
    return fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
  };
}

/** Change the served bytes without re-signing, which is the attack. */
function tampered(change: (document: any) => void): string {
  const document = JSON.parse(registryText);
  change(document);
  return JSON.stringify(document, null, 2);
}

interface ShelfOptions {
  catalog?: CatalogTitle[];
  registryUrl?: string;
  fetchText?: (url: string) => Promise<string | null>;
  publicKeyBase64?: string;
  nowMs?: number;
}

/** The real shelf, past the first run, with the index wired in. */
async function openShelf(options: ShelfOptions = {}) {
  const navigate = jest.fn();
  render(
    <KidModeScreen
      navigation={{ navigate } as never}
      catalog={options.catalog}
      registryUrl={options.registryUrl}
      fetchText={options.fetchText}
      publicKeyBase64={options.publicKeyBase64 ?? KEY}
      newSalt={() => 'test-salt'}
      nowMs={() => options.nowMs ?? NOW}
    />,
  );
  const type = (digits: string) => {
    for (const digit of digits) {
      fireEvent.press(screen.getByTestId(`kid-mode-first-run-key-${digit}`));
    }
  };
  await screen.findByTestId('kid-mode-first-run');
  type('1357');
  type('1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-done'));
  // The index is asked in an effect, so let it answer.
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
  return { navigate };
}

/** Open the parent area on an already open shelf, through the PIN. */
async function openParentArea() {
  fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
  for (const digit of '1357') {
    fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
  }
  await screen.findByTestId('kid-mode-parent-open');
}

describe('the registry served it', () => {
  /**
   * The path the feature exists for: the app has a file and its hash, the
   * index names a map for that hash, and that map is what plays.
   *
   * Seen to fail: with the `lookupMap` call taken out of `resolveMaps` and
   * replaced by a not-listed verdict, which is what the app did before this
   * existed, six of these went red and this one said:
   *
   *     ● the registry served it › hands the shelf the map the index named,
   *       for a title that carried none
   *
   *       expect(received).toBeTruthy()
   *
   *       Received: null
   *
   *       at Object.toBeTruthy (test/calmframes/mapSource.test.tsx:173:65)
   */
  it('hands the shelf the map the index named, for a title that carried none', async () => {
    const { navigate } = await openShelf({
      catalog: [burstsTitle()],
      registryUrl: REGISTRY_URL,
      fetchText: served(),
    });

    expect(screen.queryByTestId('kid-mode-home-poster-bursts')).toBeTruthy();
    expect(
      screen.getByTestId('kid-mode-home-poster-bursts').props.accessibilityLabel,
    ).toContain('checked');

    fireEvent.press(screen.getByTestId('kid-mode-home-poster-bursts'));
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    const [route, params] = navigate.mock.calls[0];
    expect(route).toBe(Screens.PLAYER_SCREEN);
    // The bytes the index verified, not a second fetch of the same URL.
    expect(params.guarded.maps.wcag).toBe(burstsMapText);
  });

  it('says which source served it, in one line a reader can tell apart', async () => {
    await openShelf({
      catalog: [burstsTitle()],
      registryUrl: REGISTRY_URL,
      fetchText: served(),
    });
    expect(console.info).toHaveBeenCalledWith(
      `[mapSource] bursts wcag: served by registry, ${BURSTS_MAP_URL}`,
    );
  });

  /**
   * Fail closed while the answer is in flight.
   *
   * A title listed on the strength of the bundled map and refused by the index
   * a moment later would be playable in between.
   */
  it('lists nothing while the index has been asked and has not answered', async () => {
    await openShelf({
      catalog: [burstsTitle()],
      registryUrl: REGISTRY_URL,
      fetchText: () => new Promise<string | null>(() => {}),
    });
    expect(screen.queryByTestId('kid-mode-home-poster-bursts')).toBeNull();
    expect(screen.getByTestId('kid-mode-home-empty')).toBeTruthy();
  });
});

describe('the registry had nothing, so the map the app holds served it', () => {
  /**
   * The offline case, which is also the flight mode case: there is no index to
   * read, so the bundled map is what plays. It is signed, bound to this file's
   * hash and checked by the same reader, so nothing is being trusted that was
   * not being trusted before.
   *
   * Seen to fail: with `registry-missing` taken out of FALL_THROUGH_REFUSALS,
   * so an unreachable index blocked instead of falling through, this said:
   *
   *     ● the registry had nothing, so the map the app holds served it › plays
   *       the bundled title when there is no index to read
   *
   *       expect(received).toBeTruthy()
   *
   *       Received: null
   *
   *       at Object.toBeTruthy (test/calmframes/mapSource.test.tsx:243:7)
   */
  it('plays the bundled title when there is no index to read', async () => {
    const { navigate } = await openShelf({
      registryUrl: REGISTRY_URL,
      fetchText: async () => null,
      publicKeyBase64: OFFLINE_PUBLIC_KEY_BASE64,
      nowMs: OFFLINE_NOW,
    });

    expect(
      screen.queryByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`),
    ).toBeTruthy();
    fireEvent.press(screen.getByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`));
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    expect(navigate.mock.calls[0][1].guarded.maps.wcag).toBe(OFFLINE_MAP_JSON);
    expect(console.info).toHaveBeenCalledWith(
      `[mapSource] ${OFFLINE_TITLE_ID} wcag: served by bundled, registry-missing`,
    );
  });

  it('falls through to the catalog map for a file the index does not list', async () => {
    const unlisted: CatalogTitle = {
      ...burstsTitle({ wcag: OFFLINE_MAP_JSON }),
      id: 'unlisted',
      sha256: 'f'.repeat(64),
    };
    const done = await resolveMaps(unlisted, {
      registryUrl: REGISTRY_URL,
      publicKeyBase64: KEY,
      nowMs: () => NOW,
      profiles: ['wcag'],
      fetchText: served(),
    });
    expect(done.refusal).toBeUndefined();
    expect(done.sources.wcag).toBe('catalog');
    expect(done.title.maps?.wcag).toBe(OFFLINE_MAP_JSON);
  });

  it('reads the index once for a whole catalog, not once per title', async () => {
    const asked: string[] = [];
    const counting = async (url: string) => {
      asked.push(url);
      return served()(url);
    };
    await resolveCatalog([burstsTitle(), burstsTitle()], {
      registryUrl: REGISTRY_URL,
      publicKeyBase64: KEY,
      nowMs: () => NOW,
      profiles: ['wcag'],
      fetchText: counting,
    });
    expect(asked.filter((url) => url === REGISTRY_URL)).toHaveLength(1);
  });

  it('asks nothing at all when no index is configured', () => {
    // The gradient by name: it is the title whose map is compiled in, and it
    // is no longer the first one in the catalog.
    const bundled = defaultCatalog().find((title) => title.id === OFFLINE_TITLE_ID);
    expect(bundled).toBeDefined();
    const done = withoutRegistry(bundled!, ['wcag']);
    expect(done.sources.wcag).toBe('bundled');
    expect(done.refusal).toBeUndefined();
  });
});

describe('the registry entry was tampered with', () => {
  /**
   * The difference that matters. A missing entry falls through to the map the
   * app already holds. A tampered one does not, even when that map is sitting
   * right there, because an index that does not check out is somebody serving
   * us something.
   *
   * Seen to fail: with `fallsThroughToLocalMap` returning true for every
   * refusal, so a tampered index fell back to the catalog map the way a
   * missing entry does, the poster was on the shelf and this said:
   *
   *     ● the registry entry was tampered with › keeps the title off the
   *       shelf, and does not fall back to the map the app holds
   *
   *       expect(received).toBeNull()
   *
   *       Received: {"_fiber": {"_debugHookTypes": null, ... "type": "View"}}
   *       (the rest of the fiber node, elided here rather than paraphrased)
   *
   *       at Object.toBeNull (test/calmframes/mapSource.test.tsx:324:65)
   */
  it('keeps the title off the shelf, and does not fall back to the map the app holds', async () => {
    const pointedElsewhere = tampered((document) => {
      document.files[BURSTS_SHA256].maps.wcag.path = 'maps/calm_gradient.wcag.json';
    });
    await openShelf({
      // The title carries a map of its own, and it is still not played.
      catalog: [burstsTitle({ wcag: burstsMapText })],
      registryUrl: REGISTRY_URL,
      fetchText: served({ [REGISTRY_URL]: pointedElsewhere }),
    });
    expect(screen.queryByTestId('kid-mode-home-poster-bursts')).toBeNull();

    await openParentArea();
    expect(screen.getByTestId('kid-mode-parent-reason-bursts').props.children).toContain(
      'the picture stays hidden',
    );
  });

  it('refuses a validly signed map that is not the one the index named', async () => {
    const done = await resolveMaps(burstsTitle({ wcag: burstsMapText }), {
      registryUrl: REGISTRY_URL,
      publicKeyBase64: KEY,
      nowMs: () => NOW,
      profiles: ['wcag'],
      fetchText: served({ [BURSTS_MAP_URL]: swappedMapText }),
    });
    expect(done.refusal).toBe('not-the-listed-map');
    // Nothing is left to play off.
    expect(done.title.maps).toEqual({});
  });

  it('falls through for exactly two refusals and blocks on the rest', () => {
    expect(fallsThroughToLocalMap('registry-missing')).toBe(true);
    expect(fallsThroughToLocalMap('not-listed')).toBe(true);
    for (const reason of [
      'registry-unparseable',
      'registry-wrong-version',
      'registry-unsigned',
      'registry-unknown-key',
      'registry-bad-signature',
      'registry-stale',
      'entry-unusable',
      'map-refused',
      'not-the-listed-map',
    ] as const) {
      expect([reason, fallsThroughToLocalMap(reason)]).toEqual([reason, false]);
    }
  });
});
