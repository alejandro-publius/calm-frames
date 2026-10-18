import { DEFAULT_MAX_MAP_AGE_MS } from '../../src/calmframes/flashMap';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import {
  CoverageSample,
  evaluateCoverage,
} from '../../src/calmframes/integration/coverageController';
import {
  attachVegaCoverage,
  VegaCoveragePlayer,
} from '../../src/calmframes/integration/vegaCoverageAdapter';
import { VegaIntegrationControls } from '../../src/calmframes/integration/VegaIntegrationControls';
import {
  coverageData,
  VerifiedCoverage,
  verifyPackagedCoverage,
} from '../../src/calmframes/integration/verifiedCoverage';
import {
  ACADIA_SOURCE_SHA256,
  packagedLibrary,
} from '../../src/calmframes/packagedLibrary';
jest.mock('@amazon-devices/react-native-w3cmedia', () => ({
  KeplerMediaControlHandler: class {},
}));
const title = packagedLibrary
  .consumerTitles(DEFAULT_SETTINGS)
  .find((t) => t.sha256 === ACADIA_SOURCE_SHA256)!;
const now = Date.parse(JSON.parse(title.maps!.wcag!).created_utc) + 60000;
const token = verifyPackagedCoverage(title, DEFAULT_SETTINGS, now)!;
const first = coverageData(token)!.intervals[0];
const base: CoverageSample = {
  identity: token.identity,
  nowMs: now,
  positionMs: 0,
  durationMs: title.durationMs!,
  paused: false,
  buffering: false,
  seeking: false,
  foreground: true,
  synchronized: true,
  playbackRate: 1,
};
const decide = (change: Partial<CoverageSample>) =>
  evaluateCoverage(token, { ...base, ...change });

it('uses exact approved metadata and refuses forged tokens, wrong assets and stale maps', () => {
  expect(token).not.toBeNull();
  expect(
    verifyPackagedCoverage(
      { ...title, renditionSha256: '0'.repeat(64) },
      DEFAULT_SETTINGS,
      now,
    ),
  ).toBeNull();
  expect(
    verifyPackagedCoverage(
      { ...title, renditionStartOffsetMs: 151 },
      DEFAULT_SETTINGS,
      now,
    ),
  ).toBeNull();
  expect(
    verifyPackagedCoverage(
      { ...title, maps: { ...title.maps, wcag: title.maps!.wcag! + ' ' } },
      DEFAULT_SETTINGS,
      now,
    ),
  ).toBeNull();
  expect(
    verifyPackagedCoverage(
      title,
      DEFAULT_SETTINGS,
      now + DEFAULT_MAX_MAP_AGE_MS,
    ),
  ).toBeNull();
  expect(verifyPackagedCoverage(title, DEFAULT_SETTINGS, NaN)).toBeNull();
  expect(
    evaluateCoverage({ identity: token.identity } as VerifiedCoverage, base)
      .action,
  ).toBe('unavailable');
  expect(decide({ nowMs: now + DEFAULT_MAX_MAP_AGE_MS }).action).toBe(
    'unavailable',
  );
  expect(decide({ nowMs: now - 1 }).action).toBe('unavailable');
});
it('uses authoritative start-inclusive/end-exclusive intervals and next boundaries', () => {
  expect(decide({ positionMs: first.startMs - 1 })).toMatchObject({
    action: 'restore',
    nextBoundary: { afterMs: 1, action: 'cover' },
  });
  expect(decide({ positionMs: first.startMs })).toMatchObject({
    action: 'cover',
    nextBoundary: { positionMs: first.endMs, action: 'restore' },
  });
  expect(decide({ positionMs: first.endMs }).action).toBe('restore');
});
it('pause inside an interval retains cover without a wall-clock release', () => {
  expect(decide({ positionMs: first.startMs + 1, paused: true })).toMatchObject(
    { action: 'cover', nextBoundary: undefined },
  );
});
it.each(['buffering', 'seeking'] as const)('%s retains cover', (key) =>
  expect(decide({ [key]: true }).action).toBe('cover'),
);
it.each(['foreground', 'synchronized'] as const)(
  'missing %s retains cover',
  (key) => expect(decide({ [key]: false }).action).toBe('cover'),
);
it.each([
  'uri',
  'assetSha256',
  'sourceSha256',
  'editionId',
  'timelineId',
] as const)('refuses mismatched %s', (key) => {
  expect(
    decide({ identity: { ...token.identity, [key]: 'other' } }).action,
  ).toBe('unavailable');
});
it.each([NaN, Infinity, -1, title.durationMs! + 1])(
  'refuses invalid clock %s',
  (positionMs) => expect(decide({ positionMs }).action).toBe('unavailable'),
);
it.each([0, -1, NaN, 2])('refuses unsupported rate %s', (playbackRate) =>
  expect(decide({ playbackRate }).action).toBe('unavailable'),
);
it('refuses duration drift and snapshots caller metadata', () => {
  expect(decide({ durationMs: base.durationMs + 1 }).action).toBe(
    'unavailable',
  );
  const input = { ...title },
    settings = { ...DEFAULT_SETTINGS };
  const isolated = verifyPackagedCoverage(input, settings, now)!;
  input.uri = 'other';
  settings.tvDiagonalIn = 1000;
  expect(evaluateCoverage(isolated, base).action).toBe('restore');
  expect(Object.isFrozen(coverageData(token)!.intervals[0])).toBe(true);
});

