/**
 * A place for remote focus to land inside long read-only text.
 *
 * On the TV, D-pad focus moves from one focusable element to the next, and a
 * page scrolls only far enough to show whatever has focus. Text between two
 * focusable elements more than a screen apart is therefore never shown. The
 * technical page's analysis record was such a gap: on the Vega Virtual Device
 * the proof's stage buttons led straight to the closing Back, past the record
 * the proof asks the viewer to read. Each section of that record sits in a
 * stop, so focus can land on it and the page scrolls to it.
 *
 * A stop has no action, and OK does nothing. It follows the rule CalmButton
 * documents: the ring is always the same width, and focus changes the ring and
 * the fill together. The stop opts out of the app's control material, which
 * would draw a button face under text that is not a button.
 */
import React from 'react';
import { StyleProp, StyleSheet, ViewStyle } from 'react-native';
import TouchableOpacity from './CalmTouchable';
import { CalmControlAppearance } from './CalmControlSurface';
import { CoastalAppearance } from './CoastalAppearance';
import { CALM_COLORS, COASTAL_COLORS, CALM_SPACE, FOCUS_RING_WIDTH, scale } from './calmStyles';

export default function ReadingStop({ testID, style, children }: {
  testID: string; style?: StyleProp<ViewStyle>; children: React.ReactNode;
}) {
  const coastal = React.useContext(CoastalAppearance);
  const colors = coastal ? COASTAL_COLORS : CALM_COLORS;
  const [focused, setFocused] = React.useState(false);
  return <CalmControlAppearance.Provider value={false}>
    <TouchableOpacity testID={testID} accessibilityRole="text" activeOpacity={1}
      // React Native makes a touchable focusable only when it has a press handler.
      onPress={() => undefined}
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
      style={[styles.stop, style, focused ? { borderColor: colors.FOCUS_RING, backgroundColor: colors.SURFACE_FOCUSED } : null]}>
      {children}
    </TouchableOpacity>
  </CalmControlAppearance.Provider>;
}

const styles = StyleSheet.create({
  stop: {
    width: '100%',
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: 'transparent',
    backgroundColor: 'transparent',
    borderRadius: scale(18),
    padding: scale(CALM_SPACE.TIGHT),
  },
});
