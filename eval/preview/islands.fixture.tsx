/** Actual Home export with the consumer islands; static browser evidence only, not Vega. */
import React from 'react';
import { act, fireEvent, render } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
import { checkedShelf } from './shelfFixtures';

test('exports Home with the three consumer islands in each selection', () => {
  const island = (entry: ReturnType<typeof checkedShelf>[number]) => titlePresentation(entry.title).menuArt ?? (titlePresentation(entry.title).art === 'coastal' ? 'coastal' : undefined);
  const titles = checkedShelf().filter(entry => island(entry));
  expect(titles.map(island).sort()).toEqual(['coastal', 'forest', 'sea-otters']);
  const out = path.resolve(__dirname, '../../build/islands-preview');
  fs.mkdirSync(out, { recursive: true });
  const save = (name: string, tree: unknown) => fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(tree));
  const wrapper = ({ children }: { children: React.ReactNode }) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider>;
  const home = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={() => {}} profiles={[{ id: 'everyone', name: 'Everyone' }] as never} activeProfileId="everyone" onChooseProfile={jest.fn()} />, { wrapper });
  fireEvent(home.getByTestId('kid-home-watch'), 'focus');
  save('home-watch', home.toJSON());
  for (const entry of titles) {
    const art = island(entry)!;
    act(() => { fireEvent(home.getByTestId('kid-home-watch'), 'blur'); });
    act(() => { fireEvent(home.getByTestId(`kid-home-poster-${entry.title.id}`), 'focus'); });
    save(`home-card-${art}`, home.toJSON());
    act(() => { fireEvent(home.getByTestId(`kid-home-poster-${entry.title.id}`), 'blur'); });
  }
  act(() => { fireEvent.press(home.getByTestId('kid-home-choose-profile')); });
  save('home-picker', home.toJSON());
  home.unmount();
  const offline = render(<KidHomeScreen titles={titles} offline onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={() => {}} />, { wrapper });
  save('home-offline', offline.toJSON());
  offline.unmount();
  const alone = render(<KidHomeScreen titles={titles.filter(entry => island(entry) === 'coastal')} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={() => {}} />, { wrapper });
  save('home-acadia-alone', alone.toJSON());
});
