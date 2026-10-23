import { mockBuffering, mockDestroy, mockEnded, mockError, mockGuard, mockMedia, startPlayer } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import { createProgressMonitor } from '../../src/calmframes/usePlaybackProgress';
import slowNative from '../../../results/native-slowdown-isolation-2026-10-17/fresh-simulator-timing.json';
import normalNative from '../../../results/compact-scene-control-2026-10-17/native/timing-events.json';
import * as continuousScene from '../../src/calmframes/continuousScene';

beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  mockDestroy.mockReset();
});
afterEach(() => { jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks(); });
const advance = (ms: number) => act(() => jest.advanceTimersByTime(ms));

test('native evidence distinguishes sustained slow progress from the successful run', () => {
  const replay = (events: Array<{ kind: string; wallClockMs: number; mediaTimeMs?: number | null; playbackRate?: number }>) => {
    const monitor = createProgressMonitor();
    let observedSlow = false;
    for (const event of events) {
      if (['pause', 'playing', 'seeking', 'seeked', 'harness-start', 'harness-stop'].includes(event.kind)) monitor.reset();
      if (event.kind === 'timeupdate' && typeof event.mediaTimeMs === 'number') {
        observedSlow ||= monitor.sample(event.wallClockMs, event.mediaTimeMs / 1000, event.playbackRate);
      }
    }
    return observedSlow;
  };
  expect(replay(slowNative)).toBe(true);
  expect(replay(normalNative)).toBe(false);
});

test('requires sustained low progress and clears only after sustained recovery', () => {
  const monitor = createProgressMonitor();
  for (let second = 0; second < 6; second++) expect(monitor.sample(second * 1000, second * 0.1)).toBe(false);
  expect(monitor.sample(6000, 0.6)).toBe(true);
  expect(monitor.sample(7000, 1.6)).toBe(true);
  expect(monitor.sample(8000, 2.6)).toBe(true);
  expect(monitor.sample(9000, 3.6)).toBe(false);
});

test.each([0.5, 1, 2])('normal progress at playback rate %s is not slow', rate => {
  const monitor = createProgressMonitor();
  for (let second = 0; second <= 15; second++) expect(monitor.sample(second * 1000, second * rate, rate)).toBe(false);
});

test.each(['sleep', 'backward', 'forward', 'rate', 'clock'] as const)('resets observation across %s discontinuity', kind => {
  const monitor = createProgressMonitor();
  for (let second = 0; second <= 6; second++) monitor.sample(second * 1000, 10);
  const sample = kind === 'sleep' ? [20000, 10, 1] : kind === 'backward' ? [7000, 2, 1]
    : kind === 'forward' ? [7000, 20, 1] : kind === 'rate' ? [7000, 10, 2] : [5000, 10, 1];
  expect(monitor.sample(...sample as [number, number, number])).toBe(false);
});

test('slow covered playback uses the compact status without moving media, cover or focus', () => {
  const view = startPlayer('covering');
  const position = mockMedia.currentTime;
  const skip = view.getByTestId('calm-card-skip');
  advance(5999);
  expect(view.queryByText('Playback slow')).toBeNull();
  advance(1);
  expect(view.getByTestId('calm-card-detail').props.children).toBe('Playback slow');
  expect(view.getByTestId('calm-card-skip')).toBe(skip);
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  expect(mockGuard.skipTo).not.toHaveBeenCalled();
  expect(mockMedia.currentTime).toBe(position);
  act(() => mockMedia.pause());
  expect(view.getByTestId('calm-card-detail').props.children).toBe('Paused');
  advance(12000);
  expect(view.queryByText('Playback slow')).toBeNull();
  act(() => { mockMedia.play(); });
  advance(5999);
  expect(view.queryByText('Playback slow')).toBeNull();
  view.unmount();
  expect(mockMedia.listeners.seeking.size).toBe(0);
  expect(mockMedia.listeners.ratechange.size).toBe(0);
});

test('outside a scene, pause immediately removes loading and slow feedback', () => {
  const view = startPlayer();
  act(() => mockBuffering(true)); advance(1000);
  expect(view.getByText('Loading')).toBeTruthy();
  act(() => mockMedia.pause());
  expect(view.queryByText('Loading')).toBeNull();
  advance(5000);
  expect(view.getByTestId('player-paused')).toBeTruthy();
  act(() => { mockBuffering(false); mockMedia.play(); });
  advance(6000); advance(1000);
  expect(view.getByText('Playback slow')).toBeTruthy();
  act(() => mockError(true));
  expect(view.queryByText('Playback slow')).toBeNull();
  expect(view.getByTestId('player-error-back')).toBeTruthy();
});

