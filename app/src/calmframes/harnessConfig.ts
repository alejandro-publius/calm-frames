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
  /** Play this URL instead of a catalog title, for example the marker clip. */
  videoUrl?: string;
  /** MP4, HLS or DASH. Defaults to MP4 when a videoUrl is given. */
  videoFormat?: string;
  /** Post timing events here during the run, because device logs get dropped. */
  eventSinkUrl?: string;
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
      reason:
        candidate.reason === 'red'
          ? 'red'
          : candidate.reason === 'pattern'
            ? 'pattern'
            : 'general',
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
  if (
    typeof candidate.eventSinkUrl === 'string' &&
    candidate.eventSinkUrl.length > 0
  ) {
    config.eventSinkUrl = candidate.eventSinkUrl;
  }
  if (typeof candidate.videoUrl === 'string' && candidate.videoUrl.length > 0) {
    config.videoUrl = candidate.videoUrl;
    config.videoFormat =
      typeof candidate.videoFormat === 'string' ? candidate.videoFormat : 'MP4';
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

/**
 * Where a debug build looks for a run over the network.
 *
 * On OS 1.2 there is no way to put a file into another package's data
 * directory from the host, so a debug build also asks a small server for a
 * run. 10.0.2.2 is the host machine as seen from the virtual device. On a real
 * stick, point this at the machine serving the run over the local network.
 *
 * This only ever runs in a debug build. A release build never reaches for the
 * network to decide what to play.
 */
export const HARNESS_CONFIG_URL =
  'http://10.0.2.2:8000/calm-frames-harness.json';

async function readHarnessConfigFromNetwork(): Promise<HarnessConfig | null> {
  const isDebugBuild = typeof __DEV__ !== 'undefined' && __DEV__;
  if (!isDebugBuild) {
    console.warn(
      '[calmframes] release build, not asking the network for a measurement run',
    );
    return null;
  }
  try {
    console.warn(`[calmframes] asking ${HARNESS_CONFIG_URL} for a run`);
    const response = await fetch(HARNESS_CONFIG_URL, {
      headers: { 'cache-control': 'no-cache' },
    });
    if (!response.ok) {
      console.warn(`[calmframes] run server answered ${response.status}`);
      return null;
    }
    const config = parseHarnessConfig(await response.text());
    console.warn(
      `[calmframes] run server gave ${config ? config.mode : 'nothing valid'}`,
    );
    return config;
  } catch (error) {
    // No server, which is the normal case. Start the app as usual.
    console.warn(`[calmframes] no run server: ${error}`);
    return null;
  }
}

/** Read the config a device was given, or null for a normal launch. */
export async function readHarnessConfig(): Promise<HarnessConfig | null> {
  try {
    console.warn('[calmframes] looking for a measurement run');
    const entries = await FileSystem.getEntries(HARNESS_CONFIG_DIR);
    if (!Array.isArray(entries) || !entries.includes(HARNESS_CONFIG_FILE)) {
      // No file on the device is the normal case, because on OS 1.2 there is
      // no way to put one there from the host. Ask the network instead.
      return readHarnessConfigFromNetwork();
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
    return config ?? (await readHarnessConfigFromNetwork());
  } catch (error) {
    console.warn(`[calmframes] could not read ${HARNESS_CONFIG_FILE}: ${error}`);
    return readHarnessConfigFromNetwork();
  }
}
