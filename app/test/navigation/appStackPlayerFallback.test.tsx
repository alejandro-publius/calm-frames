// The app stack gives the player route the harbor-opening fallback.
import { createStackNavigator } from '@amazon-devices/react-navigation__stack';
import { render } from '@testing-library/react-native';
import React from 'react';
import { useDispatch } from 'react-redux';
import AppStack from '../../src/components/navigation/AppStack';
import { playerRouteFallback } from '../../src/components/navigation/playerRouteFallback';
import { Screens } from '../../src/components/navigation/types';

jest.mock('../../src/utils/WithSuspense', () => ({
  WithSuspense: jest.fn((Component: unknown, fallback: unknown) => ({ Component, fallback })),
}));
jest.mock('../../src/components/navigation/AppDrawer', () => 'AppDrawer');
jest.mock('../../src/store/search/searchSlice', () => ({ fetchPlaylists: jest.fn() }));
jest.mock('@amazon-devices/react-navigation__stack', () => ({
  createStackNavigator: jest.fn().mockReturnValue({
    Navigator: jest.fn(({ children }) => <>{children}</>),
    Screen: jest.fn(() => null),
  }),
}));

test('the player route loads behind the harbor opening, the others keep their fallbacks', () => {
  (useDispatch as unknown as jest.Mock).mockReturnValue(jest.fn());
  render(<AppStack />);
  const screens = (createStackNavigator().Screen as unknown as jest.Mock).mock.calls.map((call) => call[0]);
  const player = screens.find((screen) => screen.name === Screens.PLAYER_SCREEN);
  expect(player.component.fallback).toBe(playerRouteFallback);
  const details = screens.find((screen) => screen.name === Screens.DETAILS_SCREEN);
  expect(details.component.fallback).toBeUndefined();
});
