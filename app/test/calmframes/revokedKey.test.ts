/**
 * A map signed by a key that has been revoked, and what the app does with it.
 *
 * This is the test for the rotation procedure in docs/SECURITY.md. The last
 * step of that procedure says: take a re-signed map and check it against the
 * old public key, and watch it fail, because a rotation nobody has seen fail
 * the old way is a rotation that might not have happened. This is the same
 * claim from the other side, and in code.
 *
 * What makes it a revocation test rather than another signature test: the map
 * here is perfectly valid. It was signed correctly, over the right bytes, by a
 * real key, and it verifies against that key in the first test below. It is
 * refused only because the app has been rebuilt with a different key. Those two
 * situations have to be told apart, because they mean different things to the
 * person reading the card: a broken signature means someone edited the map, and
 * an unknown key means this app does not know who checked it.
 *
 * The fixtures come from scripts/make_revoked_key_fixture.py, which derives both
 * keys from phrases written in the script, so no private key is in this
 * repository and anyone can rebuild them.
 */

import fs from 'fs';
import path from 'path';

import { verifyFlashMap, rejectionMessage } from '../../src/calmframes/flashMap';
import { OFFLINE_PUBLIC_KEY_BASE64 } from '../../src/calmframes/offlineTitle';

const FIXTURES = path.join(__dirname, 'fixtures');
const mapText = fs.readFileSync(
  path.join(FIXTURES, 'revoked_key.flashmap.json'),
  'utf8',
);
const keys = JSON.parse(
  fs.readFileSync(path.join(FIXTURES, 'revoked_key.json'), 'utf8'),
);

const RETIRED_KEY: string = keys.retired.public_key_base64;
const CURRENT_KEY: string = keys.current.public_key_base64;
const SOURCE_SHA256: string = keys.source_sha256;
const MADE_AT = Date.parse(keys.created_utc);

function check(publicKeyBase64: string) {
  return verifyFlashMap(mapText, {
    publicKeyBase64,
    expectedSha256: SOURCE_SHA256,
    // A second after it was made, so staleness plays no part in any of this.
    nowMs: MADE_AT + 1000,
  });
}

describe('a map signed by a revoked key', () => {
  it('is a valid map: it verifies against the key that signed it', () => {
    // If this ever fails, the rest of the file proves nothing, because a map
    // that was already broken would be refused for the wrong reason.
    const verdict = check(RETIRED_KEY);
    expect(verdict.ok).toBe(true);
    if (verdict.ok) {
      expect(verdict.map.segments).toHaveLength(2);
      expect(verdict.map.keyId).toBe(keys.retired.key_id);
    }
  });

  it('is refused once the app carries the key that replaced it', () => {
    const verdict = check(CURRENT_KEY);
    expect(verdict.ok).toBe(false);
    if (!verdict.ok) {
      expect(verdict.reason).toBe('unknown-key');
      expect(verdict.detail).toContain('this app does not hold');
    }
  });

  it('says the right thing to a parent, which is not the signature message', () => {
    const verdict = check(CURRENT_KEY);
    expect(verdict.ok).toBe(false);
    if (!verdict.ok) {
      expect(verdict.reason).toBe('unknown-key');
      const message = rejectionMessage(verdict.reason);
      expect(message).toContain('an unsupported source');
      expect(message).toContain('picture stays hidden');
      // A revoked key is not a tampered map, and the two must not read alike.
      expect(message).not.toBe(rejectionMessage('bad-signature'));
    }
  });

  it('is refused by the key the app really ships with', () => {
    // The two fixture keys are made up. This one is the constant a real build
    // carries, so this is the case that would happen in the world: a map from
    // a key that was never ours.
    const verdict = check(OFFLINE_PUBLIC_KEY_BASE64);
    expect(verdict.ok).toBe(false);
    if (!verdict.ok) {
      expect(verdict.reason).toBe('unknown-key');
    }
  });

  it('is still refused when the map claims the new key id', () => {
    // Revocation cannot rest on a field the attacker controls. The map carries
    // its own key_id and public_key, so a map that lies about both still has to
    // fail, and it fails on the signature, not on the label.
    const document = JSON.parse(mapText);
    document.signature.key_id = keys.current.key_id;
    document.signature.public_key = CURRENT_KEY;
    const verdict = verifyFlashMap(JSON.stringify(document), {
      publicKeyBase64: CURRENT_KEY,
      expectedSha256: SOURCE_SHA256,
      nowMs: MADE_AT + 1000,
    });
    expect(verdict.ok).toBe(false);
    if (!verdict.ok) {
      expect(verdict.reason).toBe('bad-signature');
    }
  });

  it('refuses every title from the revoked key, not just this one', () => {
    // One map is an anecdote. The rule is about the key, so the same map bound
    // to three different files is refused three times for the same reason.
    for (const sha of [
      SOURCE_SHA256,
      'a'.repeat(64),
      '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
    ]) {
      const verdict = verifyFlashMap(mapText, {
        publicKeyBase64: CURRENT_KEY,
        expectedSha256: sha,
        nowMs: MADE_AT + 1000,
      });
      expect(verdict.ok).toBe(false);
      if (!verdict.ok) {
        // The key is checked before the file binding, so even the map that does
        // describe this file is refused as an unknown key rather than as the
        // wrong file. Order matters: the weakest claim is checked last.
        expect(verdict.reason).toBe('unknown-key');
      }
    }
  });
});
