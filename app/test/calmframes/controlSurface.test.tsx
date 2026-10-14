import React from 'react';
import { render as renderNative, fireEvent } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import CalmButton from '../../src/calmframes/CalmButton';
import PinKeypad from '../../src/calmframes/PinKeypad';
import { CONTROL_MATERIAL, CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import { contrastRatio } from '../../src/calmframes/uiContrast';
import { CoastalAppearance } from '../../src/calmframes/CoastalAppearance';
const render = (element: React.ReactElement) => renderNative(element, { wrapper: ({ children }: { children: React.ReactNode }) => <CoastalAppearance.Provider value={false}>{children}</CoastalAppearance.Provider> });
const study = (children: React.ReactNode) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider>;

test('material is opt-in; the production surface and geometry remain intact', () => {
  const view = render(<CalmControlAppearance.Provider value={false}><CalmButton primary label="Watch now" /></CalmControlAppearance.Provider>);
  const baseline = StyleSheet.flatten(view.getByTestId('calm-button').props.style);
  expect(baseline.backgroundColor).toBe('#D88B72');
  expect(view.UNSAFE_queryAllByType('LinearGradient' as never)).toHaveLength(0);
  view.rerender(study(<CalmButton primary label="Watch now" />));
  const material = StyleSheet.flatten(view.getByTestId('calm-button').props.style);
  for (const key of ['minHeight', 'borderRadius', 'borderWidth', 'paddingHorizontal', 'paddingVertical']) expect(material[key]).toEqual(baseline[key]);
  expect(view.UNSAFE_queryAllByType('LinearGradient' as never)).toHaveLength(1);
});

test('focus, press and release remain stationary, readable and call the real action once', () => {
  const press = jest.fn();
  const view = render(study(<CalmButton primary label="Watch now" onPress={press} />));
  const control = view.getByTestId('calm-button');
  fireEvent(control, 'focus');
  const focused = StyleSheet.flatten(control.props.style);
  expect(focused.borderColor).toBe('#E6B963');
  fireEvent(control, 'pressIn', {});
  expect(view.UNSAFE_getByType('LinearGradient' as never).props.colors).toEqual(CONTROL_MATERIAL.primaryPressed);
  expect(StyleSheet.flatten(control.props.style)).toEqual(focused);
  expect(StyleSheet.flatten(view.getByTestId('calm-button-label').props.style).color).toBe('#151C26');
  fireEvent(control, 'pressOut', {});
  expect(view.UNSAFE_getByType('LinearGradient' as never).props.colors).toEqual(CONTROL_MATERIAL.primary);
  fireEvent.press(control); expect(press).toHaveBeenCalledTimes(1);
  fireEvent(control, 'blur');
  expect(StyleSheet.flatten(control.props.style).borderColor).toBe('transparent');
});

test('disabled controls and saving keypad retain their existing activation and focus rules', () => {
  const action = jest.fn();
  const view = render(study(<CalmButton primary disabled label="Watch now" onPress={action} />));
  fireEvent.press(view.getByTestId('calm-button'));
  expect(action).not.toHaveBeenCalled();
  expect(view.UNSAFE_getByType('LinearGradient' as never).props.colors).toEqual(CONTROL_MATERIAL.disabled);
  view.unmount();
  const keypad = render(study(<PinKeypad disabled entered={0} onDigit={action} onDelete={action} idPrefix="fixture" />));
  const key = keypad.getByTestId('fixture-key-1');
  expect(key.props.accessibilityState.disabled).toBe(true);
  expect(key.props.disabled).not.toBe(true);
  fireEvent.press(key); expect(action).not.toHaveBeenCalled();
});

test('tertiary has no resting plate and keeps its full target', () => {
  const view = render(study(<CalmButton tertiary quiet label="Back" />));
  expect(view.UNSAFE_queryAllByType('LinearGradient' as never)).toHaveLength(0);
  const control = view.getByTestId('calm-button');
  expect(StyleSheet.flatten(control.props.style).minHeight).toBe(88);
  fireEvent(control, 'focus');
  expect(view.UNSAFE_queryAllByType('LinearGradient' as never)).toHaveLength(1);
});

test('gradient extremes preserve text contrast even when translucent secondary is composited over white', () => {
  const composite = (color: string) => {
    if (color.length === 7) return color;
    const alpha = parseInt(color.slice(7), 16) / 255;
    return '#' + [1, 3, 5].map(i => Math.round(parseInt(color.slice(i, i + 2), 16) * alpha + 255 * (1 - alpha)).toString(16).padStart(2, '0')).join('');
  };
  for (const color of [...CONTROL_MATERIAL.primary, ...CONTROL_MATERIAL.primaryPressed]) expect(contrastRatio('#151C26', color)).toBeGreaterThanOrEqual(4.5);
  for (const color of [...CONTROL_MATERIAL.secondary, ...CONTROL_MATERIAL.secondaryPressed, ...CONTROL_MATERIAL.selected, ...CONTROL_MATERIAL.disabled]) expect(contrastRatio('#BDC2C9', composite(color))).toBeGreaterThanOrEqual(4.5);
  expect(contrastRatio('#E6B963', '#151C26')).toBeGreaterThanOrEqual(3);
  expect(contrastRatio('#9DA4AE', '#282F39')).toBeGreaterThanOrEqual(4.5);
});
