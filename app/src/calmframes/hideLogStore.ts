/**
 * Where a hide is written down, so the parent area can read it back.
 *
 * The guard already reports every cover it puts on: `useFlashGuard` calls
 * `onHide` once per interval that was actually covered. Nothing was listening.
 * The player screen and the kid mode route are two routes in one stack, and
 * the player is torn down on the way back, so a hide held in either screen's
 * state is gone by the time a parent opens the log. That is why the parent
 * area said nothing had ever been hidden while the cover was working.
 *
 * This is the shared place. A module-level store rather than a context,
 * because:
 *
 * - a context has to be provided above both routes, which means editing the
 *   navigator, and the navigator is shared with the five sample screens that
 *   have nothing to do with kid mode;
 * - the writer is not a component. It is a callback the guard fires from an
 *   effect, and a module-level function is reachable from there without
 *   threading a hook through the player's props;
 * - a module lives as long as the JavaScript context, so it survives the
 *   player unmounting, the route going back to the shelf, and the shelf being
 *   opened again. A context survives that too, but only while its provider is
 *   mounted, and the provider would sit inside the navigator.
 *
 * What it is not: storage. This is memory, so it empties when the app is
 * killed, the same as the PIN and the room setting, which is written down in
 * docs/STATUS.md rather than hidden. Writing it to /data is a separate job.
 *
 * Nothing here leaves the device.
 */

import React from 'react';
import { HideLogEntry } from './hideLog';
import { DEFAULT_SETTINGS, PresetName } from './household';
import { addProfileHide, emptyProfileLogs, ProfileLogs } from './profiles';
import { beacon } from './timingLog';

/**
 * Who a hide is filed under when the player was handed no profile.
 *
 * Kid mode always names one. Anything else reaching the guarded player is a
 * caller that did not come through the shelf, and a hide it caused is still
 * real, so it is recorded under a name that says plainly that nobody knows
 * whose it was rather than being dropped or filed under a kid who was not
 * watching. It shows up under Everyone in the parent area and in no kid's own
 * log, which is the truthful place for it.
 */
export const UNATTRIBUTED_PROFILE_ID = 'unattributed';
export const UNATTRIBUTED_PROFILE_NAME = 'Not recorded';

/**
 * One cover, with everything the parent area needs to say what happened.
 *
 * `HideLogEntry` is the engine's shape and is mirrored into the hook package,
 * so it knows about a title and a position and nothing about this app's
 * families. The three fields added here are the app's: whose sitting it was,
 * which rule set was in force, and where the cover came off.
 */
export interface HouseholdHideEntry extends HideLogEntry {
  profileId: string;
  profileName: string;
  /**
   * Where the cover came off, in media milliseconds.
   *
   * Written from the same interval `positionMs` and `durationMs` come from, so
   * the three always agree: end is start plus duration, every time.
   */
  endMs: number;
  /** The preset the cover was computed under, not the one set today. */
  preset: PresetName;
}

/** What the player knows about the sitting, which the guard does not. */
export interface HideAttribution {
  profileId?: string;
  profileName?: string;
  preset?: PresetName;
}

let logs: ProfileLogs = emptyProfileLogs();
const listeners = new Set<() => void>();

function publish(): void {
  // A copy, so a listener that unsubscribes while being called cannot change
  // the set being walked.
  for (const listener of [...listeners]) {
    listener();
  }
}

/**
 * Write one cover down.
 *
 * Called once per interval covered, from the player. The entry that was stored
 * is handed back, which is what the tests read and what makes the attribution
 * visible at the call site rather than only inside here.
 */
export function recordHide(
  entry: HideLogEntry,
  who: HideAttribution = {},
): HouseholdHideEntry {
  const stored: HouseholdHideEntry = {
    ...entry,
    profileId: who.profileId ?? UNATTRIBUTED_PROFILE_ID,
    profileName: who.profileName ?? UNATTRIBUTED_PROFILE_NAME,
    endMs: entry.positionMs + entry.durationMs,
    preset: who.preset ?? DEFAULT_SETTINGS.preset,
  };
  logs = addProfileHide(logs, stored.profileId, stored);
  beacon('hideLog.record', {
    titleId: stored.titleId,
    profileId: stored.profileId,
    startMs: stored.positionMs,
    endMs: stored.endMs,
    cause: stored.cause,
    reason: stored.reason,
    preset: stored.preset,
  });
  publish();
  return stored;
}

/** Every kid's log, keyed by profile id. The same object until a write. */
export function readHideLogs(): ProfileLogs {
  return logs;
}

/** Empty it. For tests, and for a household that asks for it later. */
/**
 * Forget one kid's record, for good.
 *
 * Called when a profile is removed. The confirmation a parent reads says the
 * hidden segment record goes with the kid, and until this existed it did not:
 * the entries stayed in the module level store, out of sight, and the Everyone
 * view would still have flattened them in. A promise a screen makes is a thing
 * the code owes.
 */
export function forgetProfile(id: string): void {
  if (!(id in logs)) {
    return;
  }
  const next: ProfileLogs = {};
  for (const [profileId, entries] of Object.entries(logs)) {
    if (profileId !== id) {
      next[profileId] = entries;
    }
  }
  logs = next;
  publish();
}

export function resetHideLogs(): void {
  logs = emptyProfileLogs();
  publish();
}

export function subscribeHideLogs(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * The logs, as a screen reads them.
 *
 * `useSyncExternalStore` rather than a state and an effect, because the player
 * can write between this screen rendering and its effect running, and the
 * subscribe-then-re-read that this does is the only version of the pattern
 * that cannot miss that write.
 */
export function useHideLogs(): ProfileLogs {
  return React.useSyncExternalStore(subscribeHideLogs, readHideLogs, readHideLogs);
}
