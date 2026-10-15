/**
 * The route that makes Calm Frames reachable.
 *
 * Before this screen, the shelf, the details page and the parent area were
 * real components that nothing in the app rendered: only tests could open
 * them. So the tests that matter here are about reachability and about what
 * is handed to the player.
 *
 * The map used is the real one bundled in the package, verified by the real
 * Ed25519 reader, so a title reaching the shelf here is a title that would
 * reach it on a device.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { BackHandler, Platform } from 'react-native';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import {
  OFFLINE_TITLE_ID,
  OFFLINE_VIDEO_URI,
} from '../../src/calmframes/offlineTitle';
import { Screens } from '../../src/components/navigation/types';
import KidModeScreen, {
  defaultCatalog,
  guardedParamsFor,
  titleDataFor,
} from '../../src/screens/KidModeScreen';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { OFFLINE_PUBLIC_KEY_BASE64 } from '../../src/calmframes/offlineTitle';
import { BENIGN_STORY_ID, BENIGN_STORY_URI } from '../../src/calmframes/benignStory';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import * as householdStorage from '../../src/calmframes/householdStorage';
import { emptyPinGate } from '../../src/calmframes/parentGate';
import { newFamily } from '../../src/calmframes/profiles';

/** A moment when the bundled map is neither unmade nor stale. */
const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;

async function renderKidMode() {
  const navigate = jest.fn();
  render(
    <KidModeScreen
      navigation={{ navigate } as never}
      newSalt={() => 'test-salt'}
      nowMs={() => NOW}
    />,
  );
  await screen.findByTestId('kid-mode-first-run');
  return { navigate };
}

/** The first run, end to end, with the PIN 1357. */
async function finishFirstRun() {
  const type = (digits: string) => {
    for (const digit of digits) {
      fireEvent.press(screen.getByTestId(`kid-mode-first-run-key-${digit}`));
    }
  };
  type('1357');
  type('1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  await act(async () => {
    fireEvent.press(screen.getByTestId('kid-mode-first-run-done'));
  });
}

