/**
 * One debug line for every call Vega Media Controls makes on the player.
 *
 * On a device the first questions are which commands arrive at all, how many
 * per press, and in what order: does a fast forward press arrive once, does
 * the remote's play button come through here or as a key. The answer is a log
 * line per call, written with console.log so the Release build strips it (see
 * releaseLogs.test.ts).
 *
 * SafeMediaControlHandler used to override only the six commands that move the
 * playhead, so play, pause and the rest went straight to the base class and
 * left no trace. They are overridden now only to log, and still hand the call
 * to the base class, which this test also checks: logging must not change what
 * a command does.
 *
 * Seen to fail, Oct 9 2026: with the seek line in goTo written with
 * console.info instead, all six seek cases went red with no line found; with
 * handlePause's override deleted, its pass-through case and the completeness
 * test went red.
 */

import fs from 'fs';
import path from 'path';

jest.mock('@amazon-devices/react-native-w3cmedia', () => {
  // The real base class keeps its callbacks on the prototype, so the mock does
  // too; an instance field would shadow the override being tested. Every call
  // that reaches the base is recorded.
  const baseCalls: string[] = [];
  class KeplerMediaControlHandler {
    static baseCalls = baseCalls;
  }
  const names = [
    'handlePlay', 'handlePause', 'handleTogglePlayPause', 'handleStop',
    'handleStartOver', 'handleFastForward', 'handleRewind', 'handleSeek',
    'handleSetPlaybackSpeed', 'handleSkipForward', 'handleSkipBackward',
    'handleSetAudioVolume', 'handleSetAudioTrack', 'handleEnableTextTrack',
    'handleNext', 'handlePrevious', 'handleEnableShuffle', 'handleSetRepeatMode',
    'handleSetRating', 'handleDisableTextTrack', 'handleGetMetadataInfo',
    'handleCustomAction', 'handleGetSessionState',
  ];
  for (const name of names) {
    (KeplerMediaControlHandler.prototype as unknown as Record<string, unknown>)[
      name
    ] = async function base() {
      baseCalls.push(name);
      return name === 'handleGetSessionState' ? [] : undefined;
    };
  }
  return { __esModule: true, KeplerMediaControlHandler };
});

import { KeplerMediaControlHandler } from '@amazon-devices/react-native-w3cmedia';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import { SafeMediaControlHandler } from '../../src/calmframes/SafeMediaControlHandler';
import { createSeekEngine } from '../../src/calmframes/seekSafety';

const PREFIX = '[SafeMediaControlHandler.ts]';

const baseCalls = (
  KeplerMediaControlHandler as unknown as { baseCalls: string[] }
).baseCalls;

function makeHandler(currentMs = 20_000) {
  const intervals = buildCoverIntervals([{ startMs: 10_000, endMs: 14_000 }], {
    guardBandMs: 500,
    durationMs: 60_000,
  });
  const engine = createSeekEngine({
    getIntervals: () => intervals,
    getDurationMs: () => 60_000,
    setCover: () => {},
    seekTo: () => {},
  });
  return new SafeMediaControlHandler({
    engine,
    getCurrentMs: () => currentMs,
    stepMs: 10_000,
  });
}

/** The debug lines the handler wrote, and nothing else. */
function handlerLines(spy: jest.SpyInstance): string[] {
  return spy.mock.calls
    .map((call) => String(call[0]))
    .filter((line) => line.startsWith(PREFIX));
}

type Call = [string, (handler: SafeMediaControlHandler) => Promise<unknown>];

