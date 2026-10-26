import React from 'react';
import TestRenderer from 'react-test-renderer';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import KidModeScreen from '../../src/screens/KidModeScreen';
import { useInterfaceSound } from '../../src/calmframes/useInterfaceSound';
import { addProfile, newFamily } from '../../src/calmframes/profiles';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { offlineTitle } from '../../src/calmframes/offlineTitle';

jest.mock('@react-native-async-storage/async-storage', () => ({}));
jest.mock('../../src/calmframes/useInterfaceSound', () => ({
  ...jest.requireActual('../../src/calmframes/useInterfaceSound'),
  useInterfaceSound: jest.fn(),
}));

const feedback = { confirm: jest.fn(), stop: jest.fn() };
const soundHook = useInterfaceSound as jest.Mock;
const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60000;

async function open(family = newFamily()) {
  let disk = JSON.stringify({
    version: 1,
    family: { ...family, interfaceSoundsEnabled: true },
    gate: setPin(emptyPinGate(), '1357', 'interface-navigation'),
  });
  const listeners: Record<string, () => void> = {};
  const storage = {
    getItem: jest.fn(async () => disk),
    setItem: jest.fn(async (_key: string, text: string) => { disk = text; }),
  };
  const navigation = {
    navigate: jest.fn(),
    isFocused: () => true,
    addListener: jest.fn((name: string, callback: () => void) => {
      listeners[name] = callback;
      return () => { delete listeners[name]; };
    }),
  };
  // The fixture includes asynchronous household hydration. Flush that initial
  // render before starting query deadlines; cold copied-lane verification can
  // otherwise consume the first wait while React still holds the loaded record.
  render(<KidModeScreen
    navigation={navigation as never}
    catalog={[offlineTitle('file:///pkg/assets/raw/offline/calm_gradient.mp4')]}
    householdStorage={storage}
    nowMs={() => NOW}
  />);
  await act(async () => {});
  return { navigation, listeners, storage };
}

async function unlock() {
  await screen.findByTestId('kid-mode-home');
  fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
  for (const digit of '1357') {
    fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
  }
  await screen.findByTestId('kid-mode-parent-open');
  feedback.confirm.mockClear();
}

beforeEach(() => {
  jest.clearAllMocks();
  feedback.confirm.mockReset();
  soundHook.mockReturnValue(feedback);
});

it('silences menu audio before opening playback and restores the route on focus', async () => {
  const { navigation, listeners } = await open();
  await screen.findByTestId('kid-mode-home');
  feedback.confirm.mockClear();
  fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
  expect(navigation.navigate).toHaveBeenCalledTimes(1);
  expect(feedback.stop).toHaveBeenCalledTimes(1);
  expect(feedback.stop.mock.invocationCallOrder[0]).toBeLessThan(navigation.navigate.mock.invocationCallOrder[0]);
  expect(feedback.confirm).not.toHaveBeenCalled();
  expect(soundHook).toHaveBeenLastCalledWith({ enabled: true, active: false });
  act(() => listeners.focus());
  expect(soundHook).toHaveBeenLastCalledWith({ enabled: true, active: true });
  act(() => listeners.blur());
  expect(feedback.stop).toHaveBeenCalledTimes(2);
  expect(soundHook).toHaveBeenLastCalledWith({ enabled: true, active: false });
});

it('confirms a saved menu preference only after persistence succeeds', async () => {
  const { storage } = await open();
  await unlock();
  let finish!: () => void;
  storage.setItem.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
  fireEvent.press(screen.getByTestId('kid-mode-parent-interface-motion'));
  expect(feedback.confirm).not.toHaveBeenCalled();
  await act(async () => finish());
  expect(feedback.confirm).toHaveBeenCalledTimes(1);
});

