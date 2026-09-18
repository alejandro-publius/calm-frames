/**
 * One button, used everywhere.
 *
 * Buttons were being written out screen by screen, which is how two screens
 * end up with focus rings of different thicknesses and nobody notices, because
 * nobody can take a screenshot of this device to compare them. One component
 * means one ring, one size and one focus behaviour, and
 * test/calmframes/tenFoot.test.tsx measures it once for every screen.
 *
 * - The border is the same width whether the button has focus or not, so
 *   nothing moves when focus moves. Focus changes the ring colour and the fill
 *   together, never colour alone.
 * - Nothing fades. A button that cannot be pressed says so in words and in its
 *   colours, rather than being drawn at half opacity, which is unreadable
 *   across a room and unreadable to a camera.
 * - `activeOpacity` is 1, so pressing does not dim it either. There is no
 *   motion in this app.
 */

import React from 'react';
import { StyleSheet, Text, TouchableOpacity } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';

export interface CalmButtonProps {
  label: string;
  onPress?: () => void;
  /** What a screen reader says. Defaults to the label. */
  accessibilityLabel?: string;
  /** Drawn as unavailable, and it does not call back. */
  disabled?: boolean;
  hasTVPreferredFocus?: boolean;
  testID?: string;
}

const CalmButton = ({
  label,
  onPress,
  accessibilityLabel,
  disabled = false,
  hasTVPreferredFocus = false,
  testID = 'calm-button',
}: CalmButtonProps) => {
  const [focused, setFocused] = React.useState(false);
  return (
    <TouchableOpacity
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled }}
      activeOpacity={1}
      hasTVPreferredFocus={hasTVPreferredFocus}
      disabled={disabled}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      onPress={onPress}
      style={[
        styles.button,
        disabled ? styles.buttonDisabled : null,
        focused && !disabled ? styles.buttonFocused : null,
      ]}>
      <Text
        testID={`${testID}-label`}
        style={[styles.label, disabled ? styles.labelDisabled : null]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    alignSelf: 'flex-start',
    paddingVertical: scale(CALM_SPACE.ROW),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  buttonFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  // Not faded: the same background, a quieter edge, and the word for it in the
  // label the caller passes.
  buttonDisabled: {
    borderColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  label: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BUTTON),
    fontWeight: '600',
  },
  labelDisabled: {
    color: CALM_COLORS.TEXT_DIM,
  },
});

export default CalmButton;
