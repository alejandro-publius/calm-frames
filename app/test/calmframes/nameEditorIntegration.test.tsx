/**
 * The name editor where item 11 meets the cloud privacy follow-up. VoiceView
 * can land on the name being typed and hears it change, while the debug focus
 * trace never names a letter key or the name itself.
 */
import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import ProfileNameEditor from '../../src/calmframes/ProfileNameEditor';
import { setTraceEnabled, TRACE_PREFIX } from '../../src/calmframes/trace';

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

test('the field says a made-up name as it changes, and the trace names neither a key nor the name', () => {
  const view = render(<ProfileNameEditor profile={{ id: 'fixture', name: 'Sam', settings: DEFAULT_SETTINGS }} taken={[]} onSave={jest.fn()} onCancel={jest.fn()} />);
  const field = () => view.getByTestId('profile-name-field');
  expect(field().props.focusable).toBe(true);
  expect(field().props.accessibilityLiveRegion).toBe('polite');
  expect(field().props.accessibilityLabel).toBe('Sam. 3 of 16 characters');
  for (const id of ['m', 'y']) {
    const key = view.getByTestId(`profile-name-key-${id}`);
    fireEvent(key, 'focus');
    fireEvent.press(key);
    fireEvent(key, 'blur');
  }
  expect(field().props.accessibilityLabel).toBe('Sammy. 5 of 16 characters');
  fireEvent(field(), 'focus');
  fireEvent(field(), 'blur');
  // Landing on the field is ordinary navigation, so it is traced, by an id that holds nothing typed.
  expect(focusLines()).toEqual([`${TRACE_PREFIX} focus profile-name-field`]);
  expect(focusLines().join(' ')).not.toMatch(/sammy|key-/i);
});
