/** Runtime-only signing with the same public test key as eval/fuzz_maps.py. */
import { createHash, createPrivateKey, createPublicKey, sign } from 'crypto';
import {
  canonicalBytesWithout,
  parseJsonNode,
} from '../../src/calmframes/canonicalJson';

const seed = createHash('sha256')
  .update('calm frames fuzz corpus, not a secret')
  .digest();
const privateKey = createPrivateKey({
  key: Buffer.concat([
    Buffer.from('302e020100300506032b657004220420', 'hex'),
    seed,
  ]),
  format: 'der',
  type: 'pkcs8',
});
export const SCENE_KEY = createPublicKey(privateKey)
  .export({ type: 'spki', format: 'der' })
  .subarray(-32)
  .toString('base64');
export const SCENE_SHA = 'a'.repeat(64);
export const SCENE_NOW = Date.parse('2026-09-01T00:00:01Z');

/** JPEG marker envelope for unit tests, not a playable or published image. */
export function jpegEnvelope(width = 1, height = 1, tag = 0): string {
  const bytes = Buffer.from([
    0xff,
    0xd8,
    0xff,
    0xe0,
    0,
    4,
    0,
    tag,
    0xff,
    0xc0,
    0,
    11,
    8,
    Math.floor(height / 256),
    height % 256,
    Math.floor(width / 256),
    width % 256,
    1,
    1,
    0x11,
    0,
    0xff,
    0xd9,
  ]);
  return `data:image/jpeg;base64,${bytes.toString('base64')}`;
}

export function sceneMap() {
  return {
    version: 1,
    created_utc: '2026-09-01T00:00:00Z',
    source: {
      path: 'numbers-only-fixture.mp4',
      sha256: SCENE_SHA,
      duration_ms: 30_000,
    },
    profile: {
      name: 'wcag',
      area_windows: [{ name: 'wcag-10deg', width_px: 32 }],
    },
    picture: { width: 640, height: 360 },
    summary: { hidden_ms: 4000 },
    segments: [
      { start_ms: 5000, end_ms: 7000, reason: 'red' },
      { start_ms: 15000, end_ms: 17000, reason: 'general' },
    ],
    scene_holds: {
      version: 1,
      holds: [
        {
          start_ms: 4500,
          end_ms: 7500,
          frame_ms: 4000,
          image_data_uri: jpegEnvelope(),
        },
        {
          start_ms: 14500,
          end_ms: 17500,
          frame_ms: 14000,
          image_data_uri: jpegEnvelope(1, 1, 1),
        },
      ],
    },
  };
}

export function signSceneMap(document: Record<string, unknown>): string {
  const plainText = JSON.stringify(document);
  const payload = canonicalBytesWithout(parseJsonNode(plainText), 'signature');
  return JSON.stringify({
    ...document,
    signature: {
      algorithm: 'ed25519',
      public_key: SCENE_KEY,
      key_id: 'fuzz-scenes-only',
      value: sign(null, Buffer.from(payload), privateKey).toString('base64'),
    },
  });
}
