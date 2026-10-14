import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { AccessibilityInfo, Animated } from 'react-native';
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import HomeHarborScene from '../../src/calmframes/HomeHarborScene';
import { checkedShelf } from './shelfFixtures';
import { BENIGN_STORY_ID } from '../../src/calmframes/benignStory';
const titles = checkedShelf();
const demo = titles.find(entry => entry.title.id === BENIGN_STORY_ID)!;
afterEach(() => jest.restoreAllMocks());

test('home is the entry, with direct playback and an optional dismissible explanation', () => {
  const play = jest.fn();
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={play} />);
  expect(screen.queryByTestId('picture-hold-introduction')).toBeNull();
  expect(screen.queryByText('Original story')).toBeNull();
  fireEvent.press(screen.getByTestId('kid-home-try-demo'));
  expect(play).toHaveBeenCalledWith(demo);
  play.mockClear();
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
