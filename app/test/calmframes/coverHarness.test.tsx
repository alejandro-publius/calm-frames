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
      <Text testID="worstDriftMs">{String(Math.round(state.worstDriftMs))}</Text>
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

  it('does not let the estimate run on through a buffer', () => {
    // `waiting` is the event a player fires when it runs out of data, and it is
    // the common one: `stalled` only arrives after the fetch has been quiet for
    // seconds. The picture covers either way, because both are uncertain events.
    // What this checks is the clock underneath: an estimate that keeps advancing
    // through a buffer comes out the far side ahead of the playhead, and every
    // number taken off it, the drift and the cover lead, is wrong by the length
    // of the buffer.
    const media = makeMediaElement();
    const intervals = buildCoverIntervals([{ startMs: 60_000, endMs: 61_000 }]);
    render(<Harness media={media} mode="timing" intervals={intervals} />);

    // The drift is the observable, not the estimate: while the picture is
    // covered the state stops being written, because applyCover returns early
    // once covered is already true. The drift is measured against the clock
    // itself, on the next event the player sends.
    media.currentTime = 1.0;
    act(() => media.fire('playing'));
    act(() => jest.advanceTimersByTime(100));
    // The first report always reads as a whole second of drift, because the
    // clock starts at zero and the player starts at one. That is the baseline
    // to beat, not a number to bound: what matters is that the buffer adds
    // nothing to it.
    const before = Number(screen.getByTestId('worstDriftMs').props.children);

    // Four seconds of buffering. The playhead does not move, and the player
    // sends nothing at all until it has data again.
    act(() => media.fire('waiting'));
    act(() => jest.advanceTimersByTime(4_000));

    // Back with data, still at the second it stopped on.
    act(() => media.fire('playing'));
    // More than one tick on purpose. The tick that flips the cover back off
    // writes mediaTimeMs through applyCover, and the drift update right after it
    // is skipped because it sees that same mediaTimeMs already in the state. The
    // tick after that one is the first that can carry the drift.
    act(() => jest.advanceTimersByTime(200));
    const after = Number(screen.getByTestId('worstDriftMs').props.children);

    expect(Math.abs(after)).toBeLessThanOrEqual(Math.abs(before));
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

describe('useCoverHarness when the player appears later', () => {
  // The player is created after the screen mounts. A harness that only looks
  // for the media element once attaches to nothing and records a run with no
  // events in it, which is what happened on the virtual device.
  const LateHarness = ({
    media,
    ready,
  }: {
    media: MediaElementLike;
    ready: boolean;
  }) => {
    const ref = React.useRef<MediaElementLike | null>(null);
    if (ready) {
      ref.current = media;
    }
    const state = useCoverHarness(ref, { mode: 'timing', intervals: [], ready });
    return <Text testID="covered">{state.covered ? 'covered' : 'clear'}</Text>;
  };

  it('attaches once the media element exists', () => {
    const media = makeMediaElement();
    const view = render(<LateHarness media={media} ready={false} />);
    expect(media.listeners.timeupdate ?? []).toHaveLength(0);

    view.rerender(<LateHarness media={media} ready={true} />);
    expect(media.listeners.timeupdate).toHaveLength(1);
    expect(media.listeners.seeking).toHaveLength(1);
  });
});
