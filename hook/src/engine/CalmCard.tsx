/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * The card: the one thing on screen that speaks to the child.
 *
 * It sits above the cover so it stays readable while the picture is hidden,
 * and below nothing else. Four things it has to get right:
 *
 * - it announces itself. accessibilityLiveRegion="polite" and the web
 *   aria-live="polite" attribute both go on the card, and the caller also
 *   pushes the same words through AccessibilityInfo;
 * - the Skip button takes D-pad focus the moment a countdown appears, because
 *   Vega does not let an app move focus with the D-pad itself, so the button
 *   has to be where focus already is;
 * - ten foot type, and a focus ring you can see across a room;
 * - no motion. Nothing fades, slides or pulses.
 */

import React, { useEffect, useRef } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import { Card, cardOffersSkip } from './cards';

export interface CalmCardProps {
  card: Card;
  /** Called when the child presses Skip on a countdown card. */
  onSkip?: (toMs: number) => void;
  /** Turn the Skip button off, for screens with no player behind them. */
  allowSkip?: boolean;
  skipAccessibilityLabel?: string;
  testID?: string;
}

export const CARD_Z_INDEX = 3;

const CalmCard = ({
  card,
  onSkip,
  allowSkip = true,
  skipAccessibilityLabel = 'Skip the flashing part',
  testID = 'calm-card',
}: CalmCardProps) => {
  const skipRef = useRef<React.ComponentRef<typeof TouchableOpacity> | null>(
    null,
  );
  const [focused, setFocused] = React.useState(false);

  const showSkip = allowSkip && cardOffersSkip(card);

  useEffect(() => {
    // A new countdown puts focus on Skip. requestTVFocus is the supported way
    // to move focus from an app; setNativeProps throws on React Native 0.83.
    if (showSkip) {
      const handle = skipRef.current as unknown as {
        requestTVFocus?: () => void;
      } | null;
      handle?.requestTVFocus?.();
    }
  }, [showSkip, card.interval?.startMs]);

  if (card.kind === 'none') {
    return null;
  }

  return (
    <View
      testID={testID}
      style={styles.container}
      pointerEvents="box-none"
      accessible
      accessibilityLiveRegion="polite"
      accessibilityRole="alert"
      accessibilityLabel={card.announcement}
      // The web attribute as well, because VoiceView reads the DOM-like tree
      // that React Native for Vega exposes.
      aria-live="polite"
      aria-label={card.announcement}>
      <View style={styles.card}>
        <Text style={styles.title} testID={`${testID}-title`}>
          {card.title}
        </Text>
        {card.detail ? (
          <Text style={styles.detail} testID={`${testID}-detail`}>
            {card.detail}
          </Text>
        ) : null}
        {showSkip ? (
          <TouchableOpacity
            ref={skipRef}
            testID={`${testID}-skip`}
            accessibilityRole="button"
            accessibilityLabel={skipAccessibilityLabel}
            activeOpacity={1}
            hasTVPreferredFocus
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onPress={() => onSkip?.(card.skipToMs ?? 0)}
            style={[styles.skip, focused ? styles.skipFocused : null]}>
            <Text style={styles.skipLabel}>Skip</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: scale(160),
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
    fontSize: scale(CALM_TYPE.CARD_TITLE),
    fontWeight: '600',
    textAlign: 'center',
  },
  detail: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.CARD_DETAIL),
    marginTop: scale(CALM_SPACE.TIGHT),
    textAlign: 'center',
  },
  skip: {
    marginTop: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  skipFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  skipLabel: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BUTTON),
    fontWeight: '600',
  },
});

export default CalmCard;
