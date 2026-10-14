/** Browser preview export. No native rendering or input behavior is implied. */
import React from 'react';
import { fireEvent, render as renderBase } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkedShelf } from './shelfFixtures';
import { CheckedTitle } from '../../src/calmframes/titleStatus';

test('export actual Harbor host trees for browser preview', () => {
  const titles = checkedShelf();
  const harbor = titles.find(item => item.title.title === 'Harbor story (prepared locally)');
  const demo = titles.find(item => item.title.id === 'calm-frames-benign-story');
  expect(harbor?.status).toBe('verified');
  expect(demo?.status).toBe('verified');
  if (!harbor || !demo) throw new Error('Real checked Harbor titles are required.');
  const stage = 'after'; // The export command replaces this for the baseline.
  const out = path.resolve(__dirname, '../../build/design-preview', stage);
  fs.mkdirSync(out, { recursive: true });
  const library = render(<KidHomeScreen titles={titles} onOpen={() => {}} onPlay={() => {}} onOpenParentArea={() => {}} />);
  fireEvent(library.getByTestId('kid-home-watch'), 'focus');
  fs.writeFileSync(path.join(out, 'library.json'), JSON.stringify(library.toJSON(), null, 2));
  library.unmount();
  const cases: Array<[string, CheckedTitle]> = [['details-harbor', harbor], ['details-demo', demo], ['details-unavailable', {...harbor, status: 'failed', rejection: 'bad-signature', reason: 'This title is unavailable. The picture stays hidden.', segments: []}]];
  for (const [name, entry] of cases) {
    const details = render(<TitleDetailsScreen entry={entry} onPlay={() => {}} onBack={() => {}} />);
    if (entry.status === 'verified') fireEvent(details.getByTestId('title-details-play'), 'focus');
    fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(details.toJSON(), null, 2));
    const info = details.queryByTestId('title-details-show-info');
    if (info) {
      fireEvent(details.getByTestId('title-details-play'), 'blur');
      fireEvent(info, 'focus');
      fs.writeFileSync(path.join(out, name + '-info.json'), JSON.stringify(details.toJSON(), null, 2));
    }
    details.unmount();
  }
});

import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
const render = (ui: React.ReactElement) => renderBase(ui, { wrapper: ({ children }: { children: React.ReactNode }) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider> });