it('confirms the press that turns selection sounds on, on the concurrent root the device uses', async () => {
  // Fabric renders on a concurrent root, where a state update made from a
  // promise is rendered in a later scheduler task. The write's continuation
  // then runs before React renders the saved record, so a confirmation raised
  // there reaches the hook while it still reads the old record and stays
  // silent. The library's render above is a legacy root, and act() flushes
  // the render first, so this test runs the write on a concurrent root with
  // act() off, the way the device does.
  const actEnvironment = global as { IS_REACT_ACT_ENVIRONMENT?: boolean };
  const wasActEnvironment = actEnvironment.IS_REACT_ACT_ENVIRONMENT;
  actEnvironment.IS_REACT_ACT_ENVIRONMENT = false;
  let disk = JSON.stringify({
    version: 1,
    family: { ...newFamily(), interfaceSoundsEnabled: false },
    gate: setPin(emptyPinGate(), '1357', 'interface-navigation'),
  });
  const storage = {
    getItem: jest.fn(async () => disk),
    setItem: jest.fn(async (_key: string, text: string) => { disk = text; }),
  };
  const navigation = { navigate: jest.fn(), isFocused: () => true, addListener: jest.fn(() => () => {}) };
  // react-test-renderer 19.2 takes this option; its 19.1 typings do not list it.
  const concurrentRoot: TestRenderer.TestRendererOptions & { unstable_isConcurrent: boolean } = {
    createNodeMock: () => null,
    unstable_isConcurrent: true,
  };
  const renderer = TestRenderer.create(
    <KidModeScreen
      navigation={navigation as never}
      catalog={[offlineTitle('file:///pkg/assets/raw/offline/calm_gradient.mp4')]}
      householdStorage={storage}
      nowMs={() => NOW}
    />,
    concurrentRoot,
  );
  const host = (testID: string) =>
    renderer.root.find((node) => node.props.testID === testID && typeof node.type === 'string');
  try {
    await waitFor(() => host('kid-mode-home'));
    fireEvent.press(host('kid-mode-home-parent-area'));
    for (const digit of '1357') {
      fireEvent.press(host(`kid-mode-parent-key-${digit}`));
    }
    await waitFor(() => host('kid-mode-parent-open'));
    feedback.confirm.mockClear();
    expect(soundHook).toHaveBeenLastCalledWith({ enabled: false, active: true });
    const enabledWhenConfirmed: boolean[] = [];
    feedback.confirm.mockImplementation(() => {
      enabledWhenConfirmed.push(soundHook.mock.calls[soundHook.mock.calls.length - 1][0].enabled);
    });
    let finish!: () => void;
    storage.setItem.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
    fireEvent.press(host('kid-mode-parent-interface-sounds'));
    expect(feedback.confirm).not.toHaveBeenCalled();
    finish();
    await waitFor(() => expect(feedback.confirm).toHaveBeenCalledTimes(1));
    const written = storage.setItem.mock.calls[storage.setItem.mock.calls.length - 1][1];
    expect(JSON.parse(written).family.interfaceSoundsEnabled).toBe(true);
    expect(enabledWhenConfirmed).toEqual([true]);
  } finally {
    renderer.unmount();
    actEnvironment.IS_REACT_ACT_ENVIRONMENT = wasActEnvironment;
  }
});

it('keeps a failed settings write silent while presenting recovery', async () => {
  const { storage } = await open();
  await unlock();
  storage.setItem.mockRejectedValueOnce(new Error('storage unavailable'));
  fireEvent.press(screen.getByTestId('kid-mode-parent-interface-motion'));
  await screen.findByTestId('kid-mode-storage-retry');
  await waitFor(() => expect(soundHook).toHaveBeenLastCalledWith({ enabled: false, active: true }));
  expect(feedback.confirm).not.toHaveBeenCalled();
});

it('waits for an added profile to save before confirming it', async () => {
  const { storage } = await open();
  await unlock();
  let finish!: () => void;
  storage.setItem.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
  fireEvent.press(screen.getByTestId('kid-mode-parent-add-profile'));
  expect(feedback.confirm).not.toHaveBeenCalled();
  await act(async () => finish());
  expect(feedback.confirm).toHaveBeenCalledTimes(1);
});

it('does not confirm an added profile when its save fails', async () => {
  const { storage } = await open();
  await unlock();
  storage.setItem.mockRejectedValueOnce(new Error('storage unavailable'));
  fireEvent.press(screen.getByTestId('kid-mode-parent-add-profile'));
  await screen.findByTestId('kid-mode-storage-retry');
  expect(feedback.confirm).not.toHaveBeenCalled();
});

it.each(['saved', 'failed'] as const)('confirms profile removal only when its write is saved: %s', async (outcome) => {
  const { storage } = await open(addProfile(newFamily(), 'Sam'));
  await unlock();
  fireEvent.press(screen.getByTestId('kid-mode-parent-profiles-profile-2'));
  fireEvent.press(screen.getByTestId('kid-mode-parent-remove-profile'));
  feedback.confirm.mockClear();
  let finish!: () => void;
  storage.setItem.mockImplementationOnce(() => new Promise<void>((resolve, reject) => {
    finish = () => outcome === 'saved' ? resolve() : reject(new Error('storage unavailable'));
  }));
  fireEvent.press(screen.getByTestId('kid-mode-parent-remove-confirm'));
  expect(feedback.confirm).not.toHaveBeenCalled();
  await act(async () => finish());
  expect(feedback.confirm).toHaveBeenCalledTimes(outcome === 'saved' ? 1 : 0);
  if (outcome === 'failed') {
    await screen.findByTestId('kid-mode-storage-retry');
  }
});
