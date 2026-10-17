import fs from 'fs';
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
