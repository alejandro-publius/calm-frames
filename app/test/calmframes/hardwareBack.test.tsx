/**
 * The remote's Back button closes one level, never more.
 *
 * Three places used to answer Back with nothing of their own, so the press
 * fell through to the shelf's handler and left the app: the profile picker on
 * the shelf, every step of the first run, and the question the parent area
 * asks before removing a kid. Each test opens the thing, presses Back through
 * the handler the screen registered last, and expects to be one level back.
 */
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { BackHandler } from 'react-native';
import FirstRunScreen from '../../src/calmframes/FirstRunScreen';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { addProfile, newFamily } from '../../src/calmframes/profiles';
import { checkedShelf } from './shelfFixtures';

type Handler = () => boolean;
let registered: Handler[] = [];
beforeEach(() => {
  registered = [];
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation(((event: string, handler: Handler) => {
    if (event === 'hardwareBackPress') registered.push(handler);
    return { remove: () => { registered = registered.filter((one) => one !== handler); } };
  }) as typeof BackHandler.addEventListener);
});
afterEach(() => jest.restoreAllMocks());

/** What the device does: the most recently registered handler answers first. */
function pressBack(): boolean {
  let handled = false;
  act(() => {
    for (const handler of [...registered].reverse()) {
      if (handler()) { handled = true; break; }
    }
  });
  return handled;
}

test('Back closes the profile picker on the shelf instead of leaving the app', () => {
  const family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');
  render(<KidHomeScreen titles={checkedShelf()} onOpen={jest.fn()} profiles={family.profiles}
    activeProfileId={family.activeProfileId} onChooseProfile={jest.fn()} />);
  expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
  fireEvent.press(screen.getByTestId('kid-home-choose-profile'));
  expect(screen.getByTestId('kid-home-profiles')).toBeTruthy();
  expect(pressBack()).toBe(true);
  expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
  // With the picker closed the shelf has nothing of its own to close.
  expect(pressBack()).toBe(false);
});

describe('Back during the first run', () => {
  const typePin = (pin: string) => { for (const digit of pin) fireEvent.press(screen.getByTestId(`first-run-key-${digit}`)); };

  it('walks back one step at a time, and asks for the PIN again before the preset', () => {
    render(<FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />);
    typePin('1357'); typePin('1357');
    expect(screen.getByTestId('first-run-preset-wcag')).toBeTruthy();
    fireEvent.press(screen.getByTestId('first-run-next'));
    expect(screen.getByTestId('first-run-tv-55')).toBeTruthy();
    fireEvent.press(screen.getByTestId('first-run-next'));
    expect(screen.getByTestId('first-run-done')).toBeTruthy();

    expect(pressBack()).toBe(true);
    expect(screen.getByTestId('first-run-tv-55')).toBeTruthy();
    expect(screen.queryByTestId('first-run-done')).toBeNull();
    expect(pressBack()).toBe(true);
    expect(screen.getByTestId('first-run-preset-wcag')).toBeTruthy();
    expect(pressBack()).toBe(true);
    expect(screen.queryByTestId('first-run-preset-wcag')).toBeNull();
    expect(screen.getByTestId('first-run-key-1')).toBeTruthy();
    // Both entries are asked for again: one matching entry is not enough.
    typePin('2468');
    expect(screen.queryByTestId('first-run-preset-wcag')).toBeNull();
    typePin('2468');
    expect(screen.getByTestId('first-run-preset-wcag')).toBeTruthy();
  });

  it('returns to the parent area from the PIN step when the parent opened it, and otherwise lets the system have it', () => {
    const onCancel = jest.fn();
    render(<FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} onCancel={onCancel} />);
    typePin('13');
    expect(pressBack()).toBe(true);
    expect(onCancel).toHaveBeenCalledTimes(1);
    screen.unmount();
    render(<FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />);
    expect(pressBack()).toBe(false);
  });
});

test('Back answers the remove-a-kid question with keeping the kid, not with leaving the parent area', () => {
  const onBack = jest.fn();
  const onFamilyChange = jest.fn();
  const family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');
  render(<ParentAreaScreen gate={setPin(emptyPinGate(), '1357', 'test-fixture', 4)} onGateChange={jest.fn()}
    settings={DEFAULT_SETTINGS} onSettingsChange={jest.fn()} family={family} onFamilyChange={onFamilyChange}
    log={emptyHideLog()} titles={[]} onBack={onBack} />);
  for (const digit of '1357') fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
  fireEvent.press(screen.getByTestId(`parent-area-profiles-${family.profiles[1].id}`));
  fireEvent.press(screen.getByTestId('parent-area-remove-profile'));
  expect(screen.getByTestId('parent-area-remove-question')).toBeTruthy();
  expect(pressBack()).toBe(true);
  expect(screen.queryByTestId('parent-area-remove-question')).toBeNull();
  expect(onFamilyChange).not.toHaveBeenCalled();
  expect(onBack).not.toHaveBeenCalled();
  // The kid is still open for editing: one level back, not two.
  expect(screen.getByTestId('parent-area-remove-profile')).toBeTruthy();
});
