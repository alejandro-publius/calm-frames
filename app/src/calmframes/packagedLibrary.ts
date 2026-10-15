/**
 * Only a catalog compiled into this build may introduce a prepared-media key.
 * The Python export/build check binds its maps and renditions to exact package
 * bytes. This module never accepts a catalog URL or a key supplied by a route.
 */
// Metro resolves .json before .ts, unlike Jest. Name the generated module
// explicitly so the signed catalog text is the same in tests and on Vega.
import { PACKAGED_LIBRARY_JSON } from '../../assets/raw/prepared-library/catalog.ts';
import { base64ToBytes } from './ed25519';
import { coverOptionsFor, HouseholdSettings, PRESET_NAMES, PresetName } from './household';
import { CatalogTitle } from './titleStatus';

type RecordValue = Record<string, unknown>;
interface PackagedCaption {
  path: string;
  sha256: string;
  label: string;
  language: string;
  mimeType: 'text/vtt';
}
interface PackagedRendition {
  path: string;
  sha256: string;
  durationMs: number;
  startOffsetMs: number;
  guardBandMs: number;
  minCoverMs: number;
  captions?: PackagedCaption[];
}
interface PackagedTitle {
  id: string;
  title: string;
  sourceSha256: string;
  durationMs: number;
  maps: Record<PresetName, { path: string; sha256: string; text: string }>;
  renditions: Record<PresetName, PackagedRendition>;
  verification: { reportSha256: string; checkedInputsSha256: string; outcome: string };
}
interface PackagedManifest {
  bundleId: string;
  publicKeyBase64: string;
  titles: PackagedTitle[];
}

const ASSET_ROOT = 'assets/raw/prepared-library';
const SHA = /^[0-9a-f]{64}$/;
const MAX_CATALOG_LENGTH = 16 * 1024 * 1024;
const MAX_MAP_LENGTH = 2 * 1024 * 1024 + 256 * 1024;

function object(value: unknown): RecordValue {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Prepared metadata must be an object.');
  }
  return value as RecordValue;
}

function text(value: unknown, limit = 200): string {
  if (typeof value !== 'string' || !value.trim() || value.length > limit) {
    throw new Error('Prepared metadata has invalid text.');
  }
  return value;
}

function digest(value: unknown): string {
  const result = text(value, 64);
  if (!SHA.test(result)) {
    throw new Error('Prepared metadata has an invalid digest.');
  }
  return result;
}

function finite(value: unknown, minimum: number, maximum: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value) ||
      value < minimum || value > maximum) {
    throw new Error('Prepared metadata has an invalid measurement.');
  }
  return value;
}

function profiles(value: unknown): RecordValue {
  const result = object(value);
  if (Object.keys(result).length !== PRESET_NAMES.length ||
      PRESET_NAMES.some((preset) => !Object.prototype.hasOwnProperty.call(result, preset))) {
    throw new Error('Every prepared preset is required.');
  }
  return result;
}

