/** Native video/captions/seekbar are explicitly represented by browser substitutes. */
import { startPlayer, mockMedia, mockError, mockBuffering } from './playbackUiHarness';
import { act, fireEvent } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';

jest.mock('../../src/utils/pixelUtils', () => ({ scaleUxToDp: (v: number) => Math.round(v * 1080 / 1080) }));
jest.mock('react-native/Libraries/Utilities/useWindowDimensions', () => ({ __esModule: true, default: () => ({ width: 1920, height: 1080, scale: 1, fontScale: 1 }) }));

test('export actual playback screen trees', () => {
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.useFakeTimers();
  const stage = 'after';
  const height = 1080;
  const folder = path.resolve(__dirname, '../../build/playback-preview', stage, String(height));
  fs.mkdirSync(folder, { recursive: true });
  for (const name of ['controls-back', 'controls-captions', 'caption-menu', 'hold-controls', 'hold-caption-menu', 'playing-hold', 'paused-hold', 'paused-countdown', 'paused-story', 'loading', 'error']) {
    const view = startPlayer(name.includes('hold') ? 'covering' : name.includes('countdown') ? 'countdown' : 'none', false, true);
    fireEvent.press(view.getByTestId('video-player-caption-btn'));
    fireEvent.press(view.getByRole('radio', { name: 'English practice captions' }));
    if (name.startsWith('paused')) act(() => mockMedia.pause());
    if (name === 'controls-back') fireEvent(view.getByTestId('header_back_icon'), 'focus');
    if (name === 'controls-captions' || name.includes('caption-menu')) fireEvent(view.getByTestId('video-player-caption-btn'), 'focus');
    if (name.includes('caption-menu')) {
      fireEvent.press(view.getByTestId('video-player-caption-btn'));
      fireEvent(view.getByTestId('video-player-caption-btn'), 'blur');
      fireEvent(view.getByRole('radio', { name: 'English practice captions' }), 'focus');
    }
    if (name.startsWith('paused') || name === 'playing-hold') act(() => jest.advanceTimersByTime(6000));
    if (name === 'loading') { act(() => mockBuffering(true)); act(() => jest.advanceTimersByTime(1000)); expect(view.getByTestId('buffering-status')).toBeTruthy(); }
    if (name === 'error') act(() => mockError(true));
    const back = view.queryByTestId('player-error-back');
    if (back) fireEvent(back, 'focus');
    expect(view.getByTestId('safe-area-view')).toBeTruthy();
    fs.writeFileSync(path.join(folder, name + '.json'), JSON.stringify(view.toJSON(), null, 2));
    view.unmount();
    jest.clearAllTimers();
  }
  jest.useRealTimers();
});
