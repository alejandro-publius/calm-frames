/**
 * Two presses, one launch.
 *
 * A remote can deliver a second Select before the navigator has moved. The
 * route used to call navigate twice; React Navigation folds the second call
 * into the first on a stack, but that is the navigator's behaviour, not the
 * route's, and a later navigator or a deep link could push twice. The route
 * now latches on the first launch and opens the latch on the navigator's
 * focus event, the same event that brings the controls back.
 *
 * Seen to fail, Oct 16 2026: with the latch removed from play() in
 * KidModeScreen, the first test reported navigate called 2 times.
 */
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { Screens } from '../../src/components/navigation/types';
import KidModeScreen from '../../src/screens/KidModeScreen';

const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;

async function startShelf() {
  const listeners: Record<string, Array<() => void>> = {};
  const navigation = {
    navigate: jest.fn(),
    isFocused: () => true,
    addListener: (event: string, listener: () => void) => {
      (listeners[event] ??= []).push(listener);
      return () => undefined;
    },
  };
  render(<KidModeScreen navigation={navigation as never} newSalt={() => 'test-salt'} nowMs={() => NOW} />);
  await screen.findByTestId('kid-mode-first-run');
  const type = (digits: string) => {
    for (const digit of digits) fireEvent.press(screen.getByTestId(`kid-mode-first-run-key-${digit}`));
  };
  type('1357');
  type('1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  await act(async () => { fireEvent.press(screen.getByTestId('kid-mode-first-run-done')); });
  const returnFromPlayer = () => {
    act(() => listeners.blur?.forEach((listener) => listener()));
    act(() => listeners.focus?.forEach((listener) => listener()));
  };
  return { navigation, returnFromPlayer };
}

/**
 * Two native presses in one JavaScript turn. The first press unmounts the
 * control, so a second fireEvent could never find it; two real remote events
 * reach the same handler before React has rendered the first.
 */
function pressTwice(testID: string) {
  const control = screen.UNSAFE_getAllByProps({ testID })[0];
  act(() => {
    control.props.onPress();
    control.props.onPress();
  });
}

it('launches once for two quick Watch presses, and again after the player returns', async () => {
  const { navigation, returnFromPlayer } = await startShelf();
  pressTwice('kid-mode-home-watch');
  expect(navigation.navigate).toHaveBeenCalledTimes(1);
  expect(navigation.navigate).toHaveBeenCalledWith(Screens.PLAYER_SCREEN, expect.objectContaining({ showHomeOpening: true }));
  returnFromPlayer();
  fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
  expect(navigation.navigate).toHaveBeenCalledTimes(2);
});

it('launches once for two quick Watch presses on Details as well', async () => {
  const { navigation, returnFromPlayer } = await startShelf();
  fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
  pressTwice('kid-mode-details-play');
  expect(navigation.navigate).toHaveBeenCalledTimes(1);
  returnFromPlayer();
  expect(screen.getByTestId('kid-mode-details-play').props.hasTVPreferredFocus).toBe(true);
});
