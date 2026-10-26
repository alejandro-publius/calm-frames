/**
 * The bundled hold stills are the signed stills, byte for byte.
 *
 * Break it: edit one byte of a file under app/assets/raw/benign-story/stills,
 * or change a sha256 in benignStoryStills.ts, and the hash test names it.
 */
import { createHash } from 'crypto';
import { existsSync, readFileSync } from 'fs';
import path from 'path';
import { BENIGN_STORY_MAPS } from '../../src/calmframes/benignStoryData';
import { BENIGN_STORY_STILLS } from '../../src/calmframes/benignStoryStills';
import { bundledStillFor } from '../../src/calmframes/bundledStills';

const PREFIX = 'data:image/jpeg;base64,';

function holdsOf(profile: string): Array<{ start_ms: number; end_ms: number; image_data_uri: string }> {
  const map = JSON.parse(BENIGN_STORY_MAPS[profile]);
  const holds = map.scene_holds?.holds ?? map.holds;
  expect(Array.isArray(holds)).toBe(true);
  return holds;
}

function sha256(bytes: Buffer): string {
  return createHash('sha256').update(bytes).digest('hex');
}

/**
 * The jest asset transformer turns require('x.jpg') into { testUri }, a path
 * relative to the transformer's own directory, so resolve from there.
 */
function bytesOf(source: unknown): Buffer {
  const uri = (source as { testUri?: string }).testUri;
  expect(typeof uri).toBe('string');
  const app = path.resolve(__dirname, '../..');
  const candidates = [
    path.resolve(app, 'node_modules/react-native/jest', uri as string),
    path.resolve(app, 'node_modules/@amazon-devices/react-native-kepler/jest', uri as string),
    path.resolve(__dirname, uri as string),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  expect(file).toBeDefined();
  return readFileSync(file as string);
}

describe('the bundled practice stills', () => {
  it.each(Object.keys(BENIGN_STORY_STILLS))('cover every hold of the %s map with the same bytes the map signed', (profile) => {
    const holds = holdsOf(profile);
    expect(holds.length).toBeGreaterThan(0);
    for (const hold of holds) {
      const entry = BENIGN_STORY_STILLS[profile].find((e) => e.startMs === hold.start_ms && e.endMs === hold.end_ms);
      expect(entry).toBeDefined();
      expect(hold.image_data_uri.startsWith(PREFIX)).toBe(true);
      const signed = Buffer.from(hold.image_data_uri.slice(PREFIX.length), 'base64');
      expect(sha256(signed)).toBe(entry!.sha256);
      expect(sha256(bytesOf(entry!.source))).toBe(entry!.sha256);
    }
    expect(BENIGN_STORY_STILLS[profile]).toHaveLength(holds.length);
  });

  it('resolve from the exact authenticated data URI and from nothing else', () => {
    for (const profile of Object.keys(BENIGN_STORY_STILLS)) {
      for (const hold of holdsOf(profile)) {
        const entry = BENIGN_STORY_STILLS[profile].find((e) => e.startMs === hold.start_ms)!;
        expect(bundledStillFor(hold.image_data_uri)).toBe(entry.source);
        expect(bundledStillFor(hold.image_data_uri + '=')).toBeUndefined();
      }
    }
    expect(bundledStillFor(undefined)).toBeUndefined();
    expect(bundledStillFor(PREFIX + 'AAAA')).toBeUndefined();
  });
});
