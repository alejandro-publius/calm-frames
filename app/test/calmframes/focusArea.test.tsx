/**
 * The real FocusArea, with the Kepler guide drawn as a recording view.
 *
 * jest.setup.ts draws FocusArea as a plain view for every other test, so this
 * file holds the area to what it asks the TV for: focus entering it goes to
 * what is inside, and no direction is trapped. Seen to fail: dropping
 * autoFocus from FocusArea.
 */
jest.unmock('../../src/calmframes/FocusArea');
jest.mock('@amazon-devices/react-native-kepler', () => {
  const ReactActual = jest.requireActual('react');
  const { View } = jest.requireActual('react-native');
  return {
    __esModule: true,
    TVFocusGuideView: ({ children, ...props }: { children?: unknown }) => ReactActual.createElement(View, { ...props, testID: 'guide' }, children),
  };
});

import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';
import FocusArea from '../../src/calmframes/FocusArea';

it('hands focus entering the area to what is inside, and traps no direction', () => {
  render(<FocusArea><Text>How Calm Frames works</Text></FocusArea>);
  const guide = screen.getByTestId('guide');
  expect(guide.props.autoFocus).toBe(true);
  for (const trap of ['trapFocusUp', 'trapFocusDown', 'trapFocusLeft', 'trapFocusRight']) {
    expect(guide.props[trap]).toBeFalsy();
  }
  expect(screen.getByText('How Calm Frames works')).toBeTruthy();
});
