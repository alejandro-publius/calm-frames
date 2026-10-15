/** Shared, stationary page chrome. Back always occupies the left navigation slot. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { COASTAL_COLORS as CALM_COLORS, CALM_FONT, CALM_TEXT, scale } from './calmStyles';
export default function CalmPageHeader({ onBack, backLabel = 'Back', backTestID, preferredBack = false, backDisabled = false, wordmark = true, children }: { onBack?: () => void; backLabel?: string; backTestID?: string; preferredBack?: boolean; backDisabled?: boolean; /** Home carries the name as its heading, so its header leaves the slot empty. */ wordmark?: boolean; children?: React.ReactNode }) {
  return <View style={styles.header}>
    <View style={styles.identity}>
      {onBack ? <CalmButton quiet compact disabled={backDisabled} label={backLabel} testID={backTestID} onPress={onBack} hasTVPreferredFocus={preferredBack} /> : wordmark ? <Text style={styles.wordmark}>Calm Frames</Text> : null}
    </View>
    <View style={styles.actions}>{children}</View>
  </View>;
}
const styles = StyleSheet.create({
  header: { width: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', minHeight: scale(88), marginBottom: scale(32) },
  identity: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
  mark: { width: scale(56), height: scale(56) },
  wordmark: { ...CALM_TEXT.supporting, fontFamily: CALM_FONT.display, letterSpacing: scale(2), color: CALM_COLORS.TEXT },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
});
