/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * The household setting, which can only ever add hides.
 *
 * CLAUDE.md: "Room settings can only add hides" and "never weaker than WCAG".
 * That has to be true by construction, not by care, so the shape of this
 * module enforces it:
 *
 * - A preset never replaces the WCAG map. It names the maps whose segments are
 *   unioned, and every preset includes `wcag`. Picking broadcast adds the
 *   broadcast map's segments to WCAG's, it does not swap one for the other.
 * - A preset's guard band and minimum cover are floored at the defaults, so no
 *   setting can make an interval shorter than the WCAG default schedule.
 * - TV size and seat distance are compared against the map, not applied to it.
 *   The app cannot recompute flash areas from a map, so when a room is
 *   stricter than anything the map measured, the title becomes pending for
 *   that household instead of quietly getting less cover than it needs.
 *
 * The room arithmetic mirrors flashmap/src/flashmap/room.py. The 10 degrees is
 * WCAG's, from docs/SPEC_SOURCES.md. The rest is trigonometry.
 */

import {
  CoverScheduleOptions,
  DEFAULT_GUARD_BAND_MS,
  DEFAULT_MIN_COVER_MS,
  FlashSegment,
} from './coverSchedule';
import { VerifiedFlashMap } from './flashMap';

export type PresetName = 'wcag' | 'broadcast' | 'extra-cautious';

export const PRESET_NAMES: PresetName[] = ['wcag', 'broadcast', 'extra-cautious'];

export interface PresetDefinition {
  name: PresetName;
  title: string;
  description: string;
  /** Maps whose segments are unioned. Every preset includes wcag. */
  mapProfiles: string[];
  guardBandMs: number;
  minCoverMs: number;
}

export const PRESETS: Record<PresetName, PresetDefinition> = {
  wcag: {
    name: 'wcag',
    title: 'Standard',
    description:
      'Uses the WCAG 2.3.1 flash thresholds included in every preset.',
    mapProfiles: ['wcag'],
    guardBandMs: DEFAULT_GUARD_BAND_MS,
    minCoverMs: DEFAULT_MIN_COVER_MS,
  },
  broadcast: {
    name: 'broadcast',
    title: 'Broadcast',
    description:
      'Adds broadcast flash checks to everything covered by Standard.',
    mapProfiles: ['wcag', 'broadcast'],
    guardBandMs: DEFAULT_GUARD_BAND_MS,
    minCoverMs: DEFAULT_MIN_COVER_MS,
  },
  'extra-cautious': {
    name: 'extra-cautious',
    title: 'Extra cautious',
    description:
      'Includes Broadcast checks and keeps the picture hidden a little longer before and after each flagged part.',
    mapProfiles: ['wcag', 'broadcast'],
    guardBandMs: 1_000,
    minCoverMs: 800,
  },
};

export interface HouseholdSettings {
  preset: PresetName;
  /** Television diagonal in inches. */
  tvDiagonalIn: number;
  /** How far the sofa is from the screen, in inches. */
  seatDistanceIn: number;
}

export const DEFAULT_SETTINGS: HouseholdSettings = {
  preset: 'wcag',
  tvDiagonalIn: 55,
  seatDistanceIn: 96,
};

/** Sizes and distances a person can pick, kept to sane ranges. */
export const TV_DIAGONAL_CHOICES_IN = [32, 43, 50, 55, 65, 75, 85];
export const SEAT_DISTANCE_CHOICES_IN = [48, 60, 72, 84, 96, 120, 144];

export function clampSettings(
  settings: Partial<HouseholdSettings> | null | undefined,
): HouseholdSettings {
  const preset = PRESET_NAMES.includes(settings?.preset as PresetName)
    ? (settings?.preset as PresetName)
    : DEFAULT_SETTINGS.preset;
  const diagonal = Number(settings?.tvDiagonalIn);
  const distance = Number(settings?.seatDistanceIn);
  return {
    preset,
    tvDiagonalIn:
      Number.isFinite(diagonal) && diagonal > 0
        ? diagonal
        : DEFAULT_SETTINGS.tvDiagonalIn,
    seatDistanceIn:
      Number.isFinite(distance) && distance > 0
        ? distance
        : DEFAULT_SETTINGS.seatDistanceIn,
  };
}

/**
 * Schedule options for a setting.
 *
 * Floored at the defaults, so no preset can produce a schedule that covers
 * less than the WCAG default one.
 */
export function coverOptionsFor(
  settings: HouseholdSettings,
): Required<Pick<CoverScheduleOptions, 'guardBandMs' | 'minCoverMs'>> {
  const preset = PRESETS[settings.preset] ?? PRESETS.wcag;
  return {
    guardBandMs: Math.max(DEFAULT_GUARD_BAND_MS, preset.guardBandMs),
    minCoverMs: Math.max(DEFAULT_MIN_COVER_MS, preset.minCoverMs),
  };
}

/** WCAG's 10 degree visual field. SPEC_SOURCES section 2. */
export const FIELD_DEGREES = 10;

export function displayWidthIn(
  tvDiagonalIn: number,
  aspectWidth = 16,
  aspectHeight = 9,
): number {
  const ratio = aspectWidth / Math.hypot(aspectWidth, aspectHeight);
  return tvDiagonalIn * ratio;
}

/** How wide a 10 degree field is on the screen surface, in inches. */
export function fieldInches(seatDistanceIn: number): number {
  return 2 * seatDistanceIn * Math.tan((Math.PI / 180) * (FIELD_DEGREES / 2));
}

/**
 * The 10 degree field as a fraction of the screen width for this room.
 *
 * Smaller means stricter: a small window is filled by a smaller patch of
 * flashing, so more content crosses the area limit.
 */
export function roomFieldFraction(settings: HouseholdSettings): number {
  return fieldInches(settings.seatDistanceIn) / displayWidthIn(settings.tvDiagonalIn);
}

/**
 * Did the analysis already measure a window at least as strict as this room?
 *
 * A map carries every area window it used, as a fraction of the picture width.
 * If the household's field is narrower than the narrowest window in the map,
 * the map cannot answer for this room.
 */
export function mapCoversRoom(
  map: Pick<VerifiedFlashMap, 'windows'>,
  settings: HouseholdSettings,
  tolerance = 0.01,
): boolean {
  if (map.windows.length === 0) {
    return false;
  }
  const narrowest = Math.min(...map.windows.map((window) => window.widthFraction));
  return roomFieldFraction(settings) >= narrowest - tolerance;
}

/**
 * Union the segments of several maps.
 *
 * buildCoverIntervals merges what overlaps, so handing it the concatenation of
 * every preset's segments gives the union. Nothing is dropped and nothing is
 * shortened.
 */
export function unionSegments(maps: Array<{ segments: FlashSegment[] }>): FlashSegment[] {
  const all: FlashSegment[] = [];
  for (const map of maps) {
    all.push(...map.segments);
  }
  return all.sort((a, b) => a.startMs - b.startMs);
}

/** Plain wording for the parent area. */
export function describeRoom(settings: HouseholdSettings): string {
  const inches = Math.round(settings.seatDistanceIn);
  const feet = Math.round((inches / 12) * 10) / 10;
  return `${Math.round(settings.tvDiagonalIn)} inch television, seats about ${feet} feet away`;
}
