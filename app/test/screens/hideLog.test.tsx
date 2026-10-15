/**
 * The hide log, from the cover that caused it to the line a parent reads.
 *
 * This is the end that was missing. The guard has always reported every cover
 * through `onHide` and the parent area has always been able to draw a log, but
 * nothing joined the two, so a household saw "Nothing has been hidden yet"
 * however much had been. The join is the module-level store in
 * hideLogStore.ts, and the test that matters is the one that goes all the way:
 * a real cover in the real player, then the shelf's parent area, with the
 * player torn down in between the way a navigation back tears it down.
 *
 * What is faked and what is not. The sample's video plumbing is replaced, the
 * same way test/screens/PlayerScreen.test.tsx replaces it, with one addition:
 * this stand in puts a fake media element in the player's ref, because the
 * cover schedule only runs against an element it can listen to. Everything
 * this test is about is real: the map is the signed bursts fixture read by the
 * real Ed25519 reader, the schedule is the real one, the store is the real one
 * and the parent area is the real screen.
 *
 * Seen to fail twice, once at each end of the join.
 *
 * With the `onHide` call taken out of PlayerScreen, so the player covers the
 * picture and tells nobody, three of these went red and the first said:
 *
 *     ● the hide log › the player writes one entry per cover, and the parent
 *       area shows it
 *
 *       expect(received).toHaveLength(expected)
 *
 *       Expected length: 1
 *       Received length: 0
 *       Received array:  []
 *
 *       at Object.toHaveLength (test/screens/hideLog.test.tsx:273:21)
 *
 * With the write left alone and the read severed instead, `profileLogs = {}`
 * in KidModeScreen rather than the store, the same test said:
 *
 *     ● the hide log › the player writes one entry per cover, and the parent
 *       area shows it
 *
 *       expect(received).toBe(expected) // Object.is equality
 *
 *       Expected: "1 part, 4 seconds in all."
 *       Received: "Nothing has been hidden yet."
 *
 *       at Object.toBe (test/screens/hideLog.test.tsx:293:72)
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import {
  readHideLogs,
  recordHide,
  resetHideLogs,
  UNATTRIBUTED_PROFILE_ID,
  forgetProfile,
  subscribeHideLogs,
} from '../../src/calmframes/hideLogStore';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { allProfileHides, logForProfile } from '../../src/calmframes/profiles';
import KidModeScreen from '../../src/screens/KidModeScreen';
import PlayerScreen from '../../src/screens/PlayerScreen';

jest.mock('../../src/w3cmedia/mediacontrols/VideoPlayerUI', () => 'VideoPlayerUI');
jest.mock('../../src/services/bif/bifService', () => ({
  getBifFrameImageSource: jest.fn(async () => null),
}));

/**
 * The fake player the stand in hands to the screen, one per test.
 *
 * Named with the `mock` prefix because a jest module factory is not allowed to
 * reach any other outside variable.
 */
let mockMedia: FakeMedia | null = null;

interface FakeMedia {
  currentTime: number;
  playbackRate: number;
  currentSrc: string;
  addEventListener: (type: string, listener: () => void) => void;
  removeEventListener: (type: string, listener: () => void) => void;
  fire: (type: string) => void;
  /** The surface and caption plumbing the screen drives. All no-ops here. */
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

/**
 * A stand in for the sample's video plumbing.
 *
 * Two things the real one does: it puts a media element in the ref the screen
 * holds, and it says the video is initialized. Both are what turn the guard's
 * schedule on.
 */
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
/** The map fixture is signed by the key this build ships, so the player reads it. */
const BURSTS_MADE_AT = Date.parse(BURSTS.created_utc);
/** The bundled title's own map, for the shelf the parent area sits on. */
const OFFLINE_MADE_AT = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc);

// Segments are 4367 to 7767, 14367 to 17767 and 24367 to 27767. With the
// default 500 ms guard band the first interval is 3867 to 8267.
const FIRST_INTERVAL_START_MS = 3_867;
const FIRST_INTERVAL_END_MS = 8_267;

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

function guardedParams(extra: Record<string, unknown> = {}) {
  return {
    sha256: BURSTS.source.sha256,
    maps: { wcag: burstsMapText },
    durationMs: 30_000,
    titleId: 'bursts',
    // Off, so nothing in this test depends on an audio path.
    chimeEnabled: false,
    profileId: 'profile-1',
    profileName: 'Kid',
    ...extra,
  };
}

/** Let the map check, which is asynchronous, finish. */
async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

/** Play from the top into the first flagged part, and out the other side. */
async function playIntoTheFirstCover(player: FakeMedia) {
  player.currentTime = 0;
  await act(async () => {
    player.fire('playing');
    jest.advanceTimersByTime(100);
  });
  player.currentTime = 5;
  await act(async () => {
    player.fire('timeupdate');
    jest.advanceTimersByTime(100);
  });
}

/** The first run, end to end, with the PIN 1357. */
function finishFirstRun() {
  const type = (digits: string) => {
    for (const digit of digits) {
      fireEvent.press(screen.getByTestId(`kid-mode-first-run-key-${digit}`));
    }
  };
  type('1357');
  type('1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-done'));
}

/** Open the parent area on a freshly rendered shelf, through the PIN. */
async function openParentArea() {
  render(
    <KidModeScreen
      navigation={{ navigate: jest.fn() } as never}
      newSalt={() => 'test-salt'}
      nowMs={() => OFFLINE_MADE_AT + 60_000}
    />,
  );
  await act(async () => { await Promise.resolve(); });
  finishFirstRun();
  await act(async () => { await Promise.resolve(); });
  fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
  for (const digit of '1357') {
    fireEvent.press(screen.getByTestId(`kid-mode-parent-key-${digit}`));
  }
  await act(async () => { await Promise.resolve(); });
}

