import { startPlayer, mockError, mockMedia, mockDestroy } from './playbackUiHarness';
import { getBifFrameImageSource } from '../../src/services/bif/bifService';
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
  await act(async () => fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'test-surface'));
  expect(view.queryByTestId('player-home-opening')).toBeNull();
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
  expect(view.queryByText(/Back to/)).toBeNull();
  fireEvent.press(view.getByTestId('player-opening-back'));
  expect(view.queryByText('Returning to your library.')).toBeNull();
  act(() => jest.advanceTimersByTime(700));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

// Back during the opening cancels the wait: the opening's own stall timeout
// firing afterwards must not surface the recovery screen or leave twice.
test('Back on the opening shell leaves once, and a late stall timeout changes nothing', () => {
  const view = startPlayer('none', true);
  fireEvent.press(view.getByTestId('player-opening-back'));
  expect(view.getByText('Going back...')).toBeTruthy();
  act(() => jest.advanceTimersByTime(700));
  expect(view.goBack).toHaveBeenCalledTimes(1);
  act(() => jest.advanceTimersByTime(15_000));
  expect(view.queryByTestId('player-error')).toBeNull();
  expect(view.queryByTestId('video-player-ui-view')).toBeNull();
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

// A confirmed asynchronous teardown needs no extra navigation delay.
test('Back returns immediately after confirmed teardown and never returns twice', async () => {
  mockDestroy.mockReturnValueOnce(true);
  const view = startPlayer('none', true);
  await act(async () => {fireEvent.press(view.getByTestId('player-opening-back'));});
  expect(mockDestroy).toHaveBeenCalled();
  expect(view.goBack).toHaveBeenCalledTimes(1);
  expect(view.queryByTestId('player-opening-back')).toBeNull();
  act(() => jest.advanceTimersByTime(15000));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

test('Back detaches the native surfaces and waits for successful teardown to return before navigation', async () => {
  const view = startPlayer('none', true);
  const clearVideo = jest.spyOn(mockMedia, 'clearSurfaceHandle');
  const clearCaptions = jest.spyOn(mockMedia, 'clearCaptionViewHandle');
  mockDestroy.mockImplementationOnce(() => {
    expect(clearVideo).toHaveBeenCalledWith('');
    expect(clearCaptions).toHaveBeenCalledWith('');
    expect(view.goBack).not.toHaveBeenCalled();
    return true;
  });
  await act(async () => {fireEvent.press(view.getByTestId('player-opening-back'));});
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

test('unconfirmed native teardown retains the 700 ms fallback rather than the fast return', () => {
  const view = startPlayer('none', true);
  mockDestroy.mockReturnValueOnce(false);
  fireEvent.press(view.getByTestId('player-opening-back'));
  expect(view.goBack).not.toHaveBeenCalled();
  act(() => jest.advanceTimersByTime(699));
  expect(view.goBack).not.toHaveBeenCalled();
  act(() => jest.advanceTimersByTime(1));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

 test('surface loss restores the static shell and stale destruction cannot clear its replacement', async () => {
  const view = startPlayer('covering', true);
  let frames = 0;
  mockMedia.getVideoPlaybackQuality = () => ({totalVideoFrames: frames, droppedVideoFrames: 0});
  const surface = () => view.getByTestId('kepler-video-surface-view');
  await act(async () => fireEvent(surface(), 'surfaceViewCreated', 'first'));
  act(() => { frames=2; jest.advanceTimersByTime(100); });
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  act(() => fireEvent(surface(), 'surfaceViewDestroyed', 'first'));
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
  await act(async () => fireEvent(surface(), 'surfaceViewCreated', 'second'));
  act(() => { fireEvent(surface(), 'surfaceViewDestroyed', 'first'); jest.advanceTimersByTime(100); });
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
  act(() => { frames=3; jest.advanceTimersByTime(100); });
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
 });

 test('a BIF result after Back is cleared and cannot restart playback', async () => {
  let finish!: (value: any) => void;
  (getBifFrameImageSource as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const view = startPlayer('none', true, false, 'fixture-bif');
  const play = jest.spyOn(mockMedia, 'play');
  await act(async () => fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'late-bif'));
  fireEvent.press(view.getByTestId('player-opening-back'));
  const clearCache = jest.fn();
  await act(async () => finish({ clearCache }));
  expect(clearCache).toHaveBeenCalledTimes(1);
  expect(play).not.toHaveBeenCalled();
 });
