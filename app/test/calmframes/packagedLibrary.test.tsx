import { PACKAGED_LIBRARY_JSON } from '../../assets/raw/prepared-library/catalog';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { ACADIA_SOURCE_SHA256, createApprovedAcadiaLibrary, createApprovedLibrary, createPackagedLibrary, packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { PACKAGED_LIBRARY_JSON as ACADIA_LIBRARY_JSON } from '../../src/calmframes/acadiaCatalog';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { defaultCatalog, guardedParamsFor, titleDataFor } from '../../src/screens/KidModeScreen';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined),
}));

const manifest = JSON.parse(PACKAGED_LIBRARY_JSON);
const nowMs = Date.parse(JSON.parse(manifest.titles[0].maps.wcag.text).created_utc) + 1000;
function checked(preset = DEFAULT_SETTINGS.preset) {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const title = packagedLibrary.titles(settings)[0];
  const entry = checkTitle(title, { settings, nowMs,
    publicKeyBase64: packagedLibrary.publicKeyFor(title, settings) ?? '' });
  return { entry, settings, data: titleDataFor(entry), guarded: guardedParamsFor(entry, settings) };
}

describe('the compiled prepared library', () => {
  it('uses the exact reviewed consumer registry and never promotes a runtime catalog', () => {
    expect(packagedLibrary.consumerTitles(DEFAULT_SETTINGS).map(title => title.sha256)).toEqual([ACADIA_SOURCE_SHA256]);
    expect(createApprovedLibrary(ACADIA_LIBRARY_JSON).problem).toBeNull();
    expect(createApprovedLibrary(ACADIA_LIBRARY_JSON + ' ').titles(DEFAULT_SETTINGS)).toEqual([]);
    expect(createApprovedLibrary(PACKAGED_LIBRARY_JSON).titles(DEFAULT_SETTINGS)).toEqual([]);
    const changed = JSON.parse(ACADIA_LIBRARY_JSON);
    changed.publicKeyBase64 = manifest.publicKeyBase64;
    expect(createApprovedLibrary(JSON.stringify(changed)).titles(DEFAULT_SETTINGS)).toEqual([]);
  });
  it.each(PRESET_NAMES)('isolates the approved Acadia key and exact %s route from Harbor', preset => {
    const settings = { ...DEFAULT_SETTINGS, preset };
    const title = packagedLibrary.titles(settings).find(one => one.sha256 === ACADIA_SOURCE_SHA256)!;
    const acadia = JSON.parse(ACADIA_LIBRARY_JSON);
    const key = packagedLibrary.publicKeyFor(title, settings)!;
    expect(key).toBe(acadia.publicKeyBase64);
    expect(key).not.toBe(manifest.publicKeyBase64);
    const entry = checkTitle(title, { settings, nowMs: Date.parse('2026-10-16T00:00:00Z'), publicKeyBase64: key });
    expect(entry.status).toBe('verified');
    expect(entry.segments.length).toBeGreaterThan(0);
    const data = titleDataFor(entry);
    const guarded = guardedParamsFor(entry, settings);
    expect(packagedLibrary.publicKeyForRoute(data, guarded)).toBe(key);
    const harbor = checked(preset);
    expect(packagedLibrary.publicKeyForRoute(harbor.data, harbor.guarded)).toBe(manifest.publicKeyBase64);
    expect(packagedLibrary.publicKeyForRoute(data, { ...guarded, maps: harbor.guarded.maps })).toBeNull();
    expect(packagedLibrary.publicKeyForRoute({ ...data, uri: harbor.data.uri }, guarded)).toBeNull();
    expect(packagedLibrary.publicKeyFor({ ...title, renditionSha256: '0'.repeat(64) }, settings)).toBeNull();
    expect(packagedLibrary.evidenceFor(title, settings)?.reportSha256).toBe(acadia.titles[0].verification.reportSha256);
  });

  it.each(['bundleId', 'publicKeyBase64', 'title', 'whitespace'])('does not extend Acadia approval to a changed %s catalog', change => {
    const bad = JSON.parse(ACADIA_LIBRARY_JSON);
    if (change === 'bundleId') bad.bundleId = 'a'.repeat(64);
    if (change === 'publicKeyBase64') bad.publicKeyBase64 = manifest.publicKeyBase64;
    if (change === 'title') bad.titles[0].title = 'Substituted';
    const raw = change === 'whitespace' ? ACADIA_LIBRARY_JSON + ' ' : JSON.stringify(bad);
    expect(createApprovedAcadiaLibrary(raw).titles(DEFAULT_SETTINGS)).toEqual([]);
    expect(createApprovedAcadiaLibrary(ACADIA_LIBRARY_JSON).problem).toBeNull();
  });
  it.each(PRESET_NAMES)('verifies the real imported source and chooses its %s rendition', (preset) => {
    const { entry, settings, data, guarded } = checked(preset);
    expect(packagedLibrary.problem).toBeNull();
    expect(entry.status).toBe('verified');
    expect(entry.segments).toEqual([]);
    expect(entry.title.sha256).toBe(manifest.titles[0].sourceSha256);
    expect(entry.title.renditionSha256).toBe(manifest.titles[0].renditions[preset].sha256);
    expect(entry.title.uri).toMatch(new RegExp(`/${preset}\\.mp4$`));
    expect(entry.title.textTrack?.[0].uri).toMatch(new RegExp(`/${preset}\\.vtt$`));
    // Harbor remains verified for regression use, outside the consumer catalog.
    expect(defaultCatalog(settings)).not.toContainEqual(entry.title);
    expect(packagedLibrary.acceptsRoute(data, guarded)).toBe(true);
  });

  it.each(['id', 'uri', 'sha256', 'durationMs', 'renditionSha256', 'renditionStartOffsetMs', 'maps', 'textTrack'])(
    'does not grant the compiled signer to a substituted %s', (field) => {
      const { entry, settings } = checked();
      const changed = { ...entry.title, [field]: 'substituted' };
      expect(packagedLibrary.publicKeyFor(changed, settings)).toBeNull();
      expect(packagedLibrary.evidenceFor(changed, settings)).toBeNull();
    });

  it.each(['sha256', 'durationMs', 'renditionSha256', 'renditionStartOffsetMs', 'titleId', 'maps'])(
    'rejects a playback route with substituted %s', (field) => {
      const { data, guarded } = checked();
      expect(packagedLibrary.acceptsRoute(data, { ...guarded, [field]: 'substituted' })).toBe(false);
    });

  it('refuses remote maps, captions, cross-preset rendition substitution and an unguarded route', () => {
    const { data, guarded } = checked();
    expect(packagedLibrary.acceptsRoute(data)).toBe(false);
    expect(packagedLibrary.acceptsRoute(data, { ...guarded, mapUrls: {} })).toBe(false);
    expect(packagedLibrary.acceptsRoute({ ...data, uri: 'https://example.invalid/source.mp4' }, guarded)).toBe(false);
    expect(packagedLibrary.acceptsRoute({ ...data, textTrack: [] }, guarded)).toBe(false);
    expect(packagedLibrary.acceptsRoute(data, { ...guarded,
      settings: { ...guarded.settings, preset: 'extra-cautious' } })).toBe(false);
  });

  it.each(['path', 'inventory', 'timing', 'key', 'duplicate', 'missing-preset'])(
    'closes a malformed compiled catalog: %s', (change) => {
      const bad = JSON.parse(PACKAGED_LIBRARY_JSON);
      if (change === 'path') bad.titles[0].renditions.wcag.path = '../source.mp4';
      if (change === 'inventory') bad.files['extra.mp4'] = 'a'.repeat(64);
      if (change === 'timing') bad.titles[0].renditions['extra-cautious'].guardBandMs = 500;
      if (change === 'key') bad.publicKeyBase64 = 'invalid';
      if (change === 'duplicate') bad.titles.push(bad.titles[0]);
      if (change === 'missing-preset') delete bad.titles[0].maps.broadcast;
      const rejected = createPackagedLibrary(JSON.stringify(bad));
      expect(rejected.problem).not.toBeNull();
      expect(rejected.titles(DEFAULT_SETTINGS)).toEqual([]);
    });

  it.each(PRESET_NAMES)('binds displayed evidence to the exact %s playback rendition', preset => {
    const { entry, settings, data, guarded } = checked(preset);
    const evidence = packagedLibrary.evidenceFor(entry.title, settings)!;
    expect(evidence.sourceSha256).toBe(guarded.sha256);
    expect(evidence.renditionSha256).toBe(guarded.renditionSha256);
    expect(evidence.renditionPath).toBe(data.uri);
    expect(evidence.reportSha256).toBe(manifest.titles[0].verification.reportSha256);
    expect(evidence.checkedInputsSha256).toBe(manifest.titles[0].verification.checkedInputsSha256);
    expect(evidence.maps).toEqual(PRESET_NAMES.map(name => ({ preset: name, sha256: manifest.titles[0].maps[name].sha256 })));
    evidence.sourceSha256 = 'altered';
    expect(packagedLibrary.evidenceFor(entry.title, settings)?.sourceSha256).toBe(guarded.sha256);
  });

  it('allows an intentionally empty build without inventing a key', () => {
    const empty = createPackagedLibrary('{"version":1,"titles":[]}');
    expect(empty.problem).toBeNull();
    expect(empty.titles(DEFAULT_SETTINGS)).toEqual([]);
    expect(empty.publicKeyBase64).toBe('');
  });
});
