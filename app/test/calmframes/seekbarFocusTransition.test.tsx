import { startPlayer, mockGuard, mockMedia } from './playbackUiHarness';
import { act } from '@testing-library/react-native';
import { benignStoryCard } from '../../src/calmframes/benignStory';
import { cardAt } from '../../src/calmframes/cards';

afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

test('the seekbar yields preferred focus when a countdown appears during playback', async () => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  const view = startPlayer('none');
  expect(view.getByTestId('seekbar-focus-guide').props.hasTVPreferredFocus).toBe(true);
  mockGuard.card = benignStoryCard(
    cardAt([{ startMs: 5000, endMs: 9000, causes: ['general'] }] as never, 3000),
  );
  act(() => mockMedia.pause()); // any player state change renders the screen again
  expect(view.getByTestId('calm-card-skip')).toBeTruthy();
  expect(view.getByTestId('seekbar-focus-guide').props.hasTVPreferredFocus).toBe(false);
  mockGuard.card = { kind: 'none' };
  await act(async () => { await mockMedia.play(); });
  expect(view.getByTestId('seekbar-focus-guide').props.hasTVPreferredFocus).toBe(true);
});
