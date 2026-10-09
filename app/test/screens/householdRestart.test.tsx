import { act, fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import React from 'react';
import KidModeScreen from '../../src/screens/KidModeScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import {
  HouseholdStorage,
  HOUSEHOLD_STORAGE_KEY,
  SavedHousehold,
} from '../../src/calmframes/householdStorage';
import {
  attemptPin,
  emptyPinGate,
  LOCKOUT_MS,
  setPin,
} from '../../src/calmframes/parentGate';
import {
  addProfile,
  newFamily,
  selectProfile,
} from '../../src/calmframes/profiles';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { offlineTitle, OFFLINE_TITLE_ID } from '../../src/calmframes/offlineTitle';
import {
  readHideLogs,
  recordHide,
  resetHideLogs,
} from '../../src/calmframes/hideLogStore';

jest.mock('@react-native-async-storage/async-storage', () => ({}));

const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;
const RECORD: SavedHousehold = {
  version: 1,
  family: newFamily(),
  gate: setPin(emptyPinGate(), '1357', 'restart-test'),
};

function memoryStorage(initial: string | null = null) {
  let disk = initial;
  return {
    getItem: jest.fn(async () => disk),
    setItem: jest.fn(async (_key: string, text: string) => {
      disk = text;
    }),
    read: () => disk,
  };
}

function open(storage: HouseholdStorage) {
  const navigate = jest.fn();
  const rendered = render(
    <KidModeScreen
      navigation={{ navigate } as never}
      catalog={[offlineTitle('file:///pkg/assets/raw/offline/calm_gradient.mp4')]}
      householdStorage={storage}
      newSalt={() => 'restart-test'}
      nowMs={() => NOW}
    />,
  );
  return { ...rendered, navigate };
}

function type(prefix: string, pin: string) {
  for (const digit of pin) {
    fireEvent.press(screen.getByTestId(`${prefix}-key-${digit}`));
  }
}

async function setup() {
  await screen.findByTestId('kid-mode-first-run');
  type('kid-mode-first-run', '1357');
  type('kid-mode-first-run', '1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-done'));
}

