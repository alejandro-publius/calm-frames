import { useTVEventHandler } from '@amazon-devices/react-native-kepler';
import { act, renderHook } from '@testing-library/react-native';
import { Platform } from 'react-native';
import { CoverInterval } from '../../src/calmframes/coverSchedule';
import {
  PictureBreakOptions,
  usePictureBreak,
} from '../../src/calmframes/usePictureBreak';

const HOLD = [{ startMs: 10_000, endMs: 12_000, sources: [] }] as unknown as CoverInterval[];

let now = 0;
const clock = () => now;
let isTV: jest.SpyInstance;

function press(eventType: string, eventKeyAction = 0) {
  const calls = (useTVEventHandler as jest.Mock).mock.calls;
  act(() => calls[calls.length - 1][0]({ eventType, eventKeyAction }));
}

function mount(initial: Partial<PictureBreakOptions> = {}) {
  return renderHook((props: PictureBreakOptions) => usePictureBreak(props), {
    initialProps: { enabled: true, intervals: [], mediaTimeMs: 3_000, nowMs: clock, ...initial },
  });
}

beforeEach(() => {
  now = 0;
  jest.useFakeTimers();
  (useTVEventHandler as jest.Mock).mockClear();
  isTV = jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(true);
});
afterEach(() => {
  jest.clearAllTimers();
  jest.useRealTimers();
  isTV.mockRestore();
});

test('Menu starts a break and a second Menu brings the picture back once the minimum has run', () => {
  const { result } = mount();
  press('menu');
  expect(result.current.resting).toBe(true);
  now = 500;
  press('menu');
  expect(result.current.resting).toBe(true);
  expect(result.current.state.waitingFor).toBe('minimum');
  now = 2_000;
  act(() => jest.advanceTimersByTime(1_501));
  expect(result.current.resting).toBe(false);
});

test('OK asks for the picture back only during a break', () => {
  const { result } = mount();
  press('select');
  expect(result.current.resting).toBe(false);
  press('menu');
  now = 2_500;
  press('select');
  expect(result.current.resting).toBe(false);
});

test('key releases, other keys and non TV platforms do nothing', () => {
  const { result } = mount();
  press('menu', 1);
  press('down');
  press('playpause');
  expect(result.current.resting).toBe(false);
  isTV.mockReturnValue(false);
  press('menu');
  expect(result.current.resting).toBe(false);
});

test('a title that is not enabled gets no break, from the key or the call', () => {
  const { result } = mount({ enabled: false });
  press('menu');
  act(() => result.current.toggle());
  expect(result.current.resting).toBe(false);
});

test('losing verification ends a break, and it does not come back by itself', () => {
  const { result, rerender } = mount();
  press('menu');
  expect(result.current.resting).toBe(true);
  rerender({ enabled: false, intervals: [], mediaTimeMs: 3_100, nowMs: clock });
  expect(result.current.resting).toBe(false);
  rerender({ enabled: true, intervals: [], mediaTimeMs: 3_200, nowMs: clock });
  expect(result.current.resting).toBe(false);
});

test('a return asked for near a hold waits for the playhead to clear it', () => {
  const { result, rerender } = mount({ intervals: HOLD, mediaTimeMs: 7_000 });
  press('menu');
  now = 3_000;
  rerender({ enabled: true, intervals: HOLD, mediaTimeMs: 9_000, nowMs: clock });
  act(() => result.current.requestReturn());
  expect(result.current.state.waitingFor).toBe('hold-soon');
  rerender({ enabled: true, intervals: HOLD, mediaTimeMs: 11_000, nowMs: clock });
  expect(result.current.resting).toBe(true);
  expect(result.current.state.waitingFor).toBe('hold-now');
  rerender({ enabled: true, intervals: HOLD, mediaTimeMs: 12_000, nowMs: clock });
  expect(result.current.resting).toBe(false);
});

test('the key handler keeps one identity across renders', () => {
  const { rerender } = mount();
  rerender({ enabled: true, intervals: [], mediaTimeMs: 3_500, nowMs: clock });
  const handlers = (useTVEventHandler as jest.Mock).mock.calls.map((call) => call[0]);
  expect(handlers.length).toBeGreaterThan(1);
  expect(new Set(handlers).size).toBe(1);
  expect(handlers[0].name).toBe('pictureBreakRemote');
});
