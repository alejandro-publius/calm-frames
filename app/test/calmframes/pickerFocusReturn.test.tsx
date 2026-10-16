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

it('opening the picker from its button asks for no other focus than the shelf had', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  back();
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  expect(screen.getByTestId('kid-home-profiles')).toBeTruthy();
  expect(preferred()).toEqual(['kid-home-watch']);
});
