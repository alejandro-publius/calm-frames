/**
 * Finding a map from a file hash, and the ways that has to be refused.
 *
 * The fixtures under `fixtures/registry` are a real signed index and the real
 * signed maps it points at, built by `pipeline/tests/make_registry_fixture.py`
 * with `pipeline/registry.py`, the same code that would build a published one.
 * The two map bodies are real analyzer output already in this repository,
 * re-signed by a key derived from a phrase in that script, because the app can
 * check an Ed25519 signature and cannot make one. There is no private key in
 * the repository. Rebuild them with:
 *
 *     .venv/bin/python pipeline/tests/make_registry_fixture.py
 *
 * `fixtures/registry_swapped_map.json` is a sham, and the name says so. It is
 * the bursts map with its segments taken out and an older date on it, signed by
 * the same key and bound to the same file: what somebody who can serve the maps
 * as well as the index would like to hand back instead of the current map. The
 * index never lists it.
 */

import fs from 'fs';
import path from 'path';
import {
  DEFAULT_MAX_REGISTRY_AGE_MS,
  entryFor,
  isInsideRegistry,
  lookupMap,
  registryRefusalMessage,
  RegistryRefusal,
  resolveMapUrl,
  SUPPORTED_REGISTRY_VERSION,
  verifyRegistry,
} from '../../src/calmframes/mapRegistry';

const FIXTURES = path.join(__dirname, 'fixtures');
const REGISTRY_DIR = path.join(FIXTURES, 'registry');
const BASE_URL = 'https://maps.example/calm-frames/';
const REGISTRY_URL = `${BASE_URL}registry.json`;

/** The public half of the fixture key. The private half is in nobody's tree. */
const KEY = '/brschmFHfvmbulBzPdh2EzwlSOUvAcvXF3X5bNAtJY=';

const registryText = fs.readFileSync(
  path.join(REGISTRY_DIR, 'registry.json'),
  'utf8',
);
const swappedMapText = fs.readFileSync(
  path.join(FIXTURES, 'registry_swapped_map.json'),
  'utf8',
);

const BURSTS_SHA256 =
  '94b63ee75c9873c23df210c82f0e65319b492666fed5383ce647754f46460c5e';
const CALM_SHA256 =
  'af2934dc45c9519bcace8db253d0a9e0c10f9db6682a04ad2cf3f906e1755224';
const MADE_AT = Date.parse(JSON.parse(registryText).created_utc);
const NOW = MADE_AT + 1000;

/** Everything the fixture directory would serve, by URL. */
function served(overrides: Record<string, string | null> = {}) {
  const asked: string[] = [];
  const fetchText = async (url: string): Promise<string | null> => {
    asked.push(url);
    if (Object.prototype.hasOwnProperty.call(overrides, url)) {
      return overrides[url];
    }
    if (!url.startsWith(BASE_URL)) {
      return null;
    }
    const file = path.join(REGISTRY_DIR, url.slice(BASE_URL.length));
    return fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : null;
  };
  return { asked, fetchText };
}

function lookup(
  overrides: Record<string, string | null> = {},
  extra: Record<string, unknown> = {},
) {
  const { asked, fetchText } = served(overrides);
  return {
    asked,
    verdict: lookupMap({
      registryUrl: REGISTRY_URL,
      expectedSha256: BURSTS_SHA256,
      publicKeyBase64: KEY,
      nowMs: NOW,
      fetchText,
      ...extra,
    }),
  };
}

/** Re-sign nothing: just change the served bytes, which is the attack. */
function tampered(change: (document: any) => void): string {
  const document = JSON.parse(registryText);
  change(document);
  return JSON.stringify(document, null, 2);
}

