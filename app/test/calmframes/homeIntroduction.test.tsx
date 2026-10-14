import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { AccessibilityInfo, Animated, StyleSheet } from 'react-native';
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { COASTAL_COLORS as CALM_COLORS } from '../../src/calmframes/calmStyles';
import HomeHarborScene from '../../src/calmframes/HomeHarborScene';
import { checkedShelf } from './shelfFixtures';
import { BENIGN_STORY_ID } from '../../src/calmframes/benignStory';
import { InterfaceSoundContext } from '../../src/calmframes/useInterfaceSound';
const titles = checkedShelf();
const demo = titles.find(entry => entry.title.id === BENIGN_STORY_ID)!;
afterEach(() => jest.restoreAllMocks());

test('practice navigation succeeds even if its optional confirmation sound fails', () => {
  const open = jest.fn();
  const launch = jest.fn();
  render(<InterfaceSoundContext.Provider value={{ confirm: () => { throw new Error('sound unavailable'); }, stop: jest.fn() }}>
    <KidHomeScreen titles={titles} onOpen={open} onLaunchControl={launch} />
  </InterfaceSoundContext.Provider>);
  expect(() => fireEvent.press(screen.getByTestId('kid-home-demo'))).not.toThrow();
  expect(launch).toHaveBeenCalledWith('demo');
  expect(open).toHaveBeenCalledTimes(1);
  expect(open).toHaveBeenCalledWith(demo);
});

test('home is the entry, with direct playback and an optional dismissible explanation', () => {
  const play = jest.fn();
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={play} />);
  expect(screen.queryByTestId('picture-hold-introduction')).toBeNull();
  expect(screen.queryByText('Original story')).toBeNull();
  expect(screen.queryByTestId('kid-home-try-demo')).toBeNull();
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  expect(screen.getByText(/Sound continues/)).toBeTruthy();
  expect(screen.queryByTestId('kid-home-watch')).toBeNull();
  expect(play).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
  expect(screen.getByTestId('kid-home-learn').props.hasTVPreferredFocus).toBe(true);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  fireEvent.press(screen.getByTestId('picture-hold-start'));
  expect(play).toHaveBeenCalledWith(demo);
});

test('an unavailable demo cannot be launched from either entry', () => {
  render(<KidHomeScreen titles={titles.map(entry => entry === demo ? { ...entry, status: 'failed' } : entry)} onOpen={jest.fn()} />);
  expect(screen.queryByTestId('kid-home-try-demo')).toBeNull();
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  expect(screen.queryByTestId('picture-hold-start')).toBeNull();
  expect(screen.getByTestId('picture-hold-dismiss').props.hasTVPreferredFocus).toBe(true);
});

test('saving blocks starting the optional demo as well as normal playback', () => {
  const play = jest.fn();
  const view = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={play} />);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  view.rerender(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={play} saving />);
  fireEvent.press(screen.getByTestId('picture-hold-start'));
  expect(play).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
  fireEvent.press(screen.getByTestId('kid-home-watch'));
  expect(play).not.toHaveBeenCalled();
});

test('home ripples require explicit accessibility permission and stop in background', async () => {
  let resolve!: (value: boolean) => void;
  let lifecycle!: (state: string) => void;
  (useKeplerAppStateManager as jest.Mock).mockReturnValue({ getCurrentState: () => 'active', addAppStateListener: (_: string, fn: typeof lifecycle) => { lifecycle = fn; return { remove: jest.fn() }; } });
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockReturnValue(new Promise(done => { resolve = done; }));
  jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(false);
  const start = jest.fn(); const stop = jest.fn();
  const loop = jest.spyOn(Animated, 'loop').mockReturnValue({ start, stop, reset: jest.fn() });
  render(<HomeHarborScene enabled />);
  expect(start).not.toHaveBeenCalled();
  await act(async () => { resolve(false); });
  expect(start).toHaveBeenCalledTimes(1);
  act(() => lifecycle('background'));
  expect(stop).toHaveBeenCalledTimes(1);
  expect(loop).toHaveBeenCalledTimes(1);
});

test.each([true, undefined])('home remains still when reduced motion is %s', async reduced => {
  (useKeplerAppStateManager as jest.Mock).mockReturnValue({ getCurrentState: () => 'active', addAppStateListener: () => ({ remove: jest.fn() }) });
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(reduced as boolean);
  jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(false);
  const loop = jest.spyOn(Animated, 'loop');
  render(<HomeHarborScene enabled />);
  await act(async () => { await Promise.resolve(); });
  expect(loop).not.toHaveBeenCalled();
});

test('home states the supported-title benefit and keeps parental controls tertiary until focused', () => {
  const parent = jest.fn();
  const details = jest.fn();
  const view = render(<KidHomeScreen titles={titles} onOpen={details} onOpenParentArea={parent} />);
  expect(view.getByText('Picture holds on supported videos. Audio continues.')).toBeTruthy();
  expect(view.queryByText('About this story')).toBeNull();
  fireEvent.press(view.getByRole('button', { name: 'Details' }));
  expect(details).toHaveBeenCalledWith(titles.find(entry => entry.title.title === 'Harbor story (prepared locally)'));
  const control = view.getByTestId('kid-home-parent-area');
  expect(StyleSheet.flatten(control.props.style)).toMatchObject({ backgroundColor: 'transparent', borderColor: 'transparent', minHeight: 88, borderWidth: 6 });
  fireEvent(control, 'focus');
  expect(StyleSheet.flatten(control.props.style)).toMatchObject({ backgroundColor: CALM_COLORS.SURFACE_FOCUSED, borderColor: CALM_COLORS.FOCUS_RING, minHeight: 88, borderWidth: 6 });
  expect(StyleSheet.flatten(view.getByTestId('kid-home-parent-area-label').props.style)).toMatchObject({ color: CALM_COLORS.TEXT, textDecorationLine: 'underline' });
  fireEvent.press(control);
  expect(parent).toHaveBeenCalledTimes(1);
  fireEvent(control, 'blur');
  expect(StyleSheet.flatten(control.props.style)).toMatchObject({ backgroundColor: 'transparent', borderColor: 'transparent' });
});
