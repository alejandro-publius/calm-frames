/** Initial caption choice. Dialogue tracks remain on by default. The two
 * bundled ambient Harbor films use optional visual descriptions, so start
 * those Off. This runs once per player; explicit menu choices own it afterward.
 * A validated playback checkpoint can restore an explicit choice before this default.
 */

import { CAPTION_DISABLE_ID } from '../constants';

/** The part of a W3C TextTrack this needs. */
export interface TextTrackLike {
  id: string;
  label?: string;
  language?: string;
  mode?: string;
}

/** The part of a W3C TextTrackList this needs: indexed, with a length. */
export interface TextTrackListLike {
  length: number;
  [index: number]: TextTrackLike | undefined;
}

/** A caption track as the title's catalog entry lists it. */
export interface ShippedTrack {
  label: string;
  language: string;
}

/** Shaka's own text tracks, which belong to the player rather than the title. */
export function isPlayerOwnTrack(track: TextTrackLike): boolean {
  return Boolean(track.label?.includes('Shaka Player'));
}

function titleTracks(tracks: TextTrackListLike | null | undefined): TextTrackLike[] {
  const found: TextTrackLike[] = [];
  for (let index = 0; index < (tracks?.length ?? 0); index += 1) {
    const track = tracks?.[index];
    if (track && !isPlayerOwnTrack(track)) {
      found.push(track);
    }
  }
  return found;
}

/** Exact ambient title identities, not a rule for all demos or all captions. */
export function usesOptionalSceneDescriptions(titleId?: string): boolean {
  return titleId === 'calm-frames-benign-story' ||
    titleId === 'prepared-de53dd81f60a44409531ad1ff57ee08fb213d9650b06c92ae1fe88a2cbbb526e';
}

/** Select the initial track; an Off result leaves all title tracks hidden.
 * Call only before a user has selected a caption option.
 */
export function showDefaultCaptions(
  tracks: TextTrackListLike | null | undefined,
  shipped: ShippedTrack[] | null | undefined,
  titleId?: string,
): string {
  if (!shipped || shipped.length === 0) {
    return CAPTION_DISABLE_ID;
  }
  const candidates = titleTracks(tracks);
  if (usesOptionalSceneDescriptions(titleId)) {
    for (const track of candidates) {
      if (track.mode === 'showing') track.mode = 'hidden';
    }
    return CAPTION_DISABLE_ID;
  }
  const first = shipped[0];
  const chosen =
    candidates.find(
      (track) => track.label === first.label && track.language === first.language,
    ) ?? candidates[0];
  if (!chosen) {
    return CAPTION_DISABLE_ID;
  }
  for (const other of candidates) {
    if (other !== chosen && other.mode === 'showing') {
      other.mode = 'hidden';
    }
  }
  chosen.mode = 'showing';
  return chosen.id;
}
