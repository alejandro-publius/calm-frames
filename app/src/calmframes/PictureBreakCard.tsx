/**
 * The card for a picture break, above the cover and clear of the captions.
 *
 * It follows CalmCard's placement, type and focus ring, with one difference
 * the seamless pass asked for: the spoken text and the button are separate
 * accessible elements, so a screen reader reaches "Back to the picture" on its
 * own rather than inside the announcement. The button takes D-pad focus when
 * the card appears, the way Skip does, and stays focusable while a return is
 * held back: disabling a focused control drops native focus on Vega
 * (docs/FRICTION_LOG.md entry 40), and a second press changes nothing anyway.
 * No motion.
 */

import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { announceForAccessibility } from './announce';
import { CARD_Z_INDEX } from './CalmCard';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  PLAYER_LAYOUT,
  scale,
} from './calmStyles';
import { PictureBreakCopy } from './pictureBreak';

export interface PictureBreakCardProps {
  copy: PictureBreakCopy;
  onReturn: () => void;
  testID?: string;
}

const PictureBreakCard = ({
  copy,
  onReturn,
  testID = 'picture-break',
}: PictureBreakCardProps) => {
  const buttonRef = useRef<React.ComponentRef<typeof TouchableOpacity> | null>(
    null,
  );
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    const handle = buttonRef.current as unknown as {
      requestTVFocus?: () => void;
    } | null;
    handle?.requestTVFocus?.();
  }, []);

  useEffect(() => {
    announceForAccessibility(copy.announcement);
  }, [copy.announcement]);

  return (
    <View testID={testID} style={styles.container} pointerEvents="box-none">
      <View style={styles.card}>
        <View
          testID={`${testID}-message`}
          accessible
          accessibilityRole="alert"
          accessibilityLiveRegion="polite"
          accessibilityLabel={copy.announcement}
          aria-live="polite"
          aria-label={copy.announcement}>
          <Text style={styles.title} testID={`${testID}-title`}>
            {copy.title}
          </Text>
          <Text style={styles.detail} testID={`${testID}-detail`}>
            {copy.detail}
          </Text>
        </View>
        <TouchableOpacity
          ref={buttonRef}
          testID={`${testID}-return`}
          accessibilityRole="button"
          accessibilityLabel={copy.returnLabel}
          activeOpacity={1}
          hasTVPreferredFocus
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onPress={onReturn}
          style={[styles.button, focused ? styles.buttonFocused : null]}>
          <Text style={styles.buttonLabel}>{copy.returnLabel}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: scale(PLAYER_LAYOUT.CARD_TOP),
    alignItems: 'center',
    zIndex: CARD_Z_INDEX,
  },
  card: {
    backgroundColor: CALM_COLORS.SURFACE,
    borderColor: CALM_COLORS.BORDER,
    borderWidth: scale(2),
    borderRadius: scale(16),
    paddingVertical: scale(CALM_SPACE.BLOCK),
    paddingHorizontal: scale(CALM_SPACE.EDGE),
    alignItems: 'center',
    maxWidth: scale(1400),
  },
  title: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.card,
    textAlign: 'center',
  },
  detail: {
    color: CALM_COLORS.TEXT_DIM,
    ...CALM_TEXT.body,
    marginTop: scale(CALM_SPACE.TIGHT),
    textAlign: 'center',
  },
  button: {
    marginTop: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
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
  buttonLabel: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.control,
  },
});

export default PictureBreakCard;
