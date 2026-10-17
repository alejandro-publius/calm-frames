import fs from 'fs';
import { generateKeyPairSync, sign } from 'crypto';
import { canonicalBytesWithout, parseJsonNode } from '../../src/calmframes/canonicalJson';
import path from 'path';

const text = fs.readFileSync(path.join(__dirname, '../../assets/raw/offline/calm_gradient.flashmap.json'), 'utf8');
const map = JSON.parse(text);
const options = {
  publicKeyBase64: map.signature.public_key,
  expectedSha256: map.source.sha256,
  nowMs: Date.parse(map.created_utc) + 1000,
};

function freshReader(run: (verify: typeof import('../../src/calmframes/flashMap').verifyFlashMap, crypto: jest.SpyInstance) => void) {
  jest.isolateModules(() => {
    const crypto = require('../../src/calmframes/ed25519');
    const spy = jest.spyOn(crypto, 'verifyEd25519');
    const { verifyFlashMap } = require('../../src/calmframes/flashMap');
    try { run(verifyFlashMap, spy); } finally { spy.mockRestore(); }
  });
}

test('reuses only authentication and still rejects expiry, wrong file and changed trust', () => {
  freshReader((verify, crypto) => {
    expect(verify(text, options).ok).toBe(true);
    expect(verify(text, options).ok).toBe(true);
    expect(crypto).toHaveBeenCalledTimes(1);
    expect(verify(text, { ...options, maxAgeMs: 0 })).toMatchObject({ ok: false, reason: 'stale' });
    expect(verify(text, { ...options, expectedSha256: '0'.repeat(64) })).toMatchObject({ ok: false, reason: 'wrong-file' });
    expect(verify(text, { ...options, publicKeyBase64: 'different' })).toMatchObject({ ok: false, reason: 'unknown-key' });
  });
});

test('changed signed content is checked and failed signatures are never cached', () => {
  freshReader((verify, crypto) => {
    expect(verify(text, options).ok).toBe(true);
    const tampered = JSON.stringify({ ...map, source: { ...map.source, path: 'changed.mp4' } });
    for (let i = 0; i < 2; i++) {
      expect(verify(tampered, options)).toMatchObject({ ok: false, reason: 'bad-signature' });
    }
    expect(crypto).toHaveBeenCalledTimes(3);
  });
});

test('callers cannot mutate a later result through the cache', () => {
  freshReader((verify) => {
    const first = verify(text, options);
    if (!first.ok) throw Error('fixture rejected');
    first.map.source.sha256 = 'changed';
    first.map.segments.push({ startMs: 0, endMs: 1000, reason: 'red' });
    const second = verify(text, options);
    expect(second.ok && second.map.source.sha256).toBe(options.expectedSha256);
    expect(second.ok && second.map.segments).toEqual(map.segments);
  });
});

test('bounded cache evicts old text and verifies it again', () => {
  freshReader((verify, crypto) => {
    for (let i = 0; i < 9; i++) expect(verify(text + ' '.repeat(i), options).ok).toBe(true);
    expect(verify(text, options).ok).toBe(true);
    expect(crypto).toHaveBeenCalledTimes(10);
  });
});

test('large signed text remains uncached', () => {
  freshReader((verify, crypto) => {
    const large = text + ' '.repeat(64 * 1024);
    expect(verify(large, options).ok).toBe(true);
    expect(verify(large, options).ok).toBe(true);
    expect(crypto).toHaveBeenCalledTimes(2);
  });
});

// Ephemeral test keys never enter a catalog or the app's trust configuration.
function signedFixture(overrides: Record<string, unknown> = {}) {
  const keys = generateKeyPairSync('ed25519');
  const publicKey = keys.publicKey.export({ type: 'spki', format: 'der' }).subarray(-32).toString('base64');
  const value = { ...map, ...overrides, signature: { ...map.signature, public_key: publicKey } };
  value.signature.value = sign(null, canonicalBytesWithout(parseJsonNode(JSON.stringify(value)), 'signature'), keys.privateKey).toString('base64');
  return { text: JSON.stringify(value), publicKey };
}

