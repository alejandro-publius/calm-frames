import { act, render, screen } from '@testing-library/react-native';
import React from 'react';
import { TouchableOpacity } from 'react-native';
import ProfilePicker from '../../src/calmframes/ProfilePicker';
import { addProfile, newFamily } from '../../src/calmframes/profiles';

it('focuses the active choice only when opening a chooser and retains accessible state without duplicate copy', () => {
  const family = addProfile(newFamily(), 'Sam');
  const view = render(<ProfilePicker profiles={family.profiles} activeProfileId={family.activeProfileId}
    title="Who is watching" focusActive onChoose={jest.fn()} />);
  const active = view.getByTestId(`profile-picker-${family.activeProfileId}`);
  expect(active.props.hasTVPreferredFocus).toBe(true);
  expect(active.props.accessibilityState).toMatchObject({checked: true, selected: true});
  expect(view.queryByTestId('profile-picker-chosen')).toBeNull();
});

it('ignores a delivered profile press while a save blocks the picker', () => {
  const family = addProfile(newFamily(), 'Sam');
  const onChoose = jest.fn();
  const picker = (disabled: boolean) => <ProfilePicker
    profiles={family.profiles} activeProfileId={family.activeProfileId}
    title="Who is watching" chosenLine="Kid is watching."
    onChoose={onChoose} disabled={disabled} />;
  const view = render(picker(true));
  // Deliver the callback directly so the handler is tested independently of
  // Pressability suppressing disabled events before they reach the component.
  const pressSam = () => screen.UNSAFE_getAllByType(TouchableOpacity)[1].props.onPress();
  act(pressSam);
  act(pressSam);
  expect(onChoose).not.toHaveBeenCalled();
  view.rerender(picker(false));
  act(pressSam);
  expect(onChoose).toHaveBeenCalledTimes(1);
  expect(onChoose).toHaveBeenCalledWith(family.profiles[1]);
});
