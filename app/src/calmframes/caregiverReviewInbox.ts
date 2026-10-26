/** Read-only caregiver reports. These records can never introduce playable media. */
import { KeplerFileSystem } from '@amazon-devices/kepler-file-system';

// Component-owned SDK mount: no user-staged intermediate directory or alias.
export const REVIEW_INBOX = '/scratch';
// SDK 0.24 native file_system.idl FileType.FILE; not POSIX st_mode bits.
const REGULAR_FILE = '5';
export const MAX_REVIEW_BYTES = 256 * 1024;
export const MAX_REVIEWS = 8;
const NAME = /^calm-frames-review-[a-f0-9]{32}\.json$/;
const SHA = /^[a-f0-9]{64}$/;
const PRESETS = ['wcag', 'broadcast', 'extra-cautious'] as const;
export interface CaregiverReview {
  title: string; sourceSha256: string; sourceBytes: number; durationMs: number;
  plans: {preset: typeof PRESETS[number]; coveredMs: number; intervals: number}[];
}
export interface ReviewFile { name: string; review: CaregiverReview; text: string; }
export interface ReviewReader {
  exists(path: string): Promise<boolean>;
  getEntries(path: string): Promise<string[]>;
  getMetadata(path: string, noFollow: boolean): Promise<{size: number; mode?: unknown; entryType?: unknown}>;
  readFileAsString(path: string, encoding: string): Promise<string>;
}
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid review');
  return value as Record<string, unknown>;
}
function number(value: unknown, max: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > max) throw new Error('Invalid review');
  return value;
}
export function parseCaregiverReview(text: string): CaregiverReview {
  if (text.length > MAX_REVIEW_BYTES) throw new Error('Review is too large');
  const data = record(JSON.parse(text)), source = record(data.source), analysis = record(data.analysis);
  if (data.schema !== 'calm-frames-caregiver-review-v1' || data.processing_permission_confirmed !== true ||
      data.permission_verified_by_application !== false || data.tv_playback_authorized !== false ||
      analysis.analysis_complete !== true || analysis.playable !== false ||
      typeof data.title !== 'string' || !data.title.trim() || data.title.length > 200 ||
      Array.from(data.title).some(char => {const code = char.charCodeAt(0); return code < 32 || code === 127 || (code >= 0x202a && code <= 0x202e) || (code >= 0x2066 && code <= 0x2069);}) ||
      typeof source.sha256 !== 'string' || !SHA.test(source.sha256) || analysis.source_sha256 !== source.sha256) {
    throw new Error('Incomplete review or unsupported permission/authorization claim');
  }
  const sourceBytes = number(source.bytes, 64 * 1024 * 1024), durationMs = number(analysis.duration_ms, 60000);
  if (!sourceBytes || !Number.isInteger(sourceBytes) || !durationMs ||
      !Number.isInteger(analysis.frame_count) || number(analysis.frame_count, 1000000) < 1) throw new Error('Invalid review');
  const hashes = record(analysis.review_map_hashes);
  for (const key of ['wcag', 'broadcast']) if (typeof hashes[key] !== 'string' || !SHA.test(hashes[key] as string)) throw new Error('Missing analysis identity');
  const plans = record(analysis.presets);
  return { title: data.title.trim(), sourceSha256: source.sha256, sourceBytes, durationMs,
    plans: PRESETS.map(preset => {
      const plan = record(plans[preset]);
      if (!Array.isArray(plan.intervals) || plan.intervals.length > 10000) throw new Error('Invalid review');
      let end = 0, sum = 0;
      for (const raw of plan.intervals) {
        const interval = record(raw), start = number(interval.start_ms, durationMs), stop = number(interval.end_ms, durationMs);
        if (start < end || stop <= start || typeof interval.reason !== 'string' || !interval.reason) throw new Error('Invalid review');
        end = stop; sum += stop - start;
      }
      if (number(plan.covered_ms, durationMs) !== sum) throw new Error('Changed review plan');
      return {preset, coveredMs: sum, intervals: plan.intervals.length};
    }) };
}
export async function readReviewFile(name: string, reader: ReviewReader = KeplerFileSystem): Promise<ReviewFile> {
  if (!NAME.test(name)) throw new Error('Unsupported review filename');
  const path = `${REVIEW_INBOX}/${name}`;
  const stat = await reader.getMetadata(path, true);
  // SDK 0.24 returns the native enum as entryType: "5", with no mode.
  // The installed JS Metadata.mode declaration does not match that bridge.
  // Never infer a file type from OpenMode or coerce other numeric strings.
  if ((stat.entryType !== REGULAR_FILE && stat.entryType !== 5) ||
      !Number.isInteger(stat.size) || stat.size <= 0 || stat.size > MAX_REVIEW_BYTES) throw new Error('Not a bounded regular review file');
  const text = await reader.readFileAsString(path, 'UTF-8');
  return {name, text, review: parseCaregiverReview(text)};
}
export async function loadReviewInbox(reader: ReviewReader = KeplerFileSystem): Promise<{files: ReviewFile[]; refused: number}> {
  if (!await reader.exists(REVIEW_INBOX)) return {files: [], refused: 0};
  const entries = await reader.getEntries(REVIEW_INBOX);
  if (entries.length > MAX_REVIEWS) throw new Error('Keep at most eight reports in the review inbox, then refresh.');
  const files: ReviewFile[] = []; let refused = 0;
  for (const name of entries.slice().sort()) {
    try { files.push(await readReviewFile(name, reader)); } catch { refused++; }
  }
  return {files, refused};
}
