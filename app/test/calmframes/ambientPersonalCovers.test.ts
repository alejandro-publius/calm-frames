import { ambientCoverPredecessor, combineAmbientCovers } from '../../src/calmframes/ambientPersonalCovers';
import { PACKAGED_LIBRARY_JSON } from '../../src/calmframes/acadiaCatalog';
import { BakedAmbientDocument } from '../../src/calmframes/bakedAmbient';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { createApprovedAcadiaLibrary } from '../../src/calmframes/packagedLibrary';
import { personalCoverAsset, PersonalCoverRecord } from '../../src/calmframes/personalCovers';
import type { PersonalCoverLoad } from '../../src/calmframes/personalCoverStorage';
import { readFileSync } from 'fs';
import { resolve } from 'path';
const library = createApprovedAcadiaLibrary(PACKAGED_LIBRARY_JSON);
const title = library.titles(DEFAULT_SETTINGS)[0];
const oldAsset = personalCoverAsset(title)!;
const currentAsset = { ...oldAsset, renditionSha256: 'a'.repeat(64) };
const evidence = library.evidenceFor(title, DEFAULT_SETTINGS)!;
const document = { sourceSha256: currentAsset.sourceSha256, renditionSha256: currentAsset.renditionSha256,
  durationMs: currentAsset.durationMs, renditionStartOffsetMs: 0, frameTimingPreserved: true,
  preset: DEFAULT_SETTINGS.preset, mapSha256: Object.fromEntries(evidence.maps.map(m => [m.preset, m.sha256])) } as BakedAmbientDocument;
const selection = ambientCoverPredecessor(document, currentAsset, DEFAULT_SETTINGS);
const record = (asset = currentAsset, startMs = 1000): PersonalCoverRecord => ({ version: 1, asset, additions: [{ startMs, endMs: startMs + 100 }] });
const ready = (r = record()): PersonalCoverLoad => ({ status: 'ready', record: r });
it.each(PRESET_NAMES)('the actual exported %s candidate retains the old household timeline', preset => {
  const report = JSON.parse(readFileSync(resolve(__dirname, '../../../results/ambient-export-2026-10-18/verification-report.json'), 'utf8'));
  const candidate: BakedAmbientDocument = JSON.parse(report.presets[preset].metadataRaw);
  const settings = { ...DEFAULT_SETTINGS, preset };
  const old = personalCoverAsset(library.titles(settings)[0])!;
  const current = { ...old, renditionSha256: candidate.renditionSha256 };
  expect(ambientCoverPredecessor(candidate, current, settings)).toEqual({ status: 'required', asset: old });
});
it('keeps current-only storage behavior when no ambient approval exists', () => {
  const current = ready();
  expect(ambientCoverPredecessor(null, currentAsset, DEFAULT_SETTINGS)).toEqual({ status: 'none' });
  expect(combineAmbientCovers(current, { status: 'blocked' }, { status: 'none' })).toBe(current);
});
it.each(PRESET_NAMES)('selects the exact historical rendition for %s', preset => {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const old = personalCoverAsset(library.titles(settings)[0])!;
  const current = { ...old, renditionSha256: 'a'.repeat(64) };
  expect(ambientCoverPredecessor({ ...document, preset }, current, settings)).toEqual({ status: 'required', asset: old });
});
it('blocks mismatched source, rendition, duration, offset, preset, maps or timing proof', () => {
  for (const change of [{ sourceSha256: 'b'.repeat(64) }, { renditionSha256: oldAsset.renditionSha256 },
    { durationMs: 1 }, { renditionStartOffsetMs: 1 }, { titleId: 'another-title' }]) {
    expect(ambientCoverPredecessor(document, { ...currentAsset, ...change }, DEFAULT_SETTINGS).status).toBe('blocked');
  }
  expect(ambientCoverPredecessor(document, undefined, DEFAULT_SETTINGS).status).toBe('blocked');
  expect(ambientCoverPredecessor(document, currentAsset, undefined).status).toBe('blocked');
  for (const change of [{ preset: 'invalid' }, { frameTimingPreserved: false },
    { mapSha256: { wcag: 'b'.repeat(64), broadcast: document.mapSha256.broadcast } }]) {
    expect(ambientCoverPredecessor({ ...document, ...change } as BakedAmbientDocument, currentAsset, DEFAULT_SETTINGS).status).toBe('blocked');
  }
});
it('inherits additions without writing or changing either record', () => {
  const current = ready(), previous = ready(record(oldAsset, 2000));
  const before = JSON.stringify([current, previous]);
  expect(combineAmbientCovers(current, previous, selection)).toEqual({ status: 'ready', record: {
    ...record(), additions: [...record().additions, ...record(oldAsset, 2000).additions] } });
  expect(JSON.stringify([current, previous])).toBe(before);
});
it.each(['loading', 'blocked'] as const)('holds protection while either record is %s', status => {
  expect(combineAmbientCovers({ status }, ready(record(oldAsset)), selection)).toEqual({ status });
  expect(combineAmbientCovers(ready(), { status }, selection)).toEqual({ status });
});
it('blocks selection failures, wrong predecessor records and excessive combined covers', () => {
  expect(combineAmbientCovers(ready(), ready(record(oldAsset)), { status: 'blocked' })).toEqual({ status: 'blocked' });
  expect(combineAmbientCovers(ready(), ready(), selection)).toEqual({ status: 'blocked' });
  const full = { ...record(), additions: Array.from({ length: 32 }, () => ({ startMs: 1000, endMs: 2000 })) };
  expect(combineAmbientCovers(ready(full), ready(record(oldAsset)), selection)).toEqual({ status: 'blocked' });
});
