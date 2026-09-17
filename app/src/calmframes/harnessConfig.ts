/**
 * Starting a measurement run without touching the remote.
 *
 * The layering test and GATE 1 both need the app to go straight into a known
 * run, on a stick, in front of a camera, without someone navigating menus
 * between takes. So the app looks for a config file in its own data directory
 * at startup and, if it finds a valid one, goes straight to the player in
 * harness mode.
 *
 * Push a run to a device:
 *
 *     vega device copy-to <file> /home/app_user/packages/<package id>/data
 *
 * The file is named calm-frames-harness.json. Delete it to get the normal app
 * back:
 *
 *     vega device run-cmd --command 'rm /home/app_user/packages/<id>/data/calm-frames-harness.json'
 *
 * A file that is missing, unreadable or invalid means a normal launch. This is
 * a measurement harness, not kid mode: kid mode fails closed and hides the
 * picture, which is enforced separately in phase 4.
 */

import { KeplerFileSystem as FileSystem } from '@amazon-devices/kepler-file-system';
import { ReferencePatch } from './CoverLayer';
import { FlashSegment } from './coverSchedule';
import { HarnessMode } from './useCoverHarness';

export const HARNESS_CONFIG_FILE = 'calm-frames-harness.json';
export const HARNESS_CONFIG_DIR = '/data';

export interface HarnessConfig {
  mode: HarnessMode;
  toggleEveryMs?: number;
  guardBandMs?: number;
  segments?: FlashSegment[];
  referencePatch?: ReferencePatch;
  scheduleLabel?: string;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function parseSegments(value: unknown): FlashSegment[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const segments: FlashSegment[] = [];
  for (const entry of value) {
    const candidate = entry as Partial<FlashSegment>;
    if (!isFiniteNumber(candidate?.startMs) || !isFiniteNumber(candidate?.endMs)) {
      return undefined;
    }
    if (candidate.endMs <= candidate.startMs) {
      return undefined;
    }
    segments.push({
      startMs: candidate.startMs,
      endMs: candidate.endMs,
      reason: candidate.reason === 'red' ? 'red' : 'general',
      label: typeof candidate.label === 'string' ? candidate.label : undefined,
    });
  }
  return segments;
}

function parsePatch(value: unknown): ReferencePatch | undefined {
  const candidate = value as Partial<ReferencePatch> | undefined;
  if (
    !candidate ||
    !isFiniteNumber(candidate.x) ||
    !isFiniteNumber(candidate.y) ||
    !isFiniteNumber(candidate.width) ||
    !isFiniteNumber(candidate.height)
  ) {
    return undefined;
  }
  return {
    x: candidate.x,
    y: candidate.y,
    width: candidate.width,
    height: candidate.height,
  };
}

/** Turn the file contents into a config, or null if it cannot be trusted. */
export function parseHarnessConfig(raw: string): HarnessConfig | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  const candidate = parsed as Partial<HarnessConfig> | null;
  if (!candidate || (candidate.mode !== 'layering' && candidate.mode !== 'timing')) {
    return null;
  }
  const config: HarnessConfig = { mode: candidate.mode };

  if (isFiniteNumber(candidate.toggleEveryMs) && candidate.toggleEveryMs > 0) {
    config.toggleEveryMs = candidate.toggleEveryMs;
  }
  if (isFiniteNumber(candidate.guardBandMs) && candidate.guardBandMs >= 0) {
    config.guardBandMs = candidate.guardBandMs;
  }
  if (typeof candidate.scheduleLabel === 'string') {
    config.scheduleLabel = candidate.scheduleLabel;
  }
  const segments = parseSegments(candidate.segments);
  if (segments) {
    config.segments = segments;
  }
  const patch = parsePatch(candidate.referencePatch);
  if (patch) {
    config.referencePatch = patch;
  }

  // A timing run with no schedule would measure nothing, so refuse it rather
  // than play a title with a cover that never comes on.
  if (config.mode === 'timing' && (!config.segments || config.segments.length === 0)) {
    return null;
  }

  return config;
}

/** Read the config a device was given, or null for a normal launch. */
export async function readHarnessConfig(): Promise<HarnessConfig | null> {
  try {
    const entries = await FileSystem.getEntries(HARNESS_CONFIG_DIR);
    if (!Array.isArray(entries) || !entries.includes(HARNESS_CONFIG_FILE)) {
      return null;
    }
    const raw = await FileSystem.readFileAsString(
      `${HARNESS_CONFIG_DIR}/${HARNESS_CONFIG_FILE}`,
      'UTF-8',
    );
    const config = parseHarnessConfig(raw);
    if (!config) {
      console.warn(
        `[calmframes] ${HARNESS_CONFIG_FILE} is present but not a valid harness config, starting normally`,
      );
    }
    return config;
  } catch (error) {
    console.warn(`[calmframes] could not read ${HARNESS_CONFIG_FILE}: ${error}`);
    return null;
  }
}
