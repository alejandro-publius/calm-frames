// With the prototype switched off, which is the default, Menu changes nothing.
// The harness first: its mocks of the SDK modules must be in place before
// anything else here requires them.
import { mockMedia } from './playbackUiHarness';
import { press, startPlayer } from './pictureBreakKeys';
import { Platform } from 'react-native';
import { PICTURE_BREAK_PROTOTYPE } from '../../src/calmframes/pictureBreakConfig';

let isTV: jest.SpyInstance;
beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(console, 'info').mockImplementation(() => {});
  isTV = jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(false);
});
afterEach(() => {
  jest.clearAllTimers();
  jest.useRealTimers();
  isTV.mockRestore();
});

test('the prototype ships switched off', () => {
  expect(PICTURE_BREAK_PROTOTYPE).toBe(false);
});

test('switched off, Menu neither covers the picture nor shows a break card', () => {
  const view = startPlayer();
  press('menu', isTV);
  expect(view.getByTestId('control-bar')).toBeTruthy();
  expect(view.queryByTestId('picture-break')).toBeNull();
  expect(view.queryByTestId('calm-frames-cover')).toBeNull();
  expect(mockMedia.paused).toBe(false);
});
