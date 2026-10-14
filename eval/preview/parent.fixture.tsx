/** In-memory household only. No saved PIN, settings or history is read or written. */
import { fireEvent, render as renderBase } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { addHideEntry, emptyHideLog } from '../../src/calmframes/hideLog';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { addProfile, newFamily } from '../../src/calmframes/profiles';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined),
}));
jest.mock('../../src/utils/pixelUtils', () => {
  const height = 1080;
  return { ...jest.requireActual('../../src/utils/pixelUtils'),
    scaleUxToDp: (value: number) => Math.round(value * height / 1080) };
});

test('export parent screens using only an in-memory fixture PIN and household', () => {
  const stage = 'after';
  const height = 1080;
  const gate = setPin(emptyPinGate(), '1357', 'preview-fixture', 4);
  const family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');
  const now = Date.UTC(2026, 9, 14, 10);
  const log = addHideEntry(emptyHideLog(), { atMs: now, titleId: 'fixture',
    titleName: 'Harbor', positionMs: 5000, durationMs: 4000, cause: 'schedule' });
  const out = path.resolve(__dirname, '../../build/parent-preview', stage, String(height));
  fs.mkdirSync(out, { recursive: true });
  for (const name of ['locked', 'wrong-pin', 'no-pin', 'household', 'child', 'saving', 'no-profiles', 'full-household', 'remove-confirm']) {
    const props = { gate: name === 'no-pin' ? emptyPinGate() : gate,
      onGateChange: jest.fn(), settings: DEFAULT_SETTINGS, onSettingsChange: jest.fn(),
      family: name === 'no-profiles' ? undefined : name === 'full-household' ? addProfile(addProfile(family, 'Ash'), 'Kit') : family, onFamilyChange: jest.fn(),
      log, profileLogs: { [family.profiles[0].id]: log }, titles: checkedShelf(),
      onBack: jest.fn(), onSetPin: jest.fn(), onCredits: jest.fn(), nowMs: () => now };
    const view = render(<ParentAreaScreen {...props} />);
    if (name !== 'no-pin' && name !== 'locked') {
      for (const digit of name === 'wrong-pin' ? '0000' : '1357') {
        fireEvent.press(view.getByTestId(`parent-area-key-${digit}`));
      }
    }
    if (name === 'child' || name === 'remove-confirm') fireEvent.press(view.getByTestId(`parent-area-profiles-${family.profiles[0].id}`));
    if (name === 'remove-confirm') fireEvent.press(view.getByTestId('parent-area-remove-profile'));
    if (name === 'saving') view.rerender(<ParentAreaScreen {...props} saving />);
    const focus = name === 'remove-confirm' ? 'parent-area-remove-keep' : name === 'no-pin' ? 'parent-area-set-pin'
      : ['locked', 'wrong-pin'].includes(name) ? 'parent-area-key-1'
        : view.queryByTestId('parent-area-back-top') ? 'parent-area-back-top' : 'parent-area-preset-wcag';
    if (name !== 'saving') fireEvent(view.getByTestId(focus), 'focus');
    expect(view.getByTestId(name === 'no-pin' || name === 'locked' || name === 'wrong-pin' ? 'parent-area' : 'parent-area-open')).toBeTruthy();
    fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(view.toJSON(), null, 2));
    view.unmount();
  }
});

import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
const render = (ui: React.ReactElement) => renderBase(ui, { wrapper: ({ children }: { children: React.ReactNode }) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider> });
