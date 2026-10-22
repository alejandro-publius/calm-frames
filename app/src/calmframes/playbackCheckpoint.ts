/** Optional local playback memory. A checkpoint never grants playback access. */
export interface CheckpointIdentity {
  profileId: string;
  titleId: string;
  uri: string;
  sourceSha256: string;
  renditionSha256: string;
  durationMs: number;
  startOffsetMs: number;
}
export interface CaptionChoice { language: string; label: string; }
export interface PlaybackCheckpoint {
  version: 1;
  identity: CheckpointIdentity;
  positionMs: number;
  captions: CaptionChoice | null;
  paused: boolean;
  savedAt: number;
}
export interface CheckpointStorage {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
}
export const CHECKPOINT_KEY = 'calm-frames.playback-checkpoints.v1';
export const MAX_CHECKPOINTS = 24;
export const MAX_CHECKPOINT_BYTES = 64 * 1024;
export const CHECKPOINT_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;
const digest = (v: unknown): v is string => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const text = (v: unknown, max: number): v is string => typeof v === 'string' && v.length > 0 && v.length <= max;
const object = (v: unknown): Record<string, unknown> => {
  if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error('Invalid checkpoint');
  return v as Record<string, unknown>;
};
export function validateCheckpointIdentity(value: unknown): CheckpointIdentity {
  const v = object(value);
  if (!text(v.profileId, 100) || !text(v.titleId, 200) || !text(v.uri, 1500) ||
      !v.uri.startsWith('file:///pkg/assets/raw/prepared-library/') ||
      !digest(v.sourceSha256) || !digest(v.renditionSha256) ||
      typeof v.durationMs !== 'number' || !Number.isFinite(v.durationMs) || v.durationMs <= 0 ||
      typeof v.startOffsetMs !== 'number' || !Number.isFinite(v.startOffsetMs)) throw new Error('Invalid checkpoint identity');
  return { profileId: v.profileId, titleId: v.titleId, uri: v.uri,
    sourceSha256: v.sourceSha256, renditionSha256: v.renditionSha256,
    durationMs: v.durationMs, startOffsetMs: v.startOffsetMs };
}
export function checkpointIdentityKey(value: CheckpointIdentity): string {
  return JSON.stringify(validateCheckpointIdentity(value));
}
function slot(identity: CheckpointIdentity): string {
  return JSON.stringify([identity.profileId, identity.titleId]);
}
export function validateCheckpoint(value: unknown, now = Date.now()): PlaybackCheckpoint {
  const v = object(value), identity = validateCheckpointIdentity(v.identity);
  if (v.version !== 1 || typeof v.positionMs !== 'number' || !Number.isFinite(v.positionMs) ||
      v.positionMs < 1000 || v.positionMs >= identity.durationMs - 1000 || typeof v.paused !== 'boolean' ||
      typeof v.savedAt !== 'number' || !Number.isSafeInteger(v.savedAt) || v.savedAt > now + 60000 ||
      v.savedAt < now - CHECKPOINT_MAX_AGE_MS) throw new Error('Invalid or expired checkpoint');
  let captions: CaptionChoice | null = null;
  if (v.captions !== null) {
    const c = object(v.captions);
    if (!text(c.language, 64) || !text(c.label, 200)) throw new Error('Invalid caption choice');
    captions = { language: c.language, label: c.label };
  }
  return { version: 1, identity, positionMs: v.positionMs, captions, paused: v.paused, savedAt: v.savedAt };
}
function decode(raw: string | null, now: number): PlaybackCheckpoint[] {
  if (raw === null) return [];
  if (raw.length > MAX_CHECKPOINT_BYTES) throw new Error('Checkpoint storage is too large');
  const value = object(JSON.parse(raw));
  if (value.version !== 1 || !Array.isArray(value.records) || value.records.length > MAX_CHECKPOINTS) throw new Error('Invalid checkpoint storage');
  // A stale/corrupt entry is optional history, never a reason to deny playback.
  return value.records.flatMap(record => {
    try { return [validateCheckpoint(record, now)]; } catch { return []; }
  });
}

/** Serialize writes across routes. A replaced session cannot overwrite its successor. */
export function createCheckpointStore(storage: CheckpointStorage, now = Date.now) {
  let queue: Promise<unknown> = Promise.resolve();
  const owners = new Map<string, number>();
  const enqueue = <T,>(work: () => Promise<T>): Promise<T> => {
    const next = queue.then(work, work); queue = next.catch(() => undefined); return next;
  };
  return {
    open(rawIdentity: CheckpointIdentity) {
      const identity = validateCheckpointIdentity(rawIdentity), key = slot(identity);
      const owner = (owners.get(key) ?? 0) + 1; owners.set(key, owner);
      let closed = false, saving = false;
      const current = () => owners.get(key) === owner;
      const write = (record: PlaybackCheckpoint | null) => enqueue(async () => {
        if (record && !current()) return false;
        try {
          const raw = await storage.getItem(CHECKPOINT_KEY);
          let records: PlaybackCheckpoint[];
          try { records = decode(raw, now()); } catch { records = []; }
          if (record && !current()) return false;
          const next = records.filter(row => slot(row.identity) !== key);
          if (record) next.unshift(record);
          const encoded = JSON.stringify({ version: 1, records: next.slice(0, MAX_CHECKPOINTS) });
          if (encoded.length > MAX_CHECKPOINT_BYTES) return false;
          await storage.setItem(CHECKPOINT_KEY, encoded);
          return record ? current() : true;
        } catch { return false; }
      });
      return {
        load: () => enqueue(async () => {
          if (closed || !current()) return null;
          try {
            const records = decode(await storage.getItem(CHECKPOINT_KEY), now());
            if (closed || !current()) return null;
            return records.find(record => checkpointIdentityKey(record.identity) === checkpointIdentityKey(identity)) ?? null;
          } catch { return null; }
        }),
        save(record: PlaybackCheckpoint): Promise<boolean> {
          if (closed || saving || !current()) return Promise.resolve(false);
          try {
            const checked = validateCheckpoint(record, now());
            if (checkpointIdentityKey(checked.identity) !== checkpointIdentityKey(identity)) return Promise.resolve(false);
            saving = true;
            return write(checked).finally(() => {saving = false;});
          } catch { return Promise.resolve(false); }
        },
        clear(): Promise<boolean> {
          if (closed || !current()) return Promise.resolve(false);
          // Completion/start over closes the writer before deleting its position.
          closed = true; return write(null);
        },
        close() { closed = true; },
      };
    },
  };
}