function setup() {
  const listeners = new Map<string, Set<() => void>>();
  const player = {
    currentTime: 0,
    duration: title.durationMs! / 1000,
    paused: true,
    playbackRate: 1,
    loop: false,
    seeking: false,
    readyState: 4,
    src: title.uri,
    currentSrc: title.uri,
    pause: jest.fn(),
    play: jest.fn(async (): Promise<void> => undefined),
    addEventListener: jest.fn((name: string, fn: () => void) => {
      if (!listeners.has(name)) listeners.set(name, new Set());
      listeners.get(name)!.add(fn);
    }),
    removeEventListener: jest.fn((name: string, fn: () => void) =>
      listeners.get(name)?.delete(fn),
    ),
  };
  const host = {
    now: () => now,
    identity: () => token.identity,
    onDecision: jest.fn(),
    presentCover: jest.fn(async (): Promise<void> => undefined),
    seek: jest.fn(async (): Promise<void> => undefined),
  };
  const adapter = attachVegaCoverage(
    player as unknown as VegaCoveragePlayer,
    token,
    host,
  );
  const emit = (name: string) => listeners.get(name)?.forEach((fn) => fn());
  const sync = () => adapter.synchronize(adapter.generation());
  const last = () =>
    host.onDecision.mock.calls[host.onDecision.mock.calls.length - 1][0];
  return { player, host, adapter, emit, sync, last, listeners };
}
beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  jest.clearAllTimers();
  jest.useRealTimers();
});
it('attach blocks until host confirms timeline; detach removes every listener and timer', () => {
  const s = setup();
  expect(s.last().action).toBe('cover');
  s.sync();
  expect(s.last().action).toBe('restore');
  s.player.paused = false;
  s.emit('timeupdate');
  expect(jest.getTimerCount()).toBe(1);
  s.adapter.detach();
  const count = s.host.onDecision.mock.calls.length;
  s.emit('timeupdate');
  jest.runAllTimers();
  expect(s.host.onDecision).toHaveBeenCalledTimes(count);
  expect([...s.listeners.values()].every((set) => set.size === 0)).toBe(true);
  expect(jest.getTimerCount()).toBe(0);
});
it('awaits presented cover before seek and refuses stale confirmation when seeking in/out', async () => {
  const s = setup();
  s.sync();
  const old = s.adapter.generation();
  let acknowledge!: () => void;
  s.host.presentCover.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        acknowledge = resolve;
      }),
  );
  const pending = s.adapter.seek(first.startMs + 1);
  expect(s.host.seek).not.toHaveBeenCalled();
  expect(s.adapter.synchronize(old)).toBe(false);
  acknowledge();
  expect(await pending).toBe(true);
  s.emit('timeupdate');
  expect(s.last().action).toBe('cover');
  s.player.currentTime = (first.startMs + 1) / 1000;
  s.emit('seeked');
  s.sync();
  expect(s.last().action).toBe('cover');
  s.host.presentCover.mockResolvedValue(undefined);
  await s.adapter.seek(first.endMs + 1);
  s.emit('timeupdate');
  expect(s.last().action).toBe('cover');
  s.player.currentTime = (first.endMs + 1) / 1000;
  s.emit('seeked');
  s.sync();
  expect(s.last().action).toBe('restore');
});
it('overlapping seeks are refused until the active operation settles', async () => {
  const s = setup();
  let done!: () => void;
  s.host.presentCover.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        done = resolve;
      }),
  );
  const one = s.adapter.seek(1000),
    two = s.adapter.seek(2000);
  expect(await two).toBe(false);
  done();
  expect(await one).toBe(true);
  expect(s.host.seek).toHaveBeenCalledTimes(1);
  expect(s.host.seek).toHaveBeenCalledWith(1000);
});
it('a dispatched transport keeps synchronization blocked until settlement', async () => {
  const s = setup();
  let finish!: () => void;
  s.host.seek.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        finish = resolve;
      }),
  );
  const one = s.adapter.seek(1000);
  await Promise.resolve();
  expect(s.host.seek).toHaveBeenCalledTimes(1);
  expect(await s.adapter.seek(2000)).toBe(false);
  expect(s.sync()).toBe(false);
  finish();
  expect(await one).toBe(true);
  expect(s.sync()).toBe(true);
});
it('background pauses, cancels pending play and requires a new confirmation on resume', async () => {
  const s = setup();
  s.sync();
  const before = s.adapter.generation();
  let done!: () => void;
  s.host.presentCover.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        done = resolve;
      }),
  );
  const pending = s.adapter.play();
  s.adapter.setForeground(false);
  done();
  expect(await pending).toBe(false);
  expect(s.player.pause).toHaveBeenCalled();
  expect(s.player.play).not.toHaveBeenCalled();
  s.adapter.setForeground(true);
  expect(s.adapter.synchronize(before)).toBe(false);
  expect(s.last().action).toBe('cover');
  s.sync();
  expect(s.last().action).toBe('restore');
});
it('waiting and stalled states cannot be cleared by a timeupdate', () => {
  const s = setup();
  s.sync();
  s.emit('waiting');
  s.emit('timeupdate');
  expect(s.last().action).toBe('cover');
  s.emit('playing');
  expect(s.last().action).toBe('cover');
  s.sync();
  expect(s.last().action).toBe('restore');
});
it('boundary timer only hides and stalled sample watchdog requires confirmation', () => {
  const s = setup();
  s.player.currentTime = (first.startMs - 10) / 1000;
  s.player.paused = false;
  s.sync();
  jest.advanceTimersByTime(10);
  expect(s.last().action).toBe('cover');
  s.emit('timeupdate');
  expect(s.last().action).toBe('cover');
  s.player.currentTime = first.startMs / 1000;
  s.emit('timeupdate');
  jest.advanceTimersByTime(250);
  expect(s.last().action).toBe('cover');
  s.player.currentTime = (first.endMs + 1) / 1000;
  s.emit('timeupdate');
  expect(s.last().action).toBe('cover');
  s.sync();
  expect(s.last().action).toBe('restore');
});
it('rapid title replacement detaches pending work; a reused player with wrong URI fails closed', async () => {
  const s = setup();
  let done!: () => void;
  s.host.presentCover.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        done = resolve;
      }),
  );
  const pending = s.adapter.play();
  s.adapter.detach();
  done();
  expect(await pending).toBe(false);
  expect(s.player.play).not.toHaveBeenCalled();
  const replacement = setup();
  replacement.player.currentSrc = 'other';
  replacement.sync();
  expect(replacement.last().action).toBe('unavailable');
});
it('rejected play or cover acknowledgment cannot restore the picture', async () => {
  const s = setup();
  s.player.play.mockRejectedValue(new Error('player refused'));
  await expect(s.adapter.play()).rejects.toThrow('player refused');
  expect(s.last().action).toBe('unavailable');
  expect(s.sync()).toBe(false);
  const other = setup();
  other.host.presentCover.mockRejectedValue(
    new Error('no compositor acknowledgment'),
  );
  await expect(other.adapter.seek(2000)).rejects.toThrow('no compositor');
  expect(other.host.seek).not.toHaveBeenCalled();
  expect(other.sync()).toBe(false);
});
it('current metadata mismatch while awaiting cover blocks movement', async () => {
  const s = setup();
  let done!: () => void;
  s.host.presentCover.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        done = resolve;
      }),
  );
  const pending = s.adapter.seek(2000);
  s.player.currentSrc = 'changed';
  done();
  expect(await pending).toBe(false);
  expect(s.host.seek).not.toHaveBeenCalled();
  expect(s.last().action).toBe('unavailable');
});
it('system controls use the adapter and refuse repeat, speed, unverified title changes and missing adapter', async () => {
  const s = setup();
  const handler = new VegaIntegrationControls(
    () => s.adapter,
    () => 5000,
    () => true,
  );
  await handler.handlePlay();
  expect(s.player.play).toHaveBeenCalledTimes(1);
  await handler.handleSeek({ seconds: 3, nanoseconds: 0 });
  expect(s.host.seek).toHaveBeenCalledWith(3000);
  await handler.handleTogglePlayPause();
  expect(s.player.play).toHaveBeenCalledTimes(2);
  for (const action of [
    () => handler.handleSetPlaybackSpeed(),
    () => handler.handleSetRepeatMode(),
    () => handler.handleNext(),
    () => handler.handlePrevious(),
  ])
    await expect(action()).rejects.toThrow();
  await expect(
    new VegaIntegrationControls(
      () => null,
      () => 0,
      () => true,
    ).handlePlay(),
  ).rejects.toThrow('unavailable');
});

