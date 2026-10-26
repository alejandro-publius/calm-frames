/** Route-level writes and profile switching, with fictional records in memory. */
import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import KidModeScreen from '../../src/screens/KidModeScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { scale } from '../../src/calmframes/calmStyles';
import { HouseholdStorage, HOUSEHOLD_STORAGE_KEY, SavedHousehold } from '../../src/calmframes/householdStorage';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { addProfile, newFamily } from '../../src/calmframes/profiles';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { offlineTitle } from '../../src/calmframes/offlineTitle';

jest.mock('@react-native-async-storage/async-storage', () => ({}));

const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;
const RECORD: SavedHousehold = {
  version: 1,
  family: addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam'),
  gate: setPin(emptyPinGate(), '1357', 'comfort-route-fixture'),
};
const press = (id: string) => fireEvent.press(screen.getByTestId(id));

function memoryStorage() {
  let disk = JSON.stringify(RECORD);
  let refuse = false;
  let pending: Promise<void> | undefined;
  return {
    getItem: jest.fn(async () => disk),
    setItem: jest.fn(async (_key: string, text: string) => {
      const wait = pending; pending = undefined;
      if (wait) await wait;
      if (refuse) { refuse = false; throw new Error('fictional storage failure'); }
      disk = text;
    }),
    read: () => JSON.parse(disk) as SavedHousehold,
    refuseNext: () => { refuse = true; },
    holdNext: () => {
      let release!: () => void;
      pending = new Promise<void>(resolve => { release = resolve; });
      return release;
    },
  };
}

function open(storage: HouseholdStorage) {
  return render(<KidModeScreen navigation={{ navigate: jest.fn() } as never}
    catalog={[offlineTitle('file:///pkg/assets/raw/offline/calm_gradient.mp4')]}
    householdStorage={storage} nowMs={() => NOW} />);
}

async function unlock() {
  for (const digit of '1357') press(`kid-mode-parent-key-${digit}`);
  await screen.findByTestId('kid-mode-parent-open');
  press('kid-mode-parent-profiles-profile-2');
}

async function parents() {
  await screen.findByTestId('kid-mode-home');
  press('kid-mode-home-parent-area');
  await unlock();
}

function infoFont() {
  return StyleSheet.flatten(screen.getByTestId('kid-mode-details-info-safety').props.style).fontSize;
}

it('persists one preference, applies it only to the watching kid and retains it after remount', async () => {
  const storage = memoryStorage();
  const view = open(storage);
  await parents();
  const before = storage.read();
  const count = storage.setItem.mock.calls.length;
  const release = storage.holdNext();
  press('kid-mode-parent-reading-comfort');
  expect(screen.getByTestId('kid-mode-parent-reading-comfort').props.accessibilityState.checked).toBe(false);
  expect(storage.read()).toEqual(before);
  await act(async () => release());
  expect(storage.setItem.mock.calls.length).toBe(count + 1);
  expect(storage.setItem.mock.calls[count][0]).toBe(HOUSEHOLD_STORAGE_KEY);
  expect(storage.read()).toEqual({ ...before, family: { ...before.family,
    profiles: [before.family.profiles[0], { ...before.family.profiles[1], readingComfortEnabled: true }],
  } });
  expect(screen.getByTestId('kid-mode-parent-reading-comfort').props.hasTVPreferredFocus).toBe(true);
  press('kid-mode-parent-back');
  press('kid-mode-home-more-info');
  press('kid-mode-details-show-info');
  expect(infoFont()).toBe(scale(36));
  press('kid-mode-details-info-back');
  press('kid-mode-details-back');
  press('kid-mode-home-choose-profile');
  await act(async () => press('kid-mode-home-profiles-profile-2'));
  press('kid-mode-home-more-info');
  press('kid-mode-details-show-info');
  expect(infoFont()).toBe(scale(40));
  view.unmount();
  open(storage);
  await screen.findByTestId('kid-mode-home');
  press('kid-mode-home-more-info');
  press('kid-mode-details-show-info');
  expect(infoFont()).toBe(scale(40));
  expect(storage.read().gate).toEqual(before.gate);
});

it('keeps the original record on write failure and retries the same preference behind the PIN', async () => {
  const storage = memoryStorage();
  open(storage);
  await parents();
  const before = storage.read();
  storage.refuseNext();
  press('kid-mode-parent-reading-comfort');
  await screen.findByTestId('kid-mode-storage');
  expect(storage.read()).toEqual(before);
  expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
  const attempted = storage.setItem.mock.calls[storage.setItem.mock.calls.length - 1][1];
  await act(async () => press('kid-mode-storage-retry'));
  expect(storage.setItem.mock.calls[storage.setItem.mock.calls.length - 1][1]).toBe(attempted);
  expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
  await unlock();
  expect(screen.getByTestId('kid-mode-parent-reading-comfort').props.accessibilityState.checked).toBe(true);
  expect(storage.read().family.profiles[0]).toEqual(before.family.profiles[0]);
  expect(storage.read().gate).toEqual(before.gate);
});
