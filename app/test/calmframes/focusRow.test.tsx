/**
 * The real FocusRow, with the Kepler guide drawn as a recording view.
 *
 * jest.setup.ts draws FocusRow as a plain view for every other test, so this
 * file holds the row to what it asks the TV for: Left and Right kept inside,
 * Up and Down free. Seen to fail: dropping trapFocusRight from FocusRow.
 */
jest.unmock('../../src/calmframes/FocusRow');
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
import FocusRow from '../../src/calmframes/FocusRow';

it('keeps Left and Right inside the row, and lets Up and Down leave it', () => {
  render(<FocusRow><Text>Back</Text><Text>Credits</Text></FocusRow>);
  const guide = screen.getByTestId('guide');
  expect(guide.props.trapFocusRight).toBe(true);
  expect(guide.props.trapFocusLeft).toBe(true);
  expect(guide.props.trapFocusUp).toBeFalsy();
  expect(guide.props.trapFocusDown).toBeFalsy();
  expect(screen.getByText('Credits')).toBeTruthy();
});
