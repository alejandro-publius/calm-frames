/** Delivery validation for independently reproduced baked ambient reports. No trust grants. */
import { createHash } from 'node:crypto';
const PRESETS = ['wcag', 'broadcast', 'extra-cautious'];
const need = (x, message = 'Invalid baked ambient verification binding.') => { if (!x) throw new Error(message); };
const digest = (raw, algorithm = 'sha256') => createHash(algorithm).update(raw).digest('hex');
const hash = (x, length = 64) => typeof x === 'string' && new RegExp(`^[a-f0-9]{${length}}$`).test(x);
const keys = (x, names) => x && typeof x === 'object' && !Array.isArray(x) && Object.keys(x).sort().join() === [...names].sort().join();
const normalized = x => Array.isArray(x) ? x.map(normalized) : x && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map(k => [k, normalized(x[k])])) : x;
const same = (a, b) => JSON.stringify(normalized(a)) === JSON.stringify(normalized(b));
export function strictJson(raw) {
  need(typeof raw === 'string');
  const value = JSON.parse(raw), stack = [];
  for (const token of raw.match(/"(?:\\.|[^"\\])*"|[{}\[\]:,]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/g) ?? []) {
    const top = stack.at(-1);
    if (token === '{' || token === '[') stack.push({ object: token === '{', expect: true, seen: new Set() });
    else if (token === '}' || token === ']') stack.pop();
    else if (token === ',' && top?.object) top.expect = true;
    else if (token.startsWith('"') && top?.object && top.expect) {
      const key = JSON.parse(token); need(!top.seen.has(key), 'Duplicate ambient report field.');
      top.seen.add(key); top.expect = false;
    }
  }
  return value;
}
function intervals(maps, preset, durationMs) {
  const guard = preset === 'extra-cautious' ? 1000 : 500, minimum = preset === 'extra-cautious' ? 800 : 400;
  const profiles = preset === 'wcag' ? ['wcag'] : ['wcag', 'broadcast'];
  const spans = profiles.flatMap(p => maps[p].segments).map(s => {
    need(Number.isFinite(s.start_ms) && Number.isFinite(s.end_ms) && s.end_ms > s.start_ms);
    const start = s.start_ms - guard;
    return { startMs: Math.max(0, start), endMs: Math.min(durationMs, Math.max(s.end_ms + guard, start + minimum)) };
  }).sort((a,b) => a.startMs - b.startMs);
  const merged = [];
  for (const span of spans) {
    if (span.endMs <= span.startMs) continue;
    const last = merged.at(-1);
    if (last && span.startMs <= last.endMs) last.endMs = Math.max(last.endMs, span.endMs);
    else merged.push(span);
  }
  return merged;
}
export function checkAmbientReport(raw, titles) {
  need(Array.isArray(titles) && titles.length > 0);
  const report = strictJson(raw);
  need(keys(report, ['version','recipe','passed','outcome','sourceSha256','publicKeyFingerprint','inputBindingRaw','presets']));
  need(report.version === 1 && report.recipe === 'baked-ambient-v1' && report.passed === true && report.outcome === 'cover proven drawn' && hash(report.publicKeyFingerprint));
  const binding = strictJson(report.inputBindingRaw);
  need(keys(binding, ['sourceSha256','ambientSha256','mapSha256','renditionSha256','metadataSha512']) && hash(binding.ambientSha256) && binding.sourceSha256 === report.sourceSha256);
  need(keys(report.presets, PRESETS));
  for (const field of ['mapSha256','renditionSha256','metadataSha512']) need(keys(binding[field], PRESETS) && Object.values(binding[field]).every(x => hash(x, field === 'metadataSha512' ? 128 : 64)));
  for (const title of titles) {
    need(title.sourceSha256 === report.sourceSha256 && title.verification.outcome === report.outcome && title.verification.checkedInputsSha256 === digest(report.inputBindingRaw));
    const maps = Object.fromEntries(PRESETS.map(p => [p, strictJson(title.maps[p].text)]));
    need(PRESETS.every(p => binding.mapSha256[p] === title.maps[p].sha256 && maps[p].signature.key_id === `sha256:${report.publicKeyFingerprint}`));
    for (const preset of PRESETS) {
      const proof = report.presets[preset];
      need(keys(proof, ['metadataRaw','ambientAnalysis','outputAnalysis','timingAudio','reproductionSha256']));
      need(digest(proof.metadataRaw, 'sha512') === binding.metadataSha512[preset]);
      const meta = strictJson(proof.metadataRaw), rendition = title.renditions[preset];
      need(keys(meta, ['version','recipe','sourceSha256','renditionSha256','ambientSha256','durationMs','renditionStartOffsetMs','preset','mapSha256','intervals','audioPreserved','frameTimingPreserved','analysis']));
      need(meta.version === 1 && meta.recipe === report.recipe && meta.preset === preset && meta.sourceSha256 === title.sourceSha256 && meta.ambientSha256 === binding.ambientSha256 &&
        meta.renditionSha256 === rendition.sha256 && meta.renditionSha256 === binding.renditionSha256[preset] && meta.renditionSha256 === proof.reproductionSha256 &&
        meta.durationMs === title.durationMs && meta.durationMs === rendition.durationMs && meta.renditionStartOffsetMs === 0 && rendition.startOffsetMs === 0 && meta.audioPreserved === true && meta.frameTimingPreserved === true);
      need(keys(meta.analysis, ['wcag','broadcast']));
      need(same(meta.mapSha256, { wcag: binding.mapSha256.wcag, broadcast: binding.mapSha256.broadcast }));
      need(Array.isArray(meta.intervals) && meta.intervals.length > 0 && same(meta.intervals, intervals(maps, preset, title.durationMs)), 'Ambient intervals differ from the authenticated app plan.');
      const timing = proof.timingAudio;
      need(keys(timing, ['frameCount','audioPacketCount','videoDurationRational','frameTimesSha256','audioPacketsSha256','sourceEqualsOutput']));
      need(timing.sourceEqualsOutput === true && Number.isInteger(timing.frameCount) && timing.frameCount > 0 && Number.isInteger(timing.audioPacketCount) && timing.audioPacketCount >= 0 && hash(timing.frameTimesSha256) && hash(timing.audioPacketsSha256));
      need(typeof timing.videoDurationRational === 'string' && /^\d+(?:\/\d+)?$/.test(timing.videoDurationRational));
      const [n, d = 1] = timing.videoDurationRational.split('/').map(Number), duration = n / d * 1000;
      need(Number.isFinite(duration) && Math.abs(duration - title.durationMs) < 0.001);
      for (const [group, expected] of [['ambientAnalysis', meta.ambientSha256], ['outputAnalysis', rendition.sha256]]) {
        need(keys(proof[group], ['wcag','broadcast']));
        for (const p of ['wcag','broadcast']) {
          const entry = proof[group][p]; need(keys(entry, ['raw','sha256']) && hash(entry.sha256) && digest(entry.raw) === entry.sha256);
          const analysis = strictJson(entry.raw);
          need(analysis.source.sha256 === expected && Array.isArray(analysis.segments) && analysis.segments.length === 0 && analysis.summary.pass === true && same(analysis.profile, maps[p].profile));
          need(analysis.profile.room.tv_diagonal_in === 85 && analysis.profile.room.seat_distance_in === 48);
          if (group === 'outputAnalysis') need(meta.analysis[p] === entry.sha256);
        }
      }
    }
  }
  return report;
}
