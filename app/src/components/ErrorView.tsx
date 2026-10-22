// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from '../calmframes/CalmButton';
import { CALM_COLORS, CALM_SURFACE, CALM_SPACE, CALM_TEXT, scale } from '../calmframes/calmStyles';

interface ErrorViewProps { navigateBack: () => void; onRetry?: () => void; recoveryBlocked?: boolean; }

const ErrorView = ({ navigateBack, onRetry, recoveryBlocked }: ErrorViewProps) => (
  <View style={styles.mainContainer} testID="player-error" accessibilityViewIsModal>
    <View style={styles.message} accessible accessibilityRole="alert" accessibilityLiveRegion="polite">
      <Text style={styles.title} testID="error-boundary-label">Playback stopped</Text>
      <Text style={styles.detail}>{recoveryBlocked ? 'The player could not close. Go back before trying again.' : onRetry ? 'Try again from your saved position.' : 'Go back and try playing the video again.'}</Text>
    </View>
    <View style={styles.actions}>
      {onRetry && <CalmButton primary label="Try again" onPress={onRetry} hasTVPreferredFocus sound={false} testID="player-error-retry" />}
      <CalmButton primary={!onRetry} label="Go back" onPress={navigateBack} hasTVPreferredFocus={!onRetry} sound={false} testID="player-error-back" />
    </View>
  </View>
);

export default ErrorView;

export const styles = StyleSheet.create({
  actions: {flexDirection: 'row', gap: scale(CALM_SPACE.ROW)},
  mainContainer: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 6,
    backgroundColor: CALM_COLORS.COVER,
    alignItems: 'flex-start', justifyContent: 'center',
    paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y),
    gap: scale(CALM_SPACE.BLOCK),
  },
  message: { alignItems: 'flex-start', maxWidth: scale(1200), gap: scale(CALM_SPACE.ROW), backgroundColor: CALM_COLORS.SURFACE, padding: scale(CALM_SURFACE.INSET), borderRadius: scale(CALM_SURFACE.STATUS_RADIUS), borderLeftWidth: scale(8), borderLeftColor: CALM_COLORS.FAILED },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.FAILED, textAlign: 'left' },
  detail: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
});
