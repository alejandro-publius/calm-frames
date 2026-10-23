/** Real player/session components; native media and guard verdicts are explicit test doubles. */
import { startPlayer, mockMedia, mockGuard, mockError, mockEnded, mockDestroy, mockLifecycleCallbacks, mockBackCallbacks, mockHandlerOwners } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CHECKPOINT_KEY, PlaybackCheckpoint } from '../../src/calmframes/playbackCheckpoint';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { MCWAY_SOURCE_SHA256 } from '../../src/calmframes/continuousScene';
const title = packagedLibrary.titles(DEFAULT_SETTINGS).find(item => item.sha256 === MCWAY_SOURCE_SHA256)!;
function checkpoint(paused = false): PlaybackCheckpoint {
  return {version: 1, identity: {profileId: 'profile-1', titleId: title.id, uri: title.uri!,
    sourceSha256: title.sha256, renditionSha256: title.renditionSha256!, durationMs: title.durationMs!, startOffsetMs: title.renditionStartOffsetMs!},
    positionMs: 135000, captions: null, paused, savedAt: Date.now()};
}
const settle = async () => {await act(async () => {await Promise.resolve(); await Promise.resolve();});};
beforeEach(async () => {
  jest.useFakeTimers(); await AsyncStorage.clear(); mockDestroy.mockReset(); mockDestroy.mockReturnValue(true);
  jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(() => {jest.useRealTimers(); jest.restoreAllMocks();});
async function open(saved?: PlaybackCheckpoint) {
  if (saved) await AsyncStorage.setItem(CHECKPOINT_KEY, JSON.stringify({version: 1, records: [saved]}));
  const view = startPlayer('none', true, false, undefined, false, true);
  await settle(); return view;
}
async function attach(view: ReturnType<typeof startPlayer>) {
  await act(async () => fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewCreated', 'surface'));
}
async function resume(view: ReturnType<typeof startPlayer>) {
  fireEvent.press(view.getByTestId('resume-playback')); await settle();
  mockGuard.requestSeek.mockImplementation(async (_source: string, ms: number) => {mockMedia.currentTime = ms / 1000;});
  await attach(view);
  await act(async () => fireEvent(view.getByTestId('recovery-picture-barrier'), 'layout', {nativeEvent: {layout: {width: 1920, height: 1080}}}));
}
test('saved session does not create a native player until a remote choice', async () => {
  const view = await open(checkpoint());
  expect(view.getByText('Resume at 2:15')).toBeTruthy();
  expect(view.queryByTestId('kepler-video-surface-view')).toBeNull();
  fireEvent.press(view.getByTestId('resume-back')); expect(view.goBack).toHaveBeenCalledTimes(1);
});
test('Resume keeps the picture barrier until actual native seek and fresh timeupdate, preserving Off captions', async () => {
  const view = await open(checkpoint()); await resume(view);
  expect(mockGuard.requestSeek).toHaveBeenCalledWith('recovery', 135000);
  expect(mockMedia.paused).toBe(true);
  act(() => mockMedia.fire('seeked'));
  expect(view.getByTestId('recovery-picture-barrier')).toBeTruthy();
  await act(async () => mockMedia.fire('timeupdate'));
  expect(view.queryByTestId('recovery-picture-barrier')).toBeNull();
  expect(mockMedia.paused).toBe(false); expect(mockMedia.textTracks[0].mode).toBe('hidden');
});
test('paused Resume cannot autoplay or trip the ordinary opening timeout', async () => {
  const view = await open(checkpoint(true)); await resume(view);
  act(() => mockMedia.fire('seeked')); await act(async () => mockMedia.fire('timeupdate'));
  act(() => jest.advanceTimersByTime(16000));
  expect(mockMedia.paused).toBe(true); expect(view.queryByTestId('player-error')).toBeNull();
  expect(view.queryByTestId('player-home-opening')).toBeNull();
});
test('Start over removes the checkpoint before the new session writes', async () => {
  const view = await open(checkpoint()); fireEvent.press(view.getByTestId('resume-start-over')); await settle();
  expect(view.queryByTestId('recovery-picture-barrier')).toBeNull();
  const raw = await AsyncStorage.getItem(CHECKPOINT_KEY);
  expect(JSON.parse(raw!).records).toEqual([]);
});
test('a native error can retry once explicitly after confirmed teardown; missing events remain covered', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockMedia.fire('seeked')); await act(async () => mockMedia.fire('timeupdate'));
  act(() => mockError(true)); expect(view.getByTestId('player-error-retry')).toBeTruthy();
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  expect(view.getByTestId('player-error-retry')).toBeTruthy();
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  expect(view.queryByTestId('player-error')).toBeNull();
  expect(view.getByTestId('recovery-picture-barrier')).toBeTruthy();
  await attach(view);
  await act(async () => fireEvent(view.getByTestId('recovery-picture-barrier'), 'layout', {}));
  act(() => jest.advanceTimersByTime(12000));
  expect(view.getByTestId('player-error')).toBeTruthy();
  expect(view.getByTestId('recovery-picture-barrier')).toBeTruthy();
});
test('unconfirmed teardown refuses another decoder and retains Back', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockError(true)); mockDestroy.mockReturnValue(false);
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  expect(view.queryByTestId('player-error-retry')).toBeNull();
  expect(view.getByText('The player could not close. Go back before trying again.')).toBeTruthy();
  expect(view.getByTestId('player-error-back')).toBeTruthy();
});
test('completion clears history and retains the continuous ending still', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockMedia.fire('seeked')); await act(async () => mockMedia.fire('timeupdate'));
  await act(async () => {mockMedia.ended = true; mockEnded(true);});
  expect(view.getByTestId('continuous-ended-still')).toBeTruthy();
  expect(JSON.parse((await AsyncStorage.getItem(CHECKPOINT_KEY))!).records).toEqual([]);
});
test('a native teardown exception leaves recovery blocked with a Back action', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockError(true)); mockDestroy.mockImplementationOnce(() => {throw new Error('native teardown');});
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  expect(view.queryByTestId('player-error-retry')).toBeNull();
  expect(view.getByTestId('player-error-back')).toBeTruthy();
});
test('Resume restores caption metadata onto a different native track ID', async () => {
  const saved = checkpoint(); saved.captions = {language: 'en', label: 'English practice captions'};
  const view = await open(saved);
  mockMedia.textTracks[0].id = 'new-native-id'; mockMedia.textTracks[0].mode = 'hidden';
  await resume(view);
  expect(mockMedia.textTracks[0].mode).toBe('showing');
});
test('a blocked current guard prevents recovery from starting the media', async () => {
  const view = await open(checkpoint());
  mockGuard.status = 'blocked';
  fireEvent.press(view.getByTestId('resume-playback')); await settle();
  expect(view.getByTestId('player-error')).toBeTruthy();
  expect(view.getByTestId('recovery-picture-barrier')).toBeTruthy();
  expect(view.queryByTestId('player-error-retry')).toBeNull();
  expect(mockGuard.requestSeek).not.toHaveBeenCalled();
});
test('edition-mismatched optional history takes the ordinary opening path', async () => {
  const saved = checkpoint(); saved.identity.renditionSha256 = 'f'.repeat(64);
  const view = await open(saved);
  expect(view.queryByTestId('resume-playback')).toBeNull();
  expect(view.getByTestId('player-home-opening')).toBeTruthy();
});