describe('reaching Calm Frames', () => {
  it('returns focus to the opened title through details, player and parent area', async () => {
    const { navigate } = await renderKidMode();
    await finishFirstRun();
    const lastPoster = 'kid-mode-home-learn';
    fireEvent.press(screen.getByTestId(lastPoster));
    fireEvent.press(screen.getByTestId('picture-hold-playback-check'));
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    expect(navigate).toHaveBeenCalledWith(Screens.PLAYER_SCREEN, expect.anything());
    // The stack retains this details route underneath the player.
    expect(screen.getByTestId('kid-mode-details-play').props.hasTVPreferredFocus).toBe(true);
    expect(screen.queryByTestId('kid-mode-home-watch')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(screen.getByTestId(lastPoster).props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId('kid-mode-home-watch').props.hasTVPreferredFocus).toBe(false);
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    fireEvent.press(screen.getByTestId('kid-mode-parent-back'));
    expect(screen.getByTestId('kid-mode-home-parent-area').props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId(lastPoster).props.hasTVPreferredFocus).toBe(false);
  });

  it('retains the home caller when playback begins with Watch now', async () => {
    const { navigate } = await renderKidMode();
    await finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
    expect(navigate).toHaveBeenCalledWith(Screens.PLAYER_SCREEN,
      expect.objectContaining({ showHomeOpening: true }));
    expect(screen.getByTestId('kid-mode-home-watch')).toBeTruthy();
    expect(screen.queryByTestId('kid-mode-details-play')).toBeNull();
  });

  it('handles remote Back through details, parent area and credits', async () => {
    const tv = jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(true);
    let back: (() => boolean | null | undefined) | undefined;
    const listener = jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_event, handler) => {
      back = handler;
      return { remove: jest.fn() };
    });
    try {
      await renderKidMode();
      await finishFirstRun();
      const poster = 'kid-mode-home-learn';
      fireEvent.press(screen.getByTestId(poster));
      fireEvent.press(screen.getByTestId('picture-hold-playback-check'));
      act(() => { expect(back?.()).toBe(true); });
      expect(screen.getByTestId(poster).props.hasTVPreferredFocus).toBe(true);
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      act(() => { expect(back?.()).toBe(true); });
      expect(screen.getByTestId('kid-mode-home-parent-area').props.hasTVPreferredFocus).toBe(true);
      expect(screen.getByTestId(poster).props.hasTVPreferredFocus).toBe(false);
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      for (const digit of '1357') {
        fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
      }
      await screen.findByTestId('kid-mode-parent-open');
      fireEvent.press(screen.getByTestId('kid-mode-parent-credits'));
      expect(screen.getByTestId('kid-mode-credits')).toBeTruthy();
      act(() => { expect(back?.()).toBe(true); });
      expect(screen.getByTestId('kid-mode-parent')).toBeTruthy();
      expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
    } finally {
      listener.mockRestore();
      tv.mockRestore();
    }
  });

  it('opens the labelled story with captions and the prepared Extra cautious timing', async () => {
    const { navigate } = await renderKidMode();
    await finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
    fireEvent.press(screen.getByTestId('picture-hold-demo-details'));
    expect(JSON.stringify(screen.getByTestId('kid-mode-details-demo-label').props.children)).toContain('picture pauses twice');
    expect(screen.getByTestId('kid-mode-details-summary').props.children).toContain('8 seconds');
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    const [, params] = navigate.mock.calls[0];
    expect(params.data.uri).toBe(BENIGN_STORY_URI);
    expect(params.data.textTrack[0].uri).toMatch(/harbor\.vtt$/);
    expect(params.guarded.settings.preset).toBe('extra-cautious');
  });
  it('opens on the first run, and lands on the shelf when it is done', async () => {
    await renderKidMode();
    expect(screen.getByTestId('kid-mode-first-run')).toBeTruthy();
    await finishFirstRun();
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
  });

  it('retains the verified playback check inside optional help', async () => {
    await renderKidMode(); await finishFirstRun();
    expect(screen.queryByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`)).toBeNull();
    fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
    expect(screen.getByTestId('picture-hold-playback-check').props.accessibilityLabel).toBe('Check playback');
  });

  it('opens the title, then hands the player the map it verified', async () => {
    const { navigate } = await renderKidMode();
    await finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
    fireEvent.press(screen.getByTestId('picture-hold-playback-check'));
    expect(screen.getByTestId('kid-mode-details')).toBeTruthy();

    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    expect(navigate).toHaveBeenCalledTimes(1);
    const [route, params] = navigate.mock.calls[0];
    expect(route).toBe(Screens.PLAYER_SCREEN);
    expect(params.data.uri).toBe(OFFLINE_VIDEO_URI);
    expect(params.guarded.sha256).toBe(
      JSON.parse(OFFLINE_MAP_JSON).source.sha256,
    );
    expect(params.guarded.maps?.wcag).toBe(OFFLINE_MAP_JSON);
    expect(params.guarded.settings).toEqual(DEFAULT_SETTINGS);
  });

  it('never navigates to the player without the map', async () => {
    // The whole project is the claim that nothing plays unchecked, so every
    // call this screen can make to the player is checked, not just the one in
    // the happy path above.
    const { navigate } = await renderKidMode();
    await finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
    fireEvent.press(screen.getByTestId('picture-hold-playback-check'));
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));

    expect(navigate.mock.calls.length).toBeGreaterThan(0);
    for (const [route, params] of navigate.mock.calls) {
      if (route !== Screens.PLAYER_SCREEN) {
        continue;
      }
      expect(typeof params?.guarded?.sha256).toBe('string');
      expect(params.guarded.sha256.length).toBe(64);
      const maps = params.guarded.maps ?? {};
      expect(Object.values(maps).filter(Boolean).length).toBeGreaterThan(0);
    }
  });

  it('reaches the parent area, behind the PIN that was just set', async () => {
    await renderKidMode();
    await finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    expect(screen.getByTestId('kid-mode-parent')).toBeTruthy();
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();

    for (const digit of '1357') {
      fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
    }
    await screen.findByTestId('kid-mode-parent-open');
    expect(screen.getByTestId('kid-mode-parent-open')).toBeTruthy();
  });

  it('comes back to the shelf from the parent area', async () => {
    await renderKidMode();
    await finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    fireEvent.press(screen.getByTestId('kid-mode-parent-back'));
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
  });

  /**
   * Set a PIN from the parent area, then finish the first run.
   *
   * On a fresh device the first run is on screen because nothing is saved
   * yet, and the route's view never left the shelf. From the parent area's
   * Set a PIN it is on screen because the view was set to the first run on
   * purpose, and finishing it has to set the view back, or the parent stays
   * on the explainer with the PIN already saved and no way off it.
   *
   * Storage refuses a household record with no PIN in it, so no device loads
   * one today and the parent area's Set a PIN is a guard rather than a path
   * a household takes. To reach the press, the loaded record is handed to the
   * route past the validator; what is written back goes through it as usual.
   *
   * Seen to fail with finishFirstRun writing the household and nothing else.
   * The explainer was still on screen after Open checked library:
   *
   *     expect(received).toBeNull()
   *
   *     Received: {"_fiber": {... "elementType": "RCTScrollView", ...}}
   *
   *     at Object.toBeNull (test/screens/KidModeScreen.test.tsx:264:58)
   */
  it('leaves the first run for the shelf after Set a PIN from the parent area', async () => {
    const loaded = jest
      .spyOn(householdStorage, 'loadHousehold')
      .mockResolvedValueOnce({
        version: 1,
        family: newFamily(DEFAULT_SETTINGS),
        gate: emptyPinGate(),
      });
    const storage = {
      getItem: jest.fn(async () => null),
      setItem: jest.fn(async () => undefined),
    };
    try {
      render(
        <KidModeScreen
          navigation={{ navigate: jest.fn() } as never}
          householdStorage={storage}
          newSalt={() => 'test-salt'}
          nowMs={() => NOW}
        />,
      );
      await screen.findByTestId('kid-mode-home');
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      // No PIN, so no keypad: the one offer is to set one.
      expect(screen.queryByTestId('kid-mode-parent-keypad')).toBeNull();
      fireEvent.press(screen.getByTestId('kid-mode-parent-set-pin'));
      expect(screen.getByTestId('kid-mode-first-run')).toBeTruthy();

      await finishFirstRun();
      expect(screen.queryByTestId('kid-mode-first-run')).toBeNull();
      expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
      expect(storage.setItem).toHaveBeenCalledTimes(1);

      // The PIN that was just set is the one the parent area now asks for.
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      for (const digit of '1357') {
        fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
      }
      await screen.findByTestId('kid-mode-parent-open');
    } finally {
      loaded.mockRestore();
    }
  });
});

describe('the shelf a household lands on', () => {
  it('keeps Harbor first and the gradient last in the bundled catalog', () => {
    const ids = defaultCatalog().map((title) => title.id);
    expect(ids[0]).toBe(BENIGN_STORY_ID);
    expect(ids[ids.length - 1]).toBe(OFFLINE_TITLE_ID);
    expect(ids.slice(1, -1)).toEqual(
      packagedLibrary.titles(DEFAULT_SETTINGS).map((title) => title.id),
    );
  });

  it('offers one dominant Harbor action and keeps diagnostics out of the primary catalog', async () => {
    await renderKidMode(); await finishFirstRun();
    expect(screen.getByTestId('kid-mode-home-watch').props.hasTVPreferredFocus).toBe(true);
    expect(screen.queryAllByTestId(/^kid-mode-home-poster-(?!image-|title-|qualifier-)/)).toHaveLength(0);
    expect(screen.queryByText('Demo')).toBeNull();
    expect(screen.queryByText('Playback test')).toBeNull();
    expect(screen.getByTestId('home-harbor-scene')).toBeTruthy();
    fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
    expect(screen.getByTestId('picture-hold-start')).toBeTruthy();
    expect(screen.getByTestId('picture-hold-playback-check')).toBeTruthy();
  });
});

describe('what goes to the player', () => {
  const gradient = defaultCatalog().find((title) => title.id === OFFLINE_TITLE_ID);
  if (!gradient) {
    throw new Error('the bundled catalog has lost the gradient');
  }
  const entry = checkTitle(gradient, {
    settings: DEFAULT_SETTINGS,
    publicKeyBase64: OFFLINE_PUBLIC_KEY_BASE64,
    nowMs: NOW,
  });

  it('builds the title data the player opens', () => {
    const data = titleDataFor(entry);
    expect(data.uri).toBe(OFFLINE_VIDEO_URI);
    expect(data.id).toBe(OFFLINE_TITLE_ID);
    expect(data.format).toBe('MP4');
  });

  it('builds the guarded parameters from the checked title itself', () => {
    const guarded = guardedParamsFor(entry, DEFAULT_SETTINGS);
    expect(guarded.sha256).toBe(entry.title.sha256);
    expect(guarded.maps).toBe(entry.title.maps);
    expect(guarded.durationMs).toBe(entry.title.durationMs);
    expect(guarded.titleId).toBe(OFFLINE_TITLE_ID);
  });
});
