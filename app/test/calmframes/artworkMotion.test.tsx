import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import { act, render, screen } from '@testing-library/react-native';
import React from 'react';
import { AccessibilityInfo, Animated, Text } from 'react-native';
import CalmArtworkMotion from '../../src/calmframes/CalmArtworkMotion';
import { scale } from '../../src/calmframes/calmStyles';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleArtwork from '../../src/calmframes/TitleArtwork';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CheckedTitle } from '../../src/calmframes/titleStatus';

function deferred() {
  let resolve!: (value: boolean) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<boolean>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
async function flush() {
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
}
const art = (enabled = true, active = true) => (
  <CalmArtworkMotion enabled={enabled} active={active}><Text>Artwork stand-in</Text></CalmArtworkMotion>
);
// Narrow the overloaded event method at this test boundary to its boolean event.
const accessibilityEvents = AccessibilityInfo as unknown as {
  addEventListener(name: string, callback: (value: boolean) => void): { remove(): void };
};
const entry: CheckedTitle = {
  title: { id: 'motion-fixture', title: 'Motion test title', uri: 'file:///fixture.mp4', sha256: 'a'.repeat(64) },
  status: 'verified', segments: [], hiddenMs: 0, verifiedProfiles: ['wcag'],
};

describe('optional one-time artwork entry', () => {
  let lifecycle: ((state: string) => void) | undefined;
  let reduction: ((value: boolean) => void) | undefined;
  let removeLifecycle: jest.Mock;
  let removeReduction: jest.Mock;
  let start: jest.Mock;
  let stop: jest.Mock;
  let query: jest.SpyInstance;
  let timing: jest.SpyInstance;
  let setValue: jest.SpyInstance;
  let manager: { getCurrentState: jest.Mock; addAppStateListener: jest.Mock };

  beforeEach(() => {
    jest.clearAllMocks();
    lifecycle = undefined;
    reduction = undefined;
    removeLifecycle = jest.fn();
    removeReduction = jest.fn();
    start = jest.fn();
    stop = jest.fn();
    manager = {
      getCurrentState: jest.fn(() => 'active'),
      addAppStateListener: jest.fn((_name, callback) => {
        lifecycle = callback;
        return { remove: removeLifecycle };
      }),
    };
    (useKeplerAppStateManager as jest.Mock).mockReturnValue(manager);
    query = jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
    jest.spyOn(accessibilityEvents, 'addEventListener').mockImplementation((name, callback) => {
      if (name === 'reduceMotionChanged') reduction = callback;
      return { remove: removeReduction };
    });
    timing = jest.spyOn(Animated, 'timing').mockReturnValue({ start, stop, reset: jest.fn() });
    setValue = jest.spyOn(Animated.Value.prototype, 'setValue');
  });
  afterEach(() => jest.restoreAllMocks());

  it('starts only after an explicit false system response and moves only the art transform', async () => {
    const pending = deferred();
    query.mockReturnValue(pending.promise);
    render(art());
    expect(timing).not.toHaveBeenCalled();
    expect(screen.getByTestId('calm-artwork-motion').props.style).not.toHaveProperty('opacity');
    await act(async () => pending.resolve(false));
    expect(setValue).toHaveBeenCalledWith(scale(6));
    expect(timing).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({
      toValue: 0, duration: 240, useNativeDriver: true, isInteraction: false,
    }));
    expect(start).toHaveBeenCalledTimes(1);
    const wrapper = screen.getByTestId('calm-artwork-motion');
    expect(wrapper.props.accessible).toBe(false);
    expect(wrapper.props.pointerEvents).toBe('none');
  });

  it.each([true, undefined, null])('stays still for a reduced or unknown response: %s', async (value) => {
    query.mockResolvedValue(value);
    render(art());
    await flush();
    expect(timing).not.toHaveBeenCalled();
    expect(setValue).not.toHaveBeenCalledWith(scale(6));
  });

  it('stays still when the reduction query fails', async () => {
    query.mockRejectedValue(new Error('unavailable'));
    render(art());
    await flush();
    expect(timing).not.toHaveBeenCalled();
  });

  it('never moves or queries by default and does not enter when enabled later', async () => {
    const view = render(<CalmArtworkMotion><Text>Art</Text></CalmArtworkMotion>);
    expect(query).not.toHaveBeenCalled();
    view.rerender(art());
    await flush();
    expect(timing).not.toHaveBeenCalled();
  });

  it('does not enter a page that was initially inactive', async () => {
    const view = render(art(true, false));
    view.rerender(art());
    await flush();
    expect(timing).not.toHaveBeenCalled();
  });

  it.each(['preference', 'inactive', 'background', 'reduction', 'unmount'])('invalidates a pending response after %s', async (event) => {
    const pending = deferred();
    query.mockReturnValue(pending.promise);
    const view = render(art());
    if (event === 'preference') view.rerender(art(false));
    if (event === 'inactive') view.rerender(art(true, false));
    if (event === 'background') act(() => lifecycle?.('background'));
    if (event === 'reduction') act(() => reduction?.(true));
    if (event === 'unmount') view.unmount();
    await act(async () => pending.resolve(false));
    expect(timing).not.toHaveBeenCalled();
    expect(setValue).not.toHaveBeenCalledWith(scale(6));
  });

  it.each(['preference', 'inactive', 'background', 'reduction', 'unmount'])('cancels and settles a running entrance after %s', async (event) => {
    const view = render(art());
    await flush();
    expect(start).toHaveBeenCalledTimes(1);
    setValue.mockClear();
    if (event === 'preference') { view.rerender(art(false)); view.rerender(art()); }
    if (event === 'inactive') { view.rerender(art(true, false)); view.rerender(art()); }
    if (event === 'background') act(() => { lifecycle?.('background'); lifecycle?.('active'); });
    if (event === 'reduction') act(() => { reduction?.(true); reduction?.(false); });
    if (event === 'unmount') view.unmount();
    await flush();
    expect(stop).toHaveBeenCalledTimes(1);
    expect(setValue).toHaveBeenCalledWith(0);
    expect(setValue).not.toHaveBeenCalledWith(scale(6));
    expect(start).toHaveBeenCalledTimes(1);
  });

  it('rechecks the system preference on foreground but never replays the entrance', async () => {
    render(art());
    await flush();
    act(() => { lifecycle?.('background'); lifecycle?.('active'); });
    await flush();
    expect(query).toHaveBeenCalledTimes(2);
    expect(start).toHaveBeenCalledTimes(1);
  });

  it('ignores an old response after a foreground recheck completes', async () => {
    const old = deferred();
    query.mockReturnValueOnce(old.promise).mockResolvedValueOnce(true);
    render(art());
    act(() => { lifecycle?.('background'); lifecycle?.('active'); });
    await flush();
    await act(async () => old.resolve(false));
    expect(query).toHaveBeenCalledTimes(2);
    expect(start).not.toHaveBeenCalled();
  });

  it('keeps the page still if initially backgrounded or lifecycle access fails', async () => {
    manager.getCurrentState.mockReturnValue('background');
    const view = render(art());
    act(() => lifecycle?.('active'));
    await flush();
    expect(start).not.toHaveBeenCalled();
    view.unmount();
    manager.getCurrentState.mockImplementation(() => { throw new Error('unsupported'); });
    render(art());
    await flush();
    expect(start).not.toHaveBeenCalled();
  });

  it('handles an unavailable motion event using query and lifecycle checks', async () => {
    jest.spyOn(accessibilityEvents, 'addEventListener').mockImplementation(() => { throw new Error('unsupported'); });
    render(art());
    await flush();
    expect(start).toHaveBeenCalledTimes(1);
    act(() => lifecycle?.('background'));
    expect(stop).toHaveBeenCalledTimes(1);
  });

  it('removes its listeners when the page leaves', async () => {
    const view = render(art());
    await flush();
    view.unmount();
    expect(removeLifecycle).toHaveBeenCalledTimes(1);
    expect(removeReduction).toHaveBeenCalledTimes(1);
  });

  it.each(['details'])('wires opt-in and activity to %s artwork while leaving controls outside', async (page) => {
    const make = (enabled = false, active = true) => page === 'library'
      ? <KidHomeScreen titles={[entry]} onOpen={jest.fn()} interfaceMotionEnabled={enabled} interfaceActive={active} />
      : <TitleDetailsScreen entry={entry} onPlay={jest.fn()} interfaceMotionEnabled={enabled} interfaceActive={active} />;
    const still = render(make());
    await flush();
    expect(timing).not.toHaveBeenCalled();
    still.unmount();
    const view = render(make(true));
    await flush();
    expect(start).toHaveBeenCalledTimes(1);
    const motion = screen.UNSAFE_getByType(CalmArtworkMotion);
    expect(motion.props.children.type).toBe(TitleArtwork);
    const action = screen.getByTestId(page === 'library' ? 'kid-home-watch' : 'title-details-play');
    expect(action.props.hasTVPreferredFocus).toBe(true);
    view.rerender(make(true, false));
    expect(stop).toHaveBeenCalledTimes(1);
    expect(start).toHaveBeenCalledTimes(1);
  });
});
