import { useHideSplashScreenCallback, usePreventHideSplashScreen } from '@amazon-devices/react-native-kepler';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import App from '../../src/App';
import { initializeStore } from '../../src/store';

jest.mock('@amazon-devices/react-native-kepler', () => ({
  Platform: { isTV: true },
  useHideSplashScreenCallback: jest.fn(),
  usePreventHideSplashScreen: jest.fn(),
}));
jest.mock('../../src/store', () => ({ initializeStore: jest.fn() }));
jest.mock('../../src/styles/ThemeBuilders', () => ({ createTheme: () => ({}) }));
jest.mock('../../src/calmframes/HarborOpening', () => 'HarborOpening');
jest.mock('../../src/components/navigation/AppStack', () => 'AppStack');
jest.mock('react-redux', () => ({ Provider: ({ children }: { children: React.ReactNode }) => children }));
jest.mock('@amazon-devices/kepler-ui-components', () => ({ ThemeProvider: ({ children }: { children: React.ReactNode }) => children }));
jest.mock('@amazon-devices/react-navigation__native', () => ({ NavigationContainer: ({ children }: { children: React.ReactNode }) => children }));

it('replaces the platform splash only after the wave root is laid out, then opens navigation', async () => {
  let resolve!: (store: unknown) => void;
  (initializeStore as jest.Mock).mockReturnValue(new Promise((yes) => { resolve = yes; }));
  const hideSplash = jest.fn();
  (useHideSplashScreenCallback as jest.Mock).mockReturnValue(hideSplash);
  render(<App />);
  expect(usePreventHideSplashScreen).toHaveBeenCalled();
  expect(hideSplash).not.toHaveBeenCalled();
  expect(screen.UNSAFE_getByType('HarborOpening' as never)).toBeTruthy();
  fireEvent(screen.getByTestId('app-root'), 'layout', { nativeEvent: { layout: { width: 1920, height: 1080 } } });
  expect(hideSplash).toHaveBeenCalledTimes(1);
  await act(async () => resolve({}));
  expect(screen.UNSAFE_queryByType('HarborOpening' as never)).toBeNull();
  expect(screen.UNSAFE_getByType('AppStack' as never)).toBeTruthy();
});
