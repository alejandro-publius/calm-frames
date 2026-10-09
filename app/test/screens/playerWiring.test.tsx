/**
 * What the player screen hands its parts, from a real guard.
 *
 * VideoPlayerUI is the sample's chrome, so it is a stand in here and what is
 * checked is what PlayerScreen gives it. Everything that decides those props is
 * real: the signed bursts map read by the real Ed25519 reader, the real
 * schedule and the real cards. The sample's video plumbing is replaced the
 * same way test/screens/hideLog.test.tsx replaces it, with a fake media
 * element in the player's ref.
 *
 * Seen to fail, Oct 9 2026: with skipOwnsSelect={false} hard wired in
 * PlayerScreen, the countdown test reported Expected true, Received false.
 * With the per change line taken out of handleAppStateChange, both app state
 * tests went red.
 */

import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import { act, render, screen } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import PlayerScreen from '../../src/screens/PlayerScreen';

jest.mock('../../src/w3cmedia/mediacontrols/VideoPlayerUI', () => 'VideoPlayerUI');
jest.mock('../../src/services/bif/bifService', () => ({
  getBifFrameImageSource: jest.fn(async () => null),
}));

/** The fake player for the current test. A jest factory may only reach mock* names. */
let mockMedia: FakeMedia | null = null;

interface FakeMedia {
  currentTime: number;
  playbackRate: number;
  currentSrc: string;
  addEventListener: (type: string, listener: () => void) => void;
  removeEventListener: (type: string, listener: () => void) => void;
  fire: (type: string) => void;
  setSurfaceHandle: () => void;
  clearSurfaceHandle: () => void;
  setCaptionViewHandle: () => void;
  clearCaptionViewHandle: () => void;
  play: () => Promise<void>;
}

function makeMedia(): FakeMedia {
  const listeners: Record<string, Array<() => void>> = {};
  return {
    currentTime: 0,
    playbackRate: 1,
    currentSrc: 'https://example.invalid/bursts.mp4',
    addEventListener(type, listener) {
      listeners[type] = [...(listeners[type] ?? []), listener];
    },
    removeEventListener(type, listener) {
      listeners[type] = (listeners[type] ?? []).filter((one) => one !== listener);
    },
    fire(type) {
      for (const listener of listeners[type] ?? []) {
        listener();
      }
    },
    setSurfaceHandle() {},
    clearSurfaceHandle() {},
    setCaptionViewHandle() {},
    clearCaptionViewHandle() {},
    async play() {},
  };
}

jest.mock('../../src/utils/VideoHandler', () => ({
  VideoHandler: class {
    data: unknown;
    private readonly ref: { current: unknown };
    private readonly setInitialized: (value: boolean) => void;

    constructor(
      videoRef: { current: unknown },
      _player: unknown,
      data: unknown,
      setIsVideoInitialized: (value: boolean) => void,
    ) {
      this.ref = videoRef;
      this.data = data;
      this.setInitialized = setIsVideoInitialized;
    }

    preBufferVideo() {
      this.ref.current = mockMedia;
      this.setInitialized(true);
    }

    destroyVideoElements() {}
  },
}));

const burstsMapText = fs.readFileSync(
  path.join(__dirname, '..', 'calmframes', 'fixtures', 'bursts.flashmap.json'),
  'utf8',
);
const BURSTS = JSON.parse(burstsMapText);
const BURSTS_MADE_AT = Date.parse(BURSTS.created_utc);

// With the default 500 ms guard band the covers are 3867 to 8267, 13867 to
// 18267 and 23867 to 28267, and each countdown starts five seconds before one.

const data = {
  id: 'bursts',
  title: 'Test pattern',
  uri: 'https://example.invalid/bursts.mp4',
  format: 'MP4',
  categories: [],
  channelID: '',
  posterUrl: '',
  description: '',
  mediaType: 'video',
  mediaSourceType: 'url',
  uhd: false,
  secure: false,
  rentAmount: '',
};

const guarded = {
  sha256: BURSTS.source.sha256,
  maps: { wcag: burstsMapText },
  durationMs: 30_000,
  titleId: 'bursts',
  chimeEnabled: false,
};

function renderPlayer(params: Record<string, unknown>) {
  return render(
    <PlayerScreen
      navigation={{ goBack: jest.fn() } as never}
      route={{ params: { data, ...params } } as never}
    />,
  );
}

async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

