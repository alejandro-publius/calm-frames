import { recoverPlayback, RECOVERY_TIMEOUT_MS, RecoveryPhase } from '../../src/calmframes/playbackRecovery';
function harness(paused = false) {
  const listeners = new Map<string, Set<() => void>>();
  const media = {currentTime: 0, readyState: 2, seeking: false, paused: true,
    pause: jest.fn(), play: jest.fn(async () => {}),
    addEventListener: (name: string, fn: () => void) => { if (!listeners.has(name)) listeners.set(name, new Set()); listeners.get(name)!.add(fn); },
    removeEventListener: (name: string, fn: () => void) => { listeners.get(name)?.delete(fn); }};
  const emit = (name: string) => [...(listeners.get(name) ?? [])].forEach(fn => fn());
  let show!: () => void; let current = true;
  const phases: RecoveryPhase[] = [];
  const seek = jest.fn(async (ms: number) => { media.currentTime = ms / 1000; });
  const recovery = recoverPlayback({media, positionMs: 135000, paused, current: () => current,
    presentCover: () => new Promise(resolve => {show = resolve;}), seek, phase: phase => phases.push(phase)});
  return {media, emit, show, phases, seek, recovery, invalidate: () => {current = false;}};
}
const tick = async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); };
beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());
test.each([['timeupdate', 'seeked'], ['seeked', 'timeupdate']])('cover precedes seek; native %s then %s confirms recovery', async (first, second) => {
  const h = harness(); expect(h.seek).not.toHaveBeenCalled(); h.show(); await tick();
  expect(h.seek).toHaveBeenCalledWith(135000); expect(h.media.play).not.toHaveBeenCalled();
  h.emit(first); expect(h.phases).not.toContain('ready');
  h.emit(second); await tick(); expect(h.media.play).toHaveBeenCalledTimes(1);
  expect(h.phases).toEqual(['covered', 'seeking', 'confirming', 'ready']);
});
test('paused recovery restores position without starting audio', async () => {
  const h = harness(true); h.show(); await tick(); h.emit('seeked'); h.emit('timeupdate'); await tick();
  expect(h.media.play).not.toHaveBeenCalled(); expect(h.phases[h.phases.length - 1]).toBe('ready');
});
test.each(['seeked', 'timeupdate'])('missing native %s fails closed with no timeout fallback', async missing => {
  const h = harness(); h.show(); await tick();
  if (missing !== 'seeked') h.emit('seeked');
  if (missing !== 'timeupdate') h.emit('timeupdate');
  jest.advanceTimersByTime(RECOVERY_TIMEOUT_MS); expect(h.phases[h.phases.length - 1]).toBe('failed');
  expect(h.media.play).not.toHaveBeenCalled(); h.emit('seeked'); h.emit('timeupdate'); await tick();
  expect(h.phases[h.phases.length - 1]).toBe('failed');
});
test('wrong or uncertain position cannot release the recovery cover', async () => {
  const h = harness(); h.show(); await tick(); h.media.currentTime = 10;
  h.emit('seeked'); h.emit('timeupdate'); await tick(); expect(h.media.play).not.toHaveBeenCalled();
  h.media.currentTime = 135; h.media.seeking = true; h.emit('seeked'); h.emit('timeupdate');
  jest.advanceTimersByTime(RECOVERY_TIMEOUT_MS); expect(h.phases[h.phases.length - 1]).toBe('failed');
});
test('Back during cover presentation cancels the late seek and all retries', async () => {
  const h = harness(); h.recovery.cancel(); h.show(); await tick(); jest.runAllTimers();
  expect(h.seek).not.toHaveBeenCalled(); expect(h.phases).toEqual(['covered', 'canceled']);
});
test('obsolete play completion pauses the old instance instead of exposing it', async () => {
  const h = harness(); let done!: () => void; h.media.play.mockImplementation(() => new Promise(resolve => {done = resolve;}));
  h.show(); await tick(); h.emit('seeked'); h.emit('timeupdate'); await tick();
  h.invalidate(); h.recovery.cancel(); done(); await tick();
  expect(h.phases[h.phases.length - 1]).toBe('canceled'); expect(h.media.pause).toHaveBeenCalled();
  expect(h.phases).not.toContain('ready');
});
test('a native error ends one attempt; it never reconstructs itself automatically', async () => {
  const h = harness(); h.show(); await tick(); h.emit('error'); h.emit('error'); jest.runAllTimers();
  expect(h.seek).toHaveBeenCalledTimes(1); expect(h.phases.filter(p => p === 'failed')).toHaveLength(1);
  expect(h.media.play).not.toHaveBeenCalled();
});