describe('the index itself', () => {
  it('verifies against the key the app holds and lists both files', () => {
    const verdict = verifyRegistry(registryText, {
      publicKeyBase64: KEY,
      nowMs: NOW,
    });
    expect(verdict.ok).toBe(true);
    if (!verdict.ok) {
      return;
    }
    expect(verdict.registry.entries).toHaveLength(2);
    const entry = entryFor(verdict.registry, BURSTS_SHA256, 'wcag');
    expect(entry?.path).toBe('maps/bursts.wcag.json');
    expect(entry?.segmentCount).toBe(3);
    expect(entryFor(verdict.registry, CALM_SHA256, 'wcag')?.segmentCount).toBe(0);
    expect(entryFor(verdict.registry, BURSTS_SHA256, 'broadcast')).toBeNull();
  });

  /**
   * Seen to fail: with the version check made unreachable, the index went on to
   * the signature check and this said:
   *
   *     expect(received).toBe(expected) // Object.is equality
   *     Expected: "registry-wrong-version"
   *     Received: "registry-bad-signature"
   *     at Object.toBe (test/calmframes/mapRegistry.test.ts:137:43)
   */
  it('reads the version this build understands and nothing else', () => {
    expect(SUPPORTED_REGISTRY_VERSION).toBe(1);
    const verdict = verifyRegistry(
      tampered((document) => {
        document.version = 2;
      }),
      { publicKeyBase64: KEY, nowMs: NOW },
    );
    expect(verdict.ok).toBe(false);
    expect(!verdict.ok && verdict.reason).toBe('registry-wrong-version');
  });

  it('refuses a missing, empty or unparseable index', () => {
    for (const text of [null, undefined, '   ']) {
      const verdict = verifyRegistry(text, { publicKeyBase64: KEY, nowMs: NOW });
      expect(!verdict.ok && verdict.reason).toBe('registry-missing');
    }
    const broken = verifyRegistry('{"version": 1, ', {
      publicKeyBase64: KEY,
      nowMs: NOW,
    });
    expect(!broken.ok && broken.reason).toBe('registry-unparseable');
  });

  /**
   * A key we do not hold is not a broken signature, and the two are told apart
   * here the way `revokedKey.test.ts` tells them apart for a map.
   *
   * Seen to fail: with the `indexPublicKey !== options.publicKeyBase64` refusal
   * made unreachable, this said:
   *
   *     expect(received).toBe(expected) // Object.is equality
   *     Expected: "registry-unknown-key"
   *     Received: "registry-bad-signature"
   *     at Object.toBe (test/calmframes/mapRegistry.test.ts:177:45)
   */
  it('refuses an unsigned index and one signed by a key it does not hold', () => {
    const unsigned = verifyRegistry(
      tampered((document) => {
        delete document.signature;
      }),
      { publicKeyBase64: KEY, nowMs: NOW },
    );
    expect(!unsigned.ok && unsigned.reason).toBe('registry-unsigned');

    const stranger = verifyRegistry(registryText, {
      publicKeyBase64: '533gF/bCDXyQppRnqiiT41+JwyyUYRN8P4YVZnCbKLQ=',
      nowMs: NOW,
    });
    expect(!stranger.ok && stranger.reason).toBe('registry-unknown-key');
  });

  /**
   * Seen to fail: with the staleness comparison made unreachable, a year old
   * index was as good as today's and this said:
   *
   *     expect(received).toBe(expected) // Object.is equality
   *     Expected: "registry-stale"
   *     Received: false
   *     at Object.toBe (test/calmframes/mapRegistry.test.ts:195:39)
   */
  it('refuses an index nobody has rebuilt for too long', () => {
    expect(DEFAULT_MAX_REGISTRY_AGE_MS).toBe(30 * 24 * 60 * 60 * 1000);
    const stale = verifyRegistry(registryText, {
      publicKeyBase64: KEY,
      nowMs: MADE_AT + DEFAULT_MAX_REGISTRY_AGE_MS + 1,
    });
    expect(!stale.ok && stale.reason).toBe('registry-stale');
    const inTime = verifyRegistry(registryText, {
      publicKeyBase64: KEY,
      nowMs: MADE_AT + DEFAULT_MAX_REGISTRY_AGE_MS,
    });
    expect(inTime.ok).toBe(true);
  });
});

