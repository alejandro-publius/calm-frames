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
 * - `activeOpacity` is 1, so pressing does not dim it either. Controls stay
 *   stationary while artwork can have its own optional entry motion.
 */

import React from 'react';
import { StyleSheet, Text, TouchableOpacity } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import { useInterfaceFeedback } from './useInterfaceSound';

export interface CalmButtonProps {
  label: string;
  primary?: boolean;
  /** Quieter navigation chrome; focus keeps the same visible ring and underline. */
  quiet?: boolean;
  onPress?: () => void;
  /** What a screen reader says. Defaults to the label. */
  accessibilityLabel?: string;
  /** Drawn as unavailable, and it does not call back. */
  disabled?: boolean;
  /** Disable confirmation for actions that start playback or confirm elsewhere. */
  sound?: boolean;
  hasTVPreferredFocus?: boolean;
  testID?: string;
}

const CalmButton = ({
  label,
  primary = false,
  quiet = false,
  onPress,
  accessibilityLabel,
  disabled = false,
  sound = true,
  hasTVPreferredFocus = false,
  testID = 'calm-button',
}: CalmButtonProps) => {
  const [focused, setFocused] = React.useState(false);
  const feedback = useInterfaceFeedback();
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
      onPress={() => {
        if (disabled || !onPress) { return; }
        onPress();
        if (sound) {
          try { feedback.confirm(); } catch { /* The action already succeeded. */ }
        }
      }}
      style={[
        styles.button,
        quiet && !primary ? styles.quiet : null,
        primary && !disabled ? styles.primary : null,
        disabled ? styles.buttonDisabled : null,
        focused && !disabled ? (primary ? styles.primaryFocused : styles.buttonFocused) : null,
      ]}>
      <Text
        testID={`${testID}-label`}
        style={[styles.label, focused && !disabled ? styles.focusedLabel : null, primary && !disabled ? (focused ? styles.focusedPrimaryLabel : styles.primaryLabel) : null, disabled ? styles.labelDisabled : null]}>
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
    borderColor: CALM_COLORS.SURFACE,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  buttonFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  quiet: {
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.ROW),
    borderColor: CALM_COLORS.BACKGROUND,
    backgroundColor: CALM_COLORS.BACKGROUND,
  },
  // Not faded: the same background, a quieter edge, and the word for it in the
  // label the caller passes.
  buttonDisabled: {
    borderColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  label: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.control,
  },
  focusedLabel: { textDecorationLine: 'underline' },
  primary: { backgroundColor: CALM_COLORS.FOCUS_RING, borderColor: CALM_COLORS.FOCUS_RING },
  primaryFocused: { backgroundColor: CALM_COLORS.INK, borderColor: CALM_COLORS.FOCUS_RING },
  focusedPrimaryLabel: { color: CALM_COLORS.TEXT },
  primaryLabel: { color: CALM_COLORS.INK },
  labelDisabled: {
    color: CALM_COLORS.TEXT_DIM,
  },
});

export default CalmButton;
