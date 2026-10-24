/**
 * A row of controls that a sideways press cannot leave.
 *
 * On the TV, D-pad focus moves to the nearest focusable in the pressed
 * direction, anywhere on the page. From the last button of a row with nothing
 * beside it, Right went looking up the page: in Parents it left Credits and
 * licences for the 6 ft seat chip several screens above, and the page
 * scrolled away from where the parent was. The guide keeps Left and Right
 * inside the row. Up and Down still leave it.
 *
 * jest.setup.ts draws this as a plain view, because the Kepler module's guide
 * is mocked to draw nothing there; focusRow.test.tsx checks the real one.
 */
import React from 'react';
import { StyleProp, ViewStyle } from 'react-native';
import { TVFocusGuideView } from '@amazon-devices/react-native-kepler';

export default function FocusRow({ style, testID, children }: {
  style?: StyleProp<ViewStyle>; testID?: string; children: React.ReactNode;
}) {
  return <TVFocusGuideView style={style} testID={testID} trapFocusLeft trapFocusRight>{children}</TVFocusGuideView>;
}