describe('a tampered index entry', () => {
  /**
   * The one this feature exists for.
   *
   * Seen to fail: with the `verifyEd25519` call in `verifyRegistry` made
   * unreachable, every edit below was believed and this said:
   *
   *     ● a tampered index entry › is refused, and the picture stays hidden
   *       expect(received).toEqual(expected) // deep equality
   *       - Expected  - 1
   *       + Received  + 1
   *         Array [
   *           "points the player at another map",
   *       -   false,
   *       +   true,
   *         ]
   *       at toEqual (test/calmframes/mapRegistry.test.ts:261:34)
   */
  it('is refused, and the picture stays hidden', async () => {
    const edits: Array<[string, (document: any) => void]> = [
      [
        'points the player at another map',
        (document) => {
          document.files[BURSTS_SHA256].maps.wcag.path = 'maps/calm_gradient.wcag.json';
        },
      ],
      [
        'names a different signature',
        (document) => {
          document.files[BURSTS_SHA256].maps.wcag.signature =
            JSON.parse(swappedMapText).signature.value;
        },
      ],
      [
        'says the title has nothing to hide',
        (document) => {
          document.files[BURSTS_SHA256].maps.wcag.segment_count = 0;
          document.files[BURSTS_SHA256].maps.wcag.hidden_ms = 0;
        },
      ],
      [
        'drops the entry for a file that has one',
        (document) => {
          delete document.files[BURSTS_SHA256];
        },
      ],
      [
        'moves the index forward in time',
        (document) => {
          document.created_utc = '2026-09-30T00:00:00Z';
        },
      ],
    ];

    for (const [what, edit] of edits) {
      const text = tampered(edit);
      const verdict = verifyRegistry(text, { publicKeyBase64: KEY, nowMs: NOW });
      expect([what, verdict.ok]).toEqual([what, false]);
      expect(!verdict.ok && verdict.reason).toBe('registry-bad-signature');

      const done = await lookupMap({
        registryUrl: REGISTRY_URL,
        expectedSha256: BURSTS_SHA256,
        publicKeyBase64: KEY,
        nowMs: NOW,
        fetchText: async (url) => (url === REGISTRY_URL ? text : null),
      });
      expect(done.ok).toBe(false);
      expect(!done.ok && registryRefusalMessage(done.reason)).toContain(
        'the picture stays hidden',
      );
    }
  });

  it('cannot be repaired by re-signing with another key', async () => {
    // The same index, read by the key that signed it and then by another.
    const { verdict } = lookup({}, { publicKeyBase64: KEY });
    expect((await verdict).ok).toBe(true);
    const wrongKey = await lookupMap({
      registryUrl: REGISTRY_URL,
      expectedSha256: BURSTS_SHA256,
      publicKeyBase64: '533gF/bCDXyQppRnqiiT41+JwyyUYRN8P4YVZnCbKLQ=',
      nowMs: NOW,
      fetchText: served().fetchText,
    });
    expect(!wrongKey.ok && wrongKey.reason).toBe('registry-unknown-key');
  });
});

describe('the lookup', () => {
  it('hands back a verified map for a file the index lists', async () => {
    const { verdict, asked } = lookup();
    const done = await verdict;
    expect(done.ok).toBe(true);
    if (!done.ok) {
      return;
    }
    expect(done.mapUrl).toBe(`${BASE_URL}maps/bursts.wcag.json`);
    expect(done.map.source.sha256).toBe(BURSTS_SHA256);
    expect(done.map.segments).toHaveLength(3);
    expect(done.entry.hiddenMs).toBe(10200);
    expect(asked).toEqual([REGISTRY_URL, `${BASE_URL}maps/bursts.wcag.json`]);
  });

  it('hands back a clean map as a map, not as a refusal', async () => {
    const { verdict } = lookup({}, { expectedSha256: CALM_SHA256 });
    const done = await verdict;
    expect(done.ok).toBe(true);
    expect(done.ok && done.map.segments).toEqual([]);
  });

  it('refuses a file the index does not list', async () => {
    const { verdict, asked } = lookup(
      {},
      { expectedSha256: 'f'.repeat(64) },
    );
    const done = await verdict;
    expect(!done.ok && done.reason).toBe('not-listed');
    // Nothing was fetched but the index itself.
    expect(asked).toEqual([REGISTRY_URL]);
  });

  /**
   * Seen to fail: with `entryFor` matching on the hash alone, the wcag map came
   * back for a broadcast lookup and this said:
   *
   *     ● the lookup › refuses a profile the index does not list for that file
   *       expect(received).toBe(expected) // Object.is equality
   *       Expected: "not-listed"
   *       Received: false
   *       at Object.toBe (test/calmframes/mapRegistry.test.ts:339:37)
   */
  it('refuses a profile the index does not list for that file', async () => {
    const { verdict } = lookup({}, { profile: 'broadcast' });
    const done = await verdict;
    expect(!done.ok && done.reason).toBe('not-listed');
  });

  /**
   * Seen to fail: with the `mapSignatureValue(...) !== entry.signature`
   * refusal made unreachable, the older map was accepted and this said:
   *
   *     ● the lookup › refuses a validly signed map that is not the one listed
   *       expect(received).toBe(expected) // Object.is equality
   *       Expected: "not-the-listed-map"
   *       Received: false
   *       at Object.toBe (test/calmframes/mapRegistry.test.ts:357:37)
   */
  it('refuses a validly signed map that is not the one listed', async () => {
    const { verdict } = lookup({
      [`${BASE_URL}maps/bursts.wcag.json`]: swappedMapText,
    });
    const done = await verdict;
    expect(!done.ok && done.reason).toBe('not-the-listed-map');
    expect(!done.ok && registryRefusalMessage(done.reason)).toContain(
      'the picture stays hidden',
    );
  });

  /**
   * The index says a map exists. What comes back still goes through the map
   * reader, whole.
   *
   * Seen to fail: with the `!mapVerdict.ok` branch made unreachable, a map that
   * was not there at all got past and was caught later, by the wrong check:
   *
   *     ● the lookup › refuses a map that is missing, or made for another file
   *       expect(received).toBe(expected) // Object.is equality
   *       Expected: "map-refused"
   *       Received: "not-the-listed-map"
   *       at Object.toBe (test/calmframes/mapRegistry.test.ts:380:43)
   */
  it('refuses a map that is missing, or made for another file', async () => {
    const missing = await lookup({
      [`${BASE_URL}maps/bursts.wcag.json`]: null,
    }).verdict;
    expect(!missing.ok && missing.reason).toBe('map-refused');
    expect(!missing.ok && missing.mapRejection).toBe('missing');

    const otherFile = await lookup({
      [`${BASE_URL}maps/bursts.wcag.json`]: fs.readFileSync(
        path.join(REGISTRY_DIR, 'maps', 'calm_gradient.wcag.json'),
        'utf8',
      ),
    }).verdict;
    expect(!otherFile.ok && otherFile.mapRejection).toBe('wrong-file');
    expect(
      !otherFile.ok && registryRefusalMessage(otherFile.reason, otherFile.mapRejection),
    ).toContain('belongs to a different file');
  });

  it('passes the staleness bound through to the map reader', async () => {
    const done = await lookup({}, { maxMapAgeMs: 1 }).verdict;
    expect(!done.ok && done.mapRejection).toBe('stale');
  });
});

