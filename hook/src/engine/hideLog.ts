/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * What was hidden, and when.
 *
 * The parent area shows this. It is the only record a household gets that the
 * thing they set up is doing something, so it has to be truthful: one entry
 * per interval that was actually covered during playback, with the title, the
 * media position, the length and why.
 *
 * It lives on the device. Nothing here is sent anywhere.
 */

export type HideCause =
  | 'schedule'
  | 'seek'
  | 'skipped'
  | 'unverified'
  | 'uncertain';

export interface HideLogEntry {
  /** Wall clock when the cover went on, milliseconds since the epoch. */
  atMs: number;
  titleId: string;
  titleName: string;
  /** Where in the title, in media milliseconds. */
  positionMs: number;
  /** How long the cover stayed on, in media milliseconds. */
  durationMs: number;
  cause: HideCause;
  /** general or red, from the map. */
  reason?: 'general' | 'red';
}

export const HIDE_LOG_LIMIT = 200;

export interface HideLogStore {
  entries: HideLogEntry[];
}

export function emptyHideLog(): HideLogStore {
  return { entries: [] };
}

/** Add an entry, newest first, keeping the log from growing without limit. */
export function addHideEntry(
  log: HideLogStore,
  entry: HideLogEntry,
  limit = HIDE_LOG_LIMIT,
): HideLogStore {
  return { entries: [entry, ...log.entries].slice(0, limit) };
}

export function totalHiddenMs(log: HideLogStore): number {
  return log.entries.reduce((total, entry) => total + entry.durationMs, 0);
}

function twoDigits(value: number): string {
  return value < 10 ? `0${value}` : String(value);
}

/** A position in a title, as minutes and seconds. */
export function formatPosition(positionMs: number): string {
  const total = Math.max(0, Math.round(positionMs / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${twoDigits(seconds)}`;
}

export function formatDuration(durationMs: number): string {
  const seconds = Math.max(1, Math.round(durationMs / 1000));
  return `${seconds} second${seconds === 1 ? '' : 's'}`;
}

/** One line for the parent area. */
export function describeHideEntry(entry: HideLogEntry): string {
  const when = new Date(entry.atMs);
  const clock = `${twoDigits(when.getHours())}:${twoDigits(when.getMinutes())}`;
  const what =
    entry.cause === 'unverified'
      ? 'kept the picture hidden, title not checked'
      : `hid ${formatDuration(entry.durationMs)}`;
  const where =
    entry.cause === 'unverified' ? '' : ` at ${formatPosition(entry.positionMs)}`;
  const how =
    entry.cause === 'seek'
      ? ', after moving the playhead'
      : entry.cause === 'skipped'
        ? ', then skipped past it'
        : entry.cause === 'uncertain'
          ? ', while the picture was not certain'
          : '';
  return `${clock} ${entry.titleName}: ${what}${where}${how}`;
}
