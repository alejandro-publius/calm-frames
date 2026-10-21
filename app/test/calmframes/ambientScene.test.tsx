import React from 'react';
import { act, fireEvent, render } from '@testing-library/react-native';
import { Animated } from 'react-native';
import AmbientScene, { ambientArtworkFor } from '../../src/calmframes/AmbientScene';
import { checkedShelf } from './shelfFixtures';

test('a still scene stays unchanged for an hour and starts motion only on an explicit preview press', () => {
  jest.useFakeTimers();
  const timing = jest.spyOn(Animated, 'timing');
  const preview = jest.fn(); const back = jest.fn();
  const view = render(<AmbientScene title="Forest" artwork="forest" onBack={back} onPreview={preview} previewSeconds={12} />);
  const picture = view.getByTestId('ambient-scene-picture');
  expect(picture.props.fadeDuration).toBe(0);
  expect(view.getByTestId('ambient-scene-back').props.hasTVPreferredFocus).toBe(true);
  act(() => jest.advanceTimersByTime(3600000));
  expect(view.getByTestId('ambient-scene-picture')).toBe(picture);
  expect(timing).not.toHaveBeenCalled();
  expect(jest.getTimerCount()).toBe(0);
  expect(preview).not.toHaveBeenCalled(); expect(back).not.toHaveBeenCalled();
  fireEvent.press(view.getByTestId('ambient-scene-preview'));
  expect(preview).toHaveBeenCalledTimes(1);
  fireEvent.press(view.getByTestId('ambient-scene-back'));
  expect(back).toHaveBeenCalledTimes(1);
  view.unmount(); timing.mockRestore(); jest.useRealTimers();
});

test('an ended preview is a still scene with no replay or timed navigation', () => {
  const back = jest.fn();
  const view = render(<AmbientScene title="Acadia" artwork="coastal" ended onBack={back} />);
  expect(view.getByText('Preview finished. This still scene stays until you leave.')).toBeTruthy();
  expect(view.queryByTestId('ambient-scene-preview')).toBeNull();
  expect(back).not.toHaveBeenCalled();
});

test('unverified entries cannot open the ambient presentation', () => {
  for (const entry of checkedShelf()) expect(ambientArtworkFor({ ...entry, status: 'blocked' } as never)).toBeUndefined();
});
