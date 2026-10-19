/** Actual component export for the local browser preview; no pixel capture. */
import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { isBundledBenignStory } from '../../src/calmframes/benignStory';
import { checkedShelf } from './shelfFixtures';
test('composition keeps Watch, Details, explanation and Back actions with truthful safety copy', () => {
  const titles = checkedShelf();
  const harbor = titles.find(item => item.title.title === 'Harbor story (prepared locally)')!;
  expect(harbor.status).toBe('verified');
  const onPlay = jest.fn(), onOpen = jest.fn(), onBack = jest.fn();
  const wrapper = ({ children }: { children: React.ReactNode }) => <CalmControlAppearance.Provider value>{children}</CalmControlAppearance.Provider>;
  const out = path.resolve(__dirname, '../../build/composition-preview/1080');
  fs.mkdirSync(out, { recursive: true });
  const save = (name: string, tree: unknown) => fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(tree));
  const home = render(<KidHomeScreen titles={titles} onOpen={onOpen} onPlay={onPlay} onOpenParentArea={() => {}} />, { wrapper });
  fireEvent(home.getByTestId('kid-home-watch'), 'focus');
  save('home', home.toJSON());
  fireEvent.press(home.getByTestId('kid-home-watch')); expect(onPlay).toHaveBeenCalledWith(harbor);
  fireEvent.press(home.getByTestId('kid-home-more-info')); expect(onOpen).toHaveBeenCalledWith(harbor);
  // The name is the header's wordmark; the shelf's own heading names the choice.
  expect(home.getByText('Calm Frames')).toBeTruthy();
  expect(home.getByTestId('kid-home-title').props.children).toBe('Choose an island');
  expect(home.queryByText('Picture holds on supported videos. Audio continues.')).toBeNull();
  expect(home.queryByText('Try the demo')).toBeNull();
  fireEvent.press(home.getByTestId('kid-home-learn')); expect(home.getByTestId('picture-hold-start')).toBeTruthy(); save('help', home.toJSON()); home.unmount();
  const demo = titles.find(item => isBundledBenignStory(item.title))!;
  const onOpenPractice = jest.fn();
  const details = render(<TitleDetailsScreen entry={harbor} onPlay={onPlay} onBack={onBack} practice={demo} onOpenPractice={onOpenPractice} />, { wrapper });
  fireEvent(details.getByTestId('title-details-play'), 'focus'); save('details', details.toJSON());
  // A video with nothing flagged says so, as a finding, not a promise.
  expect(details.getByText('No flagged scenes.')).toBeTruthy();
  expect(details.getByTestId('title-details-show-info')).toBeTruthy();
  fireEvent.press(details.getByTestId('title-details-play')); expect(onPlay).toHaveBeenCalledTimes(2);
  fireEvent.press(details.getByTestId('title-details-back')); expect(onBack).toHaveBeenCalledTimes(1);
  // The practice demo is offered on More info, beside the source and limits.
  fireEvent.press(details.getByTestId('title-details-show-info'));
  fireEvent.press(details.getByTestId('title-details-practice')); expect(onOpenPractice).toHaveBeenCalledWith(demo); details.unmount();
  const practice = render(<TitleDetailsScreen entry={demo} onPlay={onPlay} onBack={onBack} />, { wrapper });
  save('practice', practice.toJSON()); practice.unmount();
  const settings = render(<ParentAreaScreen gate={setPin(emptyPinGate(), '1357', 'preview-fixture')} onGateChange={jest.fn()} settings={DEFAULT_SETTINGS} onSettingsChange={jest.fn()} log={emptyHideLog()} titles={titles} onBack={onBack} />, { wrapper });
  save('settings', settings.toJSON()); settings.unmount();
  const blocked = render(<TitleDetailsScreen entry={{...harbor, status: 'failed', rejection: 'bad-signature', reason: 'Unavailable', segments: []}} onPlay={onPlay} onBack={onBack} />, { wrapper });
  expect(blocked.queryByTestId('title-details-play')).toBeNull(); blocked.unmount();
});
