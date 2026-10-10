/**
 * Which titles kid mode is allowed to show, and why.
 *
 * docs/BUILD_PROMPT.md 4.3: "Kid mode never lists unverified titles." So the
 * listing is not a filter applied at the end, it is the only way a title
 * reaches the grid: `kidModeTitles` takes checked titles and returns the
 * verified ones, and the parent area is the only place the others appear, with
 * the reason next to them.
 *
 * Three statuses:
 *
 *   verified  every map the preset asks for verified, and the household's room
 *             is no stricter than the analysis
 *   pending   nothing is wrong, the check has not finished, or the room is
 *             stricter than what was measured so the title needs analysing
 *             again for this household
 *   failed    a map was there and it did not verify
 */

import {
  HouseholdSettings,
  mapCoversRoom,
  PRESETS,
  unionSegments,
} from './household';
import { FlashSegment } from './coverSchedule';
import {
  MapRejection,
  rejectionMessage,
  VerifiedFlashMap,
  verifyFlashMap,
  VerifyMapOptions,
} from './flashMap';

export type TitleStatus = 'verified' | 'pending' | 'failed';

export interface CatalogTitle {
  id: string;
  title: string;
  uri: string;
  posterUrl?: string;
  /** SHA-256 of the analyzed source. Prepared renditions retain its map. */
  sha256: string;
  /** Exact prepared file, separately checked when the package is built. */
  renditionSha256?: string;
  /** Verified alignment of prepared media time with its analyzed source. */
  renditionStartOffsetMs?: number;
  /** Captions delivered separately from the prepared picture. */
  textTrack?: Array<{
    label: string;
    language: string;
    uri: string;
    mimeType: 'text/vtt';
  }>;
  /** Map text per profile name, as it was written. Missing is not an error. */
  maps?: Partial<Record<string, string | null>>;
  durationMs?: number;
  /** True when this title's BIF previews come from the safe rendition. */
  bifFromSafeRendition?: boolean;
}

export interface CheckedTitle {
  title: CatalogTitle;
  status: TitleStatus;
  /** Why it is not verified. Absent when it is. */
  rejection?: MapRejection;
  /** Plain wording for the parent area and the card. */
  reason?: string;
  segments: FlashSegment[];
  /** Milliseconds the maps say are flagged, before guard bands. */
  hiddenMs: number;
  checkedAtMs?: number;
  /** The profile names that verified. */
  verifiedProfiles: string[];
}

export interface CheckTitleOptions
  extends Omit<VerifyMapOptions, 'expectedSha256'> {
  settings: HouseholdSettings;
}

/**
 * Check one title against the household setting.
 *
 * Every profile the preset names has to verify. A missing map for a profile
 * the preset asks for is pending, not verified: silence is not a pass.
 */
export function checkTitle(
  title: CatalogTitle,
  options: CheckTitleOptions,
): CheckedTitle {
  const preset = PRESETS[options.settings.preset] ?? PRESETS.wcag;
  const verified: VerifiedFlashMap[] = [];
  const verifiedProfiles: string[] = [];

  for (const profile of preset.mapProfiles) {
    const text = title.maps?.[profile];
    const verdict = verifyFlashMap(text, {
      publicKeyBase64: options.publicKeyBase64,
      expectedSha256: title.sha256,
      nowMs: options.nowMs,
      maxAgeMs: options.maxAgeMs,
    });
    if (!verdict.ok) {
      // A map that is simply not there yet is pending. A map that is there and
      // wrong is a failure, and the parent area says which.
      const status: TitleStatus =
        verdict.reason === 'missing' ? 'pending' : 'failed';
      return {
        title,
        status,
        rejection: verdict.reason,
        reason: rejectionMessage(verdict.reason),
        segments: [],
        hiddenMs: 0,
        verifiedProfiles,
      };
    }
    verified.push(verdict.map);
    verifiedProfiles.push(profile);
  }

  const roomCovered = verified.every((map) =>
    mapCoversRoom(map, options.settings),
  );
  const segments = unionSegments(verified);
  const hiddenMs = verified.reduce(
    (total, map) => Math.max(total, map.hiddenMs),
    0,
  );
  const checkedAtMs = verified.reduce(
    (latest, map) => Math.max(latest, map.createdUtcMs),
    0,
  );

  if (!roomCovered) {
    return {
      title,
      status: 'pending',
      reason:
        'This room is stricter than the check that was run, so this title has to be checked again before kid mode can show it.',
      segments,
      hiddenMs,
      checkedAtMs,
      verifiedProfiles,
    };
  }

  return {
    title,
    status: 'verified',
    segments,
    hiddenMs,
    checkedAtMs,
    verifiedProfiles,
  };
}

export function checkTitles(
  titles: CatalogTitle[],
  options: CheckTitleOptions,
): CheckedTitle[] {
  return titles.map((title) => checkTitle(title, options));
}

/** The only way a title reaches the kid grid. */
export function kidModeTitles(checked: CheckedTitle[]): CheckedTitle[] {
  return checked.filter((entry) => entry.status === 'verified');
}

/** Wording for the shield badge under a poster. */
export function badgeLabel(status: TitleStatus): string {
  switch (status) {
    case 'verified':
      return 'Checked';
    case 'pending':
      return 'Needs check';
    case 'failed':
    default:
      return 'Check failed';
  }
}
