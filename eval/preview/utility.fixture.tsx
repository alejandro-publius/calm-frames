/** All setup data is ephemeral fixture data; never reads the connected household. */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import FirstRunScreen from '../../src/calmframes/FirstRunScreen';
import CreditsScreen from '../../src/calmframes/CreditsScreen';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
test('export setup and credits', () => {
  const out = path.resolve(__dirname, '../../build/utility-preview'); fs.mkdirSync(out, { recursive: true });
  const save = (name: string, tree: unknown) => fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(tree, null, 2));
  const view = render(<FirstRunScreen newSalt={() => 'ephemeral-preview'} rounds={4} onDone={() => {}} />);
  fireEvent(view.getByTestId('first-run-key-1'), 'focus');
  save('setup-pin', view.toJSON());
  for (const digit of '1357') fireEvent.press(view.getByTestId('first-run-key-' + digit));
  save('setup-confirm', view.toJSON());
  for (const digit of '1357') fireEvent.press(view.getByTestId('first-run-key-' + digit));
  fireEvent(view.getByTestId('first-run-preset-wcag'), 'focus');
  save('setup-preset', view.toJSON());
  fireEvent.press(view.getByTestId('first-run-next'));
  save('setup-room', view.toJSON());
  fireEvent.press(view.getByTestId('first-run-next'));
  save('setup-explainer', view.toJSON());
  view.unmount();
  const credits = render(<CreditsScreen onBack={() => {}} />);
  save('credits', credits.toJSON()); credits.unmount();
  expect(fs.existsSync(path.join(out, 'setup-pin.json'))).toBe(true);
});
