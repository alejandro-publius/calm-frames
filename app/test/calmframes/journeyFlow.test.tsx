import React from 'react';
import { act, fireEvent, render } from '@testing-library/react-native';
import { AccessibilityInfo, Animated, StyleSheet } from 'react-native';
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import JourneyStatus from '../../src/calmframes/JourneyStatus';
import LibraryOpening from '../../src/calmframes/LibraryOpening';
import PlayerOpening from '../../src/calmframes/PlayerOpening';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import HouseholdStorageScreen from '../../src/calmframes/HouseholdStorageScreen';
import { CALM_JOURNEY, CALM_TEXT, CALM_WORLD } from '../../src/calmframes/calmStyles';
import { checkedShelf } from './shelfFixtures';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));

afterEach(() => { jest.restoreAllMocks(); jest.useRealTimers(); });

test('boot is a still map until actual work completes, with no progress amount or timer', () => {
  jest.useFakeTimers();
  const timing = jest.spyOn(Animated, 'timing');
  const view = render(<LibraryOpening testID="opening" status="Loading your settings." />);
  expect(StyleSheet.flatten(view.getByTestId('opening').props.style).backgroundColor).toBe(CALM_WORLD.BACKGROUND);
  expect(view.getByRole('progressbar').props.accessibilityValue).toBeUndefined();
  expect(view.getByText('Loading your settings.')).toBeTruthy();
  expect(timing).not.toHaveBeenCalled();
  expect(jest.getTimerCount()).toBe(0);
});

test('verification, frame wait and return follow state and retain title typography and Back ownership', () => {
  const back = jest.fn();
  const view = render(<PlayerOpening title="Forest" menuArt="forest" checking onBack={back} />);
  expect(view.getByText('Checking this video...')).toBeTruthy();
  expect(view.getAllByText('Forest')).toHaveLength(2);
  fireEvent.press(view.getByTestId('player-opening-back'));
  expect(back).toHaveBeenCalledTimes(1);
  view.rerender(<PlayerOpening title="Forest" menuArt="forest" onBack={back} />);
  expect(view.getByText('Opening your video...')).toBeTruthy();
  view.rerender(<PlayerOpening title="Forest" menuArt="forest" returning onBack={back} />);
  expect(view.getByText('Going back...')).toBeTruthy();
  expect(view.queryByTestId('player-opening-back')).toBeNull();
  expect(StyleSheet.flatten(view.getAllByText('Forest')[1].props.style).fontFamily).toBe(CALM_TEXT.feature.fontFamily);
});

test.each([true, undefined, false])('journey motion obeys the system preference %s without delaying status', async (reduced) => {
  (useKeplerAppStateManager as jest.Mock).mockReturnValue({ getCurrentState: () => 'active', addAppStateListener: () => ({ remove: jest.fn() }) });
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(reduced as boolean);
  const events = AccessibilityInfo as unknown as { addEventListener(name: string, callback: (value: boolean) => void): { remove(): void } };
  jest.spyOn(events, 'addEventListener').mockReturnValue({ remove: jest.fn() });
  const stop = jest.fn();
  const timing = jest.spyOn(Animated, 'timing').mockReturnValue({ start: jest.fn(), stop, reset: jest.fn() });
  const view = render(<JourneyStatus status="Opening your video..." motionEnabled />);
  expect(view.getByText('Opening your video...')).toBeTruthy();
  await act(async () => { await Promise.resolve(); });
  if (reduced === false) expect(timing).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ duration: CALM_JOURNEY.DURATION, useNativeDriver: true, isInteraction: false }));
  else expect(timing).not.toHaveBeenCalled();
  view.unmount();
  if (reduced === false) expect(stop).toHaveBeenCalled();
});

test('selection remains visibly marked when focus moves from a poster to Watch', () => {
  const titles = checkedShelf();
  const forest = titles.find(entry => titlePresentation(entry.title).menuArt === 'forest')!;
  const play = jest.fn();
  const view = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={play} />);
  fireEvent(view.getByTestId(`kid-home-poster-${forest.title.id}`), 'focus');
  fireEvent(view.getByTestId(`kid-home-poster-${forest.title.id}`), 'blur');
  fireEvent(view.getByTestId('kid-home-watch'), 'focus');
  expect(view.getByTestId(`kid-home-selected-${forest.title.id}`)).toBeTruthy();
  fireEvent.press(view.getByTestId('kid-home-watch'));
  expect(play).toHaveBeenCalledWith(forest);
});

test('failed settings retain an actionable retry and never expose library controls', () => {
  const retry = jest.fn();
  const view = render(<HouseholdStorageScreen failed onRetry={retry} />);
  fireEvent.press(view.getByTestId('household-storage-retry'));
  expect(retry).toHaveBeenCalledTimes(1);
  expect(view.queryByTestId('kid-home-watch')).toBeNull();
});
