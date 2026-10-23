/**
 * A kid's new name, saved through the route.
 *
 * The parent area learns whether a rename committed from the route's own
 * household write, not from a callback returning. These tests run the whole
 * thing: the shelf, the PIN, the picker, the letter keys and the write to
 * storage, with a storage that can be told to fail.
 *
 * Two outcomes are written down here.
 *
 * - A write that commits changes one kid's name in the stored record and
 *   nothing else: not the id, not the settings, not the floor, not the PIN,
 *   not the record of what was hidden for that kid.
 * - A write that fails takes the route's existing path for every failed
 *   household write. The storage screen replaces Parents, its Try again
 *   writes the same renamed record, and Parents comes back behind the PIN.
 *   The typed name is not lost: it is the pending write.
 *
 * Seen to fail: with `setFamily` returning nothing, as it did before, the
 * editor had no answer to wait for and the first test's `waitFor` on the
 * editor closing timed out.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import React from 'react';
import KidModeScreen from '../../src/screens/KidModeScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { HouseholdStorage, SavedHousehold } from '../../src/calmframes/householdStorage';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { addProfile, newFamily } from '../../src/calmframes/profiles';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { offlineTitle } from '../../src/calmframes/offlineTitle';
import {
  readHideLogs,
  recordHide,
  resetHideLogs,
} from '../../src/calmframes/hideLogStore';

jest.mock('@react-native-async-storage/async-storage', () => ({}));

const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;
const RECORD: SavedHousehold = {
  version: 1,
  family: addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam'),
  // The stored record must carry the production round count, or it does not load.
  gate: setPin(emptyPinGate(), '1357', 'name-test'),
};

/** A disk in memory that can be told to refuse the next writes. */
function memoryStorage(initial: SavedHousehold) {
  let disk = JSON.stringify(initial);
  let refusals = 0;
  return {
    getItem: jest.fn(async () => disk),
    setItem: jest.fn(async (_key: string, text: string) => {
      if (refusals > 0) {
        refusals -= 1;
        throw new Error('the disk said no');
      }
      disk = text;
    }),
    read: () => JSON.parse(disk) as SavedHousehold,
    refuseNext: (count: number) => {
      refusals = count;
    },
  };
}

function open(storage: HouseholdStorage) {
  render(
    <KidModeScreen
      navigation={{ navigate: jest.fn() } as never}
      catalog={[offlineTitle('file:///pkg/assets/raw/offline/calm_gradient.mp4')]}
      householdStorage={storage}
      newSalt={() => 'name-test'}
      nowMs={() => NOW}
    />,
  );
}

const press = (testID: string) => fireEvent.press(screen.getByTestId(testID));

/** Through the PIN to Sam's editor, with Ash typed in place of Sam. */
async function typeAshForSam() {
  await screen.findByTestId('kid-mode-home');
  press('kid-mode-home-parent-area');
  for (const digit of '1357') {
    press(`kid-mode-parent-key-${digit}`);
  }
  await screen.findByTestId('kid-mode-parent-open');
  press('kid-mode-parent-profiles-profile-2');
  press('kid-mode-parent-rename-profile');
  for (let index = 0; index < 3; index += 1) {
    press('kid-mode-parent-name-key-delete');
  }
  for (const letter of 'ash') {
    press(`kid-mode-parent-name-key-${letter}`);
  }
  expect(screen.getByTestId('kid-mode-parent-name-draft').props.children).toBe('Ash');
}

describe('saving a kid\'s name through the route', () => {
  beforeEach(() => resetHideLogs());

  it('writes the new name onto the same kid and leaves the rest of the record alone', async () => {
    recordHide(
      { atMs: NOW, titleId: 'one', titleName: 'One', positionMs: 1_000, durationMs: 4_000, cause: 'schedule' },
      { profileId: 'profile-2' },
    );
    const storage = memoryStorage(RECORD);
    open(storage);
    await typeAshForSam();
    const writesBefore = storage.setItem.mock.calls.length;

    press('kid-mode-parent-name-save');
    await waitFor(() => expect(screen.queryByTestId('kid-mode-parent-name')).toBeNull());

    // One write, holding one changed name.
    expect(storage.setItem.mock.calls.length).toBe(writesBefore + 1);
    const saved = storage.read();
    expect(saved.family).toEqual({
      ...RECORD.family,
      profiles: [RECORD.family.profiles[0], { ...RECORD.family.profiles[1], name: 'Ash' }],
    });
    expect(saved.gate).toEqual(RECORD.gate);
    // The screen reads the record it saved, and focus is back on Edit name.
    expect(screen.getByTestId('kid-mode-parent-profiles-profile-2-name').props.children).toBe('Ash');
    expect(screen.getByTestId('kid-mode-parent-rename-profile').props.hasTVPreferredFocus).toBe(true);
    // The record of what was hidden is keyed by id, so it is still Ash's.
    expect(readHideLogs()['profile-2'].entries).toHaveLength(1);
  });

  it('takes the route\'s storage screen when the write fails, and its retry carries the new name', async () => {
    const storage = memoryStorage(RECORD);
    open(storage);
    await typeAshForSam();
    storage.refuseNext(1);

    press('kid-mode-parent-name-save');
    // Nothing committed, and nothing on screen says it did.
    await screen.findByTestId('kid-mode-storage');
    expect(storage.read().family.profiles[1].name).toBe('Sam');
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();

    // Try again writes the pending record, which is the renamed household.
    press('kid-mode-storage-retry');
    await screen.findByTestId('kid-mode-parent');
    const saved = storage.read();
    expect(saved.family.profiles.map((one) => [one.id, one.name])).toEqual([
      ['profile-1', 'Robin'],
      ['profile-2', 'Ash'],
    ]);
    expect(saved.family.activeProfileId).toBe(RECORD.family.activeProfileId);
    // Parents is back the way every failed write brings it back: behind the PIN.
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
    expect(screen.getByTestId('kid-mode-parent-key-1')).toBeTruthy();
  });
});
