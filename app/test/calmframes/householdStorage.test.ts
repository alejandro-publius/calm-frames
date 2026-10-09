import {
  HOUSEHOLD_STORAGE_KEY,
  loadHousehold,
  MAX_HOUSEHOLD_BYTES,
  saveHousehold,
  SavedHousehold,
  validateHousehold,
} from '../../src/calmframes/householdStorage';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import {
  emptyPinGate,
  MAX_ATTEMPTS,
  PIN_ROUNDS,
  setPin,
} from '../../src/calmframes/parentGate';
import {
  addProfile,
  effectiveSettings,
  newFamily,
  selectProfile,
} from '../../src/calmframes/profiles';

jest.mock('@react-native-async-storage/async-storage', () => ({}));

const RECORD: SavedHousehold = {
  version: 1,
  family: selectProfile(
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
  ),
  gate: {
    record: { salt: 'local-salt', hash: 'a'.repeat(128), rounds: PIN_ROUNDS },
    failedAttempts: 0,
    lockedUntilMs: 123456789,
  },
};

describe('local household record', () => {
  it('restores the exact strict floor, selected child, chime and PIN lockout', async () => {
    let disk: string | null = null;
    const storage = {
      getItem: jest.fn(async () => disk),
      setItem: jest.fn(async (_key: string, text: string) => {
        disk = text;
      }),
    };
    await saveHousehold(storage, RECORD);
    const restored = await loadHousehold(storage);
    expect(restored).toEqual(RECORD);
    expect(storage.setItem).toHaveBeenCalledWith(
      HOUSEHOLD_STORAGE_KEY,
      expect.any(String),
    );
    expect(
      effectiveSettings(restored!.family, restored!.family.profiles[1]).preset,
    ).toBe('extra-cautious');
  });

  it('only a missing key starts first run; unreadable storage rejects', async () => {
    expect(
      await loadHousehold({ getItem: async () => null, setItem: jest.fn() }),
    ).toBeNull();
    await expect(
      loadHousehold({
        getItem: async () => {
          throw new Error('unavailable');
        },
        setItem: jest.fn(),
      }),
    ).rejects.toThrow('unavailable');
  });

  it.each([
    ['bad JSON', '{'],
    ['empty record', '{}'],
    ['JSON null', 'null'],
    ['oversized', ' '.repeat(MAX_HOUSEHOLD_BYTES + 1)],
    ['future version', JSON.stringify({ ...RECORD, version: 2 })],
  ])('refuses %s without defaulting the household', async (_name, text) => {
    await expect(
      loadHousehold({ getItem: async () => text, setItem: jest.fn() }),
    ).rejects.toThrow();
  });

  it.each([
    [
      'unknown preset',
      (row: any) => {
        row.family.floor.preset = 'loose';
      },
    ],
    [
      'missing room',
      (row: any) => {
        delete row.family.floor.seatDistanceIn;
      },
    ],
    [
      'string distance',
      (row: any) => {
        row.family.floor.seatDistanceIn = '96';
      },
    ],
    [
      'zero distance',
      (row: any) => {
        row.family.floor.seatDistanceIn = 0;
      },
    ],
    [
      'missing profile settings',
      (row: any) => {
        row.family.profiles[0].settings = null;
      },
    ],
    [
      'duplicate id',
      (row: any) => {
        row.family.profiles[1].id = row.family.profiles[0].id;
      },
    ],
    [
      'unknown selected child',
      (row: any) => {
        row.family.activeProfileId = 'profile-9';
      },
    ],
    [
      'missing children',
      (row: any) => {
        row.family.profiles = [];
      },
    ],
    [
      'too many children',
      (row: any) => {
        row.family.profiles = Array(5).fill(row.family.profiles[0]);
      },
    ],
    [
      'missing PIN',
      (row: any) => {
        row.gate.record = null;
      },
    ],
    [
      'bad hash',
      (row: any) => {
        row.gate.record.hash = '1357';
      },
    ],
    [
      'unbounded hashing',
      (row: any) => {
        row.gate.record.rounds = 1e12;
      },
    ],
    [
      'negative attempts',
      (row: any) => {
        row.gate.failedAttempts = -1;
      },
    ],
    [
      'excess attempts',
      (row: any) => {
        row.gate.failedAttempts = MAX_ATTEMPTS;
      },
    ],
    [
      'invalid lockout',
      (row: any) => {
        row.gate.lockedUntilMs = 'tomorrow';
      },
    ],
    [
      'missing chime',
      (row: any) => {
        delete row.family.chimeEnabled;
      },
    ],
  ])('refuses %s', (_name, change) => {
    const row = JSON.parse(JSON.stringify(RECORD));
    change(row);
    expect(() => validateHousehold(row)).toThrow();
  });

  it('writes only known fields, never plaintext PIN or unlocked state', async () => {
    const setItem = jest.fn(async (_key: string, _text: string) => undefined);
    const gate = setPin(emptyPinGate(), '1357', 'seed');
    await saveHousehold(
      { getItem: jest.fn(), setItem },
      {
        ...RECORD,
        gate: { ...gate, pin: '1357', unlocked: true } as never,
      },
    );
    const written = JSON.parse(setItem.mock.calls[0][1]);
    expect(written.gate).toEqual(gate);
    expect(written.gate.pin).toBeUndefined();
    expect(written.gate.unlocked).toBeUndefined();
  });

  it('propagates failed writes instead of claiming they were saved', async () => {
    await expect(
      saveHousehold(
        {
          getItem: jest.fn(),
          setItem: async () => {
            throw new Error('full');
          },
        },
        RECORD,
      ),
    ).rejects.toThrow('full');
  });
});
