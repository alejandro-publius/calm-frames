/** Read-only continuity for the exact Acadia replacement; no storage migration. */
import { PACKAGED_LIBRARY_JSON } from './acadiaCatalog';
import { BakedAmbientDocument } from './bakedAmbient';
import { HouseholdSettings } from './household';
import { ACADIA_SOURCE_SHA256, createApprovedAcadiaLibrary } from './packagedLibrary';
import { PersonalCoverAsset, personalCoverAsset, validatePersonalRecord } from './personalCovers';
import type { PersonalCoverLoad } from './personalCoverStorage';

const predecessor = createApprovedAcadiaLibrary(PACKAGED_LIBRARY_JSON);
export type CoverPredecessor = { status: 'none' | 'blocked'; asset?: undefined } |
  { status: 'required'; asset: PersonalCoverAsset };

/** Caller supplies only the compiled approved ambient document, never route metadata. */
export function ambientCoverPredecessor(document: BakedAmbientDocument | null,
  current: PersonalCoverAsset | undefined, settings: HouseholdSettings | undefined): CoverPredecessor {
  if (!document || document.sourceSha256 !== ACADIA_SOURCE_SHA256) return { status: 'none' };
  if (!current || !settings || document.sourceSha256 !== current.sourceSha256 ||
      document.renditionSha256 !== current.renditionSha256 || document.durationMs !== current.durationMs ||
      document.renditionStartOffsetMs !== current.renditionStartOffsetMs || document.preset !== settings.preset ||
      !document.frameTimingPreserved) return { status: 'blocked' };
  const title = predecessor.titles(settings).find(item => item.id === current.titleId);
  const asset = title && personalCoverAsset(title);
  const evidence = title && predecessor.evidenceFor(title, settings);
  if (!asset || !evidence || asset.sourceSha256 !== current.sourceSha256 ||
      asset.durationMs !== current.durationMs || asset.renditionStartOffsetMs !== current.renditionStartOffsetMs ||
      asset.renditionSha256 === current.renditionSha256 ||
      !(['wcag', 'broadcast'] as const).every(p => evidence.maps.some(m =>
        m.preset === p && m.sha256 === document.mapSha256[p]))) return { status: 'blocked' };
  return { status: 'required', asset };
}

/** Both reads must succeed. Invalid or excessive combined additions block playback. */
export function combineAmbientCovers(current: PersonalCoverLoad, previous: PersonalCoverLoad,
  selection: CoverPredecessor): PersonalCoverLoad {
  if (selection.status === 'none') return current;
  if (selection.status !== 'required' || current.status === 'blocked' || previous.status === 'blocked') {
    return { status: 'blocked' };
  }
  if (current.status !== 'ready' || previous.status !== 'ready') return { status: 'loading' };
  try {
    const old = validatePersonalRecord(previous.record, selection.asset);
    return { status: 'ready', record: validatePersonalRecord({ ...current.record,
      additions: [...current.record.additions, ...old.additions] }, current.record.asset) };
  } catch { return { status: 'blocked' }; }
}
