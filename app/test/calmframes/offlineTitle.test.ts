/**
 * The title bundled inside the package.
 *
 * The point of this one is that the three things have to agree: the clip on
 * disk, the map text compiled into the bundle, and the copy of that map shipped
 * as an asset. If any of them drifts, the app would ship a title whose map
 * describes a different file, and the guard would refuse to play it with no
 * obvious reason why.
 */

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import {
  OFFLINE_PUBLIC_KEY_BASE64,
  OFFLINE_VIDEO_PATH,
  offlineTitle,
} from '../../src/calmframes/offlineTitle';

const APP_ROOT = path.join(__dirname, '..', '..');
const clipPath = path.join(APP_ROOT, OFFLINE_VIDEO_PATH);
const assetMapPath = path.join(
  APP_ROOT,
  'assets',
  'raw',
  'offline',
  'calm_gradient.flashmap.json',
);

describe('the bundled offline title', () => {
  it('ships a clip inside the package', () => {
    expect(fs.existsSync(clipPath)).toBe(true);
    const bytes = fs.statSync(clipPath).size;
    // Small enough that bundling it is not a burden, long enough to be a demo.
    expect(bytes).toBeGreaterThan(10_000);
    expect(bytes).toBeLessThan(5_000_000);
  });

  it('compiles in exactly the bytes of the map asset', () => {
    expect(OFFLINE_MAP_JSON).toBe(fs.readFileSync(assetMapPath, 'utf8'));
  });

  it('has a map bound to the clip that actually ships', () => {
    const digest = crypto
      .createHash('sha256')
      .update(fs.readFileSync(clipPath))
      .digest('hex');
    const title = offlineTitle('file:///whatever');
    expect(title.sha256).toBe(digest);
    expect(JSON.parse(OFFLINE_MAP_JSON).source.sha256).toBe(digest);
  });

  it('verifies against the key the app ships, with the real reader', () => {
    const title = offlineTitle('file:///whatever');
    const verdict = verifyFlashMap(title.maps?.wcag, {
      publicKeyBase64: OFFLINE_PUBLIC_KEY_BASE64,
      expectedSha256: title.sha256,
      nowMs: Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 1000,
    });
    expect(verdict.ok).toBe(true);
  });

  it('is a calm clip: the check found nothing to hide', () => {
    const map = JSON.parse(OFFLINE_MAP_JSON);
    expect(map.segments).toEqual([]);
    expect(map.summary.pass).toBe(true);
  });

  it('never ships a private key', () => {
    const offlineDir = path.join(APP_ROOT, 'assets', 'raw', 'offline');
    for (const name of fs.readdirSync(offlineDir)) {
      expect(name).not.toMatch(/\.pem$/);
      expect(name).not.toMatch(/private|secret/i);
    }
    // And the key in the source is a public key, which is 32 raw bytes.
    expect(Buffer.from(OFFLINE_PUBLIC_KEY_BASE64, 'base64')).toHaveLength(32);
  });
});
