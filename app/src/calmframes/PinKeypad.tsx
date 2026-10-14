/**
 * The keypad, used by parental controls and by the first run.
 *
 * It was written twice before this existed, which meant a focus ring in one
 * place and none in the other. The keys in the parent area could take D-pad
 * focus and showed nothing when they had it, so from a sofa you could not tell
 * which digit you were about to press. One component fixes both places at once
 * and keeps them fixed.
 *
 * It holds no PIN and no state beyond which key has focus. The digits go
 * straight to the caller, which decides what they mean.
 *
 * The shape is the one a television uses for a code: three columns, the digits
 * in phone order, zero and Delete on the last row, with Delete as wide as two
 * keys so the row is as wide as the rows above it. The keys are quiet at rest,
 * a card with no visible outline, and the one with focus gets the saffron ring
 * and the lifted fill together. The ring's width is reserved on every key, so
 * nothing moves when focus moves.
 *
 * A blocked keypad stays in the focus order. The parent area blocks it while
 * an attempt is being saved, and it used to do that with `disabled` on each
 * key, which TouchableOpacity turns into `focusable={false}` on the view
 * underneath: the key under the D-pad was told it could not hold focus at the
 * moment the fourth digit went in, so the next press landed wherever focus had
 * been sent. The block is now the accessibility state, which Pressability
 * reads as disabled and refuses the press for, and a check in the handler
 * besides. Nothing about focus changes while the save is in flight.
 */

import React from 'react';
import TouchableOpacity from './CalmTouchable';
import { StyleSheet, Text, View } from 'react-native';
import {
  CALM_CONTROL,
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';

export interface PinKeypadProps {
  /** How many digits have been typed, for the row of marks. */
  entered: number;
  onDigit: (digit: string) => void;
  onDelete: () => void;
  /** Where the first press should land, for the D-pad. */
  autoFocus?: boolean;
  /**
   * Blocked, while the caller saves an attempt. The keys say so to a screen
   * reader and ignore presses; they do not leave the focus order.
   */
  disabled?: boolean;
  /**
   * What the screen calls itself.
   *
   * The keys are named after the screen they are on, so a test says
   * parent-area-key-7 or first-run-key-7 and there is no doubt which keypad
   * was pressed.
   */
  idPrefix: string;
}

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'delete'];

/** The grid, in 1080p units: three keys across, with one row gap between. */
const KEY_WIDTH = 160;
const KEY_GAP = CALM_SPACE.ROW;
const COLUMNS = 3;

const PinKeypad = ({
  entered,
  onDigit,
  onDelete,
  autoFocus = true,
  disabled = false,
  idPrefix,
}: PinKeypadProps) => {
  const [focusedDigit, setFocusedDigit] = React.useState<string | null>(null);

  return (
    <View testID={`${idPrefix}-keypad`} style={styles.keypad}>
      <Text
        style={styles.entered}
        testID={`${idPrefix}-entered`}
        accessibilityLabel={`${entered} of four digits entered`}>
        {'*'.repeat(entered)}
      </Text>
      <View style={styles.keys}>
        {KEYS.map((digit) => (
          <TouchableOpacity
            key={digit}
            surfaceKind="keypad"
            testID={`${idPrefix}-key-${digit}`}
            accessibilityRole="button"
            accessibilityLabel={digit === 'delete' ? 'Delete the last digit' : digit}
            // Not the `disabled` prop: that would also take the key out of
            // the focus order. The state alone blocks the press and keeps it.
            accessibilityState={{ disabled }}
            activeOpacity={1}
            hasTVPreferredFocus={autoFocus && digit === '1'}
            onFocus={() => setFocusedDigit(digit)}
            onBlur={() => setFocusedDigit(null)}
            onPress={() => {
              if (!disabled) {
                if (digit === 'delete') {
                  onDelete();
                } else {
                  onDigit(digit);
                }
              }
            }}
            style={[
              styles.key,
              digit === 'delete' ? styles.keyWide : null,
              focusedDigit === digit ? styles.keyFocused : null,
            ]}>
            <Text style={[digit === 'delete' ? styles.deleteLabel : styles.keyLabel, focusedDigit === digit ? styles.focusedLabel : null]}>
              {digit === 'delete' ? 'Delete' : digit}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  focusedLabel: { textDecorationLine: 'underline' },
  keypad: {
    width: scale(COLUMNS * (KEY_WIDTH + KEY_GAP)),
  },
  /**
   * The marks for the digits typed so far.
   *
   * The line keeps its height when it is empty, so the keys do not move up
   * when the first digit goes in or down when Delete takes the last one out.
   */
  entered: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
    letterSpacing: scale(CALM_SPACE.TIGHT),
    minHeight: CALM_TEXT.screen.lineHeight,
    marginBottom: scale(CALM_SPACE.ROW),
  },
  keys: { flexDirection: 'row', flexWrap: 'wrap' },
  key: {
    width: scale(KEY_WIDTH),
    marginRight: scale(KEY_GAP),
    marginBottom: scale(KEY_GAP),
    paddingVertical: scale(CALM_SPACE.ROW),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.SURFACE,
    backgroundColor: CALM_COLORS.SURFACE,
    alignItems: 'center',
    justifyContent: 'center',
  },
  /** Delete spans two columns, so the last row is as wide as the others. */
  keyWide: {
    width: scale(KEY_WIDTH * 2 + KEY_GAP),
  },
  keyFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  keyLabel: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
  },
  /**
   * The word Delete, at control size, on a line as tall as a digit's so the
   * key stands level with the zero beside it.
   */
  deleteLabel: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
    lineHeight: CALM_TEXT.screen.lineHeight,
  },
});

export default PinKeypad;
