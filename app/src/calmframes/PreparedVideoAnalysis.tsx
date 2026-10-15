/** Read-only explanation of the verified selection, never an authorization to play. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CALM_FLOW, CALM_SPACE, CALM_TEXT, COASTAL_COLORS as COLORS, scale } from './calmStyles';
import { HouseholdSettings, PRESETS } from './household';
import { CheckedTitle } from './titleStatus';
import { packagedLibrary } from './packagedLibrary';
import { isBundledBenignStory } from './benignStory';
import { buildCoverIntervals, totalCoveredMs } from './coverSchedule';
import { coverOptionsFor } from './household';

export default function PreparedVideoAnalysis({ entry, settings, compact = false, testID = 'prepared-analysis' }: {
  entry: CheckedTitle; settings: HouseholdSettings; compact?: boolean; testID?: string;
}) {
  if (entry.status !== 'verified') return null;
  const demo = isBundledBenignStory(entry.title);
  if (demo) return compact ? <View style={styles.panel} testID={testID}>
    <Text style={styles.heading} accessibilityRole="header">Simulated picture pauses</Text>
    <Text style={styles.line}>These events were added for the demo. They are not detected flashing.</Text>
  </View> : null;
  const evidence = packagedLibrary.evidenceFor(entry.title, settings);
  if (!evidence || !PRESETS[settings.preset].mapProfiles.every(profile => entry.verifiedProfiles.includes(profile))) return null;
  const intervals = buildCoverIntervals(entry.segments, { ...coverOptionsFor(settings), durationMs: entry.title.durationMs });
  const seconds = Math.round(totalCoveredMs(intervals) / 1000);
  if (compact) return <View style={styles.panel} testID={testID}>
    <Text style={styles.heading} accessibilityRole="header">{entry.segments.length === 0 ? 'No scenes flagged' : `${entry.segments.length} flagged section${entry.segments.length === 1 ? '' : 's'}`}</Text>
    <Text style={styles.line}>{`Analyzed before playback · ${PRESETS[settings.preset].title}`}</Text>
    <Text style={styles.line}>{intervals.length === 0 ? 'This prepared video has no scheduled hidden scenes.' : `${intervals.length} scene${intervals.length === 1 ? '' : 's'} hidden for ${seconds} seconds in total, including added margins.`}</Text>
  </View>;
  return <View style={styles.record} testID={testID}>
    <Text style={styles.heading} accessibilityRole="header">Analysis record</Text>
    <Text style={styles.line}>The source was analyzed before this video was prepared. Playback uses the signed timing map for your settings.</Text>
    <Text style={styles.line}>The prepared video was checked again with the same analyzer. This is not an independent safety assessment.</Text>
    <Text style={styles.line}>Detection can miss flashing. The player does not analyze live video.</Text>
    <View style={styles.panel}>
      <Text style={styles.label}>File record</Text>
      <Text style={styles.line} testID={`${testID}-source`}>{`Source: ${evidence.sourceSha256.slice(0, 12)}`}</Text>
      <Text style={styles.line} testID={`${testID}-rendition`}>{`Playing: ${evidence.renditionSha256.slice(0, 12)}`}</Text>
      <Text style={styles.line} testID={`${testID}-report`}>{`Preparation report: ${evidence.reportSha256.slice(0, 12)}`}</Text>
      <Text style={styles.line}>{`Result: ${evidence.outcome}`}</Text>
      <Text style={styles.line}>These are short file identifiers. The build receipt contains their full hashes.</Text>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  panel: { width: '100%', maxWidth: scale(CALM_FLOW.READING_WIDTH), backgroundColor: COLORS.BACKGROUND, borderRadius: scale(18), padding: scale(CALM_SPACE.BLOCK), gap: scale(CALM_SPACE.TIGHT), marginTop: scale(CALM_SPACE.BLOCK) },
  record: { width: '100%', maxWidth: scale(CALM_FLOW.READING_WIDTH), gap: scale(CALM_SPACE.ROW), marginTop: scale(CALM_SPACE.BLOCK) },
  heading: { ...CALM_TEXT.section, color: COLORS.TEXT },
  label: { ...CALM_TEXT.control, color: COLORS.TEXT },
  line: { ...CALM_TEXT.supporting, color: COLORS.TEXT_DIM },
});