function parseManifest(raw: string): PackagedManifest {
  if (raw.length > MAX_CATALOG_LENGTH) {
    throw new Error('The prepared catalog is too large.');
  }
  const value = object(JSON.parse(raw));
  if (value.version !== 1 || !Array.isArray(value.titles) || value.titles.length > 16) {
    throw new Error('The prepared catalog version or title list is invalid.');
  }
  if (value.titles.length === 0 && Object.keys(value).length === 2) {
    return { bundleId: '', publicKeyBase64: '', titles: [] };
  }
  if (value.assetRoot !== ASSET_ROOT) {
    throw new Error('Prepared assets must remain inside their package.');
  }
  const bundleId = digest(value.bundleId);
  const publicKeyBase64 = text(value.publicKeyBase64, 44);
  if (base64ToBytes(publicKeyBase64)?.length !== 32) {
    throw new Error('The compiled prepared key is invalid.');
  }
  const files = object(value.files);
  const used = new Set<string>();
  const ids = new Set<string>();
  const artifact = (path: string, hash: unknown) => {
    const expected = digest(hash);
    if (files[path] !== expected || used.has(path)) {
      throw new Error('A prepared asset is missing, duplicated or changed.');
    }
    used.add(path);
    return expected;
  };
  const titles = value.titles.map((item): PackagedTitle => {
    const title = object(item);
    const sourceSha256 = digest(title.sourceSha256);
    const id = `prepared-${sourceSha256}`;
    if (title.id !== id || ids.has(id)) {
      throw new Error('A prepared title identity is invalid or repeated.');
    }
    ids.add(id);
    const durationMs = finite(title.durationMs, 1, 24 * 60 * 60 * 1000);
    const maps = profiles(title.maps);
    const renditions = profiles(title.renditions);
    const mapResult = {} as PackagedTitle['maps'];
    const renditionResult = {} as PackagedTitle['renditions'];
    for (const preset of PRESET_NAMES) {
      const prefix = `titles/${sourceSha256}/${preset}`;
      const map = object(maps[preset]);
      if (map.path !== `${prefix}.json`) {
        throw new Error('A prepared map path leaves its title.');
      }
      mapResult[preset] = { path: map.path, sha256: artifact(map.path, map.sha256),
        text: text(map.text, MAX_MAP_LENGTH) };
      const rendition = object(renditions[preset]);
      const timing = coverOptionsFor({ preset, tvDiagonalIn: 55, seatDistanceIn: 96 });
      if (rendition.path !== `${prefix}.mp4` ||
          rendition.guardBandMs !== timing.guardBandMs ||
          rendition.minCoverMs !== timing.minCoverMs) {
        throw new Error('A prepared rendition does not match its playback plan.');
      }
      const captions = rendition.captions;
      if (captions !== undefined && (!Array.isArray(captions) || captions.length > 1)) {
        throw new Error('The prepared caption list is invalid.');
      }
      const captionResult = (captions as unknown[] | undefined)?.map((caption) => {
        const track = object(caption);
        if (track.path !== `${prefix}.vtt` || track.mimeType !== 'text/vtt') {
          throw new Error('A prepared caption path or type is invalid.');
        }
        return { path: track.path, sha256: artifact(track.path, track.sha256),
          label: text(track.label, 80), language: text(track.language, 16),
          mimeType: 'text/vtt' as const };
      });
      renditionResult[preset] = {
        path: rendition.path, sha256: artifact(rendition.path, rendition.sha256),
        durationMs: finite(rendition.durationMs, 1, 24 * 60 * 60 * 1000),
        startOffsetMs: finite(rendition.startOffsetMs, -150, 150),
        guardBandMs: timing.guardBandMs, minCoverMs: timing.minCoverMs,
        captions: captionResult,
      };
    }
    const verification = object(title.verification);
    digest(verification.reportSha256);
    digest(verification.checkedInputsSha256);
    text(verification.outcome);
    return { id, title: text(title.title), sourceSha256, durationMs,
      maps: mapResult, renditions: renditionResult, verification: {
        reportSha256: digest(verification.reportSha256),
        checkedInputsSha256: digest(verification.checkedInputsSha256),
        outcome: text(verification.outcome),
      } };
  });
  if (Object.keys(files).length !== used.size) {
    throw new Error('The prepared bundle has unexpected assets.');
  }
  return { bundleId, publicKeyBase64, titles };
}

interface RouteTitle {
  id?: string;
  uri?: string;
  format?: string;
  textTrack?: unknown;
}
interface RouteGuard {
  sha256: string;
  maps?: unknown;
  mapUrls?: unknown;
  settings?: HouseholdSettings;
  durationMs?: number;
  renditionSha256?: string;
  renditionStartOffsetMs?: number;
  titleId?: string;
}

function sameMaps(actual: unknown, expected: CatalogTitle['maps']): boolean {
  if (!actual || typeof actual !== 'object' || Array.isArray(actual)) {
    return false;
  }
  return Object.keys(actual).length === PRESET_NAMES.length &&
    PRESET_NAMES.every((preset) => (actual as RecordValue)[preset] === expected?.[preset]);
}

