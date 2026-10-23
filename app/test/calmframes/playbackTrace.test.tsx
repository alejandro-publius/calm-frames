/**
 * The playback breadcrumbs a native checkpoint reads from the device log.
 *
 * One run on the virtual device cannot be screen-captured, so the phases are
 * read from CALM_TRACE lines instead: the first picture, each cover and each
 * wait with its media time, then Back and teardown. They must fire on state
 * changes only, never once per tick, so a long session stays a short log.
 *
 * Seen to fail, Oct 17 2026: with the picture-shown effect removed from
 * PlayerScreen, the first test found no "picture-shown" line.
 */
import { act, fireEvent } from '@testing-library/react-native';
import { setTraceEnabled, TRACE_PREFIX } from '../../src/calmframes/trace';
import { mockBuffering, mockMedia, startPlayer } from './playbackUiHarness';
import { DISMISS_CONTROLS_DELAY } from '../../src/utils/videoPlayerValues';

let warn: jest.SpyInstance;
const playbackLines = () => warn.mock.calls
  .map((call) => String(call[0]))
  .filter((line) => line.startsWith(`${TRACE_PREFIX} playback`));

beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
  setTraceEnabled(true);
});
afterEach(() => {
  setTraceEnabled(false);
  jest.useRealTimers();
  jest.restoreAllMocks();
});

test('the first picture, the cover and each wait are logged once each, with media time', async () => {
  const view = startPlayer('covering', true);
  expect(playbackLines()).toContain(`${TRACE_PREFIX} playback cover on media=6000`);
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 0, droppedVideoFrames: 0 });
  await act(async () => { fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'test-surface'); });
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 2, droppedVideoFrames: 0 });
  act(() => jest.advanceTimersByTime(100));
  expect(playbackLines()).toContain(`${TRACE_PREFIX} playback picture-shown media=6000`);
  act(() => mockBuffering(true));
  act(() => mockBuffering(false));
  const waits = playbackLines().filter((line) => line.includes('waiting'));
  expect(waits.slice(-2)).toEqual([
    `${TRACE_PREFIX} playback waiting on media=6000`,
    `${TRACE_PREFIX} playback waiting off media=6000`,
  ]);
  // Renders that change nothing the log is about add no lines.
  const before = playbackLines().length;
  act(() => mockMedia.pause());
  act(() => { mockMedia.play(); });
  act(() => jest.advanceTimersByTime(5_000));
  // Five seconds crosses DISMISS_CONTROLS_DELAY, and the controls going away
  // is a change the log reports, once. Nothing else may be added.
  expect(DISMISS_CONTROLS_DELAY).toBeLessThanOrEqual(5_100);
  expect(playbackLines().slice(before)).toEqual([`${TRACE_PREFIX} playback controls hidden`]);
  expect(playbackLines().filter((line) => line.includes('picture-shown'))).toHaveLength(1);
});

test('Back is logged with the teardown result, once', async () => {
  const view = startPlayer('none', true);
  await act(async () => {fireEvent.press(view.getByTestId('player-opening-back'));});
  // The shell turns to "Going back..." and drops its Back; the exit delay passes.
  expect(view.queryByTestId('player-opening-back')).toBeNull();
  act(() => jest.advanceTimersByTime(1_000));
  expect(view.goBack).toHaveBeenCalledTimes(1);
  const back = playbackLines().filter((line) => / (back|teardown )/.test(line));
  expect(back).toHaveLength(2);
  expect(back[0]).toBe(`${TRACE_PREFIX} playback back`);
  expect(back[1]).toMatch(/^CALM_TRACE playback teardown (ok|unconfirmed)$/);
});
