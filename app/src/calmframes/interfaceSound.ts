/** Optional menu confirmation, separate from the cue before a picture hold. */
export const INTERFACE_SOUND_URI = '/pkg/assets/raw/sound/menu-select.mp3';
export const INTERFACE_SOUND_VOLUME = 0.22;
export const INTERFACE_SOUND_INTERVAL_MS = 220;
export const INTERFACE_SOUND_MAX_AGE_MS = 220;
export const INTERFACE_SOUND_TIMEOUT_MS = 500;

export interface InterfaceFeedback {
  confirm(): void;
  stop(): void;
}

export interface InterfaceAudioPlayer {
  src: string;
  volume: number;
  currentTime: number;
  initialize(): Promise<void>;
  deinitialize(): Promise<void>;
  play(): unknown;
  pause(): void;
  addEventListener(type: string, listener: () => void): void;
  removeEventListener(type: string, listener: () => void): void;
}

function createPlayer(): InterfaceAudioPlayer {
  // The installed SDK exposes these audio categories on AudioPlayer. Their
  // native focus behavior still needs a check on the Vega Virtual Device.
  const media = require('@amazon-devices/react-native-w3cmedia');
  return new media.AudioPlayer(
    media.AudioContentType.CONTENT_TYPE_SONIFICATION,
    media.AudioUsageType.USAGE_NOTIFICATION,
  );
}

type Playback = {
  player: InterfaceAudioPlayer;
  initialized: Promise<void>;
  cleanup?: Promise<void>;
  released: boolean;
  timer?: ReturnType<typeof setTimeout>;
  listeners: Array<[string, () => void]>;
};

export function createInterfaceSoundController({
  makePlayer = createPlayer,
  now = Date.now,
}: {
  makePlayer?: () => InterfaceAudioPlayer;
  now?: () => number;
} = {}): InterfaceFeedback & { setAllowed(allowed: boolean): void } {
  let allowed = false;
  let generation = 0;
  let current: Playback | undefined;
  let lastRequest = -Infinity;

  const pause = (player: InterfaceAudioPlayer) => {
    try { player.pause(); } catch { /* Optional audio never blocks an action. */ }
  };

  const release = (playback: Playback) => {
    if (playback.released) { return; }
    playback.released = true;
    // A released playback can never sound again, so the next request may make
    // its own player at once. Waiting for this one's teardown would let a
    // single player that never answers keep the menu silent for good.
    if (current === playback) { current = undefined; }
    if (playback.timer) { clearTimeout(playback.timer); }
    for (const [event, listener] of playback.listeners) {
      try { playback.player.removeEventListener(event, listener); } catch { /* Silence. */ }
    }
    playback.listeners = [];
    pause(playback.player);
    playback.cleanup = (async () => {
      // The SDK's deinitialize() aborts an initialize() that has not answered
      // and rejects its promise, which the request's own catch releases again,
      // so there is nothing to wait for before it.
      try { await playback.player.deinitialize(); } catch { /* Silence. */ }
    })();
  };

  const stop = () => {
    // Invalidate synchronously, including initialize() that has not resolved.
    allowed = false;
    generation += 1;
    if (current) { release(current); }
  };

  const confirm = () => {
    const requestedAt = now();
    if (!allowed || current || requestedAt - lastRequest < INTERFACE_SOUND_INTERVAL_MS) { return; }
    lastRequest = requestedAt;
    const requestGeneration = generation;
    let player: InterfaceAudioPlayer;
    try { player = makePlayer(); } catch { return; }
    const playback: Playback = {
      player,
      initialized: Promise.resolve().then(() => player.initialize()),
      listeners: [],
      released: false,
    };
    current = playback;
    playback.timer = setTimeout(() => release(playback), INTERFACE_SOUND_MAX_AGE_MS);
    const valid = () => allowed && generation === requestGeneration && !playback.released;
    playback.initialized.then(async () => {
      if (!valid() || now() - requestedAt >= INTERFACE_SOUND_MAX_AGE_MS) { release(playback); return; }
      clearTimeout(playback.timer);
      player.src = INTERFACE_SOUND_URI;
      player.volume = INTERFACE_SOUND_VOLUME;
      // eslint-disable-next-line no-restricted-syntax -- rewinds only this short menu audio element, never the video playhead
      player.currentTime = 0;
      for (const [event, listener] of [
        ['ended', () => release(playback)],
        ['error', () => release(playback)],
        ['audiofocuspaused', stop],
        ['audiofocuslost', stop],
      ] as Array<[string, () => void]>) {
        player.addEventListener(event, listener);
        playback.listeners.push([event, listener]);
      }
      // Missing end events must not retain audio focus or queue another sound.
      playback.timer = setTimeout(() => release(playback), INTERFACE_SOUND_TIMEOUT_MS);
      await player.play();
      if (!valid()) { pause(player); }
    }).catch(() => release(playback));
  };

  return { confirm, stop, setAllowed: (next) => { if (next) { allowed = true; } else { stop(); } } };
}
