import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import CalmButton from '../../src/calmframes/CalmButton';
import { CalmControlAppearance, COASTAL_MATERIAL } from '../../src/calmframes/CalmControlSurface';
import { COASTAL_COLORS, COASTAL_PRIMARY_FOCUS } from '../../src/calmframes/calmStyles';
import HomeHarborScene from '../../src/calmframes/HomeHarborScene';
import { contrastRatio } from '../../src/calmframes/uiContrast';

test('coastal primary focus is stationary and contrasts with both adjacent colors', () => {
  const action = jest.fn();
  const view = render(<CalmControlAppearance.Provider value><CalmButton primary playIcon label="Play" onPress={action} /></CalmControlAppearance.Provider>);
  const button = view.getByRole('button', { name: 'Play' });
  const before = StyleSheet.flatten(button.props.style);
  fireEvent(button, 'focus');
  const after = StyleSheet.flatten(button.props.style);
  for (const key of ['minHeight', 'minWidth', 'borderRadius', 'borderWidth']) expect(after[key]).toBe(before[key]);
  expect(after.borderColor).toBe(COASTAL_PRIMARY_FOCUS);
  const colors = view.UNSAFE_getByType('LinearGradient' as never).props.colors;
  for (const color of [...colors, COASTAL_COLORS.BACKGROUND]) expect(contrastRatio(after.borderColor, color)).toBeGreaterThanOrEqual(3);
  fireEvent.press(button);
  expect(action).toHaveBeenCalledTimes(1);
});

test('menu text stays readable across resting, pressed and selected materials', () => {
  for (const color of [...COASTAL_MATERIAL.primary, ...COASTAL_MATERIAL.primaryPressed]) {
    expect(contrastRatio(COASTAL_COLORS.BACKGROUND, color)).toBeGreaterThanOrEqual(4.5);
  }
  for (const color of [...COASTAL_MATERIAL.secondary, ...COASTAL_MATERIAL.secondaryPressed, ...COASTAL_MATERIAL.selected]) {
    expect(contrastRatio(COASTAL_COLORS.TEXT_DIM, color)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(COASTAL_COLORS.FOCUS_RING, color)).toBeGreaterThanOrEqual(3);
  }
});

test('the artwork is decorative, uses the clean asset and has no baked-in UI', () => {
  const view = render(<HomeHarborScene immersive />);
  expect(view.getByTestId('home-harbor-scene').props.accessibilityElementsHidden).toBe(true);
  const image = view.UNSAFE_getByType('Image' as never);
  expect(image.props.source.testUri).toContain('coastal-zen.png');
  expect(image.props.accessible).toBeUndefined();
  expect(view.queryAllByRole('button')).toHaveLength(0);
});
