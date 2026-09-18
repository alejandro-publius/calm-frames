/**
 * The fail-closed map reader, and the arithmetic it stands on.
 *
 * The fixtures are real: `calm_gradient.flashmap.json` is the signed map for
 * the clip bundled in the package, and `bursts.flashmap.json` was made by
 * flashmap from a generated strobe clip that was deleted in the same job (the
 * safety rule in CLAUDE.md). A map is numbers, not pictures, so keeping it is
 * safe and it gives these tests real segments to work with.
 */

import fs from 'fs';
import path from 'path';
import {
  canonicalBytesWithout,
  canonicalText,
  compareCodePoints,
  nodeToPlain,
  parseJsonNode,
  utf8Bytes,
} from '../../src/calmframes/canonicalJson';
import { verifyEd25519 } from '../../src/calmframes/ed25519';
import {
  DEFAULT_MAX_MAP_AGE_MS,
  parseCreatedUtc,
  rejectionMessage,
  verifyFlashMap,
} from '../../src/calmframes/flashMap';
import { bytesToHex, sha512 } from '../../src/calmframes/sha512';

const FIXTURES = path.join(__dirname, 'fixtures');
const OFFLINE_MAP_PATH = path.join(
  __dirname,
  '..',
  '..',
  'assets',
  'raw',
  'offline',
  'calm_gradient.flashmap.json',
);

const offlineMapText = fs.readFileSync(OFFLINE_MAP_PATH, 'utf8');
const burstsMapText = fs.readFileSync(
  path.join(FIXTURES, 'bursts.flashmap.json'),
  'utf8',
);
const canonicalFixture = JSON.parse(
  fs.readFileSync(path.join(FIXTURES, 'canonical.json'), 'utf8'),
);

const OFFLINE_KEY = '533gF/bCDXyQppRnqiiT41+JwyyUYRN8P4YVZnCbKLQ=';
const OFFLINE_SHA256 =
  'af2934dc45c9519bcace8db253d0a9e0c10f9db6682a04ad2cf3f906e1755224';
const BURSTS_SHA256 = JSON.parse(burstsMapText).source.sha256;
const MADE_AT = Date.parse(JSON.parse(offlineMapText).created_utc);

function verifyOffline(text: string | null, extra: Record<string, unknown> = {}) {
  return verifyFlashMap(text, {
    publicKeyBase64: OFFLINE_KEY,
    expectedSha256: OFFLINE_SHA256,
    nowMs: MADE_AT + 1000,
    ...extra,
  });
}

describe('sha512', () => {
  it('matches the published test vectors', () => {
    expect(bytesToHex(sha512(utf8Bytes('')))).toBe(
      'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce' +
        '47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e',
    );
    expect(bytesToHex(sha512(utf8Bytes('abc')))).toBe(
      'ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a' +
        '2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f',
    );
  });

  it('hashes a message longer than one block', () => {
    const long = 'a'.repeat(1000);
    // Cross-checked against Python hashlib in the same session.
    expect(bytesToHex(sha512(utf8Bytes(long)))).toBe(
      '67ba5535a46e3f86dbfbed8cbbaf0125c76ed549ff8b0b9e03e0c88cf90fa634' +
        'fa7b12b47d77b694de488ace8d9a65967dc96df599727d3292a8d9d447709c97',
    );
  });
});

