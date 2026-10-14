/** Exports real host trees for a browser preview, not native validation. */
import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import HouseholdStorageScreen from '../../src/calmframes/HouseholdStorageScreen';
import HarborOpening from '../../src/calmframes/HarborOpening';
import PlayerOpening from '../../src/calmframes/PlayerOpening';
import { checkedShelf } from './shelfFixtures';

test('export home, optional explanation, loading and opening from actual components', () => {
  const out = path.resolve(__dirname, '../../build/home-preview');
  fs.mkdirSync(out, { recursive: true });
  const save = (name: string, tree: unknown) => fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(tree, null, 2));
  const home = render(<KidHomeScreen titles={checkedShelf()} onOpen={() => {}} onPlay={() => {}} onOpenParentArea={() => {}} />);
  fireEvent(home.getByTestId('kid-home-watch'), 'focus');
  save('home', home.toJSON());
  fireEvent.press(home.getByTestId('kid-home-learn'));
  fireEvent(home.getByTestId('picture-hold-start'), 'focus');
  save('how-it-works', home.toJSON());
  expect(home.getByText(/two scheduled practice holds/)).toBeTruthy();
  home.unmount();
  const bootstrap = render(<HarborOpening />); save('bootstrap', bootstrap.toJSON()); bootstrap.unmount();
  const loading = render(<HouseholdStorageScreen failed={false} onRetry={() => {}} />);
  save('loading', loading.toJSON()); loading.unmount();
  const opening = render(<PlayerOpening title="Harbor" onBack={() => {}} />);
  save('opening', opening.toJSON()); opening.unmount();
  const returning = render(<PlayerOpening title="Harbor" onBack={() => {}} returning />);
  save('returning', returning.toJSON()); returning.unmount();
  const error = render(<HouseholdStorageScreen failed onRetry={() => {}} />);
  fireEvent(error.getByTestId('household-storage-retry'), 'focus');
  save('storage-error', error.toJSON()); error.unmount();
});
