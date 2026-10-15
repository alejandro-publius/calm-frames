/**
 * Explain a checked title for the household that is about to watch it.
 * This is presentation only: it never changes the schedule or authorizes play.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
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
    <View testID={testID} style={styles.section}>
      <View style={styles.chapterHeading}>
        <Text style={styles.heading} accessibilityRole="header">
          Your viewing settings
        </Text>
      </View>
      <View style={styles.content}>
        <View style={styles.columns}>
          <View style={styles.summary}>
            <Text style={styles.label} testID={`${testID}-preset`}>
              {preset.title}
            </Text>
            <Text style={styles.line} testID={`${testID}-room`}>
              {describeRoom(settings)}
            </Text>
            <Text style={styles.line} testID={`${testID}-maps`}>
              {`${mapNames.join(' and ')} flash limits.`}
            </Text>
          </View>
          <View style={styles.explanation}>
            <Text style={styles.line} testID={`${testID}-continuity`}>
              Flashing scenes are replaced by a still picture while sound and captions
              continue. A larger TV or a closer seat can hide more of the video, never less.
            </Text>
          </View>
        </View>
        <Text style={styles.limits} testID={`${testID}-limits`}>
          {SAFETY_NOTE}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  section: {
    alignItems: 'flex-start',
    gap: scale(24),
    paddingTop: scale(48),
    borderTopWidth: scale(1),
    borderTopColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  chapterHeading: { width: '100%' },
  content: { width: '100%' },
  heading: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.section,
    textAlign: 'left',
  },
  label: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.control,
    marginTop: scale(CALM_SPACE.TIGHT),
    textAlign: 'left',
  },
  line: {
    color: CALM_COLORS.TEXT_DIM,
    ...CALM_TEXT.supporting,
    marginTop: scale(CALM_SPACE.TIGHT),
    textAlign: 'left',
  },
  columns: { alignItems: 'flex-start', gap: scale(24) },
  summary: { width: '100%' },
  explanation: { width: '100%' },
  limits: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(32),
    paddingTop: scale(24),
    borderTopWidth: scale(1),
    borderTopColor: CALM_COLORS.SURFACE_FOCUSED,
    textAlign: 'left',
  },
});

export default ViewingPlan;
