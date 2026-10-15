/**
 * The screen before the household record is readable.
 *
 * The library stays closed until the saved settings and the PIN gate have been
 * read, and it stays closed if that read or a later write fails. This screen
 * shows the still wave opening while loading, or a notice and retry after an
 * error. Nothing here offers a way past the record, which decides what may play.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import HomeHarborScene from './HomeHarborScene';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import StatusNotice from './StatusNotice';
import { useUiCapture } from './uiCapture';
import { HOUSEHOLD_ERROR_FRAME, HOUSEHOLD_LOADING_FRAME } from './uiFrames';

export default function HouseholdStorageScreen({
  failed,
  onRetry,
  testID = 'household-storage',
}: {
  failed: boolean;
  onRetry: () => void;
  testID?: string;
}) {
  useUiCapture(
    failed ? HOUSEHOLD_ERROR_FRAME : HOUSEHOLD_LOADING_FRAME,
    failed ? 'household storage unavailable' : 'household storage loading',
  );
  if (!failed) return <View testID={testID} style={styles.screen}>
    <HomeHarborScene />
    <CalmPageHeader />
    <View style={styles.loading} accessible accessibilityRole="progressbar" accessibilityLabel="Opening Calm Frames" accessibilityLiveRegion="polite">
      <Text style={styles.heading}>Opening Calm Frames</Text>
      <Text style={styles.detail}>Loading your settings.</Text>
    </View>
  </View>;
  return (
    <View testID={testID} style={styles.screen}>
      <CalmPageHeader />
      <StatusNotice
        notice={{
          title: "Your settings couldn't be opened or saved",
          detail: 'Nothing can play until your settings and PIN are available. Try again.',
          tone: 'blocked',
        }} />
      {/* On the page, not inside the notice: a focused primary's terracotta ring
          clears the 3 to 1 floor against the ivory page, not against the panel. */}
      <View style={styles.buttons}>
        <CalmButton
          testID={`${testID}-retry`} primary
          label="Try again"
          onPress={onRetry}
          hasTVPreferredFocus
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: CALM_COLORS.BACKGROUND,
    paddingHorizontal: scale(CALM_SPACE.SAFE_X),
    paddingVertical: scale(CALM_SPACE.SAFE_Y),
  },
  brand: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
  mark: { width: scale(80), height: scale(80) },
  wordmark: { ...CALM_TEXT.control, color: CALM_COLORS.TEXT },
  loading: { paddingTop: scale(102), maxWidth: scale(750), gap: scale(24) },
  heading: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT },
  detail: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM },
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
});
