/**
 * A title that ships captions starts with them on.
 *
 * The tracks here are plain objects shaped like the player's TextTrackList:
 * an indexed list with ids, labels, languages and a mode that can be set.
 *
 * Seen to fail, Oct 9 2026: with showDefaultCaptions returning the Off id
 * straight away, the first, second and fourth tests went red.
 */

import { CAPTION_DISABLE_ID } from '../../src/constants';
import { showDefaultCaptions } from '../../src/calmframes/defaultCaptions';

interface Track {
  id: string;
  label: string;
  language: string;
  mode: string;
}

function trackList(...tracks: Track[]) {
  return Object.assign([...tracks], {
    getTrackById: (id: string) => tracks.find((track) => track.id === id) ?? null,
  });
}

const shipped = [
  { label: 'English practice captions', language: 'en', uri: 'file:///pkg/x.vtt', mimeType: 'text/vtt' },
];

function englishTrack(): Track {
  return { id: 'n-1', label: 'English practice captions', language: 'en', mode: 'hidden' };
}

function shakaTrack(): Track {
  return { id: 'n-0', label: 'Shaka Player TextTrack', language: '', mode: 'hidden' };
}

describe('captions on by default', () => {
  it("shows the title's own track and says which one it is", () => {
    const english = englishTrack();
    const shaka = shakaTrack();
    const id = showDefaultCaptions(trackList(shaka, english), shipped);
    expect(id).toBe('n-1');
    expect(english.mode).toBe('showing');
    // Shaka's own text track is the player's business, not the title's.
    expect(shaka.mode).toBe('hidden');
  });

  it('picks the track the title shipped first, wherever the player listed it', () => {
    const spanish = { id: 'n-1', label: 'Spanish', language: 'es', mode: 'hidden' };
    const english = { ...englishTrack(), id: 'n-2' };
    const id = showDefaultCaptions(trackList(spanish, english), shipped);
    expect(id).toBe('n-2');
    expect(english.mode).toBe('showing');
    expect(spanish.mode).toBe('hidden');
  });

  it('leaves a title that ships no captions as it was', () => {
    const english = englishTrack();
    expect(showDefaultCaptions(trackList(english), [])).toBe(CAPTION_DISABLE_ID);
    expect(showDefaultCaptions(trackList(english), undefined)).toBe(CAPTION_DISABLE_ID);
    expect(english.mode).toBe('hidden');
  });

  it('keeps one track showing when another was already on', () => {
    const other = { id: 'n-3', label: 'Commentary', language: 'en', mode: 'showing' };
    const english = englishTrack();
    const tracks = trackList(other, english);
    expect(showDefaultCaptions(tracks, shipped)).toBe('n-1');
    expect(tracks.filter((track) => track.mode === 'showing')).toEqual([english]);
  });

  it('does nothing when the player has no tracks to offer', () => {
    expect(showDefaultCaptions(undefined, shipped)).toBe(CAPTION_DISABLE_ID);
    expect(showDefaultCaptions(trackList(), shipped)).toBe(CAPTION_DISABLE_ID);
    expect(showDefaultCaptions(trackList(shakaTrack()), shipped)).toBe(
      CAPTION_DISABLE_ID,
    );
  });
});


describe('optional ambient scene descriptions', () => {
  it.each(['calm-frames-benign-story', 'prepared-de53dd81f60a44409531ad1ff57ee08fb213d9650b06c92ae1fe88a2cbbb526e'])('starts %s Off without removing its track', titleId => {
    const english = { ...englishTrack(), mode: 'showing' };
    const tracks = trackList(english);
    expect(showDefaultCaptions(tracks, shipped, titleId)).toBe(CAPTION_DISABLE_ID);
    expect(tracks).toHaveLength(1);
    expect(english.mode).toBe('hidden');
  });
  it('keeps dialogue and unrelated demo caption defaults on', () => {
    const english = englishTrack();
    expect(showDefaultCaptions(trackList(english), shipped, 'dialogue-demo')).toBe(english.id);
    expect(english.mode).toBe('showing');
  });
});
