/**
 * The screen before the household record is readable.
 *
 * The library stays closed until the saved settings and the PIN gate have been
 * read, and it stays closed if that read or a later write fails. This screen
 * shows the still wave opening while loading, or a notice and retry after an
 * error. Nothing here offers a way past the record, which decides what may play.
 */

import React from 'react';
import { StyleSheet, View } from 'react-native';
import CalmButton from './CalmButton';
import HarborOpening from './HarborOpening';
import { CALM_COLORS, CALM_SPACE, scale } from './calmStyles';
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
  if (!failed) return <HarborOpening testID={testID} />;
  return (
    <View testID={testID} style={styles.screen}>
      <StatusNotice
        notice={{
          title: "Your settings couldn't be opened or saved",
          detail: 'Your library stays closed until your settings and PIN are available. Try again.',
          tone: 'blocked',
        }}>
          <View style={styles.buttons}>
            <CalmButton
              testID={`${testID}-retry`}
              label="Try again"
              onPress={onRetry}
              hasTVPreferredFocus
            />
          </View>
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
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
});
