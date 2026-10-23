import { createNativeRetryProbe } from '../../src/calmframes/nativeRetryProbe';

test('ineligible or absent checkpoint cannot inject or consume the probe', () => {
  const probe = createNativeRetryProbe(), pause = jest.fn(), fail = jest.fn();
  expect(probe.trigger(false, pause, fail)).toBe(false);
  expect(probe.used()).toBe(false);
  expect(pause).not.toHaveBeenCalled(); expect(fail).not.toHaveBeenCalled();
});

test('explicit fault pauses before failure and cannot recur after Retry or reentry', () => {
  const probe = createNativeRetryProbe(), events: string[] = [];
  const fail = () => {events.push('covered-error'); expect(probe.trigger(true, () => events.push('bad'), () => events.push('bad'))).toBe(false);};
  expect(probe.trigger(true, () => events.push('pause'), fail)).toBe(true);
  expect(events).toEqual(['pause', 'covered-error']);
  expect(probe.trigger(true, () => events.push('bad'), fail)).toBe(false);
});

test('pause exception still requests the production covered error and consumes the probe', () => {
  const probe = createNativeRetryProbe(), fail = jest.fn();
  expect(probe.trigger(true, () => {throw new Error('pause');}, fail)).toBe(true);
  expect(fail).toHaveBeenCalledTimes(1); expect(probe.used()).toBe(true);
});
