import { CHECKPOINT_KEY, CHECKPOINT_MAX_AGE_MS, createCheckpointStore, PlaybackCheckpoint,
  validateCheckpoint, CheckpointIdentity } from '../../src/calmframes/playbackCheckpoint';
const now = 1800000000000;
const identity: CheckpointIdentity = {profileId: 'profile-1', titleId: 'prepared-title',
  uri: 'file:///pkg/assets/raw/prepared-library/bundle/video.mp4', sourceSha256: 'a'.repeat(64),
  renditionSha256: 'b'.repeat(64), durationMs: 300000, startOffsetMs: 0};
const record = (changes: Partial<PlaybackCheckpoint> = {}): PlaybackCheckpoint => ({version: 1,
  identity, positionMs: 135000, captions: {language: 'en', label: 'English'}, paused: true, savedAt: now, ...changes});
function memory() {
  let value: string | null = null;
  const storage = {getItem: jest.fn(async () => value), setItem: jest.fn(async (_key: string, raw: string) => {value = raw;})};
  return {storage, store: createCheckpointStore(storage, () => now), set: (raw: string) => {value = raw;}};
}
test('round trips exact edition, caption identity and paused intent without storing protection settings', async () => {
  const {storage, store} = memory(); const session = store.open(identity);
  expect(await session.save(record())).toBe(true); session.close();
  expect(await store.open(identity).load()).toEqual(record());
  expect(storage.setItem.mock.calls[0][0]).toBe(CHECKPOINT_KEY);
  expect(JSON.parse(storage.setItem.mock.calls[0][1]).records[0].settings).toBeUndefined();
});
// The household and the verified route decide protection, never the history.
// A record edited on the device to carry its own settings, or a looser cover
// plan, loads as position and captions only. Seen to fail, Oct 23 2026, with
// validateCheckpoint returning the stored object spread over its fields.
test('a stored record carrying protection settings loads without them', async () => {
  const {store, set} = memory();
  const tampered = {...record(), settings: {preset: 'wcag', guardBandMs: 0, minCoverMs: 0},
    intervals: [], identity: {...identity, preset: 'wcag'}};
  set(JSON.stringify({version: 1, records: [tampered]}));
  const loaded = await store.open(identity).load();
  expect(loaded).toEqual(record());
  expect(Object.keys(loaded!).sort()).toEqual(['captions', 'identity', 'paused', 'positionMs', 'savedAt', 'version']);
  expect(Object.keys(loaded!.identity)).not.toContain('preset');
});
test.each(['sourceSha256', 'renditionSha256', 'uri', 'profileId', 'durationMs', 'startOffsetMs'])(
  'refuses a checkpoint for changed %s', async field => {
    const {store} = memory(); await store.open(identity).save(record());
    const other = {...identity, [field]: typeof identity[field as keyof CheckpointIdentity] === 'number' ? 23 :
      field.endsWith('Sha256') ? 'c'.repeat(64) : field === 'uri' ? identity.uri + '.other' : 'profile-2'};
    expect(await store.open(other).load()).toBeNull();
  });
test.each([NaN, Infinity, -1, 0, 300000, 299500])('rejects invalid or finished position %s', positionMs => {
  expect(() => validateCheckpoint(record({positionMs}), now)).toThrow();
});
test('corrupt, oversized and expired optional history do not prevent an ordinary start', async () => {
  const {store, set} = memory();
  for (const raw of ['{broken', 'x'.repeat(65537), JSON.stringify({version: 1, records: [record({savedAt: now - CHECKPOINT_MAX_AGE_MS - 1})]})]) {
    set(raw); expect(await store.open(identity).load()).toBeNull();
  }
});
test('completion deletes history and rejects late saves', async () => {
  const {store} = memory(); const session = store.open(identity);
  await session.save(record()); await session.clear();
  expect(await session.save(record())).toBe(false);
  expect(await store.open(identity).load()).toBeNull();
});
test('queued writes from an obsolete player cannot replace a new session', async () => {
  const {store} = memory(); const old = store.open(identity);
  const pending = old.save(record()); const next = store.open(identity);
  expect(await pending).toBe(false); expect(await old.save(record())).toBe(false);
  await next.save(record({positionMs: 160000}));
  expect((await next.load())?.positionMs).toBe(160000);
});
test('storage failures are optional, not playback failures', async () => {
  const store = createCheckpointStore({getItem: async () => {throw Error('disk');}, setItem: async () => {}}, () => now);
  const session = store.open(identity);
  expect(await session.load()).toBeNull(); expect(await session.save(record())).toBe(false);
});

test('Start over is ordered before a successor session even when its delete is queued', async () => {
  const {store} = memory(); await store.open(identity).save(record());
  const clearing = store.open(identity).clear(); const next = store.open(identity);
  expect(await clearing).toBe(true); expect(await next.load()).toBeNull();
  expect(await next.save(record({positionMs: 4000}))).toBe(true);
});
test('new valid history heals corrupt JSON without treating storage IO failure as an empty file', async () => {
  const {store, set} = memory(); set('{broken'); const next = store.open(identity);
  expect(await next.save(record())).toBe(true); expect(await next.load()).toEqual(record());
});
test('a slow write coalesces the latest paused sample and drains it after close', async () => {
  let finish!: (value: string | null) => void;
  const storage = {getItem: jest.fn().mockImplementationOnce(() => new Promise<string | null>(resolve => {finish = resolve;})).mockResolvedValue(null),
    setItem: jest.fn(async (_key: string, _raw: string) => {})};
  const session = createCheckpointStore(storage, () => now).open(identity);
  const first = session.save(record({paused: false})); await Promise.resolve();
  session.save(record({positionMs: 140000, paused: false}));
  const latest = session.save(record({positionMs: 145000, paused: true}));
  session.close(); finish(null);
  await first; await latest;
  expect(storage.setItem).toHaveBeenCalledTimes(2);
  expect(JSON.parse(storage.setItem.mock.calls[1][1]).records[0]).toMatchObject({positionMs: 145000, paused: true});
});
test('completion discards coalesced samples instead of resurrecting cleared history', async () => {
  const {store} = memory(); const session = store.open(identity);
  const first = session.save(record()); session.save(record({positionMs: 145000}));
  const clearing = session.clear(); await first; await clearing;
  expect(await store.open(identity).load()).toBeNull();
});
