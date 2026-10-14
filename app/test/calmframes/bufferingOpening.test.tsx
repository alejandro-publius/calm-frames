import { mockBuffering, mockError, mockGuard, mockMedia, startPlayer } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import * as announce from '../../src/calmframes/announce';
import { CHECKING_CARD } from '../../src/calmframes/cards';
import { MIN_VISIBLE_MS, REVEAL_DELAY_MS } from '../../src/components/BufferingWindow';

beforeEach(() => {
  jest.useFakeTimers();
  announce.resetAnnouncements();
  jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(() => { jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks(); });
const advance = (ms: number) => act(() => jest.advanceTimersByTime(ms));

test('verified initial opening suppresses hidden Loading, then a real playback stall announces it', async () => {
  const spoken = jest.spyOn(announce, 'announceForAccessibility');
  const view = startPlayer('none', true);
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 0, droppedVideoFrames: 0 });
  await act(async () => fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'test-surface'));
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS * 2);
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(spoken).not.toHaveBeenCalledWith('Loading');
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 2, droppedVideoFrames: 0 });
  advance(100);
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  advance(REVEAL_DELAY_MS - 1);
  expect(view.queryByTestId('buffering-status')).toBeNull();
  advance(1);
  expect(view.getByTestId('buffering-status')).toBeTruthy();
  expect(StyleSheet.flatten(view.getByTestId('buffering-view').props.style).backgroundColor).toBeUndefined();
  expect(spoken).toHaveBeenCalledWith('Loading');
  act(() => mockBuffering(false));
  expect(view.getByTestId('buffering-status')).toBeTruthy();
  advance(MIN_VISIBLE_MS);
  expect(view.queryByTestId('buffering-status')).toBeNull();
});

test('a stall during a signed hold preserves its still and card', () => {
  const view = startPlayer('covering');
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS);
  expect(view.getByTestId('calm-frames-cover-still')).toBeTruthy();
  expect(view.getByTestId('calm-card')).toBeTruthy();
  expect(view.getByTestId('buffering-status')).toBeTruthy();
});

test('checking card owns feedback without a duplicate announcement', () => {
  const spoken = jest.spyOn(announce, 'announceForAccessibility');
  const view = startPlayer();
  mockGuard.card = CHECKING_CARD;
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS * 2);
  expect(view.getByTestId('calm-card')).toBeTruthy();
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(spoken).not.toHaveBeenCalledWith('Loading');
});

test('error immediately removes a just-shown status and cancels its timer', () => {
  const view = startPlayer();
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS);
  expect(view.getByTestId('buffering-status')).toBeTruthy();
  act(() => mockError(true));
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(view.getByTestId('player-error-back').props.hasTVPreferredFocus).toBe(true);
  advance(MIN_VISIBLE_MS * 2);
  expect(view.queryByTestId('buffering-status')).toBeNull();
});

test('returning shell cancels a pending status before it can announce', () => {
  const spoken = jest.spyOn(announce, 'announceForAccessibility');
  const view = startPlayer('none', true);
  act(() => mockBuffering(true));
  fireEvent.press(view.getByTestId('player-opening-back'));
  advance(REVEAL_DELAY_MS * 2);
  expect(view.goBack).toHaveBeenCalledTimes(1);
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(spoken).not.toHaveBeenCalledWith('Loading');
});

test('countdown Skip stays usable with the loading plate visible', () => {
  const view = startPlayer('countdown');
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS);
  expect(view.getByTestId('buffering-status')).toBeTruthy();
  fireEvent.press(view.getByTestId('calm-card-skip'));
  expect(mockGuard.skipTo).toHaveBeenCalled();
});