describe('household setup across launches', () => {
  beforeEach(() => resetHideLogs());

  it('does not expose setup or a default shelf while stored settings are loading', async () => {
    let finish!: (text: string) => void;
    const storage = {
      getItem: () =>
        new Promise<string>((resolve) => {
          finish = resolve;
        }),
      setItem: jest.fn(),
    };
    const { navigate } = open(storage);
    expect(screen.queryByTestId('kid-mode-first-run')).toBeNull();
    expect(screen.getByTestId('kid-mode-storage')).toBeTruthy();
    expect(screen.queryByTestId('kid-mode-home')).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
    await act(async () => {
      finish(JSON.stringify(RECORD));
    });
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
  });

  it('saves setup before opening the shelf, then restores the PIN after remount', async () => {
    const storage = memoryStorage();
    const first = open(storage);
    await setup();
    await screen.findByTestId('kid-mode-home');
    expect(storage.setItem).toHaveBeenCalledWith(
      HOUSEHOLD_STORAGE_KEY,
      expect.any(String),
    );
    const written = JSON.parse(storage.read()!);
    expect(written.gate.record.hash).toHaveLength(128);
    expect(written.gate.record.pin).toBeUndefined();
    first.unmount();
    open(storage);
    await screen.findByTestId('kid-mode-home');
    expect(screen.queryByTestId('kid-mode-first-run')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
    type('kid-mode-parent', '1357');
    await screen.findByTestId('kid-mode-parent-open');
    expect(screen.getByTestId('kid-mode-parent-open')).toBeTruthy();
  });

  it('restores strict profiles and refuses the WCAG-only bundled title under Broadcast', async () => {
    const family = selectProfile(
      addProfile(
        newFamily(
          {
            ...DEFAULT_SETTINGS,
            preset: 'extra-cautious',
            tvDiagonalIn: 85,
            seatDistanceIn: 48,
          },
          'Robin',
        ),
        'Sam',
      ),
      'profile-2',
    );
    const { navigate } = open(
      memoryStorage(JSON.stringify({ ...RECORD, family })),
    );
    await screen.findByTestId('kid-mode-home');
    expect(
      screen.queryByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`),
    ).toBeNull();
    expect(screen.getByTestId('kid-mode-home-empty')).toBeTruthy();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('saves a stricter household floor and restores it on the next launch', async () => {
    const storage = memoryStorage(JSON.stringify(RECORD));
    const first = open(storage);
    await screen.findByTestId('kid-mode-home');
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    type('kid-mode-parent', '1357');
    await screen.findByTestId('kid-mode-parent-open');
    fireEvent.press(
      screen.getByTestId('kid-mode-parent-preset-extra-cautious'),
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(JSON.parse(storage.read()!).family.floor.preset).toBe(
      'extra-cautious',
    );
    first.unmount();
    open(storage);
    await screen.findByTestId('kid-mode-home');
    expect(
      screen.queryByTestId(`kid-mode-home-poster-${OFFLINE_TITLE_ID}`),
    ).toBeNull();
  });

  it('persists wrong attempts so restarting cannot reset the PIN lockout', async () => {
    const storage = memoryStorage(JSON.stringify(RECORD));
    for (let attempt = 0; attempt < 5; attempt += 1) {
      const app = open(storage);
      await screen.findByTestId('kid-mode-home');
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      type('kid-mode-parent', '0000');
      await act(async () => {
        await Promise.resolve();
      });
      app.unmount();
    }
    const stored = JSON.parse(storage.read()!);
    expect(stored.gate.lockedUntilMs).toBe(NOW + LOCKOUT_MS);
    open(storage);
    await screen.findByTestId('kid-mode-home');
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    type('kid-mode-parent', '1357');
    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
    expect(attemptPin(stored.gate, '1357', NOW).ok).toBe(false);
    expect(attemptPin(stored.gate, '1357', NOW + LOCKOUT_MS).ok).toBe(true);
  });

  it('keeps the library closed on read failure and retries without creating a new PIN', async () => {
    const storage = memoryStorage(JSON.stringify(RECORD));
    storage.getItem.mockRejectedValueOnce(new Error('unavailable'));
    const { navigate } = open(storage);
    await screen.findByTestId('kid-mode-storage-retry');
    expect(screen.queryByTestId('kid-mode-home')).toBeNull();
    expect(screen.queryByTestId('kid-mode-first-run')).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
    fireEvent.press(screen.getByTestId('kid-mode-storage-retry'));
    await screen.findByTestId('kid-mode-home');
    expect(storage.setItem).not.toHaveBeenCalled();
  });

  it('refuses corrupt stored settings on every retry without overwriting them', async () => {
    const storage = memoryStorage('{broken');
    open(storage);
    await screen.findByTestId('kid-mode-storage-retry');
    fireEvent.press(screen.getByTestId('kid-mode-storage-retry'));
    await screen.findByTestId('kid-mode-storage-retry');
    expect(screen.queryByTestId('kid-mode-first-run')).toBeNull();
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.read()).toBe('{broken');
  });

  it('retains failed setup for a save retry and never opens an unsaved library', async () => {
    const storage = memoryStorage();
    storage.setItem.mockRejectedValueOnce(new Error('full'));
    open(storage);
    await setup();
    await screen.findByTestId('kid-mode-storage-retry');
    expect(screen.queryByTestId('kid-mode-home')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-mode-storage-retry'));
    await screen.findByTestId('kid-mode-home');
    expect(storage.getItem).toHaveBeenCalledTimes(1);
    expect(storage.setItem).toHaveBeenCalledTimes(2);
    expect(JSON.parse(storage.read()!).gate.record).toEqual(RECORD.gate.record);
  });

  it('does not unlock the parent area before its PIN state is saved', async () => {
    let finish!: () => void;
    const storage = memoryStorage(JSON.stringify(RECORD));
    storage.setItem.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    open(storage);
    await screen.findByTestId('kid-mode-home');
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    type('kid-mode-parent', '1357');
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
    expect(
      screen.getByTestId('kid-mode-parent-key-1').props.accessibilityState
        .disabled,
    ).toBe(true);
    await act(async () => {
      finish();
    });
    expect(screen.getByTestId('kid-mode-parent-open')).toBeTruthy();
  });

  it('keeps the parent area locked when a correct PIN cannot be saved', async () => {
    const storage = memoryStorage(JSON.stringify(RECORD));
    storage.setItem.mockRejectedValueOnce(new Error('unavailable'));
    open(storage);
    await screen.findByTestId('kid-mode-home');
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    type('kid-mode-parent', '1357');
    await screen.findByTestId('kid-mode-storage-retry');
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
    expect(screen.queryByTestId('kid-mode-home')).toBeNull();
  });

  it('retries the intended strict floor instead of reading the older Standard setting', async () => {
    const storage = memoryStorage(JSON.stringify(RECORD));
    open(storage);
    await screen.findByTestId('kid-mode-home');
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    type('kid-mode-parent', '1357');
    await screen.findByTestId('kid-mode-parent-open');
    storage.setItem.mockRejectedValueOnce(new Error('full'));
    fireEvent.press(
      screen.getByTestId('kid-mode-parent-preset-extra-cautious'),
    );
    await screen.findByTestId('kid-mode-storage-retry');
    expect(JSON.parse(storage.read()!).family.floor.preset).toBe('wcag');
    expect(screen.queryByTestId('kid-mode-home')).toBeNull();
    fireEvent.press(screen.getByTestId('kid-mode-storage-retry'));
    await screen.findByTestId('kid-mode-parent');
    expect(JSON.parse(storage.read()!).family.floor.preset).toBe(
      'extra-cautious',
    );
    expect(storage.getItem).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('kid-mode-parent-open')).toBeNull();
  });

  it('disables setting changes during a write and does not race two floors', async () => {
    const storage = memoryStorage(JSON.stringify(RECORD));
    open(storage);
    await screen.findByTestId('kid-mode-home');
    fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
    type('kid-mode-parent', '1357');
    await screen.findByTestId('kid-mode-parent-open');
    let finish!: () => void;
    const originalWrite = storage.setItem.getMockImplementation()!;
    storage.setItem.mockImplementationOnce(
      (_key, text) =>
        new Promise<void>((resolve) => {
          finish = () => {
            originalWrite(_key, text).then(resolve);
          };
          expect(JSON.parse(text).family.floor.preset).toBe('extra-cautious');
        }),
    );
    fireEvent.press(
      screen.getByTestId('kid-mode-parent-preset-extra-cautious'),
    );
    expect(screen.getByTestId('kid-mode-parent-saving')).toBeTruthy();
    expect(
      screen.getByTestId('kid-mode-parent-preset-wcag').props.accessibilityState
        .disabled,
    ).toBe(true);
    fireEvent.press(screen.getByTestId('kid-mode-parent-preset-wcag'));
    expect(storage.setItem).toHaveBeenCalledTimes(2);
    await act(async () => {
      finish();
    });
    expect(screen.queryByTestId('kid-mode-parent-saving')).toBeNull();
    expect(JSON.parse(storage.read()!).family.floor.preset).toBe(
      'extra-cautious',
    );
  });

  it('ignores a stale read failure after a different storage source has loaded', async () => {
    let reject!: (reason: Error) => void;
    const stale = {
      getItem: () =>
        new Promise<string>((_resolve, fail) => {
          reject = fail;
        }),
      setItem: jest.fn(),
    };
    const app = open(stale);
    const current = memoryStorage(JSON.stringify(RECORD));
    app.rerender(
      <KidModeScreen
        navigation={{ navigate: jest.fn() } as never}
        householdStorage={current}
        nowMs={() => NOW}
      />,
    );
    await screen.findByTestId('kid-mode-home');
    await act(async () => {
      reject(new Error('stale failure'));
    });
    expect(screen.queryByTestId('kid-mode-storage-retry')).toBeNull();
    expect(screen.getByTestId('kid-mode-home')).toBeTruthy();
  });

  it.each(['delayed', 'failed'] as const)(
    'retains a removed profile history until its %s write commits, including retry',
    async (outcome) => {
      const family = addProfile(newFamily(), 'Sam');
      const storage = memoryStorage(JSON.stringify({ ...RECORD, family }));
      for (const profile of family.profiles) {
        recordHide(
          {
            atMs: NOW,
            titleId: 'story',
            titleName: 'Story',
            positionMs: 1000,
            durationMs: 2000,
            cause: 'schedule',
          },
          { profileId: profile.id, profileName: profile.name },
        );
      }
      open(storage);
      await screen.findByTestId('kid-mode-home');
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      type('kid-mode-parent', '1357');
      await screen.findByTestId('kid-mode-parent-open');
      fireEvent.press(screen.getByTestId('kid-mode-parent-profiles-profile-2'));
      fireEvent.press(screen.getByTestId('kid-mode-parent-remove-profile'));
      let finish!: () => void;
      const originalWrite = storage.setItem.getMockImplementation()!;
      storage.setItem.mockImplementationOnce(
        (key, text) => new Promise<void>((resolve, reject) => {
          finish = () => {
            if (outcome === 'failed') {
              reject(new Error('storage unavailable'));
            } else {
              originalWrite(key, text).then(resolve);
            }
          };
        }),
      );
      fireEvent.press(screen.getByTestId('kid-mode-parent-remove-confirm'));
      expect(readHideLogs()['profile-2']?.entries.length ?? 0).toBe(1);
      expect(JSON.parse(storage.read()!).family.profiles).toHaveLength(2);
      await act(async () => finish());
      if (outcome === 'failed') {
        await screen.findByTestId('kid-mode-storage-retry');
        expect(readHideLogs()['profile-2']?.entries.length ?? 0).toBe(1);
        expect(JSON.parse(storage.read()!).family.profiles).toHaveLength(2);
        fireEvent.press(screen.getByTestId('kid-mode-storage-retry'));
        await screen.findByTestId('kid-mode-parent');
      }
      await waitFor(() => expect(readHideLogs()['profile-2']).toBeUndefined());
      expect(JSON.parse(storage.read()!).family.profiles).toHaveLength(1);
      expect(readHideLogs()['profile-1'].entries).toHaveLength(1);
    },
  );
});
