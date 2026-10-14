import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { AccessibilityInfo, Animated, BackHandler } from 'react-native';
import HarborOpening, { HARBOR_OPENING_MS } from '../../src/calmframes/HarborOpening';
import { frameFromTree, RenderedNode } from '../../src/calmframes/uiCapture';
import { HARBOR_BOOTSTRAP_FRAME } from '../../src/calmframes/uiFrames';
import KidModeScreen from '../../src/screens/KidModeScreen';
import { newFamily } from '../../src/calmframes/profiles';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { offlineTitle } from '../../src/calmframes/offlineTitle';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';

jest.mock('@react-native-async-storage/async-storage', () => ({}));

const events = AccessibilityInfo as unknown as {
  addEventListener(name: string, callback: (value: boolean) => void): { remove(): void };
};
const flush = async () => { await act(async () => { await Promise.resolve(); }); };

describe('waves into the library', () => {
  let lifecycle: (state: string) => void;
  let reduction: (reduced: boolean) => void;
  let screenReader: (enabled: boolean) => void;
  let skip: () => boolean | null | undefined;
  let completeAnimation: (result: { finished: boolean }) => void;
  let start: jest.Mock;
  let stop: jest.Mock;
  let timing: jest.SpyInstance;
  let query: jest.SpyInstance;
  let removed: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    removed = jest.fn();
    start = jest.fn((callback) => { completeAnimation = callback; });
    stop = jest.fn();
    (useKeplerAppStateManager as jest.Mock).mockReturnValue({
      getCurrentState: () => 'active',
      addAppStateListener: (_name: string, callback: typeof lifecycle) => {
        lifecycle = callback;
        return { remove: removed };
      },
    });
    jest.spyOn(events, 'addEventListener').mockImplementation((name, callback) => {
      if (name === 'reduceMotionChanged') reduction = callback;
      if (name === 'screenReaderChanged') screenReader = callback;
      return { remove: removed };
    });
    jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_name, callback) => {
      skip = callback;
      return { remove: removed };
    });
    query = jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
    jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(false);
    timing = jest.spyOn(Animated, 'timing').mockReturnValue({ start, stop, reset: jest.fn() });
  });
  afterEach(() => { jest.restoreAllMocks(); jest.useRealTimers(); });

  it('shows the real wave palette during loading without a timer or motion query', () => {
    render(<HarborOpening />);
    expect(frameFromTree('harbor-bootstrap', screen.toJSON() as unknown as RenderedNode)).toEqual(HARBOR_BOOTSTRAP_FRAME);
    expect(screen.getByRole('progressbar').props.accessibilityLabel).toContain('Opening your library');
    expect(query).not.toHaveBeenCalled();
    expect(timing).not.toHaveBeenCalled();
    expect(jest.getTimerCount()).toBe(0);
  });

  it('cuts immediately when household motion is off', async () => {
    const finish = jest.fn();
    render(<HarborOpening onFinish={finish} />);
    await flush();
    expect(query).not.toHaveBeenCalled();
    expect(timing).not.toHaveBeenCalled();
    expect(finish).toHaveBeenCalledTimes(1);
  });

  it.each([true, null, undefined, 'error'])('cuts without movement for system preference %s', async (reduced) => {
    if (reduced === 'error') query.mockRejectedValue(new Error('unavailable'));
    else query.mockResolvedValue(reduced);
    const finish = jest.fn();
    render(<HarborOpening motionEnabled onFinish={finish} />);
    await flush();
    expect(timing).not.toHaveBeenCalled();
    expect(finish).toHaveBeenCalledTimes(1);
  });

  it('runs one native transform, then cuts; rerenders do not restart it', async () => {
    const finish = jest.fn();
    const view = render(<HarborOpening motionEnabled onFinish={finish} />);
    await flush();
    view.rerender(<HarborOpening motionEnabled onFinish={() => finish()} />);
    expect(timing).toHaveBeenCalledTimes(1);
    expect(timing).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ duration: HARBOR_OPENING_MS, useNativeDriver: true, isInteraction: false }));
    expect(finish).not.toHaveBeenCalled();
    act(() => completeAnimation({ finished: true }));
    act(() => jest.advanceTimersByTime(3000));
    expect(finish).toHaveBeenCalledTimes(1);
  });

  it.each([true, undefined])('opens the library directly for screen-reader state %s', async (enabled) => {
    (AccessibilityInfo.isScreenReaderEnabled as jest.Mock).mockResolvedValue(enabled);
    const finish = jest.fn();
    render(<HarborOpening motionEnabled onFinish={finish} />);
    await flush();
    expect(timing).not.toHaveBeenCalled();
    expect(finish).toHaveBeenCalledTimes(1);
  });

  it.each(['background', 'reduction', 'screenReader', 'back', 'inactive', 'off'])('settles immediately on %s', async (event) => {
    const finish = jest.fn();
    const view = render(<HarborOpening motionEnabled onFinish={finish} />);
    await flush();
    act(() => {
      if (event === 'background') lifecycle('background');
      if (event === 'reduction') reduction(true);
      if (event === 'screenReader') screenReader(true);
      if (event === 'back') expect(skip()).toBe(true);
    });
    if (event === 'inactive') view.rerender(<HarborOpening motionEnabled active={false} onFinish={finish} />);
    if (event === 'off') view.rerender(<HarborOpening onFinish={finish} />);
    expect(stop).toHaveBeenCalled();
    expect(finish).toHaveBeenCalledTimes(1);
  });

  it('does not hang if the system preference query never returns', async () => {
    query.mockReturnValue(new Promise(() => {}));
    const finish = jest.fn();
    render(<HarborOpening motionEnabled onFinish={finish} />);
    await flush();
    act(() => jest.advanceTimersByTime(HARBOR_OPENING_MS + 600));
    expect(finish).toHaveBeenCalledTimes(1);
    expect(timing).not.toHaveBeenCalled();
  });

  it('ignores late preference resolution after unmount and removes subscriptions', async () => {
    let resolve!: (reduced: boolean) => void;
    query.mockReturnValue(new Promise<boolean>((yes) => { resolve = yes; }));
    const finish = jest.fn();
    const view = render(<HarborOpening motionEnabled onFinish={finish} />);
    view.unmount();
    await act(async () => resolve(false));
    act(() => jest.runOnlyPendingTimers());
    expect(timing).not.toHaveBeenCalled();
    expect(finish).not.toHaveBeenCalled();
    expect(removed).toHaveBeenCalledTimes(4);
  });

  it('opens the shelf as soon as storage is ready, without a timed arrival', async () => {
    const family = { ...newFamily(), interfaceMotionEnabled: true };
    const storage = {
      getItem: async () => JSON.stringify({ version: 1, family, gate: setPin(emptyPinGate(), '1357', 'arrival-test') }),
      setItem: jest.fn(),
    };
    render(<KidModeScreen navigation={{ navigate: jest.fn() } as never} householdStorage={storage}
      catalog={[offlineTitle('file:///fixture.mp4')]}
      nowMs={() => Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000} />);
    await flush();
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
    expect(screen.queryByTestId('harbor-opening')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    await flush();
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
    expect(screen.queryByTestId('harbor-opening')).toBeNull();
  });
});
