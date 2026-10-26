import { createHash } from 'crypto';
import { loadBakedAmbient, mayShowBakedAmbient, BakedAmbientState, BakedAmbientDocument } from '../../src/calmframes/bakedAmbient';
import { bakedAmbientForRendition } from '../../src/calmframes/approvedBakedAmbient';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { personalCoverAsset } from '../../src/calmframes/personalCovers';
const hash = (s: string) => s.repeat(64);
const draft = () => ({ version: 1, recipe: 'baked-ambient-v1', sourceSha256: hash('a'), renditionSha256: hash('b'),
  ambientSha256: hash('c'), durationMs: 10000, renditionStartOffsetMs: 0, preset: 'wcag',
  mapSha256: { wcag: hash('d'), broadcast: hash('e') }, intervals: [{ startMs: 1000, endMs: 4000 }],
  audioPreserved: true, frameTimingPreserved: true, analysis: { wcag: hash('f'), broadcast: hash('0') } });
const digest = (raw: string) => createHash('sha512').update(raw).digest('hex');
const load = (value: unknown = draft()) => { const raw = JSON.stringify(value); return loadBakedAmbient(raw, digest(raw)); };
const asset = { titleId: 'test', sourceSha256: hash('a'), renditionSha256: hash('b'), durationMs: 10000, renditionStartOffsetMs: 0 };
const state: BakedAmbientState = { acceptedPreparedRoute: true, verified: true, scheduledCover: true, buffering: false,
  paused: false, opening: false, returning: false, ended: false, error: false, personalCoversReady: true, personalCoverCount: 0 };
const maps = [{ preset: 'wcag', sha256: hash('d') }, { preset: 'broadcast', sha256: hash('e') }];
const show = (doc = load(), s = state, a = asset, spans = draft().intervals, time = 2000, p = 'wcag', m = maps) =>
  mayShowBakedAmbient(doc, a, p, m, spans, time, s);
it.each(PRESET_NAMES)('activates only the exact approved ocean %s rendition and both complete spans', preset => {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const title = packagedLibrary.consumerTitles(settings)[0];
  const identity = personalCoverAsset(title)!;
  const doc = bakedAmbientForRendition(identity.renditionSha256, preset)!;
  const evidence = packagedLibrary.evidenceFor(title, settings)!;
  expect(evidence.bundleId).toBe('0f31fe96f3db5fb4fbae4c0856f3b6091718936255adceb6b2d88a738725ebeb');
  expect(doc).not.toBeNull();
  expect(doc.ambientSha256).toBe('ad315810e01b93be05da5ab59625212d98ceacb37bf43920513e824bf141020d');
  expect(identity.renditionSha256).toBe(preset === 'extra-cautious' ? '8aa6b3566e325b2b89863b221ce2b428ed7ba1ff5abf4cdc41a80ec415121e63' : '07abfc85a4a37291d432e4570d207ae464b3c88608a79922058df47071ed91cc');
  expect(doc.intervals).toHaveLength(2);
  for (const span of doc.intervals) {
    expect(mayShowBakedAmbient(doc, identity, preset, evidence.maps, doc.intervals, span.startMs, state)).toBe(true);
    expect(mayShowBakedAmbient(doc, identity, preset, evidence.maps, doc.intervals, span.endMs, state)).toBe(false);
    expect(mayShowBakedAmbient(doc, identity, preset, evidence.maps, doc.intervals, span.startMs,
      { ...state, personalCoverCount: 1 })).toBe(false);
  }
});
it('only permits reviewed exact metadata, not a route-shaped document or current registry', () => {
  expect(show()).toBe(true);
  expect(show(draft() as BakedAmbientDocument)).toBe(false);
  expect(bakedAmbientForRendition(hash('b'))).toBeNull();
  expect(Object.isFrozen(load()!.intervals[0])).toBe(true);
});
it.each(['acceptedPreparedRoute', 'verified', 'scheduledCover', 'personalCoversReady'] as const)('keeps fallback without %s', key => {
  expect(show(load(), { ...state, [key]: false })).toBe(false);
});
it.each(['buffering', 'paused', 'opening', 'returning', 'ended', 'error'] as const)('keeps fallback during %s', key => {
  expect(show(load(), { ...state, [key]: true })).toBe(false);
});
it('keeps household additions opaque, including unknown storage state', () => {
  expect(show(load(), { ...state, personalCoverCount: 1 })).toBe(false);
  expect(show(load(), { ...state, personalCoverCount: -1 })).toBe(false);
});
it('binds exact rendition, source, duration, timeline, preset, maps and complete base interval list', () => {
  for (const key of ['sourceSha256', 'renditionSha256', 'durationMs', 'renditionStartOffsetMs'] as const) {
    expect(show(load(), state, { ...asset, [key]: typeof asset[key] === 'number' ? 1 : hash('f') })).toBe(false);
  }
  expect(show(load(), state, asset, [{ startMs: 1001, endMs: 4000 }])).toBe(false);
  expect(show(load(), state, asset, [...draft().intervals, { startMs: 5000, endMs: 6000 }])).toBe(false);
  expect(show(load(), state, asset, draft().intervals, 2000, 'broadcast')).toBe(false);
  expect(show(load(), state, asset, draft().intervals, 2000, 'wcag', [])).toBe(false);
  for (const t of [999, 4000, NaN, Infinity]) expect(show(load(), state, asset, draft().intervals, t)).toBe(false);
  expect(show(load(), state, asset, draft().intervals, 1000)).toBe(true);
});
it('rejects tampered bytes, duplicates, missing proof flags, invalid spans and unknown fields', () => {
  const raw = JSON.stringify(draft());
  expect(loadBakedAmbient(raw + ' ', digest(raw))).toBeNull();
  const duplicate = raw.replace('"version":1', '"version":1,"version":1');
  expect(loadBakedAmbient(duplicate, digest(duplicate))).toBeNull();
  for (const delta of [{ audioPreserved: false }, { frameTimingPreserved: false }, { approved: true },
    { intervals: [{ startMs: 4000, endMs: 1000 }] }, { intervals: [] }, { renditionStartOffsetMs: 1 }]) {
    expect(load({ ...draft(), ...delta })).toBeNull();
  }
});
