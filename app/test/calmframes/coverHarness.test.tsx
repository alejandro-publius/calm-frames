/**
 * Tests for the cover layer and the harness that drives it.
 *
 * These cover the wiring that GATE 1 depends on: that the cover appears and
 * disappears when the schedule says so, that anything which makes the playhead
 * uncertain hides the picture at once, and that the cover leaves the camera's
 * reference patch visible.
 *
 * Every assertion here was seen to fail: each rule was broken on purpose in
 * the source and the suite went red before the file was restored.
 */
import { act, render, screen } from '@testing-library/react-native';
import React from 'react';
import { Text } from 'react-native';
import CoverLayer from '../../src/calmframes/CoverLayer';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import {
  MediaElementLike,
  useCoverHarness,
} from '../../src/calmframes/useCoverHarness';

describe('CoverLayer', () => {
  it('renders nothing while the picture is safe', () => {
    render(<CoverLayer visible={false} />);
    expect(screen.queryByTestId('calm-frames-cover')).toBeNull();
  });

  it('covers the whole screen when there is no reference patch', () => {
    render(<CoverLayer visible={true} />);
    expect(screen.getByTestId('calm-frames-cover')).toBeTruthy();
    expect(screen.queryByTestId('calm-frames-cover-top')).toBeNull();
  });

  it('leaves the reference patch visible', () => {
    render(
      <CoverLayer
        visible={true}
        screenWidth={1920}
        screenHeight={1080}
        referencePatch={{ x: 48, y: 48, width: 96, height: 96 }}
      />,
    );
    const top = screen.getByTestId('calm-frames-cover-top');
    const bottom = screen.getByTestId('calm-frames-cover-bottom');
    const left = screen.getByTestId('calm-frames-cover-left');
    const right = screen.getByTestId('calm-frames-cover-right');

    // Above the patch, then below it, then the two sides beside it.
    expect(top.props.style).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ top: 0, height: 48, width: 1920 }),
      ]),
    );
    expect(bottom.props.style).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ top: 144, height: 936, width: 1920 }),
      ]),
    );
    expect(left.props.style).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ left: 0, width: 48, height: 96 }),
      ]),
    );
    expect(right.props.style).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ left: 144, width: 1776, height: 96 }),
      ]),
    );
  });
});

/** A media element we can drive from a test. */
function makeMediaElement(): MediaElementLike & {
  fire: (type: string) => void;
  listeners: Record<string, Array<() => void>>;
} {
  const listeners: Record<string, Array<() => void>> = {};
  return {
    currentTime: 0,
    playbackRate: 1,
    listeners,
    addEventListener(type: string, listener: () => void) {
      listeners[type] = [...(listeners[type] ?? []), listener];
    },
    removeEventListener(type: string, listener: () => void) {
      listeners[type] = (listeners[type] ?? []).filter((l) => l !== listener);
    },
    fire(type: string) {
      for (const listener of listeners[type] ?? []) {
        listener();
      }
    },
  };
}

const Harness = ({
  media,
  mode,
  intervals,
}: {
  media: MediaElementLike;
  mode: 'layering' | 'timing';
  intervals?: ReturnType<typeof buildCoverIntervals>;
}) => {
  const ref = React.useRef<MediaElementLike | null>(media);
  const state = useCoverHarness(ref, { mode, intervals, tickMs: 50 });
  return (
    <>
      <Text testID="covered">{state.covered ? 'covered' : 'clear'}</Text>
      <CoverLayer visible={state.covered} />
    </>
  );
};

describe('useCoverHarness', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('layering mode leaves the picture alone for the first interval', () => {
    const media = makeMediaElement();
    render(<Harness media={media} mode="layering" />);
    expect(screen.getByTestId('covered').props.children).toBe('clear');
  });

  it('layering mode covers after five seconds and uncovers after ten', () => {
    const media = makeMediaElement();
    render(<Harness media={media} mode="layering" />);

    act(() => jest.advanceTimersByTime(5_100));
    expect(screen.getByTestId('covered').props.children).toBe('covered');
    expect(screen.queryByTestId('calm-frames-cover')).toBeTruthy();

    act(() => jest.advanceTimersByTime(5_000));
    expect(screen.getByTestId('covered').props.children).toBe('clear');
    expect(screen.queryByTestId('calm-frames-cover')).toBeNull();
  });

  it('timing mode covers while the playhead is inside an interval', () => {
    const media = makeMediaElement();
    const intervals = buildCoverIntervals([{ startMs: 2_000, endMs: 3_000 }], {
      guardBandMs: 500,
    });
    render(<Harness media={media} mode="timing" intervals={intervals} />);

    // The player reports 1.0 s and starts running.
    media.currentTime = 1.0;
    act(() => media.fire('playing'));
    act(() => jest.advanceTimersByTime(100));
    expect(screen.getByTestId('covered').props.children).toBe('clear');

    // The wall clock reaches the guard band before any timeupdate arrives,
    // which is the whole point of running the schedule on a clock.
    act(() => jest.advanceTimersByTime(600));
    expect(screen.getByTestId('covered').props.children).toBe('covered');
  });

  it('timing mode hides the picture at once when buffering starts', () => {
    const media = makeMediaElement();
    const intervals = buildCoverIntervals([{ startMs: 60_000, endMs: 61_000 }]);
    render(<Harness media={media} mode="timing" intervals={intervals} />);

    media.currentTime = 1.0;
    act(() => media.fire('playing'));
    act(() => jest.advanceTimersByTime(100));
    expect(screen.getByTestId('covered').props.children).toBe('clear');

    act(() => media.fire('waiting'));
    expect(screen.getByTestId('covered').props.children).toBe('covered');
  });

  it('timing mode hides the picture at once when a seek starts', () => {
    const media = makeMediaElement();
    const intervals = buildCoverIntervals([{ startMs: 60_000, endMs: 61_000 }]);
    render(<Harness media={media} mode="timing" intervals={intervals} />);

    media.currentTime = 1.0;
    act(() => media.fire('playing'));
    act(() => jest.advanceTimersByTime(100));
    expect(screen.getByTestId('covered').props.children).toBe('clear');

    act(() => media.fire('seeking'));
    expect(screen.getByTestId('covered').props.children).toBe('covered');
  });

  it('keeps the cover on until playback is confirmed again', () => {
    const media = makeMediaElement();
    const intervals = buildCoverIntervals([{ startMs: 60_000, endMs: 61_000 }]);
    render(<Harness media={media} mode="timing" intervals={intervals} />);

    media.currentTime = 1.0;
    act(() => media.fire('playing'));
    act(() => jest.advanceTimersByTime(100));
    act(() => media.fire('seeking'));
    act(() => jest.advanceTimersByTime(2_000));
    expect(screen.getByTestId('covered').props.children).toBe('covered');

    media.currentTime = 5.0;
    act(() => media.fire('seeked'));
    act(() => jest.advanceTimersByTime(100));
    expect(screen.getByTestId('covered').props.children).toBe('clear');
  });

  it('subscribes to every media event it needs, and unsubscribes on teardown', () => {
    const media = makeMediaElement();
    const view = render(<Harness media={media} mode="timing" intervals={[]} />);
    for (const type of [
      'timeupdate',
      'seeking',
      'seeked',
      'waiting',
      'stalled',
      'pause',
      'playing',
      'ratechange',
      'ended',
      'error',
    ]) {
      expect(media.listeners[type]?.length).toBe(1);
    }
    view.unmount();
    for (const type of Object.keys(media.listeners)) {
      expect(media.listeners[type].length).toBe(0);
    }
  });
});
