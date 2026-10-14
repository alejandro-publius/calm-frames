import '@testing-library/jest-native/extend-expect';
import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { CALM_COLORS } from '../../src/calmframes/calmStyles';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
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
    expect(back.props.accessibilityLabel).toBe('Back to library');
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
});
