import { mockEnded, mockError, mockGuard, mockMedia, startPlayer } from './playbackUiHarness';
import React from 'react';
import { act, fireEvent, render } from '@testing-library/react-native';
import { AccessibilityInfo, StyleSheet } from 'react-native';
import CalmCard from '../../src/calmframes/CalmCard';
import { Card, cardAt, NO_CARD, cardOffersSkip } from '../../src/calmframes/cards';
import { buildCoverIntervals, isCovered } from '../../src/calmframes/coverSchedule';
import { resetAnnouncements } from '../../src/calmframes/announce';
import { playbackCard, usePlaybackCardAnnouncement, CARD_ANNOUNCEMENT_SETTLE_MS } from '../../src/calmframes/usePlaybackPresentation';

const intervals = buildCoverIntervals([
  { startMs: 5000, endMs: 5200, reason: 'general' },
  { startMs: 5500, endMs: 5900, reason: 'red' },
], { guardBandMs: 0, minCoverMs: 0, durationMs: 20000 });
const playing = { paused: false, buffering: false, ended: false };
const presented = (time: number) => playbackCard(cardAt(intervals, time), playing);
let speak: jest.Mock;
beforeEach(() => {
  jest.useFakeTimers(); resetAnnouncements();
  speak = jest.fn();
  (AccessibilityInfo as any).announceForAccessibilityWithOptions = speak;
  jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(() => { jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks(); });

function Sequence({ time, paused = false, ended = false }: { time: number; paused?: boolean; ended?: boolean }) {
  const card = playbackCard(cardAt(intervals, time), { ...playing, paused, ended });
  usePlaybackCardAnnouncement(card, paused);
  return <CalmCard card={card} stableLayout manualAnnouncements />;
}

test('short adjacent scenes keep identical words and Skip placement while cover changes immediately', () => {
  const view = render(<Sequence time={1000} />);
  const detailStyle = StyleSheet.flatten(view.getByTestId('calm-card-detail').props.style);
  const buttonStyle = StyleSheet.flatten(view.getByTestId('calm-card-skip').props.style);
  const detail = view.getByTestId('calm-card-detail').props.children;
  const visibility: boolean[] = [];
  for (const time of [4999, 5000, 5199, 5200, 5499, 5500, 5899]) {
    view.rerender(<Sequence time={time} />);
    expect(view.getByTestId('calm-card-title').props.children).toBe('Flashing scenes');
    expect(view.getByTestId('calm-card-detail').props.children).toBe(detail);
    expect(StyleSheet.flatten(view.getByTestId('calm-card-detail').props.style)).toEqual(detailStyle);
    expect(StyleSheet.flatten(view.getByTestId('calm-card-skip').props.style)).toEqual(buttonStyle);
    visibility.push(isCovered(intervals, time));
  }
  expect(visibility).toEqual([false, true, true, false, false, true, true]);
  expect(presented(5200).skipToMs).toBe(6000);
  view.rerender(<Sequence time={5900} />);
  expect(view.queryByTestId('calm-card')).toBeNull();
});

test('near-boundary countdown and cover share one speech message; completed scenes do not announce', () => {
  const view = render(<Sequence time={4999} />);
  act(() => jest.advanceTimersByTime(100));
  view.rerender(<Sequence time={5000} />);
  act(() => jest.advanceTimersByTime(CARD_ANNOUNCEMENT_SETTLE_MS - 100));
  expect(speak).toHaveBeenCalledTimes(1);
  expect(speak).toHaveBeenCalledWith(presented(5000).announcement, { queue: false });
  view.rerender(<Sequence time={5200} />);
  view.rerender(<Sequence time={5500} />);
  view.rerender(<Sequence time={5900} />);
  act(() => jest.advanceTimersByTime(1000));
  expect(speak).toHaveBeenCalledTimes(1);
});

test('fleeting scheduled messages cancel speech, without delaying the visible Skip action', () => {
  const view = render(<Sequence time={5800} />);
  expect(view.getByTestId('calm-card-skip')).toBeTruthy();
  act(() => jest.advanceTimersByTime(100));
  view.rerender(<Sequence time={6000} />);
  act(() => jest.advanceTimersByTime(1000));
  expect(speak).not.toHaveBeenCalled();
});

test('pause replaces pending speech immediately, resume never queues the paused claim', () => {
  const view = render(<Sequence time={5000} />);
  view.rerender(<Sequence time={5000} paused />);
  expect(view.getByTestId('calm-card-detail').props.children).toMatch(/^Paused/);
  expect(speak).toHaveBeenCalledTimes(1);
  expect(speak.mock.calls[0][0]).toMatch(/Paused/);
  expect(speak.mock.calls[0][0]).not.toMatch(/sound continues/i);
  view.rerender(<Sequence time={5000} />);
  act(() => jest.advanceTimersByTime(600));
  expect(speak).toHaveBeenCalledTimes(2);
  expect(speak.mock.calls[1][0]).not.toMatch(/Paused|sound continues/i);
});

test('ended clears the card and pending speech immediately', () => {
  const view = render(<Sequence time={5000} />);
  view.rerender(<Sequence time={5000} ended />);
  expect(view.queryByTestId('calm-card')).toBeNull();
  act(() => jest.advanceTimersByTime(1000));
  expect(speak).not.toHaveBeenCalled();
});

test('backward and forward seek positions use the current interval, never a held Skip target', () => {
  for (const time of [5600, 4999, 5100, 5600]) {
    const raw = cardAt(intervals, time);
    const card = playbackCard(raw, playing);
    expect(cardOffersSkip(card)).toBe(true);
    expect(card.skipToMs).toBe(raw.interval!.endMs + 100);
    expect(raw.kind === 'covering' ? raw.skipToMs : undefined).toBeUndefined();
  }
  expect(presented(8000)).toBe(NO_CARD);
});

test('buffering and paused copy never claim that audio is playing', () => {
  for (const state of [{ ...playing, buffering: true }, { ...playing, paused: true }]) {
    const card = playbackCard(cardAt(intervals, 5100), state);
    expect(card.detail).not.toMatch(/sound continues|sound continued/i);
    expect(card.skipToMs).toBe(5300);
  }
});

test('the real player keeps Skip immediate during a cover and repeated actions use guarded seeking only', () => {
  const view = startPlayer('covering');
  const before = mockMedia.currentTime;
  expect(view.getByTestId('calm-frames-cover')).toBeTruthy();
  const button = view.getByTestId('calm-card-skip');
  fireEvent.press(button); fireEvent.press(button);
  expect(mockGuard.skipTo).toHaveBeenNthCalledWith(1, 9100);
  expect(mockGuard.skipTo).toHaveBeenNthCalledWith(2, 9100);
  expect(mockMedia.currentTime).toBe(before);
  expect(mockGuard.covered).toBe(true);
  expect(view.getByTestId('calm-card').props.accessibilityLiveRegion).toBe('none');
});

test.each(['error', 'ended'] as const)('real player removes stale Skip immediately on %s', event => {
  const view = startPlayer('covering');
  act(() => event === 'error' ? mockError(true) : mockEnded(true));
  expect(view.queryByTestId('calm-card-skip')).toBeNull();
  expect(mockGuard.skipTo).not.toHaveBeenCalled();
  act(() => jest.advanceTimersByTime(600));
  expect(speak.mock.calls.some(([message]) => String(message).includes('Practice cover'))).toBe(false);
});

test('a refusal replaces scheduled speech immediately instead of waiting behind it', () => {
  const Speech = ({ card }: { card: Card }) => {
    usePlaybackCardAnnouncement(card);
    return <CalmCard card={card} manualAnnouncements />;
  };
  const view = render(<Speech card={presented(5000)} />);
  const refusal = cardAt([], 0, { rejection: 'bad-signature' });
  view.rerender(<Speech card={refusal} />);
  expect(speak).toHaveBeenCalledTimes(1);
  expect(speak).toHaveBeenCalledWith(refusal.announcement, { queue: false });
  expect(view.queryByTestId('calm-card-skip')).toBeNull();
  act(() => jest.advanceTimersByTime(1000));
  expect(speak).toHaveBeenCalledTimes(1);
});
