/**
 * The card: the one thing on screen that speaks to the child.
 *
 * It sits above the cover so it stays readable while the picture is hidden,
 * and below nothing else. It hangs from the upper part of the safe area, out
 * of the band at the bottom where captions are drawn (PLAYER_LAYOUT in
 * calmStyles.ts says why). Four things it has to get right:
 *
 * - the consumer player owns explicit speech for the final visible copy;
 *   other callers retain the live-region fallback;
 * - Skip takes D-pad focus when it appears and keeps the same action slot
 *   through the consumer countdown and cover;
 * - ten foot type, and a focus ring you can see across a room;
 * - no motion. Nothing fades, slides or pulses.
 */

import TouchableOpacity from './CalmTouchable';
import React, { useEffect, useRef } from 'react';
import { StyleSheet, Text,  View } from 'react-native';
import {
  CALM_CONTROL,
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  PLAYER_LAYOUT,
  scale,
} from './calmStyles';
import { Card, cardOffersSkip } from './cards';

export interface CalmCardProps {
  card: Card;
  /** Called only when the viewer presses the visible Skip action. */
  onSkip?: (toMs: number) => void;
  /** Turn the Skip button off, for screens with no player behind them. */
  allowSkip?: boolean;
  skipAccessibilityLabel?: string;
  testID?: string;
  /** Consumer player uses one stable action slot and one explicit speech path. */
  stableLayout?: boolean;
  manualAnnouncements?: boolean;
}

export const CARD_Z_INDEX = 3;

const CalmCard = ({
  card,
  onSkip,
  allowSkip = true,
  skipAccessibilityLabel = 'Skip past this scene',
  testID = 'calm-card',
  stableLayout = false,
  manualAnnouncements = false,
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
      accessibilityLiveRegion={manualAnnouncements ? "none" : "polite"}
      accessibilityRole={manualAnnouncements ? "text" : "alert"}
      accessibilityLabel={card.announcement}
      // The web attribute as well, because VoiceView reads the DOM-like tree
      // that React Native for Vega exposes.
      aria-live={manualAnnouncements ? "off" : "polite"}
      aria-label={card.announcement}>
      <View style={[styles.card, stableLayout ? styles.stableCard : null]}>
        <Text style={styles.title} testID={`${testID}-title`}>
          {card.title}
        </Text>
        {card.detail ? (
          <Text style={[styles.detail, stableLayout ? styles.stableDetail : null]} testID={`${testID}-detail`}>
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
    top: scale(PLAYER_LAYOUT.CARD_TOP),
    alignItems: 'center',
    zIndex: CARD_Z_INDEX,
  },
  card: {
    backgroundColor: CALM_COLORS.SURFACE,
    borderColor: CALM_COLORS.BORDER,
    borderWidth: scale(2),
    borderRadius: scale(24),
    paddingVertical: scale(CALM_SPACE.BLOCK),
    paddingHorizontal: scale(CALM_SPACE.EDGE),
    alignItems: 'center',
    maxWidth: scale(1400),
  },
  stableCard: { width: scale(1200) },
  stableDetail: { minHeight: scale(100) },
  title: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.card,
    textAlign: 'center',
  },
  detail: {
    color: CALM_COLORS.TEXT_DIM,
    ...CALM_TEXT.body, marginTop: scale(CALM_SPACE.TIGHT),
    textAlign: 'center',
  },
  skip: {
    marginTop: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(CALM_CONTROL.RADIUS),
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
    ...CALM_TEXT.control,
  },
});

export default CalmCard;