test('background exits an active recovery and late media events cannot start sound', async () => {
  const view = await open(checkpoint()); await resume(view);
  await act(async () => {for (const fn of [...mockLifecycleCallbacks]) fn('background');});
  expect(view.goBack).toHaveBeenCalledTimes(1);
  act(() => {mockMedia.fire('seeked'); mockMedia.fire('timeupdate'); jest.advanceTimersByTime(16000);});
  expect(mockMedia.paused).toBe(true); expect(view.goBack).toHaveBeenCalledTimes(1);
});
test('hardware Back dismisses the resume choice and never starts a decoder', async () => {
  const view = await open(checkpoint());
  act(() => {for (const fn of [...mockBackCallbacks].reverse()) {if (fn()) break;}});
  expect(view.goBack).toHaveBeenCalledTimes(1);
  expect(view.queryByTestId('kepler-video-surface-view')).toBeNull();
});
test('new native positions persist with current captions and survive leaving', async () => {
  const view = await open(); await attach(view);
  await act(async () => {mockMedia.currentTime = 64; mockMedia.fire('timeupdate');});
  const records = JSON.parse((await AsyncStorage.getItem(CHECKPOINT_KEY))!).records;
  expect(records[0].positionMs).toBe(64000);
  expect(records[0].identity.renditionSha256).toBe(title.renditionSha256);
  expect(records[0].paused).toBe(false);
});
test('Back still exits when a native detach throws after recovery fails', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockError(true));
  jest.spyOn(mockMedia, 'clearSurfaceHandle').mockImplementation(() => {throw new Error('native detach');});
  fireEvent.press(view.getByTestId('player-error-back'));
  act(() => jest.advanceTimersByTime(5000));
  expect(view.goBack).toHaveBeenCalledTimes(1);
});
test('surface loss after successful Resume pauses audio and retains retry/Back', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockMedia.fire('seeked')); await act(async () => mockMedia.fire('timeupdate'));
  expect(mockMedia.paused).toBe(false);
  fireEvent(view.getByTestId('kepler-video-surface-view'), 'surfaceViewDestroyed', 'surface');
  expect(mockMedia.paused).toBe(true);
  expect(view.getByTestId('player-error-back')).toBeTruthy();
  expect(view.getByTestId('player-error-retry')).toBeTruthy();
});
test('Back preserves playing intent despite synchronous native teardown pause', async () => {
  const view = await open(); await attach(view);
  await act(async () => {mockMedia.currentTime = 64; mockMedia.fire('timeupdate');});
  mockDestroy.mockImplementationOnce(() => {mockMedia.pause(); return true;});
  await act(async () => {for (const fn of [...mockLifecycleCallbacks]) fn('background');});
  const records = JSON.parse((await AsyncStorage.getItem(CHECKPOINT_KEY))!).records;
  expect(records[0].paused).toBe(false);
  expect(view.goBack).toHaveBeenCalledTimes(1);
});
test('unmount invalidates pending initialization even before a media instance exists', async () => {
  const view = startPlayer('none', true, false, undefined, false, true, true);
  await settle(); mockDestroy.mockClear();
  view.unmount();
  expect(mockDestroy).toHaveBeenCalledTimes(1);
});

