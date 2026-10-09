import { PACKAGED_LIBRARY_JSON } from '../../assets/raw/prepared-library/catalog';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { createPackagedLibrary, packagedLibrary } from '../../src/calmframes/packagedLibrary';
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
  it.each(PRESET_NAMES)('verifies the real imported source and chooses its %s rendition', (preset) => {
    const { entry, settings, data, guarded } = checked(preset);
    expect(packagedLibrary.problem).toBeNull();
    expect(entry.status).toBe('verified');
    expect(entry.segments).toEqual([]);
    expect(entry.title.sha256).toBe(manifest.titles[0].sourceSha256);
    expect(entry.title.renditionSha256).toBe(manifest.titles[0].renditions[preset].sha256);
    expect(entry.title.uri).toMatch(new RegExp(`/${preset}\\.mp4$`));
    expect(entry.title.textTrack?.[0].uri).toMatch(new RegExp(`/${preset}\\.vtt$`));
    expect(defaultCatalog(settings)).toContainEqual(entry.title);
    expect(packagedLibrary.acceptsRoute(data, guarded)).toBe(true);
  });

  it.each(['id', 'uri', 'sha256', 'durationMs', 'renditionSha256', 'renditionStartOffsetMs', 'maps', 'textTrack'])(
    'does not grant the compiled signer to a substituted %s', (field) => {
      const { entry, settings } = checked();
      const changed = { ...entry.title, [field]: 'substituted' };
      expect(packagedLibrary.publicKeyFor(changed, settings)).toBeNull();
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

  it('allows an intentionally empty build without inventing a key', () => {
    const empty = createPackagedLibrary('{"version":1,"titles":[]}');
    expect(empty.problem).toBeNull();
    expect(empty.titles(DEFAULT_SETTINGS)).toEqual([]);
    expect(empty.publicKeyBase64).toBe('');
  });
});
