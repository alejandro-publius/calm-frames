/**
 * Remote presses for the picture break tests. The playback harness is
 * imported first, so its mocks of the SDK modules are in place before the
 * mocked useTVEventHandler is read here.
 */
import { startPlayer } from './playbackUiHarness';
import { useTVEventHandler } from '@amazon-devices/react-native-kepler';
import { act } from '@testing-library/react-native';

export { startPlayer };

/**
 * The latest listener registered by one component, told apart by a name its
 * source must contain: the break's named function, the controls' OK handling
 * and the player screen's end-of-title handling.
 */
function latestListener(marker: string): (evt: unknown) => void {
  const handlers = (useTVEventHandler as jest.Mock).mock.calls
    .map((call) => call[0])
    .filter((handler) => handler.name === marker || String(handler).includes(marker));
  expect(handlers.length).toBeGreaterThan(0);
  return handlers[handlers.length - 1];
}

/**
 * One key press, heard by every listener in a single dispatch with no render
 * in between, which is how the device delivers it. The platform reads as a TV
 * only during the press: mounting as a TV needs a BackHandler the harness does
 * not mock.
 */
export function press(eventType: 'menu' | 'select', isTV: jest.SpyInstance) {
  const listeners = [
    latestListener('pictureBreakRemote'),
    latestListener('okIsSkip'),
    latestListener('isVideoEnded'),
  ];
  expect(new Set(listeners).size).toBe(3);
  isTV.mockReturnValue(true);
  act(() => {
    for (const listener of listeners) {
      listener({ eventKeyAction: 0, eventType });
    }
  });
  isTV.mockReturnValue(false);
}
