/**
 * Whether the player is allowed to show a picture at all.
 *
 * The player screen came from the Vega video sample, where anything in the
 * catalog plays on request. Calm Frames cannot work that way: a title reaches
 * the player with its signed map in hand, or it does not play. Until now that
 * was true only because the one screen that navigates to the player passed the
 * map, which is a promise about call sites rather than a guarantee. Any new
 * screen, any deep link and any leftover sample screen would have played
 * whatever it was handed.
 *
 * So the decision lives here, the player asks it on every render, and there
 * are exactly three answers:
 *
 *   guarded    a checked title with its map. The flash guard runs and decides
 *              frame by frame what is covered.
 *   harness    a measurement run, started from a config file on the device.
 *              The cover harness is in charge, and nobody is watching: these
 *              runs play a marker clip at the camera, not content at a child.
 *   unguarded  anything else. The picture stays hidden and a card says why.
 *
 * The third one is the point. It is not an error state to be tidied away
 * later: it is the app refusing to do the thing it exists to prevent.
 */

import { Card, cardAt } from './cards';
import { HarnessMode } from './useCoverHarness';

export type PlaybackAccess = 'guarded' | 'harness' | 'unguarded';

export interface PlaybackAccessInput {
  /** The guarded parameters the route was given, if any. */
  guarded?: { sha256?: string; maps?: unknown; mapUrls?: unknown } | null;
  /** The measurement harness mode, "off" when there is not one. */
  coverTest?: HarnessMode | null;
}

/**
 * What the player is allowed to do with what it was handed.
 *
 * Guarded parameters with no map and no map URL are not guarded parameters.
 * An empty object would otherwise turn the guard off and read as if it were
 * on, which is the worst of the three.
 */
export function playbackAccess(input: PlaybackAccessInput): PlaybackAccess {
  const guarded = input.guarded;
  const hasMaps =
    guarded !== null &&
    guarded !== undefined &&
    (hasAnyEntry(guarded.maps) || hasAnyEntry(guarded.mapUrls));
  if (hasMaps && typeof guarded?.sha256 === 'string' && guarded.sha256.length > 0) {
    return 'guarded';
  }
  if (input.coverTest && input.coverTest !== 'off') {
    return 'harness';
  }
  return 'unguarded';
}

function hasAnyEntry(value: unknown): boolean {
  if (!value || typeof value !== 'object') {
    return false;
  }
  return Object.values(value as Record<string, unknown>).some(
    (entry) => typeof entry === 'string' && entry.length > 0,
  );
}

/** True when the picture has to stay hidden whatever the playhead is doing. */
export function mustStayHidden(access: PlaybackAccess): boolean {
  return access === 'unguarded';
}

/**
 * What the card says when the player was opened with nothing to check.
 *
 * The same card a missing map produces, with wording for this case: there is
 * no map here at all, checked or otherwise.
 */
export const UNGUARDED_CARD: Card = cardAt([], 0, {
  rejection: 'missing',
  blockedDetail:
    'This video is unavailable. The picture stays hidden while sound and captions keep playing.',
});
