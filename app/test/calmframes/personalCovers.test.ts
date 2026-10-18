import { buildCoverIntervals, isCovered } from '../../src/calmframes/coverSchedule';
import { personalCoverAsset, personalAssetKey, PersonalCoverAsset, validatePersonalCovers, withPersonalCovers } from '../../src/calmframes/personalCovers';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { loadPersonalCovers, savePersonalCovers } from '../../src/calmframes/personalCoverStorage';
jest.mock('@react-native-async-storage/async-storage', () => ({}));
const asset: PersonalCoverAsset = { titleId: 'prepared', sourceSha256: 'a'.repeat(64),
  renditionSha256: 'b'.repeat(64), durationMs: 10000, renditionStartOffsetMs: 0 };

it('unions overlaps without changing any base sample, reason or source', () => {
  const base = buildCoverIntervals([{ startMs: 2000, endMs: 4000, reason: 'red' }]);
  const before = JSON.stringify(base);
  const combined = withPersonalCovers(base, [{ startMs: 1000, endMs: 2500 }, { startMs: 4500, endMs: 6000 }], 10000);
  expect(combined).toHaveLength(1);
  expect(combined[0]).toMatchObject({ startMs: 500, endMs: 6500, reason: 'red' });
  for (let ms = 0; ms <= 10000; ms += 10) {
    if (isCovered(base, ms)) expect(isCovered(combined, ms)).toBe(true);
  }
  expect(JSON.stringify(base)).toBe(before);
  expect(withPersonalCovers(base, [], 10000)).toEqual(base);
});

it.each<unknown[]>([
  [{ startMs: -1, endMs: 10 }], [{ startMs: 10, endMs: 10 }],
  [{ startMs: 20, endMs: 10 }], [{ startMs: 0, endMs: 10001 }],
  [{ startMs: 0.1, endMs: 10 }], [{ startMs: NaN, endMs: 10 }],
  [{ startMs: 0, endMs: Infinity }], [{ startMs: '0', endMs: 10 }],
  Array.from({ length: 33 }, () => ({ startMs: 0, endMs: 10 })),
])('refuses invalid or unbounded additions %#', (value) => {
  expect(() => validatePersonalCovers(value, 10000)).toThrow();
});

it('persists exact-asset additions and never reuses them for another rendition', async () => {
  const values = new Map<string, string>();
  const storage = { getItem: jest.fn(async (key: string) => values.get(key) ?? null),
    setItem: jest.fn(async (key: string, value: string) => { values.set(key, value); }) };
  const original = { version: 1 as const, asset, additions: [{ startMs: 0, endMs: 1000 }] };
  await savePersonalCovers(original, storage);
  expect(await loadPersonalCovers(asset, storage)).toEqual(original);
  const next = { ...asset, renditionSha256: 'c'.repeat(64) };
  expect(personalAssetKey(asset)).not.toEqual(personalAssetKey(next));
  expect((await loadPersonalCovers(next, storage)).additions).toEqual([]);
  await savePersonalCovers({ ...original, additions: [] }, storage);
  expect((await loadPersonalCovers(asset, storage)).additions).toEqual([]);
});

it('fails closed for corrupt, mismatched, oversized or unreadable saved records', async () => {
  for (const text of ['{', 'x'.repeat(8193), JSON.stringify({ version: 1, asset: { ...asset, durationMs: 2 }, additions: [] }),
    JSON.stringify({ version: 1, asset, additions: [{ startMs: 0, endMs: 10001 }] })]) {
    await expect(loadPersonalCovers(asset, { getItem: async () => text, setItem: async () => {} })).rejects.toThrow();
  }
  await expect(loadPersonalCovers(asset, { getItem: async () => { throw new Error('read'); }, setItem: async () => {} })).rejects.toThrow();
});

it('accepts the actual approved Acadia identity with its fractional duration', () => {
  const title = packagedLibrary.consumerTitles(DEFAULT_SETTINGS)[0];
  const exact = personalCoverAsset(title);
  expect(exact).toBeDefined();
  expect(exact!.durationMs).toBe(title.durationMs);
  expect(() => withPersonalCovers([], [{ startMs: 0, endMs: 1000 }], exact!.durationMs)).not.toThrow();
});

it('rejects duplicate storage keys instead of silently dropping saved additions', async () => {
  const original = JSON.stringify({ version: 1, asset, additions: [{ startMs: 100, endMs: 900 }] });
  const ambiguous = original.slice(0, -1) + ',"additions":[]}';
  const storage = { getItem: async () => ambiguous, setItem: jest.fn() };
  await expect(loadPersonalCovers(asset, storage)).rejects.toThrow();
  expect(storage.setItem).not.toHaveBeenCalled();
});
