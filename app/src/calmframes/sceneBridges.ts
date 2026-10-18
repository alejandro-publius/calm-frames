/** Optional creator text. These records cannot add, remove or shorten a cover. */
import { nodeToPlain, parseJsonNode, utf8Bytes } from './canonicalJson';
import { sha512 } from './sha512';

export const MIN_SCENE_BRIDGE_MS = 6000;
export const MAX_SCENE_BRIDGE_TEXT = 120;
export const MAX_SCENE_BRIDGE_WORDS = 20;
export const MAX_SCENE_BRIDGE_ENTRIES = 32;
export const MAX_SCENE_BRIDGE_BYTES = 16384;

export interface SceneBridgeAsset {
  titleId: string;
  renditionStartOffsetMs: number;
  sourceSha256: string;
  renditionSha256: string;
  durationMs: number;
}
export interface SceneBridgeInterval { startMs: number; endMs: number }
export interface SceneBridgeEntry extends SceneBridgeInterval { text: string }
export interface SceneBridgeDocument extends SceneBridgeAsset {
  version: 1;
  authorConfirmed: true;
  testFixture: boolean;
  entries: readonly SceneBridgeEntry[];
}
export interface SceneBridgePresentation {
  text: string;
  label: 'Creator note' | 'Scene bridge test';
}

const verified = new WeakSet<SceneBridgeDocument>();
const HASH = /^[a-f0-9]{64}$/;
const exactKeys = (value: Record<string, unknown>, keys: string[]) =>
  Object.keys(value).sort().join(',') === keys.sort().join(',');
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/** Shared creator/runtime validation: no control characters, markup or long lines. */
export function sceneBridgeTextError(text: unknown, durationMs: number): string | null {
  if (typeof text !== 'string' || !text.length || text !== text.trim()) {
    return 'Write a short sentence without leading or trailing spaces.';
  }
  if (text.length > MAX_SCENE_BRIDGE_TEXT || /[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u2028-\u202e\u2060-\u206f<>]/u.test(text)) {
    return 'Use at most 120 characters of plain text on one line.';
  }
  const words = text.split(/\s+/u);
  if (words.length > MAX_SCENE_BRIDGE_WORDS || words.some(word => word.length > 24)) {
    return 'Use at most 20 short words.';
  }
  if (!Number.isFinite(durationMs) || durationMs < MIN_SCENE_BRIDGE_MS ||
      words.length > Math.floor((durationMs - 2000) / 500)) {
    return 'Allow at least six seconds and enough time to read this sentence.';
  }
  return null;
}

/** For an editor or build gate. A valid draft still needs explicit compiled review. */
export function validateSceneBridgeDocument(value: unknown): string | null {
  if (!record(value) || !exactKeys(value, ['version', 'titleId', 'sourceSha256', 'renditionSha256', 'renditionStartOffsetMs', 'durationMs', 'authorConfirmed', 'testFixture', 'entries']) ||
      value.version !== 1 || typeof value.titleId !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,159}$/.test(value.titleId) ||
      typeof value.renditionStartOffsetMs !== 'number' || !Number.isFinite(value.renditionStartOffsetMs) || Math.abs(value.renditionStartOffsetMs as number) > (value.durationMs as number) ||
      value.authorConfirmed !== true || typeof value.testFixture !== 'boolean' ||
      typeof value.sourceSha256 !== 'string' || !HASH.test(value.sourceSha256) ||
      typeof value.renditionSha256 !== 'string' || !HASH.test(value.renditionSha256) ||
      typeof value.durationMs !== 'number' || !Number.isFinite(value.durationMs) || value.durationMs > 86400000 || (value.durationMs as number) <= 0 ||
      !Array.isArray(value.entries) || value.entries.length > MAX_SCENE_BRIDGE_ENTRIES) {
    return 'The scene bridge document or exact media identity is invalid.';
  }
  let previousEnd = -1;
  for (const entry of value.entries) {
    if (!record(entry) || !exactKeys(entry, ['startMs', 'endMs', 'text']) ||
        typeof entry.startMs !== 'number' || !Number.isFinite(entry.startMs) || typeof entry.endMs !== 'number' || !Number.isFinite(entry.endMs) ||
        (entry.startMs as number) < 0 || (entry.endMs as number) > (value.durationMs as number) ||
        (entry.startMs as number) < previousEnd) {
      return 'Use ordered, nonoverlapping intervals inside this exact rendition.';
    }
    const error = sceneBridgeTextError(entry.text, (entry.endMs as number) - (entry.startMs as number));
    if (error) { return error; }
    previousEnd = entry.endMs as number;
  }
  return null;
}

/** The checksum is compiled review input, never accepted from a route or upload. */
export function loadSceneBridges(raw: unknown, expectedSha512: string): SceneBridgeDocument | null {
  if (typeof raw !== 'string' || raw.length > MAX_SCENE_BRIDGE_BYTES || !/^[a-f0-9]{128}$/.test(expectedSha512)) { return null; }
  try {
    const bytes = utf8Bytes(raw);
    if (bytes.length > MAX_SCENE_BRIDGE_BYTES) { return null; }
    const digest = Array.from(sha512(bytes), byte => byte.toString(16).padStart(2, '0')).join('');
    if (digest !== expectedSha512) { return null; }
    // The strict parser rejects duplicate keys instead of silently accepting the last one.
    const value = nodeToPlain(parseJsonNode(raw));
    if (validateSceneBridgeDocument(value)) { return null; }
    const document = value as unknown as SceneBridgeDocument;
    document.entries.forEach(Object.freeze);
    Object.freeze(document.entries);
    Object.freeze(document);
    verified.add(document);
    return document;
  } catch { return null; }
}

/** Only immutable base covers qualify. Personal additions never supply a bridge interval. */
export function resolveSceneBridge(
  document: SceneBridgeDocument | null | undefined,
  asset: SceneBridgeAsset,
  baseIntervals: readonly SceneBridgeInterval[],
  positionMs: number,
): SceneBridgePresentation | undefined {
  if (!document || !verified.has(document) || !Number.isFinite(positionMs) || positionMs < 0 ||
      document.titleId !== asset.titleId || document.renditionStartOffsetMs !== asset.renditionStartOffsetMs ||
      document.sourceSha256 !== asset.sourceSha256 || document.renditionSha256 !== asset.renditionSha256 ||
      document.durationMs !== asset.durationMs || positionMs >= asset.durationMs) { return undefined; }
  const entry = document.entries.find(one => positionMs >= one.startMs && positionMs < one.endMs &&
    baseIntervals.some(base => base.startMs === one.startMs && base.endMs === one.endMs));
  return entry ? { text: entry.text, label: document.testFixture ? 'Scene bridge test' : 'Creator note' } : undefined;
}