// The playhead is at 20 s and the one cover runs from 9.5 s to 14.5 s, so
// three of these land inside it and three do not.
const SEEKS: Array<[string, (handler: SafeMediaControlHandler) => Promise<unknown>, RegExp]> = [
  ['handleSeek', (h) => h.handleSeek({ seconds: 12, nanoseconds: 0 }), /asked for 12000 ms, going to 12000 ms, cover first/],
  ['handleSkipForward', (h) => h.handleSkipForward({ seconds: 5, nanoseconds: 0 }), /asked for 25000 ms, going to 25000 ms, no cover needed/],
  ['handleSkipBackward', (h) => h.handleSkipBackward({ seconds: 8, nanoseconds: 0 }), /asked for 12000 ms, going to 12000 ms, cover first/],
  ['handleFastForward', (h) => h.handleFastForward(), /asked for 30000 ms, going to 30000 ms, no cover needed/],
  ['handleRewind', (h) => h.handleRewind(), /asked for 10000 ms, going to 10000 ms, cover first/],
  ['handleStartOver', (h) => h.handleStartOver(), /asked for 0 ms, going to 0 ms, no cover needed/],
];

const PASS_THROUGH: Call[] = [
  ['handlePlay', (h) => h.handlePlay()],
  ['handlePause', (h) => h.handlePause()],
  ['handleTogglePlayPause', (h) => h.handleTogglePlayPause()],
  ['handleStop', (h) => h.handleStop()],
  ['handleSetPlaybackSpeed', (h) => h.handleSetPlaybackSpeed(2)],
  ['handleSetAudioVolume', (h) => h.handleSetAudioVolume(0.5)],
  ['handleSetAudioTrack', (h) => h.handleSetAudioTrack({} as never)],
  ['handleEnableTextTrack', (h) => h.handleEnableTextTrack({} as never)],
  ['handleDisableTextTrack', (h) => h.handleDisableTextTrack()],
  ['handleNext', (h) => h.handleNext()],
  ['handlePrevious', (h) => h.handlePrevious()],
  ['handleEnableShuffle', (h) => h.handleEnableShuffle(true)],
  ['handleSetRepeatMode', (h) => h.handleSetRepeatMode(0 as never)],
  ['handleSetRating', (h) => h.handleSetRating({} as never, 3)],
  ['handleGetMetadataInfo', (h) => h.handleGetMetadataInfo({} as never)],
  ['handleCustomAction', (h) => h.handleCustomAction({} as never)],
  ['handleGetSessionState', (h) => h.handleGetSessionState()],
];

describe('every media control call leaves one debug line', () => {
  let log: jest.SpyInstance;

  beforeEach(() => {
    baseCalls.length = 0;
    log = jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    log.mockRestore();
  });

  it.each(SEEKS)('%s says where it was asked to go and what the guard did', async (name, call, detail) => {
    await call(makeHandler());
    const lines = handlerLines(log);
    expect(lines).toHaveLength(1);
    expect(lines[0].startsWith(`${PREFIX} - ${name} - `)).toBe(true);
    expect(lines[0]).toMatch(detail);
    // Still never the base class, which would move the playhead uncovered.
    expect(baseCalls).toEqual([]);
  });

  it.each(PASS_THROUGH)('%s is logged and still handed to the base class', async (name, call) => {
    await call(makeHandler());
    const lines = handlerLines(log);
    expect(lines).toHaveLength(1);
    expect(lines[0].startsWith(`${PREFIX} - ${name} - `)).toBe(true);
    expect(baseCalls).toEqual([name]);
  });

  it('overrides every callback the pinned SDK declares, so none goes unlogged', () => {
    // Read from the SDK's own declaration rather than a list kept here, so a
    // callback added by a new SDK shows up as a failure instead of a silence.
    const declaration = fs.readFileSync(
      path.join(
        __dirname,
        '..',
        '..',
        'node_modules',
        '@amazon-devices',
        'react-native-w3cmedia',
        'dist',
        'interface',
        'KeplerMediaControlHandler.d.ts',
      ),
      'utf8',
    );
    const declared = [...declaration.matchAll(/^\s+(handle\w+)\(/gm)].map(
      (match) => match[1],
    );
    expect(declared.length).toBeGreaterThan(20);
    const own = Object.getOwnPropertyNames(SafeMediaControlHandler.prototype);
    expect(declared.filter((name) => !own.includes(name))).toEqual([]);
    // And the two lists above are that same set, so each one is exercised.
    expect(
      [...SEEKS.map((one) => one[0]), ...PASS_THROUGH.map((one) => one[0])].sort(),
    ).toEqual([...declared].sort());
  });
});
