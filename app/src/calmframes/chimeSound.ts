/**
 * The sound the chime cue makes.
 *
 * `useChimeCue` decides WHEN a chime should sound and refuses to raise one that
 * no cover follows. This file is the other half: what actually makes a noise.
 * They are separate so the rule can be tested without a speaker, and so this
 * file can fail to silence without taking the rule down with it.
 *
 * The audio path is `AudioPlayer` from `@amazon-devices/react-native-w3cmedia`,
 * which the package's own README describes as implementing `HTMLAudioElement`,
 * and which is a different class from the `VideoPlayer` the title plays
 * through. That matters: CLAUDE.md's rule about one player per process is about
 * `KeplerCaptionsView`, and a second video surface would be a problem, but an
 * audio element is not a video surface.
 *
 * Audible warning-cue playback still needs explicit native verification.
 * Recorded film audio does not establish that this separate cue was heard.
 * The import is resolved at call time and audio failures are swallowed: a
 * missing courtesy sound must not interrupt the picture guard or the title.
 */

/** Where the bundled chime lands in the package, the same way the offline clip does. */
export const CHIME_URI = 'file:///pkg/assets/raw/sound/calm-chime.mp3';

type AudioLike = {
  src: string;
  volume?: number;
  currentTime?: number;
  play: () => unknown;
  initialize?: () => Promise<unknown>;
};

let cached: AudioLike | null = null;
let tried = false;

/**
 * How loud the chime is, against the title's own sound.
 *
 * Quiet on purpose. It has to be audible over a film without being the loudest
 * thing in the room, and a child who is startled by the warning is worse off
 * than one who is not warned.
 */
export const CHIME_VOLUME = 0.35;

async function element(): Promise<AudioLike | null> {
  if (cached || tried) {
    return cached;
  }
  tried = true;
  try {
    // Resolved at call time rather than imported at the top, so a bundle
    // without the module still loads this file.
    const media = require('@amazon-devices/react-native-w3cmedia');
    const AudioPlayer = media?.AudioPlayer;
    if (typeof AudioPlayer !== 'function') {
      return null;
    }
    const player: AudioLike = new AudioPlayer();
    if (typeof player.initialize === 'function') {
      await player.initialize();
    }
    player.src = CHIME_URI.slice('file://'.length);
    player.volume = CHIME_VOLUME;
    cached = player;
    return cached;
  } catch {
    // No module, no audio device, or a player that refused to start. Silence.
    return null;
  }
}

/**
 * Play the chime once, and never let it matter if it cannot.
 *
 * Returns nothing and throws nothing. `useChimeCue` calls this from inside a
 * render effect, and an exception there would take the player down over a
 * courtesy sound.
 */
export function playChime(): void {
  void (async () => {
    try {
      const player = await element();
      if (!player) {
        return;
      }
      // Rewind first: the same element plays every chime, and a finished one
      // sitting at its end would make no sound at all.
      // eslint-disable-next-line no-restricted-syntax -- the chime's audio element, not the picture; nothing here moves the video playhead
      player.currentTime = 0;
      await player.play();
    } catch {
      // Swallowed on purpose. See the note at the top of this file.
    }
  })();
}

/** Test seam: forget the cached element so the next call builds a new one. */
export function resetChimeSound(): void {
  cached = null;
  tried = false;
}