test('delayed teardown stays covered, then requires explicit Retry after confirmation', async () => {
  const view = await open(checkpoint()); await resume(view);
  act(() => mockError(true));
  let confirm!: (value: boolean) => void;
  mockDestroy.mockImplementationOnce(() => new Promise<boolean>(resolve => {confirm = resolve;}));
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  expect(view.getByText('Closing the player. You can go back while it finishes.')).toBeTruthy();
  expect(view.queryByTestId('player-error-retry')).toBeNull();
  act(() => jest.advanceTimersByTime(20000));
  expect(view.getByTestId('player-error')).toBeTruthy();
  await act(async () => confirm(true));
  expect(view.getByTestId('player-error-retry')).toBeTruthy();
  expect(view.getByTestId('player-error')).toBeTruthy();
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  expect(view.queryByTestId('player-error')).toBeNull();
});
test.each(['back', 'background', 'unmount'])('late native completion cannot replace decoder after %s', async (exit) => {
  const view = await open(checkpoint()); await resume(view); act(() => mockError(true));
  let confirm!: (value: boolean) => void;
  mockDestroy.mockImplementationOnce(() => new Promise<boolean>(resolve => {confirm = resolve;}));
  fireEvent.press(view.getByTestId('player-error-retry')); await settle();
  const calls = mockDestroy.mock.calls.length;
  if (exit === 'unmount') view.unmount();
  else if (exit === 'back') fireEvent.press(view.getByTestId('player-error-back'));
  else act(() => {for (const fn of [...mockLifecycleCallbacks]) fn('background');});
  await act(async () => {confirm(true); jest.advanceTimersByTime(1000);});
  expect(mockDestroy).toHaveBeenCalledTimes(calls);
  if (exit !== 'unmount') expect(view.goBack).toHaveBeenCalledTimes(1);
  expect(mockMedia.paused).toBe(true);
});

test('one keyed player retains its native handler owner across state renders', async () => {
  mockHandlerOwners.length = 0;
  const view = await open(checkpoint()); await resume(view);
  act(() => mockMedia.fire('seeked')); await act(async () => mockMedia.fire('timeupdate'));
  act(() => mockError(true));
  expect(mockHandlerOwners).toHaveLength(1);
});
