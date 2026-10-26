/** Exact packaged editions only. No route-supplied signer or new trust API. */
import { buildCoverIntervals, CoverInterval } from '../coverSchedule';
import { coverOptionsFor, HouseholdSettings } from '../household';
import { packagedLibrary } from '../packagedLibrary';
import { CatalogTitle, checkTitle } from '../titleStatus';

export interface PlaybackIdentity {
  readonly uri: string;
  readonly sourceSha256: string;
  readonly assetSha256: string;
  readonly editionId: string;
  readonly timelineId: string;
}
// Opaque at runtime as well as at the TypeScript boundary.
export interface VerifiedCoverage {
  readonly identity: Readonly<PlaybackIdentity>;
}
interface VerifiedData {
  durationMs: number;
  intervals: CoverInterval[];
  validAt: (nowMs: number) => boolean;
}
const verified = new WeakMap<VerifiedCoverage, VerifiedData>();
export function coverageData(
  token: VerifiedCoverage,
): VerifiedData | undefined {
  return verified.get(token);
}

export function verifyPackagedCoverage(
  input: CatalogTitle,
  inputSettings: HouseholdSettings,
  nowMs: number,
): VerifiedCoverage | null {
  if (!Number.isFinite(nowMs)) return null;
  // Detach mutable caller objects before validation; signed text remains exact.
  const title: CatalogTitle = JSON.parse(JSON.stringify(input));
  const settings: HouseholdSettings = { ...inputSettings };
  const publicKeyBase64 = packagedLibrary.publicKeyFor(title, settings);
  const evidence = packagedLibrary.evidenceFor(title, settings);
  if (
    !publicKeyBase64 ||
    !evidence ||
    !title.renditionSha256 ||
    !title.durationMs
  )
    return null;
  const validAt = (time: number) =>
    Number.isFinite(time) &&
    time >= nowMs &&
    checkTitle(title, { settings, publicKeyBase64, nowMs: time }).status ===
      'verified';
  if (!validAt(nowMs)) return null;
  try {
    const checked = checkTitle(title, { settings, publicKeyBase64, nowMs });
    const intervals = buildCoverIntervals(checked.segments, {
      ...coverOptionsFor(settings),
      durationMs: title.durationMs,
      renditionStartOffsetMs: title.renditionStartOffsetMs,
    });
    const identity = Object.freeze({
      uri: title.uri,
      sourceSha256: title.sha256,
      assetSha256: title.renditionSha256,
      editionId: evidence.bundleId,
      timelineId: `${evidence.bundleId}:${settings.preset}:${title.renditionStartOffsetMs}`,
    });
    const token = Object.freeze({ identity });
    intervals.forEach((interval) => {
      interval.sources.forEach(Object.freeze);
      Object.freeze(interval.sources);
      Object.freeze(interval);
    });
    Object.freeze(intervals);
    verified.set(
      token,
      Object.freeze({ durationMs: title.durationMs, intervals, validAt }),
    );
    return token;
  } catch {
    return null;
  }
}
