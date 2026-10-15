/** Audio calls are mocked here; audible balance and native focus need Vega. */
import { useKeplerAppStateManager, useTVEventHandler } from '@amazon-devices/react-native-kepler';
import { act, fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { AccessibilityInfo, AppState } from 'react-native';
import CalmButton from '../../src/calmframes/CalmButton';
import {
  createInterfaceSoundController,
  InterfaceFeedback,
  INTERFACE_SOUND_INTERVAL_MS,
  INTERFACE_SOUND_MAX_AGE_MS,
  INTERFACE_SOUND_TIMEOUT_MS,
  INTERFACE_SOUND_URI,
  INTERFACE_SOUND_VOLUME,
} from '../../src/calmframes/interfaceSound';
import { InterfaceSoundContext, useInterfaceSound } from '../../src/calmframes/useInterfaceSound';

function player() {
  const listeners = new Map<string, () => void>();
  return {
    src: '', volume: 1, currentTime: 1,
    initialize: jest.fn().mockResolvedValue(undefined),
    deinitialize: jest.fn().mockResolvedValue(undefined),
    play: jest.fn().mockResolvedValue(undefined), pause: jest.fn(),
    addEventListener: jest.fn((event, listener) => { listeners.set(event, listener); }),
    removeEventListener: jest.fn((event) => { listeners.delete(event); }),
    emit: (event: string) => listeners.get(event)?.(),
  };
}
const flush = async () => { for (let i = 0; i < 12; i += 1) { await Promise.resolve(); } };
function deferred() {
  let resolve!: () => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<void>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

describe('optional menu audio controller', () => {
  beforeEach(() => { jest.useFakeTimers(); });
  afterEach(() => { jest.useRealTimers(); });

  it('makes no player until allowed and uses a separate packaged selection sound', async () => {
    const audio = player();
    const makePlayer = jest.fn(() => audio);
    const sound = createInterfaceSoundController({ makePlayer });
    sound.confirm();
    expect(makePlayer).not.toHaveBeenCalled();
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    expect(audio.src).toBe('/pkg/assets/raw/sound/menu-select.mp3');
    expect(audio.src).toBe(INTERFACE_SOUND_URI);
    expect(audio.volume).toBe(INTERFACE_SOUND_VOLUME);
    expect(audio.currentTime).toBe(0);
    expect(audio.play).toHaveBeenCalledTimes(1);
    sound.stop();
    await flush();
  });

  it('drops overlapping and rapid confirmations without queuing a replay', async () => {
    const audio = player();
    const makePlayer = jest.fn(() => audio);
    const sound = createInterfaceSoundController({ makePlayer });
    sound.setAllowed(true);
    sound.confirm();
    sound.confirm();
    await flush();
    sound.confirm();
    expect(audio.play).toHaveBeenCalledTimes(1);
    audio.emit('ended');
    await flush();
    sound.confirm();
    expect(makePlayer).toHaveBeenCalledTimes(1);
    jest.advanceTimersByTime(INTERFACE_SOUND_INTERVAL_MS);
    sound.confirm();
    await flush();
    expect(audio.play).toHaveBeenCalledTimes(2);
    sound.stop();
    await flush();
  });

  it('invalidates pending initialization immediately, even if re-enabled before it resolves', async () => {
    const audio = player();
    const pending = deferred();
    audio.initialize.mockReturnValue(pending.promise);
    const sound = createInterfaceSoundController({ makePlayer: () => audio });
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    sound.stop();
    sound.setAllowed(true);
    sound.confirm();
    pending.resolve();
    await flush();
    expect(audio.play).not.toHaveBeenCalled();
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
  });

  it('drops a delayed initialization instead of sounding after the action', async () => {
    const audio = player();
    const pending = deferred();
    audio.initialize.mockReturnValue(pending.promise);
    const sound = createInterfaceSoundController({ makePlayer: () => audio });
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    jest.advanceTimersByTime(INTERFACE_SOUND_MAX_AGE_MS);
    expect(audio.pause).toHaveBeenCalled();
    // The SDK aborts an initialization that has not answered when the player
    // is deinitialized, so the release does not wait for the answer.
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
    pending.resolve();
    await flush();
    expect(audio.play).not.toHaveBeenCalled();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
  });

  it.each(['initialize', 'deinitialize'])('recovers from a player whose %s never answers', async (method) => {
    const stuck = player();
    stuck[method as 'initialize' | 'deinitialize'].mockReturnValue(new Promise<void>(() => {}));
    const good = player();
    const makePlayer = jest.fn().mockReturnValueOnce(stuck).mockReturnValue(good);
    const sound = createInterfaceSoundController({ makePlayer });
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    if (method === 'deinitialize') {
      expect(stuck.play).toHaveBeenCalledTimes(1);
      stuck.emit('ended');
    }
    jest.advanceTimersByTime(INTERFACE_SOUND_MAX_AGE_MS);
    await flush();
    expect(stuck.pause).toHaveBeenCalled();
    expect(stuck.deinitialize).toHaveBeenCalledTimes(1);
    // One player that never answers must not silence the menu for the rest
    // of the screen's life: the next request after the interval gets its own.
    jest.advanceTimersByTime(INTERFACE_SOUND_INTERVAL_MS);
    sound.confirm();
    await flush();
    expect(makePlayer).toHaveBeenCalledTimes(2);
    expect(good.play).toHaveBeenCalledTimes(1);
    sound.stop();
    await flush();
    expect(good.deinitialize).toHaveBeenCalledTimes(1);
  });

  it.each(['ended', 'error', 'audiofocuspaused', 'audiofocuslost'])('releases the player on %s', async (event) => {
    const audio = player();
    const sound = createInterfaceSoundController({ makePlayer: () => audio });
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    audio.emit(event);
    await flush();
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
    expect(audio.removeEventListener).toHaveBeenCalledTimes(4);
  });

  it('releases audio when the native end event never arrives', async () => {
    const audio = player();
    const sound = createInterfaceSoundController({ makePlayer: () => audio });
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    jest.advanceTimersByTime(INTERFACE_SOUND_TIMEOUT_MS);
    await flush();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
  });

  it.each(['initialize', 'play', 'deinitialize'])('contains a rejected %s call', async (method) => {
    const audio = player();
    audio[method as 'initialize' | 'play' | 'deinitialize'].mockRejectedValue(new Error('Unavailable'));
    const sound = createInterfaceSoundController({ makePlayer: () => audio });
    sound.setAllowed(true);
    expect(() => sound.confirm()).not.toThrow();
    await flush();
    sound.stop();
    await flush();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
  });

  it('contains constructor and pause failures', async () => {
    const unavailable = createInterfaceSoundController({ makePlayer: () => { throw new Error('No SDK'); } });
    unavailable.setAllowed(true);
    expect(() => unavailable.confirm()).not.toThrow();
    const audio = player();
    audio.pause.mockImplementation(() => { throw new Error('No audio'); });
    const sound = createInterfaceSoundController({ makePlayer: () => audio });
    sound.setAllowed(true);
    sound.confirm();
    await flush();
    expect(() => sound.stop()).not.toThrow();
    await flush();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
  });
});

describe('menu sound lifecycle', () => {
  let audio: ReturnType<typeof player>;
  let makePlayer: jest.Mock;
  let appEvents: Map<string, (next?: string) => void>;
  let keplerEvents: Map<string, (next?: string) => void>;
  let readerEvent: (next: boolean) => void;
  let feedback: InterfaceFeedback;
  let subscriptions: jest.Mock[];
  const media = require('@amazon-devices/react-native-w3cmedia');
  const originalAppState = AppState.currentState;

  const Capture = ({ enabled = true, active = true }: { enabled?: boolean; active?: boolean }) => {
    feedback = useInterfaceSound({ enabled, active });
    return null;
  };

  beforeEach(() => {
    jest.useFakeTimers();
    audio = player();
    (useTVEventHandler as jest.Mock).mockClear();
    makePlayer = jest.fn(() => audio);
    media.AudioPlayer = makePlayer;
    media.AudioContentType = { CONTENT_TYPE_SONIFICATION: 4 };
    media.AudioUsageType = { USAGE_NOTIFICATION: 4 };
    appEvents = new Map();
    keplerEvents = new Map();
    subscriptions = [];
    const subscribe = (target: Map<string, (next?: string) => void>, event: string, listener: (next?: string) => void) => {
      target.set(event, listener);
      const remove = jest.fn(() => { target.delete(event); });
      subscriptions.push(remove);
      return { remove };
    };
    AppState.currentState = 'active';
    const appState = AppState as unknown as {
      addEventListener(event: string, callback: (next?: string) => void): { remove(): void };
    };
    jest.spyOn(appState, 'addEventListener').mockImplementation((event, callback) => subscribe(appEvents, event, callback));
    (useKeplerAppStateManager as jest.Mock).mockReturnValue({
      getCurrentState: () => 'active',
      addEventListener: (event: string, callback: (next?: string) => void) => subscribe(keplerEvents, event, callback),
    });
    const accessibility = AccessibilityInfo as unknown as {
      addEventListener(event: string, callback: (next: boolean) => void): { remove(): void };
    };
    jest.spyOn(accessibility, 'addEventListener').mockImplementation((event, callback) => {
      if (event === 'screenReaderChanged') { readerEvent = callback; }
      const remove = jest.fn();
      subscriptions.push(remove);
      return { remove };
    });
    jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(false);
  });

  afterEach(() => {
    AppState.currentState = originalAppState;
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  it('keeps a held remote selection silent after its first cue even beyond the cooldown', async () => {
    const view = render(<Capture />);
    await act(flush);
    const calls = (useTVEventHandler as jest.Mock).mock.calls;
    const key = calls[calls.length - 1][0];
    key({ eventType: 'select', eventKeyAction: 0 });
    feedback.confirm();
    await act(flush);
    audio.emit('ended');
    jest.advanceTimersByTime(1000);
    key({ eventType: 'select', eventKeyAction: 0 });
    feedback.confirm();
    await act(flush);
    expect(audio.play).toHaveBeenCalledTimes(1);
    key({ eventType: 'select', eventKeyAction: 1 });
    key({ eventType: 'select', eventKeyAction: 0 });
    feedback.confirm();
    await act(flush);
    expect(audio.play).toHaveBeenCalledTimes(2);
    view.unmount();
  });

  it('stays silent until accessibility resolves, then uses the SDK sonification notification categories', async () => {
    const pending = deferred();
    (AccessibilityInfo.isScreenReaderEnabled as jest.Mock).mockReturnValue(pending.promise.then(() => false));
    const view = render(<Capture />);
    feedback.confirm();
    expect(makePlayer).not.toHaveBeenCalled();
    pending.resolve();
    await act(flush);
    feedback.confirm();
    await act(flush);
    expect(makePlayer).toHaveBeenCalledWith(4, 4);
    expect(audio.play).toHaveBeenCalledTimes(1);
    view.unmount();
    await flush();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
    expect(subscriptions.every((remove) => remove.mock.calls.length === 1)).toBe(true);
  });

  it.each([{ enabled: false, active: true }, { enabled: true, active: false }])('stays silent with %j', async (props) => {
    const view = render(<Capture {...props} />);
    await act(flush);
    feedback.confirm();
    await act(flush);
    expect(makePlayer).not.toHaveBeenCalled();
    view.unmount();
  });

  it('keeps a live screen-reader change ahead of a stale initial query', async () => {
    const pending = deferred();
    (AccessibilityInfo.isScreenReaderEnabled as jest.Mock).mockReturnValue(pending.promise.then(() => false));
    const view = render(<Capture />);
    readerEvent(true);
    pending.resolve();
    await act(flush);
    feedback.confirm();
    expect(makePlayer).not.toHaveBeenCalled();
    readerEvent(false);
    feedback.confirm();
    await act(flush);
    expect(audio.play).toHaveBeenCalledTimes(1);
    readerEvent(true);
    await act(flush);
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
    view.unmount();
  });

  it('stays silent when the screen-reader query fails', async () => {
    (AccessibilityInfo.isScreenReaderEnabled as jest.Mock).mockRejectedValue(new Error('No accessibility state'));
    const view = render(<Capture />);
    await act(flush);
    feedback.confirm();
    expect(makePlayer).not.toHaveBeenCalled();
    view.unmount();
  });

  it.each(['app', 'kepler'])('stays silent while %s foreground state is unknown', async (source) => {
    if (source === 'app') { AppState.currentState = 'unknown'; }
    if (source === 'kepler') {
      const manager = (useKeplerAppStateManager as jest.Mock)();
      manager.getCurrentState = () => 'unknown';
    }
    const view = render(<Capture />);
    await act(flush);
    feedback.confirm();
    expect(makePlayer).not.toHaveBeenCalled();
    view.unmount();
  });

  it.each(['app-background', 'kepler-background', 'blur', 'reader', 'disable', 'inactive', 'unmount'])('cancels a pending sound on %s', async (reason) => {
    const pending = deferred();
    audio.initialize.mockReturnValue(pending.promise);
    const view = render(<Capture />);
    await act(flush);
    feedback.confirm();
    await act(flush);
    switch (reason) {
      case 'app-background': appEvents.get('change')?.('background'); break;
      case 'kepler-background': keplerEvents.get('change')?.('background'); break;
      case 'blur': keplerEvents.get('blur')?.(); break;
      case 'reader': readerEvent(true); break;
      case 'disable': view.rerender(<Capture enabled={false} />); break;
      case 'inactive': view.rerender(<Capture active={false} />); break;
      case 'unmount': view.unmount(); break;
    }
    pending.resolve();
    await act(flush);
    expect(audio.play).not.toHaveBeenCalled();
    expect(audio.deinitialize).toHaveBeenCalledTimes(1);
    if (reason !== 'unmount') { view.unmount(); }
  });

  it('keeps stop latched through an immediate post-action confirmation and restores only on activation', async () => {
    const view = render(<Capture />);
    await act(flush);
    const first = feedback;
    feedback.stop();
    feedback.confirm();
    expect(makePlayer).not.toHaveBeenCalled();
    view.rerender(<Capture active={false} />);
    view.rerender(<Capture active />);
    expect(feedback).toBe(first);
    feedback.confirm();
    await act(flush);
    expect(audio.play).toHaveBeenCalledTimes(1);
    view.unmount();
  });
});

describe('button menu feedback', () => {
  it('does not sound when focus moves without an activation', () => {
    const confirm = jest.fn();
    const view = render(<InterfaceSoundContext.Provider value={{ confirm, stop: jest.fn() }}>
      <CalmButton label="Library" onPress={jest.fn()} />
    </InterfaceSoundContext.Provider>);
    fireEvent(view.getByRole('button'), 'focus');
    fireEvent(view.getByRole('button'), 'blur');
    expect(confirm).not.toHaveBeenCalled();
  });
  it('confirms only after the action and contains feedback failures', () => {
    const order: string[] = [];
    const confirm = jest.fn(() => { order.push('sound'); throw new Error('Silent failure'); });
    const view = render(
      <InterfaceSoundContext.Provider value={{ confirm, stop: jest.fn() }}>
        <CalmButton label="Library" onPress={() => { order.push('action'); }} />
      </InterfaceSoundContext.Provider>,
    );
    expect(() => fireEvent.press(view.getByRole('button'))).not.toThrow();
    expect(order).toEqual(['action', 'sound']);
  });

  it.each(['disabled', 'no-action', 'opt-out'])('does not sound for %s', (reason) => {
    const confirm = jest.fn();
    const onPress = jest.fn();
    const view = render(
      <InterfaceSoundContext.Provider value={{ confirm, stop: jest.fn() }}>
        <CalmButton label="Watch" disabled={reason === 'disabled'} sound={reason !== 'opt-out'}
          onPress={reason === 'no-action' ? undefined : onPress} />
      </InterfaceSoundContext.Provider>,
    );
    fireEvent.press(view.getByRole('button'));
    expect(confirm).not.toHaveBeenCalled();
    expect(onPress).toHaveBeenCalledTimes(reason === 'opt-out' ? 1 : 0);
  });

  it('keeps controls working without a sound provider', () => {
    const onPress = jest.fn();
    const view = render(<CalmButton label="Continue" onPress={onPress} />);
    fireEvent.press(view.getByRole('button'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('does not confirm an action that throws', () => {
    const confirm = jest.fn();
    const view = render(
      <InterfaceSoundContext.Provider value={{ confirm, stop: jest.fn() }}>
        <CalmButton label="Continue" onPress={() => { throw new Error('Action failed'); }} />
      </InterfaceSoundContext.Provider>,
    );
    expect(() => fireEvent.press(view.getByRole('button'))).toThrow('Action failed');
    expect(confirm).not.toHaveBeenCalled();
  });
});
