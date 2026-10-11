/**
 * Explain a checked title for the household that is about to watch it.
 * This is presentation only: it never changes the schedule or authorizes play.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
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
        Your viewing settings
      </Text>
      <View style={styles.columns}>
        <View style={styles.summary}>
          <Text style={styles.label} testID={`${testID}-preset`}>
            {preset.title}
          </Text>
          <Text style={styles.line} testID={`${testID}-room`}>
            {describeRoom(settings)}
          </Text>
          <Text style={styles.line} testID={`${testID}-maps`}>
            {`Checked against ${mapNames.join(' and ')} thresholds.`}
          </Text>
        </View>
        <View style={styles.explanation}>
          <Text style={styles.line} testID={`${testID}-continuity`}>
            When a part is hidden, a checked still or dark screen covers the picture
            while sound and captions continue.
          </Text>
          <Text style={styles.line}>
            The picture stays covered while seeking or when playback timing is
            uncertain. Room settings can only hide additional parts.
          </Text>
        </View>
      </View>
      <Text style={styles.limits} testID={`${testID}-limits`}>
        {SAFETY_NOTE}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: CALM_COLORS.SURFACE,
    borderRadius: scale(20),
    padding: scale(40),
  },
  heading: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.section,
  },
  label: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.control,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  line: {
    color: CALM_COLORS.TEXT_DIM,
    ...CALM_TEXT.supporting,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  columns: { flexDirection: 'row', gap: scale(64), marginTop: scale(12) },
  summary: { width: scale(520) },
  explanation: { flex: 1 },
  limits: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(32),
    paddingTop: scale(24),
    borderTopWidth: scale(1),
    borderTopColor: CALM_COLORS.BORDER,
  },
});

export default ViewingPlan;
