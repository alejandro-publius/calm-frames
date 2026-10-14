import { startPlayer, mockMedia, mockGuard, mockError, mockSeekFocus } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { CALM_COLORS, FOCUS_RING_WIDTH } from '../../src/calmframes/calmStyles';

beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  mockSeekFocus.mockClear();
});
afterEach(() => { jest.clearAllTimers(); jest.useRealTimers(); });

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

test('caption choices expose the active track and selecting Off returns focus to the seekbar', () => {
  const view = startPlayer();
  fireEvent.press(view.getByTestId('video-player-caption-btn'));
  const english = view.getByRole('radio', { name: 'English practice captions' });
  expect(english.props.accessibilityState.checked).toBe(true);
  expect(english.props.hasTVPreferredFocus).toBe(true);
  const off = view.getByRole('radio', { name: 'Off' });
  fireEvent(off, 'focus');
  expect(StyleSheet.flatten(view.getByRole('radio', { name: 'Off' }).props.style).borderColor).toBe(CALM_COLORS.FOCUS_RING);
  fireEvent.press(off);
  expect(view.queryByRole('radio', { name: 'Off' })).toBeNull();
  expect(mockMedia.textTracks[0].mode).toBe('hidden');
  expect(mockSeekFocus).toHaveBeenCalledTimes(1);
});

test.each(['covering', 'countdown', 'none'] as const)('pause stays visible after controls hide in %s state and clears on Play', kind => {
  const view = startPlayer(kind);
  const cardBefore = mockGuard.card;
  const coveredBefore = mockGuard.covered;
  act(() => mockMedia.pause());
  act(() => jest.advanceTimersByTime(6000));
  expect(view.queryByTestId('control-bar')).toBeNull();
  expect(view.getByTestId('player-paused')).toBeTruthy();
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
  if (kind !== 'none') expect(view.getByTestId('calm-card-detail').props.children).toBe(cardBefore.detail);
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
