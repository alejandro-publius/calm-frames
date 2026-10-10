/**
 * The chime reaches the platform, and it reaches it with our asset.
 *
 * What this is NOT. It is not proof that a sound comes out of a television.
 * Capturing the audio the virtual device produces was the first thing tried and
 * it is not available: the device is QEMU and it is started with no audio
 * backend, so there is no stream to record. `scripts/stick_day.py` therefore
 * asks whoever runs the stick to listen, and `app/assets/raw/sound/README.md`
 * says plainly that nothing has heard it.
 *
 * What this IS. Proof that `playChime` constructs the platform's AudioPlayer,
 * points it at the bundled asset, and calls play. That is the whole of what this
 * side of the boundary can be held to, and it is worth holding, because the file
 * swallows every audio failure on purpose and a silent no-op would otherwise
 * look exactly like a working chime.
 *
 * Seen to fail: pointing `player.src` at a different path gives
 * `Expected: "file:///pkg/assets/raw/sound/calm-chime.mp3" / Received:
 * "file:///pkg/assets/raw/offline/calm_gradient.mp4"`, and returning early
 * before `play()` gives `Expected number of calls: 1 / Received number of
 * calls: 0`.
 */

// Prefixed with `mock` because jest.mock factories are hoisted above every
// other statement and may only reach variables named that way.
const mockPlayed = jest.fn();
const mockInitialize = jest.fn(() => Promise.resolve());
const mockConstructed: Array<Record<string, unknown>> = [];

jest.mock(
  '@amazon-devices/react-native-w3cmedia',
  () => ({
    AudioPlayer: function AudioPlayer(this: Record<string, unknown>) {
      mockConstructed.push(this);
      this.initialize = mockInitialize;
      this.play = mockPlayed;
    },
  }),
  { virtual: true },
);

import { CHIME_URI, CHIME_VOLUME, playChime, resetChimeSound } from '../../src/calmframes/chimeSound';

describe('the chime reaches the platform', () => {
  beforeEach(() => {
    resetChimeSound();
    mockPlayed.mockClear();
    mockInitialize.mockClear();
    mockConstructed.length = 0;
  });

  it('builds the platform audio player and points it at the bundled chime', async () => {
    playChime();
    // playChime returns nothing and does its work in a promise, so let the
    // microtask queue drain before asking what happened.
    await new Promise((resolve) => setImmediate(resolve));

    expect(mockConstructed).toHaveLength(1);
    expect(mockInitialize).toHaveBeenCalled();
    expect(mockConstructed[0].src).toBe('/pkg/assets/raw/sound/calm-chime.mp3');
    expect(mockConstructed[0].volume).toBe(CHIME_VOLUME);
    expect(mockPlayed).toHaveBeenCalledTimes(1);
  });

  it('plays the asset that is actually in the package', () => {
    // The path the Kepler file system README gives for package assets. If the
    // asset moves, this is the line that should stop it moving quietly.
    expect(CHIME_URI).toBe('file:///pkg/assets/raw/sound/calm-chime.mp3');
  });

  it('reuses one player rather than building one per chime', async () => {
    playChime();
    await new Promise((resolve) => setImmediate(resolve));
    playChime();
    await new Promise((resolve) => setImmediate(resolve));

    expect(mockConstructed).toHaveLength(1);
    expect(mockPlayed).toHaveBeenCalledTimes(2);
  });
});
