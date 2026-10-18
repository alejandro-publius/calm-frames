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
  expect(spoken).not.toHaveBeenCalledWith('Loading', { force: true, queue: false });
  mockMedia.getVideoPlaybackQuality = () => ({ totalVideoFrames: 2, droppedVideoFrames: 0 });
  advance(100);
  expect(view.queryByTestId('player-home-opening')).toBeNull();
  advance(REVEAL_DELAY_MS - 1);
  expect(view.queryByTestId('buffering-status')).toBeNull();
  advance(1);
  expect(view.getByTestId('buffering-status')).toBeTruthy();
  expect(StyleSheet.flatten(view.getByTestId('buffering-view').props.style).backgroundColor).toBeUndefined();
  expect(spoken).toHaveBeenCalledWith('Loading', { force: true, queue: false });
  act(() => mockBuffering(false));
  expect(view.getByTestId('buffering-status')).toBeTruthy();
  advance(MIN_VISIBLE_MS);
  expect(view.queryByTestId('buffering-status')).toBeNull();
});

test('a stall during a signed hold preserves its still and gives the card sole status ownership', () => {
  const view = startPlayer('covering');
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS);
  expect(view.getByTestId('calm-frames-cover-still')).toBeTruthy();
  expect(view.getByTestId('calm-card')).toBeTruthy();
  expect(view.getByTestId('calm-card-detail').props.children).toBe('Loading');
  expect(view.queryByTestId('buffering-status')).toBeNull();
});

test('checking card owns feedback without a duplicate announcement', () => {
  const spoken = jest.spyOn(announce, 'announceForAccessibility');
  const view = startPlayer();
  mockGuard.card = CHECKING_CARD;
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS * 2);
  expect(view.getByTestId('calm-card')).toBeTruthy();
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(spoken).not.toHaveBeenCalledWith('Loading', { force: true, queue: false });
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
  expect(spoken).not.toHaveBeenCalledWith('Loading', { force: true, queue: false });
});

test('Skip stays usable while its card owns the waiting status', () => {
  const view = startPlayer('countdown');
  act(() => mockBuffering(true));
  advance(REVEAL_DELAY_MS);
  expect(view.queryByTestId('buffering-status')).toBeNull();
  expect(view.getByTestId('calm-card-detail').props.children).toBe('Loading');
  fireEvent.press(view.getByTestId('calm-card-skip'));
  expect(mockGuard.skipTo).toHaveBeenCalled();
});


test('a scheduled cover retains opacity and compact Skip through pause without a large message', () => {
  const view = startPlayer('covering');
  mockGuard.coverImageUri = undefined;
  act(() => mockBuffering(true));
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  expect(view.queryByTestId('calm-frames-cover-fallback')).toBeNull();
  expect(view.queryByText('This scene is covered')).toBeNull();
  act(() => mockMedia.pause());
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  expect(view.queryByTestId('calm-frames-cover-fallback')).toBeNull();
  expect(view.getByTestId('calm-card-detail').props.children).toBe('Paused');
  fireEvent.press(view.getByTestId('calm-card-skip'));
  expect(mockGuard.skipTo).toHaveBeenCalled();
  mockGuard.covered = false;
  mockGuard.card = { kind: 'none', title: '', announcement: '' };
  act(() => mockBuffering(false));
  expect(view.queryByTestId('calm-frames-cover-fallback')).toBeNull();
});
