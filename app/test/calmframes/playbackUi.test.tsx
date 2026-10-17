import { startPlayer, mockMedia, mockGuard, mockError, mockSeekFocus, remote } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import { Platform, StyleSheet } from 'react-native';
import { CALM_COLORS, FOCUS_RING_WIDTH } from '../../src/calmframes/calmStyles';

beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  mockSeekFocus.mockClear();
});
afterEach(() => { jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks(); });

test.each(['none', 'countdown'] as const)('seekbar yields initial and restored preferred focus to Skip during %s', kind => {
  jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(true);
  const view = startPlayer(kind);
  expect(view.getByTestId('seekbar-focus-guide').props.hasTVPreferredFocus).toBe(kind !== 'countdown');
  act(() => jest.advanceTimersByTime(6000));
  expect(view.queryByTestId('kui-seekbar')).toBeNull();
  remote('down');
  expect(view.getByTestId('seekbar-focus-guide').props.hasTVPreferredFocus).toBe(kind !== 'countdown');
  if (kind === 'countdown') {
    expect(view.getByTestId('calm-card-skip').props.hasTVPreferredFocus).toBe(true);
  }
});

test('initialized playback exposes named captions and a stationary contrasting focus ring', () => {
  const view = startPlayer();
  const button = view.getByRole('button', { name: 'Captions' });
  const initial = StyleSheet.flatten(button.props.style);
  expect(initial.borderWidth).toBe(FOCUS_RING_WIDTH);
  fireEvent(button, 'focus');
  const focused = StyleSheet.flatten(view.getByRole('button', { name: 'Captions' }).props.style);
  expect(focused.borderWidth).toBe(initial.borderWidth);
  expect(focused.borderColor).toBe(CALM_COLORS.FOCUS_RING);
  expect(focused.backgroundColor).toBe(CALM_COLORS.SURFACE_FOCUSED);
  expect(view.getByRole('button', { name: 'Back' })).toBeTruthy();
  expect(view.getByTestId('kui-seekbar')).toBeTruthy();
});

test('ambient Harbor starts Off, honors explicit On through playback updates, and can return Off', () => {
  const view = startPlayer();
  fireEvent.press(view.getByTestId('video-player-caption-btn'));
  const english = view.getByRole('radio', { name: 'English practice captions' });
  expect(english.props.accessibilityState.checked).toBe(false);
  expect(view.getByRole('radio', { name: 'Off' }).props.accessibilityState.checked).toBe(true);
  expect(mockMedia.textTracks[0].mode).toBe('hidden');
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(false);
  fireEvent.press(english);
  act(() => { mockMedia.pause(); mockMedia.play(); mockMedia.fire('timeupdate'); });
  expect(mockMedia.textTracks[0].mode).toBe('showing');
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(true);
  fireEvent.press(view.getByTestId('video-player-caption-btn'));
  expect(view.getByRole('radio', { name: 'English practice captions' }).props.accessibilityState.checked).toBe(true);
  const off = view.getByRole('radio', { name: 'Off' });
  fireEvent(off, 'focus');
  expect(StyleSheet.flatten(view.getByRole('radio', { name: 'Off' }).props.style).borderColor).toBe(CALM_COLORS.FOCUS_RING);
  fireEvent.press(off);
  expect(view.queryByRole('radio', { name: 'Off' })).toBeNull();
  expect(mockMedia.textTracks[0].mode).toBe('hidden');
  expect(mockSeekFocus).toHaveBeenCalledTimes(2);
});

test.each(['covering', 'countdown', 'none'] as const)('pause stays visible after controls hide in %s state and clears on Play', kind => {
  const view = startPlayer(kind);
  const cardBefore = mockGuard.card;
  const coveredBefore = mockGuard.covered;
  act(() => mockMedia.pause());
  act(() => jest.advanceTimersByTime(6000));
  expect(view.queryByTestId('control-bar')).toBeNull();
  // One paused statement on screen: the scene card says it during a countdown
  // or a cover, the corner banner says it otherwise. Seen to fail, Oct 17 2026,
  // with the banner shown in every state: two statements, card and banner.
  expect(view.queryAllByText(/^Paused/)).toHaveLength(1);
  if (kind === 'none') expect(view.getByTestId('player-paused')).toBeTruthy();
  else expect(view.queryByTestId('player-paused')).toBeNull();
  if (kind !== 'none') {
    expect(view.getByTestId('calm-card-detail').props.children).toMatch(/Paused/);
    expect(view.getByTestId('calm-card').props.accessibilityLabel).toMatch(/Paused/);
    expect(view.getByTestId('calm-card-detail').props.children).not.toMatch(/keep playing/);
  }
  if (kind === 'countdown') {
    fireEvent.press(view.getByTestId('calm-card-skip'));
    expect(mockGuard.skipTo).toHaveBeenCalledWith(cardBefore.skipToMs);
  }
  expect(mockGuard.card).toBe(cardBefore);
  expect(mockGuard.covered).toBe(coveredBefore);
  expect(mockMedia.currentTime).toBe(kind === 'countdown' ? 3 : 6);
  act(() => { mockMedia.play(); });
  expect(view.queryByTestId('player-paused')).toBeNull();
  if (kind !== 'none') expect(view.getByTestId('calm-card-detail').props.children).toBe('This demo hides the picture during planned scenes. You can skip ahead.');
  view.unmount();
  expect(mockMedia.listeners.pause.size).toBe(0);
  expect(mockMedia.listeners.play.size).toBe(0);
  expect(mockMedia.listeners.ended.size).toBe(0);
});

test('recovery paints above the retained cover and Back leaves once', () => {
  const view = startPlayer('countdown');
  act(() => mockError(true));
  const cover = view.getByTestId('calm-frames-cover');
  const error = view.getByTestId('player-error');
  expect(StyleSheet.flatten(error.props.style).zIndex).toBeGreaterThan(StyleSheet.flatten(cover.props.style).zIndex);
  expect(StyleSheet.flatten(error.props.style).position).toBe('absolute');
  expect(StyleSheet.flatten(error.props.style).backgroundColor).toBe('#000000');
  expect(view.queryByTestId('calm-card-skip')).toBeNull();
  expect(view.queryByTestId('video-player-ui-view')).toBeNull();
  const back = view.getByTestId('player-error-back');
  expect(back.props.hasTVPreferredFocus).toBe(true);
  fireEvent.press(back);
  fireEvent.press(back);
  act(() => jest.advanceTimersByTime(701));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});

test('choosing the active caption track closes its menu without changing media or the hold', () => {
  const view = startPlayer('covering');
  fireEvent.press(view.getByTestId('video-player-caption-btn'));
  fireEvent.press(view.getByRole('radio', { name: 'English practice captions' }));
  const card = mockGuard.card;
  const position = mockMedia.currentTime;
  fireEvent.press(view.getByTestId('video-player-caption-btn'));
  const selected = view.getByRole('radio', { name: 'English practice captions' });
  expect(selected.props.accessibilityState.checked).toBe(true);
  expect(view.getByTestId('kepler-captions-view').props.show).toBe(true);
  expect(view.getByTestId('calm-card')).toBeTruthy();
  fireEvent.press(selected);
  expect(view.queryByRole('radio', { name: 'English practice captions' })).toBeNull();
  expect(mockMedia.textTracks[0].mode).toBe('showing');
  expect(mockMedia.currentTime).toBe(position);
  expect(mockGuard.card).toBe(card);
  expect(mockGuard.covered).toBe(true);
  expect(mockSeekFocus).toHaveBeenCalledTimes(2);
});
