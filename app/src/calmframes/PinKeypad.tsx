/**
 * The keypad, used by the parent area and by the first run.
 *
 * It was written twice before this existed, which meant a focus ring in one
 * place and none in the other. The keys in the parent area could take D-pad
 * focus and showed nothing when they had it, so from a sofa you could not tell
 * which digit you were about to press. One component fixes both places at once
 * and keeps them fixed.
 *
 * It holds no PIN and no state beyond which key has focus. The digits go
 * straight to the caller, which decides what they mean.
 */

import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';

export interface PinKeypadProps {
  /** How many digits have been typed, for the row of dots. */
  entered: number;
  onDigit: (digit: string) => void;
  /** Where the first press should land, for the D-pad. */
  autoFocus?: boolean;
  /**
   * What the screen calls itself.
   *
   * The keys are named after the screen they are on, so a test says
   * parent-area-key-7 or first-run-key-7 and there is no doubt which keypad
   * was pressed.
   */
  idPrefix: string;
}

const DIGITS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];

const PinKeypad = ({
  entered,
  onDigit,
  autoFocus = true,
  idPrefix,
}: PinKeypadProps) => {
  const [focusedDigit, setFocusedDigit] = React.useState<string | null>(null);

  return (
    <View testID={`${idPrefix}-keypad`}>
      <Text
        style={styles.entered}
        testID={`${idPrefix}-entered`}
        accessibilityLabel={`${entered} of four digits entered`}>
        {'*'.repeat(entered)}
      </Text>
      <View style={styles.keypad}>
        {DIGITS.map((digit) => (
          <TouchableOpacity
            key={digit}
            testID={`${idPrefix}-key-${digit}`}
            accessibilityRole="button"
            accessibilityLabel={digit}
            activeOpacity={1}
            hasTVPreferredFocus={autoFocus && digit === '1'}
            onFocus={() => setFocusedDigit(digit)}
            onBlur={() => setFocusedDigit(null)}
            onPress={() => onDigit(digit)}
            style={[styles.key, focusedDigit === digit ? styles.keyFocused : null]}>
            <Text style={styles.keyLabel}>{digit}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  entered: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SCREEN_TITLE),
    letterSpacing: scale(12),
    minHeight: scale(72),
  },
  keypad: { flexDirection: 'row', flexWrap: 'wrap', maxWidth: scale(620) },
  key: {
    width: scale(160),
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.ROW),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
    alignItems: 'center',
  },
  keyFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  keyLabel: { color: CALM_COLORS.TEXT, fontSize: scale(CALM_TYPE.SCREEN_TITLE) },
});

export default PinKeypad;
