/** Reviewed baked pixels only. This never changes the guard, intervals or seek funnel. */
import { nodeToPlain, parseJsonNode, utf8Bytes } from './canonicalJson';
import { sha512 } from './sha512';
import { SceneBridgeAsset, SceneBridgeInterval } from './sceneBridges';

export interface BakedAmbientDocument {
  version: 1;
  recipe: 'baked-ambient-v1';
  sourceSha256: string;
  renditionSha256: string;
  ambientSha256: string;
  durationMs: number;
  renditionStartOffsetMs: 0;
  preset: 'wcag' | 'broadcast' | 'extra-cautious';
  mapSha256: { wcag: string; broadcast: string };
  intervals: readonly SceneBridgeInterval[];
  audioPreserved: true;
  frameTimingPreserved: true;
  analysis: { wcag: string; broadcast: string };
}
const checked = new WeakSet<BakedAmbientDocument>();
const hash = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const keys = (value: unknown, names: string[]): boolean => Boolean(value && typeof value === 'object' &&
  !Array.isArray(value) && Object.keys(value).sort().join(',') === [...names].sort().join(','));

/** expectedSha512 is compiled reviewed input, never a route or uploaded assertion. */
export function loadBakedAmbient(raw: string, expectedSha512: string): BakedAmbientDocument | null {
  try {
    if (typeof raw !== 'string' || raw.length > 16384 || !/^[a-f0-9]{128}$/.test(expectedSha512)) return null;
    const bytes = utf8Bytes(raw);
    if (bytes.length > 16384 || Array.from(sha512(bytes), x => x.toString(16).padStart(2, '0')).join('') !== expectedSha512) return null;
    const value = nodeToPlain(parseJsonNode(raw)) as unknown as BakedAmbientDocument;
    if (!keys(value, ['version', 'recipe', 'sourceSha256', 'renditionSha256', 'ambientSha256', 'durationMs',
      'renditionStartOffsetMs', 'preset', 'mapSha256', 'intervals', 'audioPreserved', 'frameTimingPreserved', 'analysis']) ||
      value.version !== 1 || value.recipe !== 'baked-ambient-v1' || value.renditionStartOffsetMs !== 0 ||
      !hash(value.sourceSha256) || !hash(value.renditionSha256) || !hash(value.ambientSha256) ||
      typeof value.durationMs !== 'number' || !Number.isFinite(value.durationMs) || value.durationMs <= 0 || value.durationMs > 86400000 ||
      !['wcag', 'broadcast', 'extra-cautious'].includes(value.preset) || value.audioPreserved !== true || value.frameTimingPreserved !== true ||
      !keys(value.mapSha256, ['wcag', 'broadcast']) || !Object.values(value.mapSha256).every(hash) ||
      !keys(value.analysis, ['wcag', 'broadcast']) || !Object.values(value.analysis).every(hash) ||
      !Array.isArray(value.intervals) || !value.intervals.length || value.intervals.length > 128) return null;
    let end = -1;
    for (const span of value.intervals) {
      if (!keys(span, ['startMs', 'endMs']) || !Number.isFinite(span.startMs) || !Number.isFinite(span.endMs) ||
        span.startMs < 0 || span.startMs < end || span.endMs <= span.startMs || span.endMs > value.durationMs) return null;
      end = span.endMs;
      Object.freeze(span);
    }
    Object.freeze(value.intervals); Object.freeze(value.mapSha256); Object.freeze(value.analysis); Object.freeze(value);
    checked.add(value);
    return value;
  } catch { return null; }
}

export interface BakedAmbientState {
  acceptedPreparedRoute: boolean;
  verified: boolean;
  scheduledCover: boolean;
  buffering: boolean;
  paused: boolean;
  opening: boolean;
  returning: boolean;
  ended: boolean;
  error: boolean;
  personalCoversReady: boolean;
  personalCoverCount: number;
}

/** Exact catalog identity AND checked maps AND an ordinary stable scheduled cover.
 * Uncertainty, seeks, loading, personal additions and missing approvals keep the opaque layer.
 */
export function mayShowBakedAmbient(document: BakedAmbientDocument | null, asset: SceneBridgeAsset | undefined,
  preset: string | undefined, maps: readonly { preset: string; sha256: string }[],
  baseIntervals: readonly SceneBridgeInterval[], positionMs: number, state: BakedAmbientState): boolean {
  if (!document || !checked.has(document) || !asset || !state.acceptedPreparedRoute || !state.verified ||
      !state.scheduledCover || state.buffering || state.paused || state.opening || state.returning || state.ended || state.error ||
      !state.personalCoversReady || state.personalCoverCount !== 0 || !Number.isFinite(positionMs) ||
      document.sourceSha256 !== asset.sourceSha256 || document.renditionSha256 !== asset.renditionSha256 ||
      document.durationMs !== asset.durationMs || document.renditionStartOffsetMs !== asset.renditionStartOffsetMs || document.preset !== preset ||
      !(['wcag', 'broadcast'] as const).every(p => maps.some(m => m.preset === p && m.sha256 === document.mapSha256[p])) ||
      baseIntervals.length !== document.intervals.length || !document.intervals.every((span, index) =>
        span.startMs === baseIntervals[index].startMs && span.endMs === baseIntervals[index].endMs)) return false;
  return document.intervals.some(span => positionMs >= span.startMs && positionMs < span.endMs);
}
