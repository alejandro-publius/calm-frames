/** Local setup is one versioned record. Invalid records never become defaults. */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { HouseholdSettings, PRESET_NAMES } from './household';
import { MAX_ATTEMPTS, PIN_ROUNDS, PinGateState } from './parentGate';
import { Family, MAX_PROFILES, MAX_PROFILE_NAME } from './profiles';

export const HOUSEHOLD_STORAGE_KEY = 'calm-frames.household.v1';
export const MAX_HOUSEHOLD_BYTES = 16 * 1024;

export interface SavedHousehold {
  version: 1;
  family: Family;
  gate: PinGateState;
}

export interface HouseholdStorage {
  getItem: (key: string) => Promise<string | null>;
  setItem: (key: string, value: string) => Promise<void>;
}

export const deviceHouseholdStorage: HouseholdStorage = AsyncStorage;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Invalid household record');
  }
  return value as Record<string, unknown>;
}

function settings(value: unknown): HouseholdSettings {
  const row = object(value);
  if (
    !PRESET_NAMES.includes(row.preset as HouseholdSettings['preset']) ||
    typeof row.tvDiagonalIn !== 'number' ||
    !Number.isFinite(row.tvDiagonalIn) ||
    row.tvDiagonalIn <= 0 ||
    typeof row.seatDistanceIn !== 'number' ||
    !Number.isFinite(row.seatDistanceIn) ||
    row.seatDistanceIn <= 0
  ) {
    throw new Error('Invalid household settings');
  }
  return {
    preset: row.preset as HouseholdSettings['preset'],
    tvDiagonalIn: row.tvDiagonalIn,
    seatDistanceIn: row.seatDistanceIn,
  };
}

/** Reconstruct known fields only; never persist plaintext digits or an unlock. */
export function validateHousehold(value: unknown): SavedHousehold {
  const row = object(value);
  const family = object(row.family);
  const gate = object(row.gate);
  const record = object(gate.record);
  if (
    row.version !== 1 ||
    !Array.isArray(family.profiles) ||
    family.profiles.length < 1 ||
    family.profiles.length > MAX_PROFILES ||
    typeof family.chimeEnabled !== 'boolean' ||
    (family.interfaceMotionEnabled !== undefined && typeof family.interfaceMotionEnabled !== 'boolean') ||
    (family.interfaceSoundsEnabled !== undefined && typeof family.interfaceSoundsEnabled !== 'boolean') ||
    typeof record.salt !== 'string' ||
    record.salt.length < 1 ||
    record.salt.length > 128 ||
    typeof record.hash !== 'string' ||
    !/^[a-f0-9]{128}$/.test(record.hash) ||
    record.rounds !== PIN_ROUNDS ||
    !Number.isInteger(gate.failedAttempts) ||
    (gate.failedAttempts as number) < 0 ||
    (gate.failedAttempts as number) >= MAX_ATTEMPTS ||
    !(
      gate.lockedUntilMs === null ||
      (Number.isSafeInteger(gate.lockedUntilMs) &&
        (gate.lockedUntilMs as number) > 0)
    )
  ) {
    throw new Error('Invalid household or PIN record');
  }
  const profiles = family.profiles.map((item) => {
    const profile = object(item);
    if (
      typeof profile.id !== 'string' ||
      !/^profile-[1-9][0-9]{0,8}$/.test(profile.id) ||
      typeof profile.name !== 'string' ||
      profile.name.trim().length === 0 ||
      profile.name.length > MAX_PROFILE_NAME ||
      (profile.readingComfortEnabled !== undefined && typeof profile.readingComfortEnabled !== 'boolean')
    ) {
      throw new Error('Invalid household profile');
    }
    return {
      id: profile.id,
      name: profile.name,
      settings: settings(profile.settings),
      readingComfortEnabled: profile.readingComfortEnabled === true,
    };
  });
  if (
    new Set(profiles.map((profile) => profile.id)).size !== profiles.length ||
    !profiles.some((profile) => profile.id === family.activeProfileId)
  ) {
    throw new Error('Invalid active household profile');
  }
  return {
    version: 1,
    family: {
      floor: settings(family.floor),
      profiles,
      activeProfileId: family.activeProfileId as string,
      chimeEnabled: family.chimeEnabled,
      interfaceMotionEnabled: family.interfaceMotionEnabled === true,
      interfaceSoundsEnabled: family.interfaceSoundsEnabled === true,
    },
    gate: {
      record: { salt: record.salt, hash: record.hash, rounds: PIN_ROUNDS },
      failedAttempts: gate.failedAttempts as number,
      lockedUntilMs: gate.lockedUntilMs as number | null,
    },
  };
}

export async function loadHousehold(
  storage: HouseholdStorage,
): Promise<SavedHousehold | null> {
  const text = await storage.getItem(HOUSEHOLD_STORAGE_KEY);
  if (text === null) {
    return null;
  }
  if (text.length > MAX_HOUSEHOLD_BYTES) {
    throw new Error('Household record exceeds its bound');
  }
  return validateHousehold(JSON.parse(text));
}

export async function saveHousehold(
  storage: HouseholdStorage,
  value: SavedHousehold,
): Promise<void> {
  const text = JSON.stringify(validateHousehold(value));
  if (text.length > MAX_HOUSEHOLD_BYTES) {
    throw new Error('Household record exceeds its bound');
  }
  await storage.setItem(HOUSEHOLD_STORAGE_KEY, text);
}
