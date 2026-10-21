import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { StyleSheet, View } from 'react-native';
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
    expect(contrastRatio(COASTAL_COLORS.INK, color)).toBeGreaterThanOrEqual(4.5);
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
  expect(image.props.source.testUri).toContain('harbor-cinematic.png');
  expect(image.props.accessible).toBeUndefined();
  expect(view.queryAllByRole('button')).toHaveLength(0);
});


test('balanced Home Watch matches Details geometry and never grows on focus or press', () => {
  const view = render(<CalmControlAppearance.Provider value>
    <View><CalmButton primary balanced playIcon label="Watch" testID="watch" />
    <CalmButton quiet label="Details" testID="details" /></View>
  </CalmControlAppearance.Provider>);
  const watch = view.getByTestId('watch');
  const details = view.getByTestId('details');
  const before = StyleSheet.flatten(watch.props.style);
  const other = StyleSheet.flatten(details.props.style);
  for (const key of ['minHeight', 'paddingHorizontal', 'paddingVertical', 'borderRadius', 'borderWidth']) expect(before[key]).toBe(other[key]);
  expect(before.minHeight).toBe(88);
  expect(before.minWidth).toBeUndefined();
  expect(before.borderRadius).toBe(18);
  expect(StyleSheet.flatten(view.getByTestId('watch-label').props.style).fontSize).toBe(36);
  const geometry = (style: any) => ['minHeight', 'minWidth', 'paddingHorizontal', 'paddingVertical', 'borderRadius', 'borderWidth', 'transform'].map(k => style[k]);
  fireEvent(watch, 'focus');
  fireEvent(watch, 'pressIn', {});
  expect(geometry(StyleSheet.flatten(watch.props.style))).toEqual(geometry(before));
  expect(StyleSheet.flatten(watch.props.style).borderColor).toBe(COASTAL_PRIMARY_FOCUS);
});
