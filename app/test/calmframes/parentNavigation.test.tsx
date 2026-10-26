import '@testing-library/jest-native/extend-expect';
import { act, fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { COASTAL_COLORS as CALM_COLORS } from '../../src/calmframes/calmStyles';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { checkTitle } from '../../src/calmframes/titleStatus';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { newFamily } from '../../src/calmframes/profiles';

describe('parent header navigation', () => {
  it.each([false, true])('offers Back immediately after unlocking, with saving=%s', saving => {
    const onBack = jest.fn();
    const onFamilyChange = jest.fn();
    const onSettingsChange = jest.fn();
    const props = { gate: setPin(emptyPinGate(), '1357', 'test-fixture', 4),
      onGateChange: jest.fn(), settings: DEFAULT_SETTINGS, onSettingsChange,
      family: newFamily(DEFAULT_SETTINGS, 'Robin'), onFamilyChange,
      log: emptyHideLog(), titles: [], onBack };
    const view = render(<ParentAreaScreen {...props} />);
    expect(view.queryByTestId('parent-area-back-top')).toBeNull();
    expect(view.queryByTestId('parent-area-preset-wcag')).toBeNull();
    for (const digit of '0000') fireEvent.press(view.getByTestId(`parent-area-key-${digit}`));
    expect(view.queryByTestId('parent-area-back-top')).toBeNull();
    expect(view.queryByTestId('parent-area-preset-wcag')).toBeNull();
    for (const digit of '1357') fireEvent.press(view.getByTestId(`parent-area-key-${digit}`));
    view.rerender(<ParentAreaScreen {...props} saving={saving} />);
    const back = view.getByTestId('parent-area-back-top');
    expect(back.props.hasTVPreferredFocus).toBe(true);
    expect(back.props.accessibilityLabel).toBe('Back');
    expect(back.props.accessibilityState).toEqual({ disabled: saving });
    fireEvent(back, 'focus');
    if (!saving) {
      expect(back).toHaveStyle({ borderColor: CALM_COLORS.FOCUS_RING });
      expect(view.getByTestId('parent-area-back-top-label')).toHaveStyle({ textDecorationLine: 'underline' });
    }
    fireEvent.press(back);
    expect(onBack).toHaveBeenCalledTimes(saving ? 0 : 1);
    expect(onFamilyChange).not.toHaveBeenCalled();
    expect(onSettingsChange).not.toHaveBeenCalled();
    expect(view.getByTestId('parent-area-back').props.accessibilityState).toEqual({ disabled: saving });
  });
  it('keeps the editor behind the PIN and returns focus to its exact opener', async () => {
    const title = packagedLibrary.consumerTitles(DEFAULT_SETTINGS)[0];
    const entry = checkTitle(title, { settings: DEFAULT_SETTINGS, nowMs: Date.now(),
      publicKeyBase64: packagedLibrary.publicKeyFor(title, DEFAULT_SETTINGS) ?? '' });
    const view = render(<ParentAreaScreen gate={setPin(emptyPinGate(), '1357', 'test-fixture', 4)}
      onGateChange={jest.fn()} settings={DEFAULT_SETTINGS} onSettingsChange={jest.fn()}
      log={emptyHideLog()} titles={[entry]} onBack={jest.fn()} />);
    const opener = `parent-area-extra-${title.id}`;
    expect(view.queryByTestId(opener)).toBeNull();
    for (const digit of '1357') fireEvent.press(view.getByTestId(`parent-area-key-${digit}`));
    fireEvent.press(view.getByTestId(opener));
    await act(async () => { await Promise.resolve(); });
    expect(view.getByTestId('personal-covers')).toBeTruthy();
    fireEvent.press(view.getByTestId('extra-back'));
    expect(view.getByTestId(opener).props.hasTVPreferredFocus).toBe(true);
    expect(view.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);
  });

});

test('caregiver review inbox remains behind the existing PIN and restores its opener', async () => {
  const view = render(<ParentAreaScreen gate={setPin(emptyPinGate(), '1357', 'test-fixture', 4)}
    onGateChange={jest.fn()} settings={DEFAULT_SETTINGS} onSettingsChange={jest.fn()}
    log={emptyHideLog()} titles={[]} onBack={jest.fn()} />);
  expect(view.queryByTestId('parent-area-reviews')).toBeNull();
  for (const digit of '1357') fireEvent.press(view.getByTestId(`parent-area-key-${digit}`));
  fireEvent.press(view.getByTestId('parent-area-reviews')); await act(async () => {});
  expect(view.getByTestId('caregiver-reviews')).toBeTruthy();
  fireEvent.press(view.getByTestId('caregiver-reviews-back'));
  expect(view.queryByTestId('caregiver-reviews')).toBeNull();
  expect(view.getByTestId('parent-area-reviews').props.hasTVPreferredFocus).toBe(true);
});
