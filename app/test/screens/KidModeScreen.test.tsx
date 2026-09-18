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

import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
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

/** A moment when the bundled map is neither unmade nor stale. */
const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;

function renderKidMode() {
  const navigate = jest.fn();
  render(
    <KidModeScreen
      navigation={{ navigate } as never}
      newSalt={() => 'test-salt'}
      nowMs={() => NOW}
    />,
  );
  return { navigate };
}

/** The first run, end to end, with the PIN 1357. */
function finishFirstRun() {
  const type = (digits: string) => {
    for (const digit of digits) {
      fireEvent.press(screen.getByTestId(`kid-mode-first-run-key-${digit}`));
    }
  };
  type('1357');
  type('1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-done'));
}

describe('reaching Calm Frames', () => {
  it('opens on the first run, and lands on the shelf when it is done', () => {
    renderKidMode();
    expect(screen.getByTestId('kid-mode-first-run')).toBeTruthy();
    finishFirstRun();
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
  });

  it('lists the bundled title, checked by the real reader', () => {
    renderKidMode();
    finishFirstRun();
    expect(
      screen.getByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`),
    ).toBeTruthy();
    expect(
      screen.getByTestId(`kid-mode-home-badge-${OFFLINE_TITLE_ID}-label`).props
        .children,
    ).toBe('Checked');
  });

  it('opens the title, then hands the player the map it verified', () => {
    const { navigate } = renderKidMode();
    finishFirstRun();
    fireEvent.press(screen.getByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`));
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

  it('never navigates to the player without the map', () => {
    // The whole project is the claim that nothing plays unchecked, so every
    // call this screen can make to the player is checked, not just the one in
    // the happy path above.
    const { navigate } = renderKidMode();
    finishFirstRun();
    fireEvent.press(screen.getByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`));
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

  it('reaches the parent area, behind the PIN that was just set', () => {
    renderKidMode();
    finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    expect(screen.getByTestId('kid-mode-parent')).toBeTruthy();
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();

    for (const digit of '1357') {
      fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
    }
    expect(screen.getByTestId('kid-mode-parent-open')).toBeTruthy();
  });

  it('comes back to the shelf from the parent area', () => {
    renderKidMode();
    finishFirstRun();
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    fireEvent.press(screen.getByTestId('kid-mode-parent-back'));
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
  });
});

describe('what goes to the player', () => {
  const entry = checkTitle(defaultCatalog()[0], {
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
