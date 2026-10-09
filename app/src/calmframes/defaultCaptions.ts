/**
 * Captions on from the start, for a title that ships them.
 *
 * Captions are half of what keeps a hidden part followable: while the cover is
 * on, the words carry on above it. A child who first has to find
 * the caption menu has already missed the part they were for. So a title that
 * ships a caption track starts with that track showing, and the caption menu
 * turns it off like any other choice.
 *
 * Only the title's own tracks count. Shaka adds text tracks of its own to an
 * adaptive stream, labelled "Shaka Player ...", which CaptionOptions keeps out
 * of the menu for the same reason. A title that ships no captions is left as
 * it was.
 *
 * This decides which track and sets its mode. PlayerScreen does it once, when
 * the player is ready, and keeps the chosen id so the captions view shows and
 * the caption menu opens on the right choice.
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

/**
 * Show the title's first shipped caption track, and say which one it is.
 *
 * Returns the id of the track now showing, or CAPTION_DISABLE_ID when the
 * title ships no captions or the player has none of them. Any other title
 * track that was showing is hidden, so one track shows at a time, which is
 * what the caption menu keeps to as well.
 */
export function showDefaultCaptions(
  tracks: TextTrackListLike | null | undefined,
  shipped: ShippedTrack[] | null | undefined,
): string {
  if (!shipped || shipped.length === 0) {
    return CAPTION_DISABLE_ID;
  }
  const candidates = titleTracks(tracks);
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
