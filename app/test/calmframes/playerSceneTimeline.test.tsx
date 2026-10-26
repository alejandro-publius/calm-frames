import { startPlayer, mockGuard, mockBuffering, mockMedia } from './playbackUiHarness';
import { act } from '@testing-library/react-native';
import { CALM_COLORS } from '../../src/calmframes/calmStyles';
import { StyleSheet } from 'react-native';
beforeEach(() => { jest.useFakeTimers(); jest.spyOn(console, 'log').mockImplementation(() => {}); });
afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

it('shows verified rendition-relative intervals without a second focus target or seek path', () => {
  const view = startPlayer('none');
  // These are already offset-adjusted guard intervals, not raw source-map times.
  mockGuard.intervals = [{ startMs: 1000, endMs: 3000, reason: 'general', sources: [] }];
  act(() => mockBuffering(true));
  expect(StyleSheet.flatten(view.getByTestId('player-scenes-mark-0').props.style)).toMatchObject({left:'5%',width:'10%'});
  expect(StyleSheet.flatten(view.getByTestId('player-scenes-track').props.style).backgroundColor).toBe(CALM_COLORS.SURFACE);
  expect(StyleSheet.flatten(view.getByTestId('player-scenes-mark-0').props.style).backgroundColor).toBe(CALM_COLORS.PENDING);
  expect(view.getByTestId('player-scenes-track').props.pointerEvents).toBe('none');
  expect(mockGuard.requestSeek).not.toHaveBeenCalled();
  act(() => { mockMedia.currentTime = 2; jest.advanceTimersByTime(1000); });
  expect(StyleSheet.flatten(view.getByTestId('player-scenes-position').props.style).left).toBe('10%');
  mockGuard.status = 'checking';
  act(() => mockBuffering(false));
  expect(view.queryByTestId('player-scenes-track')).toBeNull();
  expect(mockGuard.requestSeek).not.toHaveBeenCalled();
});
