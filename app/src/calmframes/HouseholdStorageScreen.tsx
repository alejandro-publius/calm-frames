import React from 'react';
import { StyleSheet, View } from 'react-native';
import CalmButton from './CalmButton';
import { CALM_COLORS, CALM_SPACE, scale } from './calmStyles';
import StatusNotice from './StatusNotice';
import { useUiCapture } from './uiCapture';
import { HOUSEHOLD_LOADING_FRAME, HOUSEHOLD_ERROR_FRAME } from './uiFrames';

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
  return (
    <View testID={testID} style={styles.screen}>
      <StatusNotice
        notice={{
          title: failed
            ? 'Your settings could not be opened or saved'
            : 'Getting your household ready',
          detail: failed
            ? 'The library stays closed until your settings and parent PIN are available. Try again.'
            : 'Your settings and parent PIN stay on this television.',
          tone: failed ? 'blocked' : 'waiting',
        }}
      >
        {failed ? (
          <CalmButton
            testID={`${testID}-retry`}
            label="Try again"
            onPress={onRetry}
            hasTVPreferredFocus
          />
        ) : null}
      </StatusNotice>
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
});
