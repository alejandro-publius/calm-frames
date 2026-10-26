import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import CalmButton from '../../src/calmframes/CalmButton';
import { COASTAL_COLORS } from '../../src/calmframes/calmStyles';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import PinKeypad from '../../src/calmframes/PinKeypad';
import ProfileNameEditor from '../../src/calmframes/ProfileNameEditor';
import { setTraceEnabled, trace, TRACE_PREFIX } from '../../src/calmframes/trace';

let warn: jest.SpyInstance;
const focusLines = () => warn.mock.calls
  .map(call => String(call[0]))
  .filter(line => line.startsWith(`${TRACE_PREFIX} focus`));

beforeEach(() => {
  warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
  setTraceEnabled(true);
});

afterEach(() => {
  setTraceEnabled(false);
  jest.restoreAllMocks();
});

test.each(['first-run', 'parent-area'])('%s PIN keys keep their actions and focus without revealing digits in debug traces', (idPrefix) => {
  const onDigit = jest.fn();
  const onDelete = jest.fn();
  const view = render(<PinKeypad entered={0} onDigit={onDigit} onDelete={onDelete} idPrefix={idPrefix} />);
  for (const digit of '1234567890') {
    const key = view.getByTestId(`${idPrefix}-key-${digit}`);
    expect(key.props.accessibilityLabel).toBe(digit);
    fireEvent(key, 'focus');
    expect(StyleSheet.flatten(key.props.style).borderColor).toBe(COASTAL_COLORS.FOCUS_RING);
    fireEvent.press(key);
    fireEvent(key, 'blur');
    expect(StyleSheet.flatten(key.props.style).borderColor).toBe(COASTAL_COLORS.SURFACE);
  }
  const remove = view.getByTestId(`${idPrefix}-key-delete`);
  fireEvent(remove, 'focus');
  fireEvent.press(remove);
  expect(onDigit.mock.calls.map(call => call[0])).toEqual([...'1234567890']);
  expect(onDelete).toHaveBeenCalledTimes(1);
  expect(focusLines()).toEqual([]);

  view.rerender(<PinKeypad disabled entered={0} onDigit={onDigit} onDelete={onDelete} idPrefix={idPrefix} />);
  fireEvent(view.getByTestId(`${idPrefix}-key-1`), 'focus');
  fireEvent.press(view.getByTestId(`${idPrefix}-key-1`));
  expect(onDigit).toHaveBeenCalledTimes(10);
  expect(focusLines()).toEqual([]);
});

test('the name grid stays private while typing, focusing every key and saving', () => {
  const onSave = jest.fn();
  const view = render(<ProfileNameEditor profile={{ id: 'fixture', name: 'Kid', settings: DEFAULT_SETTINGS }} taken={[]} onSave={onSave} onCancel={jest.fn()} />);
  for (const id of [...'abcdefghijklmnopqrstuvwxyz', 'shift', 'space', 'delete']) {
    const key = view.getByTestId(`profile-name-key-${id}`);
    fireEvent(key, 'focus');
    expect(StyleSheet.flatten(key.props.style).borderColor).toBe(COASTAL_COLORS.FOCUS_RING);
    fireEvent(key, 'blur');
  }
  for (const id of ['delete', 'delete', 'delete', 's', 'a', 'm']) {
    const key = view.getByTestId(`profile-name-key-${id}`);
    fireEvent(key, 'focus');
    fireEvent.press(key);
    fireEvent(key, 'blur');
  }
  expect(view.getByTestId('profile-name-draft').props.children).toBe('Sam');
  expect(view.getByTestId('profile-name-key-a').props.accessibilityLabel).toBe('Small A');
  expect(focusLines()).toEqual([]);

  const save = view.getByTestId('profile-name-save');
  fireEvent(save, 'focus');
  fireEvent.press(save);
  expect(onSave).toHaveBeenCalledWith('Sam');
  expect(focusLines()).toEqual([`${TRACE_PREFIX} focus profile-name-save`]);
});

test('ordinary navigation keeps its focus trace and callbacks', () => {
  const onFocus = jest.fn();
  const onBlur = jest.fn();
  const onPress = jest.fn();
  const view = render(<CalmButton label="Details" testID="fixture-details" onFocus={onFocus} onBlur={onBlur} onPress={onPress} sound={false} />);
  const control = view.getByTestId('fixture-details');
  fireEvent(control, 'focus');
  fireEvent.press(control);
  fireEvent(control, 'blur');
  expect(focusLines()).toEqual([`${TRACE_PREFIX} focus fixture-details`]);
  expect(onFocus).toHaveBeenCalledTimes(1);
  expect(onPress).toHaveBeenCalledTimes(1);
  expect(onBlur).toHaveBeenCalledTimes(1);
});

test('non-development tracing remains disabled even when tracing is enabled', () => {
  const descriptor = Object.getOwnPropertyDescriptor(global, '__DEV__');
  expect(descriptor).toBeDefined();
  try {
    Object.defineProperty(global, '__DEV__', { ...descriptor, value: false });
    trace('focus', 'fixture-details');
    expect(warn).not.toHaveBeenCalled();
  } finally {
    Object.defineProperty(global, '__DEV__', descriptor!);
  }
});