describe('an entry path', () => {
  /**
   * Seen to fail: with `isInsideRegistry` returning true for everything, this
   * said:
   *
   *     ● an entry path › that leaves the index is refused without being
   *       fetched
   *       expect(received).toBe(expected) // Object.is equality
   *       Expected: false
   *       Received: true
   *       at Object.toBe (test/calmframes/mapRegistry.test.ts:422:37)
   */
  it('that leaves the index is refused without being fetched', async () => {
    for (const bad of [
      'https://elsewhere.example/evil.json',
      '//elsewhere.example/evil.json',
      '/etc/passwd',
      '../../outside/map.json',
      'maps\\wcag.json',
      '',
    ]) {
      expect(isInsideRegistry(bad)).toBe(false);
      expect(resolveMapUrl(REGISTRY_URL, bad)).toBeNull();
    }
    expect(resolveMapUrl(REGISTRY_URL, 'maps/wcag.json')).toBe(
      `${BASE_URL}maps/wcag.json`,
    );
    expect(resolveMapUrl(`${REGISTRY_URL}?v=2`, 'maps/wcag.json')).toBe(
      `${BASE_URL}maps/wcag.json`,
    );

    const text = tampered((document) => {
      document.files[BURSTS_SHA256].maps.wcag.path =
        'https://elsewhere.example/evil.json';
    });
    const asked: string[] = [];
    const done = await lookupMap({
      registryUrl: REGISTRY_URL,
      expectedSha256: BURSTS_SHA256,
      publicKeyBase64: KEY,
      nowMs: NOW,
      fetchText: async (url) => {
        asked.push(url);
        return url === REGISTRY_URL ? text : null;
      },
    });
    // The index signature catches the edit first, which is the point of
    // signing it. The path check is the second lock: it holds for an index
    // built by something other than our builder, and it is checked before
    // anything is fetched.
    expect(!done.ok && done.ok).toBe(false);
    expect(asked).toEqual([REGISTRY_URL]);
  });
});

describe('the wording', () => {
  it('says the picture stays hidden for every refusal there is', () => {
    const reasons: RegistryRefusal[] = [
      'registry-missing',
      'registry-unparseable',
      'registry-wrong-version',
      'registry-unsigned',
      'registry-unknown-key',
      'registry-bad-signature',
      'registry-stale',
      'not-listed',
      'entry-unusable',
      'map-refused',
      'not-the-listed-map',
    ];
    for (const reason of reasons) {
      expect(registryRefusalMessage(reason)).toContain('the picture stays hidden');
    }
    expect(registryRefusalMessage('map-refused', 'bad-signature')).toContain(
      'changed after it was signed',
    );
  });
});
