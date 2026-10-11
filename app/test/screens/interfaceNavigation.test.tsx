import React from 'react';
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

function open(family = newFamily()) {
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
  render(<KidModeScreen
    navigation={navigation as never}
    catalog={[offlineTitle('file:///pkg/assets/raw/offline/calm_gradient.mp4')]}
    householdStorage={storage}
    nowMs={() => NOW}
  />);
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
  soundHook.mockReturnValue(feedback);
});

it('silences menu audio before opening playback and restores the route on focus', async () => {
  const { navigation, listeners } = open();
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
  const { storage } = open();
  await unlock();
  let finish!: () => void;
  storage.setItem.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
  fireEvent.press(screen.getByTestId('kid-mode-parent-interface-motion'));
  expect(feedback.confirm).not.toHaveBeenCalled();
  await act(async () => finish());
  expect(feedback.confirm).toHaveBeenCalledTimes(1);
});

it('keeps a failed settings write silent while presenting recovery', async () => {
  const { storage } = open();
  await unlock();
  storage.setItem.mockRejectedValueOnce(new Error('storage unavailable'));
  fireEvent.press(screen.getByTestId('kid-mode-parent-interface-motion'));
  await screen.findByTestId('kid-mode-storage-retry');
  await waitFor(() => expect(soundHook).toHaveBeenLastCalledWith({ enabled: false, active: true }));
  expect(feedback.confirm).not.toHaveBeenCalled();
});

it('waits for an added profile to save before confirming it', async () => {
  const { storage } = open();
  await unlock();
  let finish!: () => void;
  storage.setItem.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
  fireEvent.press(screen.getByTestId('kid-mode-parent-add-profile'));
  expect(feedback.confirm).not.toHaveBeenCalled();
  await act(async () => finish());
  expect(feedback.confirm).toHaveBeenCalledTimes(1);
});

it('does not confirm an added profile when its save fails', async () => {
  const { storage } = open();
  await unlock();
  storage.setItem.mockRejectedValueOnce(new Error('storage unavailable'));
  fireEvent.press(screen.getByTestId('kid-mode-parent-add-profile'));
  await screen.findByTestId('kid-mode-storage-retry');
  expect(feedback.confirm).not.toHaveBeenCalled();
});

it.each(['saved', 'failed'] as const)('confirms profile removal only when its write is saved: %s', async (outcome) => {
  const { storage } = open(addProfile(newFamily(), 'Sam'));
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