describe('ed25519 verify', () => {
  // RFC 8032 section 7.1, test vectors 1 and 2.
  const hexToBytes = (hex: string) =>
    Uint8Array.from(hex.match(/../g)!.map((pair) => parseInt(pair, 16)));

  it('accepts the RFC 8032 empty message vector', () => {
    const publicKey = hexToBytes(
      'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a',
    );
    const signature = hexToBytes(
      'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155' +
        '5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b',
    );
    expect(verifyEd25519(signature, new Uint8Array(0), publicKey)).toBe(true);
  });

  it('accepts the RFC 8032 one byte message vector and rejects a changed byte', () => {
    const publicKey = hexToBytes(
      '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c',
    );
    const message = hexToBytes('72');
    const signature = hexToBytes(
      '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da' +
        '085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00',
    );
    expect(verifyEd25519(signature, message, publicKey)).toBe(true);
    expect(verifyEd25519(signature, hexToBytes('73'), publicKey)).toBe(false);
  });

  it('refuses a signature of the wrong length and a scalar at the group order', () => {
    const publicKey = hexToBytes(
      '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c',
    );
    expect(verifyEd25519(new Uint8Array(63), new Uint8Array(0), publicKey)).toBe(
      false,
    );
    const atOrder = new Uint8Array(64);
    // L, little endian, in the S half: RFC 8032 says refuse it.
    atOrder.set(
      hexToBytes('edd3f55c1a631258d69cf7a2def9de1400000000000000000000000000000010'),
      32,
    );
    expect(verifyEd25519(atOrder, new Uint8Array(0), publicKey)).toBe(false);
  });
});

describe('canonical json', () => {
  it('rebuilds exactly the bytes Python signed', () => {
    for (const [name, text] of [
      ['offline', offlineMapText],
      ['bursts', burstsMapText],
    ] as const) {
      const bytes = canonicalBytesWithout(parseJsonNode(text), 'signature');
      expect(bytes.length).toBe(canonicalFixture[name].canonical_bytes);
      expect(bytesToHex(sha512(bytes))).toBe(
        canonicalFixture[name].canonical_sha512,
      );
    }
  });

  it('keeps the way a number was written', () => {
    // 1450.0 parsed and printed by JavaScript would be "1450", which would
    // break every signature made by the Python producer.
    const node = parseJsonNode('{"b":1450.0,"a":1e-3}');
    expect(canonicalText(node)).toBe('{"a":1e-3,"b":1450.0}');
    expect(nodeToPlain(node)).toEqual({ a: 0.001, b: 1450 });
  });

  it('sorts keys by code point and refuses duplicates', () => {
    expect(canonicalText(parseJsonNode('{"b":1,"A":2,"a":3}'))).toBe(
      '{"A":2,"a":3,"b":1}',
    );
    expect(compareCodePoints('A', 'a')).toBeLessThan(0);
    expect(() => parseJsonNode('{"a":1,"a":2}')).toThrow(/duplicate/);
  });

  it('refuses text that is not JSON', () => {
    expect(() => parseJsonNode('{"a":1,}')).toThrow();
    expect(() => parseJsonNode('{"a":01}')).toThrow();
    expect(() => parseJsonNode('{"a":1} trailing')).toThrow();
  });
});

