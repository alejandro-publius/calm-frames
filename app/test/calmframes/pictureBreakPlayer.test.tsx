// The picture break inside the real player screen, prototype switched on.
// Only native media, SDK widgets and the guard's inputs are simulated, by the
// shared playback harness.
jest.mock('../../src/calmframes/pictureBreakConfig', () => ({ PICTURE_BREAK_PROTOTYPE: true }));
jest.mock('../../src/calmframes/hideLogStore', () => ({
  ...jest.requireActual('../../src/calmframes/hideLogStore'),
  recordHide: jest.fn(),
}));

// The harness first: its mocks of the SDK modules must be in place before
// anything else here requires them.
import { mockGuard, mockMedia } from './playbackUiHarness';
import { press as pressKey, startPlayer } from './pictureBreakKeys';
import { act, fireEvent } from '@testing-library/react-native';
import { Platform, StyleSheet } from 'react-native';
import { CALM_COLORS, FOCUS_RING_WIDTH } from '../../src/calmframes/calmStyles';
import { recordHide } from '../../src/calmframes/hideLogStore';
import { startUiCapture, stopUiCapture } from '../../src/calmframes/uiCapture';
import { ALL_UI_FRAMES } from '../../src/calmframes/uiFrames';

let isTV: jest.SpyInstance;

function press(eventType: 'menu' | 'select') {
  pressKey(eventType, isTV);
}

beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(console, 'info').mockImplementation(() => {});
  isTV = jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(false);
  (recordHide as jest.Mock).mockClear();
});
afterEach(() => {
  jest.clearAllTimers();
  jest.useRealTimers();
  isTV.mockRestore();
});

test('one Menu press hides the picture while the film keeps playing with the captions the viewer chose', () => {
  const view = startPlayer();
  // Harbor's captions start Off since d52d657; this viewer turns them on.
  fireEvent.press(view.getByTestId('video-player-caption-btn'));
  fireEvent.press(view.getByRole('radio', { name: 'English practice captions' }));
  expect(mockMedia.textTracks[0].mode).toBe('showing');
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(true);
  expect(view.queryByTestId('calm-frames-cover')).toBeNull();
  press('menu');
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  expect(view.getByTestId('picture-break-title').props.children).toBe('Picture break');
  expect(view.getByTestId('picture-break-detail').props.children).toBe(
    'Sound and captions keep playing. Press OK to bring the picture back.',
  );
  expect(view.queryByTestId('calm-card')).toBeNull();
  expect(mockMedia.paused).toBe(false);
  expect(mockMedia.currentTime).toBe(6);
  expect(mockGuard.requestSeek).not.toHaveBeenCalled();
  expect(mockGuard.skipTo).not.toHaveBeenCalled();
  expect(mockMedia.textTracks[0].mode).toBe('showing');
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(true);
});

test('the way back is one focused button, reachable on its own by a screen reader', () => {
  const view = startPlayer();
  press('menu');
  const back = view.getByRole('button', { name: 'Back to the picture' });
  expect(back.props.hasTVPreferredFocus).toBe(true);
  const message = view.getByTestId('picture-break-message');
  expect(message.props.accessibilityLiveRegion).toBe('polite');
  expect(message.props.accessibilityLabel).toMatch(/^Picture break\. /);
  fireEvent.press(back);
  expect(view.getByTestId('picture-break-detail').props.children).toBe('The picture comes back in a moment.');
  fireEvent.press(view.getByRole('button', { name: 'Back to the picture' }));
  act(() => jest.advanceTimersByTime(2_100));
  expect(view.queryByTestId('picture-break')).toBeNull();
  expect(view.queryByTestId('calm-frames-cover')).toBeNull();
  expect(mockMedia.paused).toBe(false);
});

test('OK during a break brings the picture back and never pauses the film', () => {
  const view = startPlayer();
  press('menu');
  act(() => jest.advanceTimersByTime(6_000));
  expect(view.queryByTestId('control-bar')).toBeNull();
  press('select');
  expect(mockMedia.paused).toBe(false);
  expect(view.queryByTestId('picture-break')).toBeNull();
  expect(view.queryByTestId('calm-frames-cover')).toBeNull();
});

