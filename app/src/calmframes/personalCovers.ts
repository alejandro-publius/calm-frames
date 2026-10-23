/** Local additions use prepared-media time. They never edit verified maps. */
import { buildCoverIntervals, CoverInterval } from './coverSchedule';

export interface PersonalCoverAsset {
  titleId: string;
  sourceSha256: string;
  renditionSha256: string;
  durationMs: number;
  renditionStartOffsetMs: number;
}
export interface PersonalCover { startMs: number; endMs: number }
export interface PersonalCoverRecord {
  version: 1;
  asset: PersonalCoverAsset;
  additions: PersonalCover[];
}
export const MAX_PERSONAL_COVERS = 32;
const HASH = /^[a-f0-9]{64}$/;

export function personalCoverAsset(value: {
  id?: string; sha256?: string; renditionSha256?: string;
  durationMs?: number; renditionStartOffsetMs?: number;
}): PersonalCoverAsset | undefined {
  if (!value.id || value.id.length > 200 || !HASH.test(value.sha256 ?? '') ||
      !HASH.test(value.renditionSha256 ?? '') ||
      !Number.isFinite(value.durationMs) || (value.durationMs ?? 0) <= 0 ||
      !Number.isFinite(value.renditionStartOffsetMs ?? 0) ||
      Math.abs(value.renditionStartOffsetMs ?? 0) > 150) return undefined;
  return {
    titleId: value.id, sourceSha256: value.sha256!,
    renditionSha256: value.renditionSha256!, durationMs: value.durationMs!,
    renditionStartOffsetMs: value.renditionStartOffsetMs ?? 0,
  };
}

export function personalAssetKey(asset: PersonalCoverAsset): string {
  const validated = personalCoverAsset({ id: asset.titleId, sha256: asset.sourceSha256,
    renditionSha256: asset.renditionSha256, durationMs: asset.durationMs,
    renditionStartOffsetMs: asset.renditionStartOffsetMs });
  if (!validated) throw new Error('Invalid prepared video identity');
  return JSON.stringify(validated);
}

export function validatePersonalCovers(value: unknown, durationMs: number): PersonalCover[] {
  if (!Number.isFinite(durationMs) || durationMs <= 0 || !Array.isArray(value) ||
      value.length > MAX_PERSONAL_COVERS) throw new Error('Invalid extra covers');
  return value.map((entry) => {
    if (!entry || typeof entry !== 'object' ||
        !Number.isSafeInteger(entry.startMs) || !Number.isSafeInteger(entry.endMs) ||
        entry.startMs < 0 || entry.endMs <= entry.startMs || entry.endMs > durationMs) {
      throw new Error('Choose a start before the end, within this video.');
    }
    return { startMs: entry.startMs, endMs: entry.endMs };
  });
}

export function validatePersonalRecord(value: unknown, asset: PersonalCoverAsset): PersonalCoverRecord {
  const record = value as PersonalCoverRecord | null;
  if (!record || record.version !== 1 || !record.asset ||
      personalAssetKey(record.asset) !== personalAssetKey(asset)) {
    throw new Error('Extra covers belong to a different prepared video.');
  }
  return { version: 1, asset, additions: validatePersonalCovers(record.additions, asset.durationMs) };
}

/** Copy and union; never mutate, re-pad or shorten the verified base. */
export function withPersonalCovers(
  base: CoverInterval[], additions: PersonalCover[], durationMs: number,
): CoverInterval[] {
  const extra = buildCoverIntervals(validatePersonalCovers(additions, durationMs).map((entry) => ({ ...entry, label: 'Personal extra cover' })), { durationMs });
  const merged: CoverInterval[] = [];
  for (const interval of [...base, ...extra].sort((a, b) => a.startMs - b.startMs)) {
    const previous = merged[merged.length - 1];
    if (previous && interval.startMs <= previous.endMs) {
      previous.endMs = Math.max(previous.endMs, interval.endMs);
      if (interval.reason === 'red' || interval.reason === 'pattern' && previous.reason !== 'red') {
        previous.reason = interval.reason;
      }
      previous.sources.push(...interval.sources);
    } else merged.push({ ...interval, sources: [...interval.sources] });
  }
  return merged;
}