it('Pause cancels pending resume and blocks synchronization until acknowledgment settles', async () => {
  const s = setup();
  let done!: () => void;
  s.host.presentCover.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        done = resolve;
      }),
  );
  const pending = s.adapter.play();
  expect(s.sync()).toBe(false);
  expect(s.last().action).toBe('cover');
  s.adapter.pause();
  done();
  expect(await pending).toBe(false);
  expect(s.player.play).not.toHaveBeenCalled();
});
it('a detached lifecycle callback cannot pause a reused player', () => {
  const s = setup();
  s.adapter.detach();
  s.adapter.setForeground(false);
  s.adapter.pause();
  expect(s.player.pause).not.toHaveBeenCalled();
});

it('refuses a player already configured to loop', () => {
  const s = setup();
  s.player.loop = true;
  expect(s.sync()).toBe(false);
  expect(s.last().action).toBe('unavailable');
});
it('listener registration failure rolls back subscriptions after requesting cover', () => {
  const s = setup();
  s.adapter.detach();
  s.host.onDecision.mockClear();
  const add = s.player.addEventListener.getMockImplementation()!;
  s.player.addEventListener.mockImplementation((name, fn) => {
    expect(s.host.onDecision.mock.calls[0][0].action).toBe('cover');
    if (name === 'waiting') throw new Error('registration failed');
    add(name, fn);
  });
  expect(() =>
    attachVegaCoverage(
      s.player as unknown as VegaCoveragePlayer,
      token,
      s.host,
    ),
  ).toThrow('registration failed');
  expect([...s.listeners.values()].every((set) => set.size === 0)).toBe(true);
});

it('late dispatched play completion after Pause is refused and paused again', async () => {
  const s = setup();
  let complete!: () => void;
  s.player.play.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        complete = resolve;
      }),
  );
  const pending = s.adapter.play();
  await Promise.resolve();
  expect(s.player.play).toHaveBeenCalledTimes(1);
  s.adapter.pause();
  complete();
  expect(await pending).toBe(false);
  expect(s.player.pause).toHaveBeenCalledTimes(2);
  expect(s.last().action).toBe('cover');
});
