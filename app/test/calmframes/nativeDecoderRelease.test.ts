import {createDecoderReleaseBarrier} from '../../src/calmframes/nativeDecoderRelease';
const tick = async () => {await Promise.resolve(); await Promise.resolve();};
function deferred() {let resolve!: () => void; let reject!: () => void;
  const promise = new Promise<void>((yes, no) => {resolve = yes; reject = no;});
  return {promise, resolve, reject};}
afterEach(() => jest.useRealTimers());
test('new decoder remains blocked after timeout until actual native completion', async () => {
  jest.useFakeTimers(); const barrier = createDecoderReleaseBarrier(), work = deferred(), media = {};
  const destroy = jest.fn(() => work.promise), released = barrier.release(media, destroy);
  expect(barrier.release(media, destroy)).toBe(released);
  const waiting = barrier.wait(1500); await tick();
  jest.advanceTimersByTime(1500); expect(await waiting).toBe(false);
  expect(barrier.state(media)?.done).toBe(false); expect(destroy).toHaveBeenCalledTimes(1);
  work.resolve(); expect(await released).toBe(true); expect(await barrier.wait()).toBe(true);
});
test('rejection or synchronous failure cannot certify a replacement', async () => {
  for (const destroy of [() => Promise.reject(new Error('native')), () => {throw new Error('native');}]) {
    const barrier = createDecoderReleaseBarrier();
    expect(await barrier.release({}, destroy)).toBe(false);
    expect(await barrier.wait()).toBe(false);
  }
});
test('all outstanding native owners must confirm, even when another completes first', async () => {
  jest.useFakeTimers(); const barrier = createDecoderReleaseBarrier(), a = deferred(), b = deferred();
  const first = barrier.release({}, () => a.promise); barrier.release({}, () => b.promise);
  a.resolve(); await first; const waiting = barrier.wait(20); jest.advanceTimersByTime(20);
  expect(await waiting).toBe(false); b.resolve(); await tick(); expect(await barrier.wait()).toBe(true);
});
