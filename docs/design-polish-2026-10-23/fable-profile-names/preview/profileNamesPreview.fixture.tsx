/**
 * Export the name editor's states as host trees, for a browser approximation.
 *
 * In-memory household only: a fixture PIN, Robin and Sam, no storage read or
 * written. Copy this file to app/test/calmframes/profileNamesPreview.test.tsx,
 * run it with jest, then delete the copy. It writes one JSON tree per state
 * to app/build/profile-names-preview/1080, which render_preview.py draws.
 * Sizes are 1080p units because scaleUxToDp is pinned to the identity here.
 */
import { act, fireEvent, render as renderBase } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';
import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { addProfile, Family, newFamily } from '../../src/calmframes/profiles';
import { checkedShelf } from './shelfFixtures';

jest.mock('../../src/utils/pixelUtils', () => ({
  ...jest.requireActual('../../src/utils/pixelUtils'),
  scaleUxToDp: (value: number) => Math.round(value),
}));

const render = (ui: React.ReactElement) =>
  renderBase(ui, {
    wrapper: ({ children }: { children: React.ReactNode }) => (
      <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider>
    ),
  });

test('export the name editor states from an in-memory household', async () => {
  const out = path.resolve(__dirname, '../../build/profile-names-preview/1080');
  fs.mkdirSync(out, { recursive: true });
  const gate = setPin(emptyPinGate(), '1357', 'preview-fixture', 4);
  const family: Family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');
  let settle: ((accepted: boolean) => void) | null = null;
  const onRenameProfile = jest.fn(
    (_family: Family) =>
      new Promise<boolean>((resolve) => {
        settle = resolve;
      }),
  );
  const props = {
    gate,
    onGateChange: jest.fn(),
    settings: DEFAULT_SETTINGS,
    onSettingsChange: jest.fn(),
    log: emptyHideLog(),
    family,
    onFamilyChange: jest.fn(),
    onRenameProfile,
    titles: checkedShelf(),
    onBack: jest.fn(),
    onCredits: jest.fn(),
    nowMs: () => Date.UTC(2026, 9, 23, 18),
  };
  const view = render(<ParentAreaScreen {...props} />);
  const press = (id: string) => fireEvent.press(view.getByTestId(id));
  const focus = (id: string) => fireEvent(view.getByTestId(id), 'focus');
  const blur = (id: string) => fireEvent(view.getByTestId(id), 'blur');
  const save = (name: string) =>
    fs.writeFileSync(path.join(out, `${name}.json`), JSON.stringify(view.toJSON(), null, 2));

  for (const digit of '1357') press(`parent-area-key-${digit}`);
  press('parent-area-profiles-profile-2');
  focus('parent-area-rename-profile');
  save('01-kid-selected');

  press('parent-area-rename-profile');
  focus('parent-area-name-key-a');
  save('02-editor-open');
  blur('parent-area-name-key-a');

  for (let index = 0; index < 3; index += 1) press('parent-area-name-key-delete');
  for (const letter of 'ro') press(`parent-area-name-key-${letter}`);
  press('parent-area-name-key-shift');
  focus('parent-area-name-key-b');
  save('03-editor-typing');
  blur('parent-area-name-key-b');

  press('parent-area-name-key-shift');
  for (const letter of 'bin') press(`parent-area-name-key-${letter}`);
  focus('parent-area-name-save');
  press('parent-area-name-save');
  save('04-editor-refused');

  for (let index = 0; index < 5; index += 1) press('parent-area-name-key-delete');
  for (const letter of 'ash') press(`parent-area-name-key-${letter}`);
  press('parent-area-name-save');
  save('05-editor-saving');

  await act(async () => {
    settle!(false);
  });
  focus('parent-area-name-retry');
  save('06-editor-failed');

  press('parent-area-name-retry');
  await act(async () => {
    settle!(true);
  });
  const renamed: Family = onRenameProfile.mock.calls[1][0];
  view.rerender(<ParentAreaScreen {...props} family={renamed} />);
  focus('parent-area-rename-profile');
  save('07-renamed');

  expect(fs.readdirSync(out).filter((name) => name.endsWith('.json'))).toHaveLength(7);
  view.unmount();
});