test('seeking clears slow state and gives the new position a full observation window', () => {
  const view = startPlayer('covering');
  advance(6000);
  expect(view.getByText('Playback slow')).toBeTruthy();
  act(() => mockMedia.fire('seeking'));
  advance(10000);
  expect(view.queryByText('Playback slow')).toBeNull();
  act(() => { mockMedia.currentTime = 15; mockMedia.fire('seeked'); });
  advance(6000);
  expect(view.queryByText('Playback slow')).toBeNull();
});

test('ended video tears down and returns once without a presentation delay', async () => {
  mockDestroy.mockReturnValue(true);
  const view = startPlayer('covering');
  await act(async () => { mockMedia.ended = true; mockMedia.fire('ended'); mockEnded(true); });
  expect(mockDestroy).toHaveBeenCalledTimes(1);
  expect(view.goBack).toHaveBeenCalledTimes(1);
  expect(view.queryByTestId('calm-card-skip')).toBeNull();
  expect(view.queryByTestId('video-player-ui-view')).toBeNull();
  act(() => mockEnded(true)); advance(3000);
  expect(mockDestroy).toHaveBeenCalledTimes(1);
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

test('ended video retains the teardown fallback and cancels it if unmounted', () => {
  mockDestroy.mockReturnValue(false);
  const view = startPlayer();
  act(() => mockEnded(true));
  expect(mockDestroy).toHaveBeenCalledTimes(1);
  expect(view.goBack).not.toHaveBeenCalled();
  advance(699); expect(view.goBack).not.toHaveBeenCalled();
  advance(1); expect(view.goBack).toHaveBeenCalledTimes(1);
  view.unmount();
  const next = startPlayer();
  act(() => mockEnded(true));
  next.unmount(); advance(1000);
  expect(next.goBack).not.toHaveBeenCalled();
});


test('optional video preview ends on a stationary scene until explicit Back', async () => {
  mockDestroy.mockReturnValue(true);
  const view = startPlayer('none', true, false, undefined, true);
  act(() => { mockMedia.ended = true; mockMedia.fire('ended'); mockEnded(true); });
  expect(view.getByTestId('preview-ended-still')).toBeTruthy();
  expect(mockDestroy).toHaveBeenCalledTimes(1);
  expect(mockMedia.paused).toBe(true);
  expect(view.queryByTestId('kepler-video-surface-view')).toBeNull();
  expect(view.queryByTestId('video-player-ui-view')).toBeNull();
  advance(300000);
  expect(view.goBack).not.toHaveBeenCalled();
  expect(view.getByTestId('preview-ended-still')).toBeTruthy();
  await act(async () => {fireEvent.press(view.getByTestId('preview-ended-still-back'));});
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

test('continuous scene releases transport and retains its final frame until explicit Back', async () => {
  jest.spyOn(continuousScene, 'continuousEndingForRoute').mockReturnValue({ uri: 'measured-final-frame-fixture' });
  mockDestroy.mockReturnValue(true);
  const view = startPlayer();
  act(() => { mockMedia.ended = true; mockMedia.fire('ended'); mockEnded(true); });
  expect(view.getByTestId('continuous-ended-still-picture').props.source).toEqual({ uri: 'measured-final-frame-fixture' });
  expect(view.getByTestId('continuous-ended-still-picture').props.fadeDuration).toBe(0);
  expect(mockDestroy).toHaveBeenCalledTimes(1);
  expect(mockMedia.paused).toBe(true);
  expect(view.queryByTestId('kepler-video-surface-view')).toBeNull();
  expect(view.queryByTestId('video-player-ui-view')).toBeNull();
  advance(3600000);
  expect(view.goBack).not.toHaveBeenCalled();
  expect(view.getByTestId('continuous-ended-still')).toBeTruthy();
  await act(async () => {fireEvent.press(view.getByTestId('continuous-ended-still-back'));});
  expect(view.goBack).toHaveBeenCalledTimes(1);
});