describe('the hide log', () => {
  beforeEach(() => {
    resetHideLogs();
    mockMedia = makeMedia();
    jest.useFakeTimers();
    jest.setSystemTime(BURSTS_MADE_AT + 1_000);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('the player writes one entry per cover, and the parent area shows it', async () => {
    const player = mockMedia as FakeMedia;
    const { unmount } = render(
      <PlayerScreen
        navigation={{ goBack: jest.fn() } as never}
        route={{ params: { data, guarded: guardedParams() } } as never}
      />,
    );
    await settle();
    await playIntoTheFirstCover(player);

    expect(screen.getByTestId('calm-frames-cover')).toBeTruthy();
    const entries = logForProfile(readHideLogs(), 'profile-1').entries;
    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      titleId: 'bursts',
      titleName: 'Test pattern',
      profileId: 'profile-1',
      profileName: 'Kid',
      positionMs: FIRST_INTERVAL_START_MS,
      endMs: FIRST_INTERVAL_END_MS,
      durationMs: FIRST_INTERVAL_END_MS - FIRST_INTERVAL_START_MS,
      cause: 'schedule',
      reason: 'general',
      preset: 'wcag',
    });

    // The way back from the player: the screen is torn down, then the shelf is
    // opened again from nothing. The line is still there, because the store is
    // a module rather than either screen's state.
    unmount();
    jest.setSystemTime(OFFLINE_MADE_AT + 60_000);
    await openParentArea();
    expect(screen.getByTestId('kid-mode-parent-total').props.children).toBe(
      '1 scene hidden, 4 seconds in total.',
    );
    expect(screen.getByTestId('kid-mode-parent-log-0').props.children).toContain(
      'Test pattern',
    );
  });

  it('writes one entry for a cover, however long it is held', async () => {
    const player = mockMedia as FakeMedia;
    render(
      <PlayerScreen
        navigation={{ goBack: jest.fn() } as never}
        route={{ params: { data, guarded: guardedParams() } } as never}
      />,
    );
    await settle();
    await playIntoTheFirstCover(player);

    // Twenty more scheduler ticks inside the same interval, which is what a
    // second of real playback looks like.
    for (const at of [5.5, 6, 6.5, 7, 7.5]) {
      player.currentTime = at;
      await act(async () => {
        player.fire('timeupdate');
        jest.advanceTimersByTime(200);
      });
    }
    expect(logForProfile(readHideLogs(), 'profile-1').entries).toHaveLength(1);
  });

  it('files a hide under the kid who was watching, and nobody else', async () => {
    const player = mockMedia as FakeMedia;
    render(
      <PlayerScreen
        navigation={{ goBack: jest.fn() } as never}
        route={{
          params: {
            data,
            guarded: guardedParams({ profileId: 'profile-2', profileName: 'Sam' }),
          },
        } as never}
      />,
    );
    await settle();
    await playIntoTheFirstCover(player);

    expect(logForProfile(readHideLogs(), 'profile-2').entries).toHaveLength(1);
    expect(logForProfile(readHideLogs(), 'profile-1').entries).toEqual([]);
    expect(allProfileHides(readHideLogs()).entries).toHaveLength(1);
  });

  it('records a hide nobody can attribute rather than dropping it', () => {
    // A caller that did not come through the shelf still gets a guarded
    // player, and a cover it caused is still something that happened.
    const stored = recordHide({
      atMs: 1_000,
      titleId: 'bursts',
      titleName: 'Test pattern',
      positionMs: 1_000,
      durationMs: 2_000,
      cause: 'schedule',
    });
    expect(stored.profileId).toBe(UNATTRIBUTED_PROFILE_ID);
    expect(stored.endMs).toBe(3_000);
    expect(allProfileHides(readHideLogs()).entries).toHaveLength(1);
  });

  it('says nothing has been hidden when nothing has', async () => {
    await openParentArea();
    expect(screen.getByTestId('kid-mode-parent-total').props.children).toBe(
      'No scenes hidden yet.',
    );
  });
});

describe('removing a kid removes their record', () => {
  /**
   * The confirmation a parent reads says the hidden segment record goes with
   * the kid. Until forgetProfile existed it did not: the entries stayed in the
   * module level store, out of sight, and the Everyone view would still have
   * flattened them in. A promise a screen makes is a thing the code owes.
   *
   * Seen to fail. Making forgetProfile return without touching `logs` reads
   * `expect(received).toBeUndefined() / Received: [{...}]` on the first case,
   * and `expect(jest.fn()).toHaveBeenCalled() / Number of calls: 0` on the
   * second.
   */
  const hide = (profileId: string, titleId: string) =>
    recordHide(
      {
        atMs: 1_000,
        titleId,
        titleName: 'Test pattern',
        positionMs: 1_000,
        durationMs: 1_000,
        cause: 'schedule',
      },
      { profileId, profileName: profileId },
    );

  it('forgets the entries, and leaves every other kid alone', () => {
    resetHideLogs();
    hide('kid-a', 't1');
    hide('kid-b', 't2');
    expect(readHideLogs()['kid-a'].entries).toHaveLength(1);

    forgetProfile('kid-a');

    expect(readHideLogs()['kid-a']).toBeUndefined();
    expect(readHideLogs()['kid-b'].entries).toHaveLength(1);
  });

  it('tells anyone watching the store that it changed', () => {
    resetHideLogs();
    hide('kid-a', 't1');
    const heard = jest.fn();
    const stop = subscribeHideLogs(heard);
    forgetProfile('kid-a');
    stop();
    expect(heard).toHaveBeenCalled();
  });
});