test('pressing OK twice to get the picture back does not pause, and OK pauses again a moment later', () => {
  const view = startPlayer();
  press('menu');
  act(() => jest.advanceTimersByTime(6_000));
  expect(view.queryByTestId('control-bar')).toBeNull();
  press('select');
  expect(view.queryByTestId('picture-break')).toBeNull();
  expect(mockMedia.paused).toBe(false);
  press('select');
  expect(mockMedia.paused).toBe(false);
  act(() => jest.advanceTimersByTime(1_100));
  press('select');
  expect(mockMedia.paused).toBe(true);
});

test('a break shows the plain cover, never the scene still', () => {
  const view = startPlayer('covering');
  expect(view.getByTestId('calm-frames-cover-still')).toBeTruthy();
  press('menu');
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  expect(view.queryByTestId('calm-frames-cover-still')).toBeNull();
});

test('when the schedule still covers, ending the break leaves the picture covered', () => {
  const view = startPlayer('covering');
  press('menu');
  act(() => jest.advanceTimersByTime(2_100));
  press('menu');
  expect(view.queryByTestId('picture-break')).toBeNull();
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  expect(view.getByTestId('calm-card')).toBeTruthy();
});

test('with captions off, as Harbor starts, the card says so and the break leaves them off', () => {
  const view = startPlayer();
  expect(mockMedia.textTracks[0].mode).toBe('hidden');
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(false);
  press('menu');
  expect(view.getByTestId('picture-break-detail').props.children).toBe(
    'Sound keeps playing. Captions are off. Press OK to bring the picture back.',
  );
  expect(mockMedia.textTracks[0].mode).toBe('hidden');
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(false);
});

test('a title that is not verified gets no break', () => {
  const view = startPlayer();
  mockGuard.status = 'blocked';
  press('menu');
  expect(view.queryByTestId('picture-break')).toBeNull();
});

test('a break is not written to the exposure history', () => {
  const view = startPlayer();
  press('menu');
  act(() => jest.advanceTimersByTime(2_100));
  press('menu');
  expect(view.queryByTestId('picture-break')).toBeNull();
  expect(recordHide).not.toHaveBeenCalled();
});

test('the return button shows the same focus ring as every other control', () => {
  const view = startPlayer();
  press('menu');
  const button = view.getByTestId('picture-break-return');
  const resting = StyleSheet.flatten(button.props.style);
  expect(resting.borderWidth).toBe(FOCUS_RING_WIDTH);
  expect(resting.borderColor).not.toBe(CALM_COLORS.FOCUS_RING);
  fireEvent(button, 'focus');
  const focused = StyleSheet.flatten(view.getByTestId('picture-break-return').props.style);
  expect(focused.borderWidth).toBe(resting.borderWidth);
  expect(focused.borderColor).toBe(CALM_COLORS.FOCUS_RING);
  expect(focused.backgroundColor).toBe(CALM_COLORS.SURFACE_FOCUSED);
  fireEvent(view.getByTestId('picture-break-return'), 'blur');
  expect(StyleSheet.flatten(view.getByTestId('picture-break-return').props.style).borderColor)
    .toBe(resting.borderColor);
});

test('a break records only frames the app flash check already analyzes', () => {
  startUiCapture();
  const view = startPlayer();
  press('menu');
  expect(view.getByTestId('picture-break')).toBeTruthy();
  const timeline = stopUiCapture();
  const known = new Set(ALL_UI_FRAMES.map((frame) => frame.screen));
  const player = timeline.filter((entry) => entry.screen.startsWith('player-'));
  expect(player.length).toBeGreaterThan(0);
  expect(player[player.length - 1].screen).toMatch(/^player-covered-covering/);
  for (const entry of player) {
    expect(known.has(entry.screen)).toBe(true);
  }
});