test.each([
  ['signature bytes', { ...map, signature: { ...map.signature, value: Buffer.alloc(64).toString('base64') } }, 'bad-signature'],
  ['payload with the same filename', { ...map, source: { ...map.source, sha256: '0'.repeat(64) } }, 'bad-signature'],
  ['map intervals', { ...map, segments: [{ start_ms: 0, end_ms: 500, reason: 'red' }] }, 'bad-signature'],
  ['algorithm', { ...map, signature: { ...map.signature, algorithm: 'other' } }, 'unsigned'],
  ['version', { ...map, version: 999 }, 'wrong-version'],
  ['signer', { ...map, signature: { ...map.signature, public_key: Buffer.alloc(32).toString('base64') } }, 'unknown-key'],
])('a warm cache still rejects changed %s', (_name, altered, reason) => {
  freshReader((verify) => {
    expect(verify(text, options).ok).toBe(true);
    expect(verify(JSON.stringify(altered), options)).toMatchObject({ ok: false, reason });
  });
});

test('key rotation and removal override warm authentication; the key label grants no trust', () => {
  const rotated = signedFixture();
  freshReader((verify, crypto) => {
    expect(verify(text, options).ok).toBe(true);
    const newTrust = { ...options, publicKeyBase64: rotated.publicKey };
    expect(verify(text, newTrust)).toMatchObject({ ok: false, reason: 'unknown-key' });
    expect(verify(rotated.text, newTrust).ok).toBe(true);
    // Rotated fixture deliberately retains the old key_id label. Only raw public
    // key equality with the caller's current trust anchor can authorize it.
    expect(verify(rotated.text, options)).toMatchObject({ ok: false, reason: 'unknown-key' });
    expect(verify(rotated.text, { ...newTrust, publicKeyBase64: '' })).toMatchObject({ ok: false, reason: 'unknown-key' });
    expect(crypto).toHaveBeenCalledTimes(2);
  });
});

test('clock expiry and file identity are re-evaluated after warming, independent of path', () => {
  freshReader((verify, crypto) => {
    expect(verify(text, options).ok).toBe(true);
    expect(verify(text, { ...options, nowMs: options.nowMs + 91 * 86400000 })).toMatchObject({ ok: false, reason: 'stale' });
    expect(verify(text, { ...options, expectedSha256: 'different-file-with-same-name' })).toMatchObject({ ok: false, reason: 'wrong-file' });
    expect(verify(text, options).ok).toBe(true);
    expect(crypto).toHaveBeenCalledTimes(1);
  });
});

test('authenticated malformed structure never becomes an eligible cached verdict', () => {
  const malformed = signedFixture({ segments: [{ start_ms: 20, end_ms: 10 }] });
  freshReader((verify, crypto) => {
    const trusted = { ...options, publicKeyBase64: malformed.publicKey };
    expect(verify(malformed.text, trusted)).toMatchObject({ ok: false, reason: 'unparseable' });
    expect(verify(malformed.text, trusted)).toMatchObject({ ok: false, reason: 'unparseable' });
    // Authentication can be reused; structure rejection must still run.
    expect(crypto).toHaveBeenCalledTimes(1);
  });
});

test("interleaved callers cannot inherit another caller's identity or trust decisions", async () => {
  let verify!: typeof import('../../src/calmframes/flashMap').verifyFlashMap;
  jest.isolateModules(() => { verify = require('../../src/calmframes/flashMap').verifyFlashMap; });
  const results = await Promise.all(Array.from({ length: 32 }, (_, index) => Promise.resolve().then(() => {
    const input = index % 3 === 0 ? { ...options, expectedSha256: 'wrong' }
      : index % 3 === 1 ? { ...options, publicKeyBase64: '' } : options;
    return { index, result: verify(text, input) };
  })));
  for (const { index, result } of results) {
    if (index % 3 === 2) expect(result.ok).toBe(true);
    else expect(result).toMatchObject({ ok: false, reason: index % 3 === 0 ? 'wrong-file' : 'unknown-key' });
  }
});

test('module reload starts with no persistent authentication cache', () => {
  for (let i = 0; i < 2; i++) freshReader((verify, crypto) => {
    expect(verify(text, options).ok).toBe(true);
    expect(crypto).toHaveBeenCalledTimes(1);
  });
});
