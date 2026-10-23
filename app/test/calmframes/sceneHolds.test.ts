import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import {
  MAX_SCENE_HOLD_BYTES,
  MAX_SCENE_HOLD_ENCODED_TOTAL,
  MAX_SCENE_MAP_TEXT_LENGTH,
  readSceneHolds,
  sceneHoldForInterval,
} from '../../src/calmframes/sceneHolds';
import {
  jpegEnvelope,
  SCENE_KEY,
  SCENE_NOW,
  SCENE_SHA,
  sceneMap,
  signSceneMap,
} from './sceneHoldFixtures';

const verify = (text: string) =>
  verifyFlashMap(text, {
    publicKeyBase64: SCENE_KEY,
    expectedSha256: SCENE_SHA,
    nowMs: SCENE_NOW,
  });

describe('signed scene holds', () => {
  it('authenticates optional images and keeps legacy and empty maps valid', () => {
    const map = sceneMap();
    expect(verify(signSceneMap(map))).toMatchObject({
      ok: true,
      map: {
        sceneHolds: [
          {
            startMs: 4500,
            endMs: 7500,
            frameMs: 4000,
            imageDataUri: jpegEnvelope(),
          },
          { startMs: 14500, endMs: 17500 },
        ],
      },
    });
    const legacy = { ...map } as Record<string, unknown>;
    delete legacy.scene_holds;
    expect(verify(signSceneMap(legacy))).toMatchObject({
      ok: true,
      map: { sceneHolds: [] },
    });
    map.scene_holds.holds = [];
    expect(verify(signSceneMap(map))).toMatchObject({
      ok: true,
      map: { sceneHolds: [] },
    });
  });

  it('refuses image bytes changed after signing', () => {
    const signed = signSceneMap(sceneMap());
    const changed = signed.replace(jpegEnvelope(), jpegEnvelope(1, 1, 2));
    expect(changed).not.toBe(signed);
    expect(verify(changed)).toMatchObject({
      ok: false,
      reason: 'bad-signature',
    });
  });

  it.each([
    [
      'unknown version',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.version = 2;
      },
    ],
    [
      'negative start',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].start_ms = -1;
      },
    ],
    [
      'reversed bounds',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].end_ms = 4000;
      },
    ],
    [
      'past the title',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[1].end_ms = 30001;
      },
    ],
    [
      'overlap',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[1].start_ms = 7000;
      },
    ],
    [
      'future frame',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].frame_ms = 4501;
      },
    ],
    [
      'frame at cover start',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].frame_ms = 4500;
      },
    ],
    [
      'frame too far back',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[1].frame_ms = 9499;
      },
    ],
    [
      'negative frame',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].frame_ms = -1;
      },
    ],
    [
      'flagged source frame',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[1].frame_ms = 6000;
      },
    ],
    [
      'no matching segment',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].end_ms = 4900;
      },
    ],
    [
      'remote URL',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri =
          'https://example.invalid/still.jpg';
      },
    ],
    [
      'other data MIME',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri =
          'data:image/png;base64,/9j/2Q==';
      },
    ],
    [
      'malformed base64',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri = 'data:image/jpeg;base64,%%%=';
      },
    ],
    [
      'not a JPEG',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri = 'data:image/jpeg;base64,AAAA';
      },
    ],
    [
      'missing dimensions',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri =
          'data:image/jpeg;base64,/9j/2Q==';
      },
    ],
    [
      'large decoded dimensions',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri = jpegEnvelope(1281, 1);
      },
    ],
    [
      'zero dimension',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds[0].image_data_uri = jpegEnvelope(0, 1);
      },
    ],
    [
      'too many holds',
      (map: ReturnType<typeof sceneMap>) => {
        map.scene_holds.holds = Array(33).fill(map.scene_holds.holds[0]);
      },
    ],
  ])('fails closed for a signed %s field', (_name, mutate) => {
    const map = sceneMap();
    mutate(map);
    expect(verify(signSceneMap(map))).toMatchObject({
      ok: false,
      reason: 'unparseable',
    });
  });

  it('rejects malformed optional objects rather than treating them as legacy', () => {
    const map = sceneMap();
    for (const scene_holds of [
      null,
      [],
      true,
      { version: 1 },
      { version: 1, holds: [null] },
    ]) {
      expect(verify(signSceneMap({ ...map, scene_holds }))).toMatchObject({
        ok: false,
        reason: 'unparseable',
      });
    }
  });

  it('accepts a preceding frame exactly five seconds back and an explicit neutral card', () => {
    const map = sceneMap();
    map.scene_holds.holds[1].frame_ms = 9500;
    expect(verify(signSceneMap(map))).toMatchObject({ ok: true });
    const neutral = {
      ...map,
      scene_holds: {
        version: 1,
        holds: [{ ...map.scene_holds.holds[0], frame_ms: null }],
      },
    };
    expect(verify(signSceneMap(neutral))).toMatchObject({ ok: true });
  });

  it('bounds image allocations and total text before signature work', () => {
    const map = sceneMap();
    map.scene_holds.holds[0].image_data_uri = `data:image/jpeg;base64,${Buffer.alloc(
      MAX_SCENE_HOLD_BYTES + 1,
    ).toString('base64')}`;
    const segments = map.segments.map((one) => ({
      startMs: one.start_ms,
      endMs: one.end_ms,
    }));
    expect(readSceneHolds(map.scene_holds, segments, 30000)).toBeNull();
    expect(verify('x'.repeat(MAX_SCENE_MAP_TEXT_LENGTH + 1))).toMatchObject({
      ok: false,
      reason: 'unparseable',
    });
    // Each descriptor is individually bounded; the aggregate limit is separate.
    const header = Buffer.from(jpegEnvelope().split(',')[1], 'base64');
    const bounded = Buffer.concat([
      header.subarray(0, -2),
      Buffer.alloc(MAX_SCENE_HOLD_BYTES - header.length),
      header.subarray(-2),
    ]);
    const image = `data:image/jpeg;base64,${bounded.toString('base64')}`;
    const holds = Array.from({ length: 13 }, (_, index) => ({
      start_ms: index * 10000,
      end_ms: index * 10000 + 9000,
      frame_ms: null,
      image_data_uri: image,
    }));
    expect(
      holds.reduce((sum, hold) => sum + hold.image_data_uri.length, 0),
    ).toBeGreaterThan(MAX_SCENE_HOLD_ENCODED_TOTAL);
    const matchingSegments = holds.map((hold) => ({
      startMs: hold.start_ms + 500,
      endMs: hold.end_ms - 500,
    }));
    expect(
      readSceneHolds({ version: 1, holds }, matchingSegments, null),
    ).toBeNull();
  });

  it('uses exact full containment and shifts source time by the rendition offset', () => {
    const map = sceneMap();
    const holds = readSceneHolds(
      map.scene_holds,
      map.segments.map((one) => ({ startMs: one.start_ms, endMs: one.end_ms })),
      30000,
    )!;
    const source = [{ startMs: 5000, endMs: 7000, reason: 'red' as const }];
    const interval = buildCoverIntervals(source)[0];
    expect(sceneHoldForInterval(holds, interval)?.imageDataUri).toBe(
      jpegEnvelope(),
    );
    expect(
      sceneHoldForInterval(holds, { ...interval, startMs: 4499 }),
    ).toBeUndefined();
    expect(
      sceneHoldForInterval(holds, { ...interval, endMs: 7501 }),
    ).toBeUndefined();
    const shifted = buildCoverIntervals(source, {
      renditionStartOffsetMs: 100,
    })[0];
    expect(sceneHoldForInterval(holds, shifted, 100)?.imageDataUri).toBe(
      jpegEnvelope(),
    );
    expect(sceneHoldForInterval(holds, shifted)).toBeUndefined();
    const widened = buildCoverIntervals(source, { guardBandMs: 1000 })[0];
    expect(sceneHoldForInterval(holds, widened)).toBeUndefined();
    expect(sceneHoldForInterval(holds, undefined)).toBeUndefined();
  });
});
