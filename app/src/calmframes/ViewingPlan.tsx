/**
 * Explain a checked title for the household that is about to watch it.
 * This is presentation only: it never changes the schedule or authorizes play.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TYPE, scale } from './calmStyles';
import { SAFETY_NOTE } from './copy';
import { describeRoom, HouseholdSettings, PRESETS } from './household';
import { CheckedTitle } from './titleStatus';

export interface ViewingPlanProps {
  entry: CheckedTitle;
  settings: HouseholdSettings;
  testID?: string;
}

const ViewingPlan = ({
  entry,
  settings,
  testID = 'viewing-plan',
}: ViewingPlanProps) => {
  const preset = PRESETS[settings.preset] ?? PRESETS.wcag;
  // An old checked entry is not an explanation of a newly stricter preset.
  // The shelf rechecks it; this presentation must not imply that it already did.
  if (
    entry.status !== 'verified' ||
    !preset.mapProfiles.every((profile) =>
      entry.verifiedProfiles.includes(profile),
    )
  ) {
    return null;
  }
  const mapNames = preset.mapProfiles.map((profile) =>
    profile === 'wcag' ? 'WCAG 2.3.1' : 'broadcast',
  );

  return (
    <View testID={testID} style={styles.card}>
      <Text style={styles.heading} accessibilityRole="header">
        Your viewing plan
      </Text>
      <Text style={styles.label} testID={`${testID}-preset`}>
        {preset.title}
      </Text>
      <Text style={styles.line} testID={`${testID}-room`}>
        {describeRoom(settings)}
      </Text>
      <Text style={styles.line} testID={`${testID}-maps`}>
        {`Checked maps: ${mapNames.join(' and ')}.`}
      </Text>
      <Text style={styles.line} testID={`${testID}-continuity`}>
        A checked still when available, otherwise an opaque cover. Sound and
        captions keep going.
      </Text>
      <Text style={styles.line}>
        Seeking or uncertain playback returns to an opaque cover. Room settings
        can only add hides.
      </Text>
      <Text style={styles.line} testID={`${testID}-limits`}>
        {SAFETY_NOTE}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: CALM_COLORS.SURFACE,
    borderRadius: scale(12),
    padding: scale(CALM_SPACE.BLOCK),
  },
  heading: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SECTION),
    fontWeight: '700',
  },
  label: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    fontWeight: '600',
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  line: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
});

export default ViewingPlan;
