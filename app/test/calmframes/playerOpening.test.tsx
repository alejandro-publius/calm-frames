import { startPlayer, mockError, mockMedia } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
beforeEach(() => { jest.useFakeTimers(); jest.spyOn(console, 'log').mockImplementation(() => {}); });
afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

test('home shell stays until a surface and frame are ready, then exposes the guarded player', async () => {
  const view = startPlayer('covering', true);
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
  expect(view.queryByTestId('video-player-ui-view')).toBeNull();
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 0, droppedVideoFrames: 0 });
  await act(async () => { fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'test-surface'); });
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 2, droppedVideoFrames: 0 });
  act(() => jest.advanceTimersByTime(100));
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  expect(view.getByTestId('video-player-ui-view')).toBeTruthy();
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
});

test('a real playback error replaces the opening and retains an exit', () => {
  const view = startPlayer('none', true);
  act(() => mockError(true));
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  expect(view.getByTestId('player-error')).toBeTruthy();
  fireEvent.press(view.getByTestId('player-error-back'));
  expect(view.getByText('Going back...')).toBeTruthy();
  act(() => jest.advanceTimersByTime(700));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

// The same shell is used over either retained caller; Back must not name a destination.
test('opening uses destination-neutral Back and returns through the existing stack', () => {
  const view = startPlayer('none', true);
  expect(view.getByText('Back')).toBeTruthy();
  expect(view.queryByText('Back to library')).toBeNull();
  fireEvent.press(view.getByTestId('player-opening-back'));
  expect(view.queryByText('Returning to your library.')).toBeNull();
  act(() => jest.advanceTimersByTime(700));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});