export function concernsPackagedLibrary(title: RouteTitle): boolean {
  return Boolean(title.id?.startsWith('prepared-') ||
    title.uri?.startsWith(`file:///pkg/${ASSET_ROOT}/`));
}

/** The only production input is the build's static import above. */
export function createPackagedLibrary(raw: string) {
  let manifest: PackagedManifest = { bundleId: '', publicKeyBase64: '', titles: [] };
  let problem: string | null = null;
  try {
    manifest = parseManifest(raw);
  } catch {
    problem = 'The library could not be opened.';
  }
  const uri = (path: string) => `file:///pkg/${ASSET_ROOT}/${manifest.bundleId}/${path}`;
  const titles = (settings: HouseholdSettings): CatalogTitle[] => {
    if (!PRESET_NAMES.includes(settings.preset)) {
      return [];
    }
    return manifest.titles.map((title) => {
      const rendition = title.renditions[settings.preset];
      return {
        id: title.id, title: title.title, uri: uri(rendition.path),
        sha256: title.sourceSha256, durationMs: title.durationMs,
        renditionSha256: rendition.sha256, renditionStartOffsetMs: rendition.startOffsetMs,
        maps: Object.fromEntries(PRESET_NAMES.map((preset) => [preset, title.maps[preset].text])),
        textTrack: rendition.captions?.map((caption) => ({ label: caption.label,
          language: caption.language, mimeType: caption.mimeType, uri: uri(caption.path) })),
        bifFromSafeRendition: true,
      };
    });
  };
  const match = (title: CatalogTitle, settings: HouseholdSettings) =>
    titles(settings).find((expected) => expected.id === title.id &&
      expected.uri === title.uri && expected.sha256 === title.sha256 &&
      expected.durationMs === title.durationMs &&
      expected.renditionSha256 === title.renditionSha256 &&
      expected.renditionStartOffsetMs === title.renditionStartOffsetMs &&
      sameMaps(title.maps, expected.maps) &&
      JSON.stringify(title.textTrack) === JSON.stringify(expected.textTrack));
  return {
    problem,
    titles,
    /** Read-only evidence, using the same exact identity predicate as playback. */
    evidenceFor: (title: CatalogTitle, settings: HouseholdSettings) => {
      if (!match(title, settings)) return null;
      const item = manifest.titles.find((candidate) => candidate.id === title.id)!;
      return {
        bundleId: manifest.bundleId, sourceSha256: item.sourceSha256,
        renditionSha256: item.renditions[settings.preset].sha256,
        renditionPath: uri(item.renditions[settings.preset].path),
        renditionStartOffsetMs: item.renditions[settings.preset].startOffsetMs,
        preset: settings.preset,
        maps: PRESET_NAMES.map((preset) => ({ preset, sha256: item.maps[preset].sha256 })),
        ...item.verification,
      };
    },
    publicKeyFor: (title: CatalogTitle, settings: HouseholdSettings): string | null =>
      match(title, settings) ? manifest.publicKeyBase64 : null,
    acceptsRoute: (data: RouteTitle, guarded?: RouteGuard): boolean => {
      if (!guarded?.settings || guarded.mapUrls !== undefined ||
          guarded.titleId !== data.id || data.format !== 'MP4') {
        return false;
      }
      const expected = titles(guarded.settings).find((title) => title.id === data.id);
      return Boolean(expected && expected.uri === data.uri &&
        expected.sha256 === guarded.sha256 && expected.durationMs === guarded.durationMs &&
        expected.renditionSha256 === guarded.renditionSha256 &&
        expected.renditionStartOffsetMs === guarded.renditionStartOffsetMs &&
        sameMaps(guarded.maps, expected.maps) &&
        JSON.stringify(data.textTrack) === JSON.stringify(expected.textTrack));
    },
    /** Lookup follows a successful acceptsRoute check, never route-supplied keys. */
    get publicKeyBase64() { return manifest.publicKeyBase64; },
  };
}

export const packagedLibrary = createPackagedLibrary(PACKAGED_LIBRARY_JSON);
