// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from '../calmframes/CalmButton';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from '../calmframes/calmStyles';

interface ErrorViewProps { navigateBack: () => void; }

const ErrorView = ({ navigateBack }: ErrorViewProps) => (
  <View style={styles.mainContainer} testID="player-error" accessibilityViewIsModal>
    <View style={styles.message} accessible accessibilityRole="alert" accessibilityLiveRegion="polite">
      <Text style={styles.title} testID="error-boundary-label">Playback stopped</Text>
      <Text style={styles.detail}>Go back and try playing the video again.</Text>
    </View>
    <View>
      <CalmButton primary label="Go back" onPress={navigateBack} hasTVPreferredFocus sound={false} testID="player-error-back" />
    </View>
  </View>
);

export default ErrorView;

export const styles = StyleSheet.create({
  mainContainer: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 6,
    backgroundColor: CALM_COLORS.COVER,
    alignItems: 'flex-start', justifyContent: 'center',
    paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y),
    gap: scale(CALM_SPACE.BLOCK),
  },
  message: { alignItems: 'flex-start', maxWidth: scale(1200), gap: scale(CALM_SPACE.ROW) },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.FAILED, textAlign: 'left' },
  detail: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
});
