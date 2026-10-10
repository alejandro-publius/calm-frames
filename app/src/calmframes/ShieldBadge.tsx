/**
 * The shield on a poster.
 *
 * Kid mode only ever shows checked titles, so in the grid the badge is a
 * reassurance rather than a warning. The parent area shows the other two
 * states, which is where the badge earns its colours.
 *
 * Colour is never the only signal: each state also has its own word, because a
 * badge that means something only if you can tell green from amber is not an
 * accessible badge.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { badgeLabel, TitleStatus } from './titleStatus';

export interface ShieldBadgeProps {
  status: TitleStatus;
  testID?: string;
}

const COLOURS: Record<TitleStatus, string> = {
  verified: CALM_COLORS.VERIFIED,
  pending: CALM_COLORS.PENDING,
  failed: CALM_COLORS.FAILED,
};

const ShieldBadge = ({ status, testID = 'shield-badge' }: ShieldBadgeProps) => (
  <View
    testID={testID}
    accessible
    accessibilityLabel={badgeLabel(status)}
    style={[styles.badge, { borderColor: COLOURS[status] }]}>
    <Text style={[styles.label, { color: COLOURS[status] }]} testID={`${testID}-label`}>
      {badgeLabel(status)}
    </Text>
  </View>
);

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderWidth: scale(3),
    borderRadius: scale(10),
    paddingVertical: scale(6),
    paddingHorizontal: scale(CALM_SPACE.TIGHT),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  label: {
    ...CALM_TEXT.supporting,
  },
});

export default ShieldBadge;