describe('verifyFlashMap', () => {
  it('accepts the signed map bundled in the package', () => {
    const verdict = verifyOffline(offlineMapText);
    expect(verdict.ok).toBe(true);
    if (verdict.ok) {
      expect(verdict.map.segments).toEqual([]);
      expect(verdict.map.source.path).toBe('calm_gradient.mp4');
      expect(verdict.map.profileName).toBe('wcag');
      expect(verdict.map.windows[0].name).toBe('wcag-10deg');
      // WCAG's 10 degree window is 341 of 1024 across, which is a third of the
      // picture whatever the analysis size was.
      expect(verdict.map.windows[0].widthFraction).toBeCloseTo(341 / 1024, 2);
    }
  });

  it('reads the segments of a real map that has some', () => {
    const verdict = verifyFlashMap(burstsMapText, {
      publicKeyBase64: OFFLINE_KEY,
      expectedSha256: BURSTS_SHA256,
      nowMs: Date.parse(JSON.parse(burstsMapText).created_utc) + 1000,
    });
    expect(verdict.ok).toBe(true);
    if (verdict.ok) {
      expect(verdict.map.segments.map((segment) => segment.startMs)).toEqual([
        4367, 14367, 24367,
      ]);
      expect(verdict.map.hiddenMs).toBe(10200);
    }
  });

  // The five cases docs/BUILD_PROMPT.md 4.3 names, one test each.

  it('fails closed when the map is missing', () => {
    for (const nothing of [null, undefined, '', '   ']) {
      const verdict = verifyOffline(nothing as string | null);
      expect(verdict).toMatchObject({ ok: false, reason: 'missing' });
    }
  });

  it('fails closed when the map is stale', () => {
    const verdict = verifyOffline(offlineMapText, {
      nowMs: MADE_AT + DEFAULT_MAX_MAP_AGE_MS + 1,
    });
    expect(verdict).toMatchObject({ ok: false, reason: 'stale' });
    // One millisecond earlier it is still good, so the boundary is where the
    // comment says it is.
    expect(
      verifyOffline(offlineMapText, { nowMs: MADE_AT + DEFAULT_MAX_MAP_AGE_MS }).ok,
    ).toBe(true);
  });

  it('fails closed when the map is unsigned', () => {
    const parsed = JSON.parse(offlineMapText);
    delete parsed.signature;
    expect(verifyOffline(JSON.stringify(parsed))).toMatchObject({
      ok: false,
      reason: 'unsigned',
    });

    const wrongAlgorithm = JSON.parse(offlineMapText);
    wrongAlgorithm.signature.algorithm = 'rsa';
    expect(verifyOffline(JSON.stringify(wrongAlgorithm))).toMatchObject({
      ok: false,
      reason: 'unsigned',
    });
  });

  it('fails closed when the map is unparseable', () => {
    expect(verifyOffline(offlineMapText.slice(0, 200))).toMatchObject({
      ok: false,
      reason: 'unparseable',
    });
    expect(verifyOffline('not json at all')).toMatchObject({
      ok: false,
      reason: 'unparseable',
    });
    expect(verifyOffline('[]')).toMatchObject({
      ok: false,
      reason: 'unparseable',
    });
  });

  it('fails closed when the map is bound to a different file', () => {
    const verdict = verifyOffline(offlineMapText, {
      expectedSha256: 'f'.repeat(64),
    });
    expect(verdict).toMatchObject({ ok: false, reason: 'wrong-file' });
  });

  // Three more ways a map can be wrong, each with the same answer.

  it('fails closed when the map was signed by a key we do not hold', () => {
    const verdict = verifyFlashMap(offlineMapText, {
      publicKeyBase64: canonicalFixture.other_public_key_b64,
      expectedSha256: OFFLINE_SHA256,
      nowMs: MADE_AT + 1000,
    });
    expect(verdict).toMatchObject({ ok: false, reason: 'unknown-key' });
  });

  it('fails closed when one character of the map was changed after signing', () => {
    const tampered = offlineMapText.replace('"pass": true', '"pass": false');
    expect(tampered).not.toBe(offlineMapText);
    expect(verifyOffline(tampered)).toMatchObject({
      ok: false,
      reason: 'bad-signature',
    });
  });

  it('fails closed when a segment is added to a signed map', () => {
    const parsed = JSON.parse(offlineMapText);
    parsed.segments.push({ start_ms: 0, end_ms: 1000, reason: 'general' });
    expect(verifyOffline(JSON.stringify(parsed))).toMatchObject({
      ok: false,
      reason: 'bad-signature',
    });
  });

  it('refuses a version it does not understand', () => {
    const parsed = JSON.parse(offlineMapText);
    parsed.version = 2;
    expect(verifyOffline(JSON.stringify(parsed))).toMatchObject({
      ok: false,
      reason: 'wrong-version',
    });
  });

  it('only accepts UTC timestamps in the shape the spec names', () => {
    expect(parseCreatedUtc('2026-09-17T22:00:00Z')).toBe(
      Date.UTC(2026, 8, 17, 22, 0, 0),
    );
    expect(parseCreatedUtc('2026-09-17 22:00:00')).toBeNull();
    expect(parseCreatedUtc('2026-09-17T22:00:00+02:00')).toBeNull();
    expect(parseCreatedUtc('not a date')).toBeNull();
  });

  it('has plain wording for every rejection', () => {
    for (const reason of [
      'missing',
      'stale',
      'unsigned',
      'unknown-key',
      'bad-signature',
      'wrong-file',
      'wrong-version',
      'unparseable',
    ] as const) {
      const message = rejectionMessage(reason);
      expect(message).toMatch(/picture stays hidden/);
      expect(message).not.toMatch(/[–—]/);
    }
  });
});