/** Put the playhead at a time and let the schedule see it. */
async function playAt(seconds: number) {
  const media = mockMedia as FakeMedia;
  media.currentTime = seconds;
  await act(async () => {
    media.fire('playing');
    media.fire('timeupdate');
    jest.advanceTimersByTime(100);
  });
}

/** The props PlayerScreen handed the sample's chrome on its last render. */
function chromeProps(): Record<string, unknown> {
  const found = screen.UNSAFE_root.findAll(
    (node) => (node.type as unknown) === 'VideoPlayerUI',
  );
  expect(found).toHaveLength(1);
  return found[0].props as Record<string, unknown>;
}

const cardKind = () =>
  screen.queryByTestId('calm-card-title')?.props.children ?? 'none';

describe('the player hands OK to Skip only while Skip is on screen', () => {
  beforeEach(() => {
    mockMedia = makeMedia();
    jest.useFakeTimers();
    jest.setSystemTime(BURSTS_MADE_AT + 1_000);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('gives OK to Skip during each countdown and back afterwards', async () => {
    renderPlayer({ guarded });
    await settle();

    await playAt(1);
    expect(cardKind()).toBe('Flashing part coming up');
    expect(screen.getByTestId('calm-card-skip')).toBeTruthy();
    expect(chromeProps().skipOwnsSelect).toBe(true);

    await playAt(5);
    expect(cardKind()).toBe('Hiding a flashing part');
    expect(chromeProps().skipOwnsSelect).toBe(false);

    await playAt(8.5);
    expect(cardKind()).toMatch(/^Hid /);
    expect(chromeProps().skipOwnsSelect).toBe(false);

    // The next countdown takes OK again.
    await playAt(9);
    expect(cardKind()).toBe('Flashing part coming up');
    expect(chromeProps().skipOwnsSelect).toBe(true);
  });

  it('leaves OK alone on a card with no Skip button', async () => {
    // A title with no map: the picture stays hidden behind the refusal card,
    // which has nothing to skip.
    renderPlayer({});
    await settle();
    expect(cardKind()).toBe('Not checked yet');
    expect(screen.queryByTestId('calm-card-skip')).toBeNull();
    expect(chromeProps().skipOwnsSelect).toBe(false);
  });
});

/** The 'change' listener PlayerScreen gave Kepler most recently. */
function appStateListener(): (state: string) => void {
  const manager = (useKeplerAppStateManager as jest.Mock).mock.results[0]
    .value as { addAppStateListener: jest.Mock };
  const changes = manager.addAppStateListener.mock.calls.filter(
    (call) => call[0] === 'change',
  );
  expect(changes.length).toBeGreaterThan(0);
  return changes[changes.length - 1][1];
}

describe('every Kepler app state change leaves a debug line', () => {
  let log: jest.SpyInstance;

  beforeEach(() => {
    mockMedia = makeMedia();
    jest.useFakeTimers();
    jest.setSystemTime(BURSTS_MADE_AT + 1_000);
    log = jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    log.mockRestore();
    jest.useRealTimers();
  });

  const appStateLines = () =>
    log.mock.calls
      .map((call) => String(call[0]))
      .filter((line) => line.startsWith('[PlayerScreen.tsx] - handleAppStateChange'));

  it('says which state arrived, and that a kid mode player leaves on background', async () => {
    renderPlayer({ guarded });
    await settle();
    const listener = appStateListener();

    act(() => listener('inactive'));
    act(() => listener('active'));
    act(() => listener('background'));

    expect(appStateLines()).toEqual([
      '[PlayerScreen.tsx] - handleAppStateChange - KeplerAppStateChange to inactive',
      '[PlayerScreen.tsx] - handleAppStateChange - KeplerAppStateChange to active',
      '[PlayerScreen.tsx] - handleAppStateChange - KeplerAppStateChange to background',
      '[PlayerScreen.tsx] - handleAppStateChange - background, leaving the player',
    ]);
  });

  it('says a measurement run stays on the player when it is sent to the background', async () => {
    renderPlayer({ coverTest: 'layering', toggleEveryMs: 1_000 });
    await settle();

    act(() => appStateListener()('background'));

    expect(appStateLines()).toEqual([
      '[PlayerScreen.tsx] - handleAppStateChange - KeplerAppStateChange to background',
      '[PlayerScreen.tsx] - handleAppStateChange - background, a measurement run stays on the player',
    ]);
  });
});
