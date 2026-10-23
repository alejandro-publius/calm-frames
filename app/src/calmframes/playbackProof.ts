/** Presentation evidence only. Never consulted to authorize a route or remove a cover. */
import { nodeToPlain, parseJsonNode, utf8Bytes } from './canonicalJson';
import { sha512 } from './sha512';
import { PLAYBACK_PROOF_RECORDS } from './approvedPlaybackProof';
import { packagedLibrary } from './packagedLibrary';
import { HouseholdSettings, PRESETS } from './household';
import { CheckedTitle } from './titleStatus';
import { FlashSegment } from './coverSchedule';

interface Measurement { profile: string; findings: number | null; analyzer: string | null }
export interface PlaybackProof {
  version: 1; bundleId: string; titleId: string; preset: string;
  sourceSha256: string; renditionSha256: string; reportSha256: string; checkedInputsSha256: string;
  durationMs: number; renditionStartOffsetMs: number; outcome: string;
  source: Array<Measurement & { mapSha256: string }>;
  output: Measurement[]; frameCount: number | null; timingPreserved: boolean;
}
const keys = (value: unknown, names: string[]) => Boolean(value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join() === [...names].sort().join());
const hash = (x: unknown): x is string => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
const count = (x: unknown) => typeof x === 'number' && Number.isSafeInteger(x) && x >= 0;
const analyzer = (x: unknown) => x === null || (typeof x === 'string' && x.length > 0 && x.length <= 129);
const profiles = ['wcag', 'broadcast', 'extra-cautious'];
const measurement = (m: Measurement) => m && profiles.includes(m.profile) &&
  (m.findings === null || count(m.findings)) && analyzer(m.analyzer);

/** Digest comes from compiled input, never a route, network response or user upload. */
export function loadPlaybackProof(raw: string, expectedSha512: string): PlaybackProof | null {
  try {
    if (typeof raw !== 'string' || raw.length > 8192 || !/^[a-f0-9]{128}$/.test(expectedSha512)) return null;
    const bytes = utf8Bytes(raw);
    if (bytes.length > 8192 || Array.from(sha512(bytes), x => x.toString(16).padStart(2, '0')).join('') !== expectedSha512) return null;
    const value = nodeToPlain(parseJsonNode(raw)) as unknown as PlaybackProof;
    if (!keys(value, ['version', 'bundleId', 'titleId', 'preset', 'sourceSha256', 'renditionSha256', 'durationMs',
      'renditionStartOffsetMs', 'reportSha256', 'checkedInputsSha256', 'outcome', 'source', 'output', 'frameCount', 'timingPreserved']) ||
      value.version !== 1 || !profiles.includes(value.preset) || typeof value.titleId !== 'string' ||
      ![value.bundleId, value.sourceSha256, value.renditionSha256, value.reportSha256, value.checkedInputsSha256].every(hash) ||
      !Number.isFinite(value.durationMs) || value.durationMs <= 0 || !Number.isFinite(value.renditionStartOffsetMs) ||
      !['no flagged segments', 'cover proven drawn', 'cover not proven'].includes(value.outcome) ||
      (value.frameCount !== null && (!count(value.frameCount) || value.frameCount === 0)) || typeof value.timingPreserved !== 'boolean' ||
      !Array.isArray(value.source) || value.source.length < 1 || value.source.length > 2 ||
      !Array.isArray(value.output) || value.output.length < 1 || value.output.length > 2 ||
      !value.source.every(m => keys(m, ['profile', 'mapSha256', 'findings', 'analyzer']) && measurement(m) && hash(m.mapSha256) && count(m.findings)) ||
      !value.output.every(m => keys(m, ['profile', 'findings', 'analyzer']) && measurement(m)) ||
      new Set(value.output.map(m => m.profile)).size !== value.output.length) return null;
    value.source.forEach(Object.freeze); value.output.forEach(Object.freeze);
    Object.freeze(value.source); Object.freeze(value.output);
    return Object.freeze(value);
  } catch { return null; }
}

const cache = new Map<string, PlaybackProof | null>();
export function playbackProofFor(entry: CheckedTitle, settings: HouseholdSettings): PlaybackProof | null {
  const preset = PRESETS[settings.preset];
  if (!preset || entry.status !== 'verified' || !preset.mapProfiles.every(profile => entry.verifiedProfiles.includes(profile))) return null;
  const evidence = packagedLibrary.evidenceFor(entry.title, settings);
  if (!evidence) return null;
  for (const registration of PLAYBACK_PROOF_RECORDS) {
    // Parsing is cheap; hash only a selected record, never all titles during boot.
    let identity: PlaybackProof;
    try { identity = JSON.parse(registration.raw); } catch { continue; }
    if (identity.titleId !== entry.title.id || identity.preset !== settings.preset) continue;
    const cacheKey = registration.sha512 + registration.raw;
    if (!cache.has(cacheKey)) cache.set(cacheKey, loadPlaybackProof(registration.raw, registration.sha512));
    const proof = cache.get(cacheKey);
    if (!proof || proof.bundleId !== evidence.bundleId || proof.sourceSha256 !== evidence.sourceSha256 ||
      proof.renditionSha256 !== evidence.renditionSha256 || proof.reportSha256 !== evidence.reportSha256 ||
      proof.checkedInputsSha256 !== evidence.checkedInputsSha256 || proof.outcome !== evidence.outcome ||
      proof.durationMs !== entry.title.durationMs || proof.renditionStartOffsetMs !== entry.title.renditionStartOffsetMs ||
      proof.source.map(m => m.profile).join() !== preset.mapProfiles.join()) return null;
    const expectedSegments: FlashSegment[] = [];
    for (const item of proof.source) {
      if (!evidence.maps.some(m => m.preset === item.profile && m.sha256 === item.mapSha256)) return null;
      try {
        const map = JSON.parse(entry.title.maps![item.profile]!);
        const version = map.generator?.name && map.generator?.version ? `${map.generator.name} ${map.generator.version}` : null;
        if (map.segments.length !== item.findings || version !== item.analyzer) return null;
        for (const segment of map.segments) expectedSegments.push({ startMs: segment.start_ms, endMs: segment.end_ms,
          reason: segment.reason === 'general' ? 'general' : segment.reason === 'pattern' ? 'pattern' : 'red' });
      } catch { return null; }
    }
    expectedSegments.sort((a, b) => a.startMs - b.startMs);
    if (expectedSegments.length !== entry.segments.length || expectedSegments.some((segment, index) =>
      segment.startMs !== entry.segments[index].startMs || segment.endMs !== entry.segments[index].endMs ||
      segment.reason !== entry.segments[index].reason)) return null;
    return proof;
  }
  return null;
}
