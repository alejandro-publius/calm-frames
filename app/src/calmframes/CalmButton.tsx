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
import { CoastalAppearance } from './CoastalAppearance';
import TouchableOpacity from './CalmTouchable';
import { StyleSheet, Text } from 'react-native';
import {
  CALM_CONTROL,
  CALM_COLORS,
  COASTAL_COLORS,
  COASTAL_PRIMARY_FOCUS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import { CalmControlAppearance } from './CalmControlSurface';
import { useInterfaceFeedback } from './useInterfaceSound';

export interface CalmButtonProps {
  label: string;
  playIcon?: boolean;
  primary?: boolean;
  /** Quieter navigation chrome; focus keeps the same visible ring and underline. */
  quiet?: boolean;
  /** Text-only at rest; retains a full target and the standard visible focus treatment. */
  tertiary?: boolean;
  /** Smaller quiet links retain the minimum TV text size and full focus boundary. */
  compact?: boolean;
  onPress?: () => void;
  onFocus?: () => void;
  onBlur?: () => void;
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
  playIcon = false,
  primary = false,
  quiet = false,
  tertiary = false,
  compact = false,
  onPress,
  onFocus,
  onBlur,
  accessibilityLabel,
  disabled = false,
  sound = true,
  hasTVPreferredFocus = false,
  testID = 'calm-button',
}: CalmButtonProps) => {
  const coastal = React.useContext(CoastalAppearance);
  const styles = coastal ? coastalStyles : darkStyles;
  const [pressed, setPressed] = React.useState(false);
  const [focused, setFocused] = React.useState(false);
  const feedback = useInterfaceFeedback();
  const study = React.useContext(CalmControlAppearance);
  return (
    <TouchableOpacity
      testID={testID}
      surfaceKind={primary ? 'primary' : tertiary || (quiet && (compact || coastal)) ? 'tertiary' : 'secondary'}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled }}
      activeOpacity={1}
      hasTVPreferredFocus={hasTVPreferredFocus}
      disabled={disabled}
      onPressIn={() => setPressed(true)}
      onPressOut={() => setPressed(false)}
      onFocus={() => { setFocused(true); onFocus?.(); }}
      onBlur={() => { setFocused(false); setPressed(false); onBlur?.(); }}
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
        tertiary && !primary ? styles.tertiary : null,
        primary && !disabled ? styles.primary : null,
        disabled ? styles.buttonDisabled : null,
        focused && !disabled ? (primary ? styles.primaryFocused : styles.buttonFocused) : null,
      ]}>
      {playIcon ? <Text accessible={false} importantForAccessibility="no" style={[styles.label, styles.playIcon, primary && !disabled ? ((focused || pressed) ? styles.focusedPrimaryLabel : styles.primaryLabel) : null, disabled ? styles.labelDisabled : null]}>▶</Text> : null}
      <Text
        testID={`${testID}-label`}
        style={[styles.label, compact ? styles.compactLabel : null, focused && !disabled ? styles.focusedLabel : null, primary && !disabled ? ((focused || pressed) ? styles.focusedPrimaryLabel : styles.primaryLabel) : null, disabled ? styles.labelDisabled : null, study && primary && !disabled ? styles.primaryLabel : null]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
};

const makeStyles = (colors: Record<keyof typeof CALM_COLORS, string>, coastal = false) => StyleSheet.create({
  button: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: scale(CALM_CONTROL.MIN_HEIGHT),
    justifyContent: 'center',
    paddingVertical: scale(15),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: colors.SURFACE,
    backgroundColor: colors.SURFACE,
  },
  buttonFocused: {
    borderColor: colors.FOCUS_RING,
    backgroundColor: colors.SURFACE_FOCUSED,
  },
  // Decorative, but drawn at the ten foot text floor like everything else on the screen.
  playIcon: { marginRight: scale(20), fontSize: scale(34) },
  quiet: {
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.ROW),
    borderColor: coastal ? 'transparent' : colors.BACKGROUND,
    backgroundColor: coastal ? 'transparent' : colors.BACKGROUND,
  },
  tertiary: { borderColor: 'transparent', backgroundColor: 'transparent' },
  // Not faded: the same background, a quieter edge, and the word for it in the
  // label the caller passes.
  buttonDisabled: {
    borderColor: colors.SURFACE_FOCUSED,
  },
  label: {
    color: colors.TEXT,
    ...CALM_TEXT.control,
  },
  compactLabel: { ...CALM_TEXT.supporting },
  focusedLabel: { textDecorationLine: 'underline' },
  primary: { backgroundColor: colors.PRIMARY, borderColor: colors.PRIMARY, ...(coastal ? { borderRadius: scale(64), minWidth: scale(280), paddingHorizontal: scale(48), minHeight: scale(108) } : {}) },
  primaryFocused: { backgroundColor: colors.PRIMARY, borderColor: COASTAL_PRIMARY_FOCUS },
  focusedPrimaryLabel: { color: colors.INK },
  primaryLabel: { color: coastal ? colors.BACKGROUND : colors.INK },
  labelDisabled: {
    color: colors.TEXT_DISABLED,
  },
});

const darkStyles = makeStyles(CALM_COLORS);
const coastalStyles = makeStyles(COASTAL_COLORS, true);
export default CalmButton;
