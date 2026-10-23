/**
 * Back from the profile picker puts focus on the button that opened it.
 *
 * The chips leave the tree when the picker closes, so the remote's focus has
 * to be told where to go; before this it was left for the platform to guess.
 * The same one-value rule covers How it works: whichever header panel was
 * dismissed last is the control that takes focus.
 *
 * Seen to fail, Oct 16 2026: with setReturnToHeader('profile') removed from
 * the picker's Back handler in KidHomeScreen, the first test reported
 * Expected ["kid-home-choose-profile"], Received ["kid-home-watch"].
 */
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { BackHandler } from 'react-native';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { Profile } from '../../src/calmframes/profiles';
import { checkedShelf } from './shelfFixtures';

const titles = checkedShelf();
const profiles = [
  { id: 'everyone', name: 'Everyone' },
  { id: 'robin', name: 'Robin' },
] as unknown as Profile[];

function preferred(): string[] {
  const ids = screen.UNSAFE_root
    .findAll((node) => node.props.hasTVPreferredFocus === true && typeof node.props.testID === 'string')
    .map((node) => node.props.testID as string);
  return [...new Set(ids)];
}

let handlers: Array<() => boolean | null | undefined> = [];
beforeEach(() => {
  handlers = [];
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_, handler) => {
    handlers.push(handler);
    return { remove: () => { handlers = handlers.filter((one) => one !== handler); } };
  });
});
afterEach(() => jest.restoreAllMocks());
const back = () => act(() => { expect([...handlers].reverse().some((handler) => handler() === true)).toBe(true); });

it('returns focus to the profile button, and only there, after Back closes the picker', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  expect(preferred()).toEqual(['kid-home-watch']);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  expect(screen.getByTestId('kid-home-profiles')).toBeTruthy();
  back();
  expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
  expect(preferred()).toEqual(['kid-home-choose-profile']);
});

it('the panel dismissed last decides: How it works, then the picker, then How it works again', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
  expect(preferred()).toEqual(['kid-home-learn']);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  back();
  expect(preferred()).toEqual(['kid-home-choose-profile']);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
  expect(preferred()).toEqual(['kid-home-learn']);
});

// Opening the picker moves focus onto the profile already watching (Oct 23,
// bd55e47). Watch stays on screen beneath the picker, so it has to stop asking
// while the picker is open, or two controls ask at once and the device picks.
// Seen to fail, Oct 23 2026: before KidHomeScreen held Watch's request back
// while the picker was open, this reported
// ["kid-home-profiles-everyone", "kid-home-watch"].
it('opening the picker asks for focus on the active profile alone', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  back();
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  expect(screen.getByTestId('kid-home-profiles')).toBeTruthy();
  expect(preferred()).toEqual(['kid-home-profiles-everyone']);
});

it('choosing a profile closes the picker and returns focus to its button alone', () => {
  const onChooseProfile = jest.fn();
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={onChooseProfile} />);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  fireEvent.press(screen.getByTestId('kid-home-profiles-robin'));
  expect(onChooseProfile).toHaveBeenCalledWith(profiles[1]);
  expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
  expect(preferred()).toEqual(['kid-home-choose-profile']);
});

// The choice is written to storage, and every control that opens something is
// disabled while it is. If the picker closed on the press, focus would be sent
// to the profile button while that button cannot take it, and the remote would
// be left with nothing focused until the write finished. So the picker waits,
// with its chips still focusable, and closes once the write is done.
it('a choice that is still saving keeps the picker open until the save ends', () => {
  // The write starts inside the press, as KidModeScreen's does, so the render
  // that follows the press already says it is saving.
  let finishSave = () => {};
  const Shelf = () => {
    const [saving, setSaving] = React.useState(false);
    finishSave = () => setSaving(false);
    return <KidHomeScreen titles={titles} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone"
      onChooseProfile={() => setSaving(true)} saving={saving} />;
  };
  render(<Shelf />);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  fireEvent.press(screen.getByTestId('kid-home-profiles-robin'));
  expect(screen.getByTestId('kid-home-profiles')).toBeTruthy();
  expect(screen.getByTestId('kid-home-profiles-robin').props.focusable).toBe(true);
  expect(screen.getByTestId('kid-home-profiles-robin').props.accessibilityState.disabled).toBe(true);
  act(() => finishSave());
  expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
  expect(preferred()).toEqual(['kid-home-choose-profile']);
});

it('How it works after the picker asks for Back alone, on the Acadia-only shelf', () => {
  // Seen to fail, Oct 16 2026: before How it works cleared the header request, this
  // reported ["kid-home-choose-profile", "picture-hold-dismiss"], two controls asking.
  const consumer = titles.filter((entry) => entry.title.title.startsWith('Acadia'));
  expect(consumer.length).toBe(1);
  render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  back();
  expect(preferred()).toEqual(['kid-home-choose-profile']);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  expect(preferred()).toEqual(['picture-hold-dismiss']);
});
