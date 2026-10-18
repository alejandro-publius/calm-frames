import { useEffect, useState } from 'react';
import { deviceHouseholdStorage, HouseholdStorage } from './householdStorage';
import {
  PersonalCoverAsset, PersonalCoverRecord, personalAssetKey, validatePersonalRecord,
} from './personalCovers';

const PREFIX = 'calm-frames.extra-covers.v1:';
export async function loadPersonalCovers(
  asset: PersonalCoverAsset, storage: HouseholdStorage = deviceHouseholdStorage,
): Promise<PersonalCoverRecord> {
  const text = await storage.getItem(PREFIX + personalAssetKey(asset));
  if (text === null) return { version: 1, asset, additions: [] };
  if (text.length > 8192) throw new Error('Extra covers record is too large.');
  return validatePersonalRecord(JSON.parse(text), asset);
}
export async function savePersonalCovers(
  value: PersonalCoverRecord, storage: HouseholdStorage = deviceHouseholdStorage,
): Promise<void> {
  const checked = validatePersonalRecord(value, value.asset);
  await storage.setItem(PREFIX + personalAssetKey(checked.asset), JSON.stringify(checked));
}
export type PersonalCoverLoad =
  | { status: 'loading' | 'blocked'; record?: undefined }
  | { status: 'ready'; record: PersonalCoverRecord };
export function usePersonalCovers(asset: PersonalCoverAsset | undefined): PersonalCoverLoad {
  const key = asset ? personalAssetKey(asset) : '';
  const [loaded, setLoaded] = useState<{ key: string; value: PersonalCoverLoad }>();
  useEffect(() => {
    let active = true;
    if (asset) {
      loadPersonalCovers(asset).then((record) => {
        if (active) setLoaded({ key, value: { status: 'ready', record } });
      }).catch(() => {
        if (active) setLoaded({ key, value: { status: 'blocked' } });
      });
    }
    return () => { active = false; };
    // Identity primitives, not caller object allocation, govern loading.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return loaded?.key === key ? loaded.value : { status: 'loading' };
}
