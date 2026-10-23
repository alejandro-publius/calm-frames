/** Test-only trigger wiring; media is doubled here, not native acceptance. */
import { startPlayer, mockMedia, mockDestroy } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

test('explicit probe feeds the real Retry component and waits for release before replacement', async () => {
  jest.useFakeTimers(); await AsyncStorage.clear();
  mockDestroy.mockReset();
  let release!: (confirmed: boolean) => void;
  mockDestroy.mockReturnValue(new Promise<boolean>(resolve => {release = resolve;}));
  const view = startPlayer('none', true, false, undefined, false, true);
  await act(async () => {await Promise.resolve(); await Promise.resolve();});
  expect(view.getByText('TEST BUILD: synthetic failure')).toBeTruthy();
  expect(view.queryByTestId('native-retry-probe-trigger')).toBeNull();
  await act(async () => fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'surface'));
  mockMedia.getVideoPlaybackQuality = () => ({totalVideoFrames: 2, droppedVideoFrames: 0});
  act(() => jest.advanceTimersByTime(100));
  await act(async () => {mockMedia.currentTime = 11; mockMedia.fire('timeupdate'); await mockMedia.play();});
  await act(async () => mockMedia.fire('timeupdate'));
  fireEvent.press(view.getByTestId('native-retry-probe-trigger'));
  expect(mockMedia.paused).toBe(true);
  expect(view.getByTestId('player-error-retry')).toBeTruthy();
  fireEvent.press(view.getByTestId('player-error-retry'));
  await act(async () => {await Promise.resolve();});
  expect(view.getByText('Closing player…')).toBeTruthy();
  expect(view.queryByTestId('player-error-retry')).toBeNull();
  expect(mockDestroy).toHaveBeenCalledTimes(1);
  await act(async () => {release(true); await Promise.resolve();});
  expect(view.getByTestId('player-error-retry')).toBeTruthy();
  expect(view.queryByTestId('native-retry-probe-trigger')).toBeNull();
  view.unmount(); jest.useRealTimers();
});
