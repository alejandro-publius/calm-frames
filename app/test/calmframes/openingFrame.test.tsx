import React from 'react';
import { act, render } from '@testing-library/react-native';
import { Text } from 'react-native';
import useOpeningFrame, { hasOpeningFrame } from '../../src/calmframes/useOpeningFrame';

test('a decoded, non-dropped frame and current data are required', () => {
  expect(hasOpeningFrame(null)).toBe(false);
  expect(hasOpeningFrame({ readyState: 1, getVideoPlaybackQuality: () => ({ totalVideoFrames: 5, droppedVideoFrames: 0 }) })).toBe(false);
  expect(hasOpeningFrame({ readyState: 2, getVideoPlaybackQuality: () => ({ totalVideoFrames: 5, droppedVideoFrames: 5 }) })).toBe(false);
  expect(hasOpeningFrame({ readyState: 2, getVideoPlaybackQuality: () => ({ totalVideoFrames: 5, droppedVideoFrames: 1 }) })).toBe(true);
});

test('the opening waits for verification and surface, then swaps atomically without a delay', () => {
  jest.useFakeTimers();
  const timeout = jest.fn();
  const media = { current: { readyState: 2, getVideoPlaybackQuality: () => ({ totalVideoFrames: 1, droppedVideoFrames: 0 }) } };
  function Probe({ verified, surfaceReady }: { verified: boolean; surfaceReady: boolean }) {
    const ready = useOpeningFrame({ media, enabled: true, verified, surfaceReady, onTimeout: timeout });
    return <Text>{ready ? 'picture' : 'opening'}</Text>;
  }
  const view = render(<Probe verified={false} surfaceReady />);
  expect(view.getByText('opening')).toBeTruthy();
  view.rerender(<Probe verified surfaceReady={false} />);
  expect(view.getByText('opening')).toBeTruthy();
  view.rerender(<Probe verified surfaceReady />);
  expect(view.getByText('picture')).toBeTruthy();
  act(() => jest.advanceTimersByTime(15000));
  expect(timeout).not.toHaveBeenCalled();
  view.unmount(); jest.useRealTimers();
});

test('a stalled first frame becomes a recoverable error rather than an endless loading screen', () => {
  jest.useFakeTimers();
  const timeout = jest.fn();
  const media = { current: null };
  function Probe() { useOpeningFrame({ media, enabled: true, verified: false, surfaceReady: false, onTimeout: timeout }); return null; }
  const view = render(<Probe />);
  act(() => jest.advanceTimersByTime(15000));
  expect(timeout).toHaveBeenCalledTimes(1);
  view.unmount(); jest.useRealTimers();
});
