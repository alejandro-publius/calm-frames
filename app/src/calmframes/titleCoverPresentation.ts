/** Copy classification only; it cannot grant playback or remove a cover. */
import { bakedAmbientForRendition } from './approvedBakedAmbient';
import { CoverInterval } from './coverSchedule';
import { HouseholdSettings } from './household';
import { packagedLibrary } from './packagedLibrary';
import { CheckedTitle } from './titleStatus';

export function hasBakedOceanPresentation(entry: CheckedTitle, settings: HouseholdSettings,
  intervals: readonly CoverInterval[]): boolean {
  if (entry.status !== 'verified') return false;
  const title = entry.title;
  const evidence = packagedLibrary.evidenceFor(title, settings);
  const document = bakedAmbientForRendition(title.renditionSha256, settings.preset);
  return Boolean(evidence && document && document.ambientSha256 === 'ad315810e01b93be05da5ab59625212d98ceacb37bf43920513e824bf141020d' && document.sourceSha256 === title.sha256 &&
    document.durationMs === title.durationMs && document.renditionStartOffsetMs === title.renditionStartOffsetMs &&
    (['wcag', 'broadcast'] as const).every(p => evidence.maps.some(m =>
      m.preset === p && m.sha256 === document.mapSha256[p])) &&
    intervals.length === document.intervals.length && intervals.every((span, index) =>
      span.startMs === document.intervals[index].startMs && span.endMs === document.intervals[index].endMs));
}
