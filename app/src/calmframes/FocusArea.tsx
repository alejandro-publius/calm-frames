/**
 * A region the remote can enter even when what it holds reaches out of sight.
 *
 * On the TV, D-pad focus moves to the nearest focusable whose frame lies in
 * the pressed direction. A reading stop at the foot of a scroller can have a
 * frame that runs past the scroller's visible edge, down beside the controls
 * below it, so Up from those controls never found it: on the first run's
 * explainer, Up from Open library stayed where it was. The guide's frame is
 * the scroller's visible one, so Up enters it, and the guide hands focus to
 * the first focusable inside, then to whichever was focused there last. Down
 * from inside leaves it as usual.
 *
 * jest.setup.ts draws this as a plain view, because the Kepler module's guide
 * is mocked to draw nothing there; focusArea.test.tsx checks the real one.
 */
import React from 'react';
import { StyleProp, ViewStyle } from 'react-native';
import { TVFocusGuideView } from '@amazon-devices/react-native-kepler';

export default function FocusArea({ style, testID, children }: {
  style?: StyleProp<ViewStyle>; testID?: string; children: React.ReactNode;
}) {
  return <TVFocusGuideView style={style} testID={testID} autoFocus>{children}</TVFocusGuideView>;
}
