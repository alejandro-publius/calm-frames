import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import CalmButton from '../../src/calmframes/CalmButton';
import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import { WorldAppearance, WORLD } from '../../src/calmframes/CoastalWorld';
import PlayerOpening from '../../src/calmframes/PlayerOpening';
import ProfilePicker from '../../src/calmframes/ProfilePicker';
import { COASTAL_COLORS } from '../../src/calmframes/calmStyles';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { contrastRatio, measureText, RenderedNode } from '../../src/calmframes/uiContrast';

test.each([false, true])('a world primary action is visible at rest and legible through focus and press, balanced=%s', balanced => {
  const press = jest.fn();
  const content = (disabled = false) => <CalmControlAppearance.Provider value><WorldAppearance.Provider value>
    <CalmButton primary balanced={balanced} playIcon label="Watch" disabled={disabled} onPress={press} />
  </WorldAppearance.Provider></CalmControlAppearance.Provider>;
  const view = render(content());
  const button = () => view.getByRole('button', { name: 'Watch' });
  const style = () => StyleSheet.flatten(button().props.style);
  const resting = style();
  const readable = () => {
    for (const line of measureText(view.toJSON() as unknown as RenderedNode, { background: WORLD.BACKGROUND })) {
      expect(line.contrast).toBeGreaterThanOrEqual(4.5);
    }
  };
  expect(contrastRatio(resting.backgroundColor, WORLD.BACKGROUND)).toBeGreaterThanOrEqual(3);
  readable();
  // Remote events can arrive before the view reports focus. Ink must still
  // match the fill actually painted, including the decorative play icon.
  fireEvent(button(), 'pressIn', {});
  readable();
  fireEvent(button(), 'pressOut', {});
  expect(style().backgroundColor).toBe(resting.backgroundColor);
  fireEvent(button(), 'focus');
  expect(contrastRatio(style().borderColor, style().backgroundColor)).toBeGreaterThanOrEqual(3);
  expect(contrastRatio(style().borderColor, WORLD.BACKGROUND)).toBeGreaterThanOrEqual(3);
  readable();
  fireEvent(button(), 'pressIn', {});
  readable();
  for (const property of ['minHeight', 'minWidth', 'borderRadius', 'borderWidth', 'paddingHorizontal', 'paddingVertical']) {
    expect(style()[property]).toEqual(resting[property]);
  }
  fireEvent(button(), 'pressOut', {});
  fireEvent.press(button());
  expect(press).toHaveBeenCalledTimes(1);
  fireEvent(button(), 'blur');
  expect(style().backgroundColor).toBe(resting.backgroundColor);
  readable();
  view.rerender(content(true));
  readable();
  fireEvent.press(button());
  expect(press).toHaveBeenCalledTimes(1);
});

test('a primary action stays legible and stationary during focus and immediate press feedback', () => {
  const press = jest.fn();
  const view = render(<CalmButton primary label="Watch now" onPress={press} />);
  const button = () => view.getByRole('button', { name: 'Watch now' });
  const resting = StyleSheet.flatten(button().props.style);
  fireEvent(button(), 'focus');
  fireEvent(button(), 'pressIn', {});
  const down = StyleSheet.flatten(button().props.style);
  expect(down.borderRadius).toBe(resting.borderRadius);
  expect(down.borderWidth).toBe(resting.borderWidth);
  expect(down.paddingHorizontal).toBe(resting.paddingHorizontal);
  expect(down.backgroundColor).toBe(COASTAL_COLORS.PRIMARY);
  for (const line of measureText(view.toJSON() as unknown as RenderedNode, { background: COASTAL_COLORS.BACKGROUND })) {
    expect(line.contrast).toBeGreaterThanOrEqual(4.5);
  }
  fireEvent(button(), 'pressOut', {});
  fireEvent.press(button()); expect(press).toHaveBeenCalledTimes(1);
  view.rerender(<CalmButton primary label="Saving changes" disabled onPress={press} />);
  fireEvent.press(view.getByRole('button', { name: 'Saving changes' }));
  expect(press).toHaveBeenCalledTimes(1);
});

test('opening offers one real Back action and returning offers status without a fake button', () => {
  const back = jest.fn();
  const view = render(<PlayerOpening title="Harbor" onBack={back} />);
  expect(view.getAllByRole('button')).toHaveLength(1);
  fireEvent.press(view.getByRole('button', { name: 'Back' }));
  expect(back).toHaveBeenCalledTimes(1);
  view.rerender(<PlayerOpening title="Harbor" onBack={back} returning />);
  expect(view.queryAllByRole('button')).toHaveLength(0);
  expect(view.getByText('Going back…').props.accessibilityLiveRegion).toBe('polite');
});

test('selection remains explicit when focus moves to a different profile', () => {
  const profiles = ['Robin', 'Sam'].map(name => ({ id: name, name, settings: DEFAULT_SETTINGS }));
  const view = render(<ProfilePicker profiles={profiles} activeProfileId="Robin" title="Who is watching" chosenLine="Robin is watching" onChoose={jest.fn()} />);
  fireEvent(view.getByRole('radio', { name: 'Sam' }), 'focus');
  expect(view.getByRole('radio', { name: 'Robin, watching' }).props.accessibilityState.checked).toBe(true);
  expect(view.getByRole('radio', { name: 'Sam' }).props.accessibilityState.checked).toBe(false);
  expect(view.getAllByText('✓')).toHaveLength(1);
});
