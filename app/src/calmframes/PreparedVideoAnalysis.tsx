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
  const findings = buildCoverIntervals(entry.segments, { guardBandMs: 0, minCoverMs: 0, durationMs: entry.title.durationMs });
  const period = (span: { startMs: number; endMs: number }) => `${(span.startMs / 1000).toFixed(1)} to ${(span.endMs / 1000).toFixed(1)} sec`;
  const seconds = Math.round(totalCoveredMs(intervals) / 1000);
  if (compact) return <View style={styles.panel} testID={testID}>
    <Text style={styles.heading} accessibilityRole="header">{findings.length === 0 ? 'No scenes flagged' : `${findings.length} flagged period${findings.length === 1 ? '' : 's'}`}</Text>
    <Text style={styles.line}>{`Analyzed before playback · ${PRESETS[settings.preset].title}`}</Text>
    <Text style={styles.line}>{intervals.length === 0 ? 'This prepared video has no scheduled hidden scenes.' : `${intervals.length} scene${intervals.length === 1 ? '' : 's'} hidden for ${seconds} seconds in total, including added margins.`}</Text>
  </View>;
  return <View style={styles.record} testID={testID}>
    <Text style={styles.heading} accessibilityRole="header">Analysis record</Text>
    <Text style={styles.line}>The source was analyzed before this video was prepared. Playback uses the signed timing map for your settings.</Text>
    <Text style={styles.line}>The prepared video was checked again with the same analyzer. This is not an independent safety assessment.</Text>
    <Text style={styles.line}>Detection can miss flashing. The player does not analyze live video.</Text>
    {findings.length > 0 ? <View style={styles.panel}>
      <Text style={styles.label}>Detected in the source</Text>
      {findings.map(span => <Text key={span.startMs} style={styles.line}>{period(span)}</Text>)}
      <Text style={styles.line}>Overlapping findings are counted once. These are measured findings, not demo events.</Text>
      <Text style={styles.label}>Covered in this version</Text>
      {intervals.map(span => <Text key={span.startMs} style={styles.line}>{period(span)}</Text>)}
    </View> : null}
    {PRESETS[settings.preset].mapProfiles.map(profile => {
      // These exact map texts belong to the compiled identity above and were
      // verified by checkTitle. The presentation summary is never consulted.
      const map = JSON.parse(entry.title.maps![profile]!);
      const rule = map.profile.general_flash;
      const windows = map.profile.area_windows.map((window: { name: string; width_px: number; height_px: number }) => `${window.name}: ${window.width_px} × ${window.height_px}`).join('; ');
      return <View key={profile} style={styles.panel}>
        <Text style={styles.label}>{profile === 'wcag' ? 'WCAG analysis' : 'Broadcast analysis'}</Text>
        <Text style={styles.line}>{`Working picture: ${map.color.analysis_width} × ${map.color.analysis_height} pixels. Area windows: ${windows}.`}</Text>
        <Text style={styles.line}>{rule.metric === 'bt1886-nits'
          ? `General flash rule: ${rule.min_delta} nits change, dark image below ${rule.dark_image_below} nits, assumed peak ${map.profile.peak_nits} nits (BT.1886).`
          : `General flash rule: relative luminance change ${rule.min_delta}, dark image below ${rule.dark_image_below}.`}</Text>
        {map.profile.room ? <Text style={styles.line}>{`Preparation room: ${map.profile.room.tv_diagonal_in}-inch screen at ${map.profile.room.seat_distance_in / 12} feet.`}</Text> : null}
        <Text style={styles.line}>{map.profile.pattern_rule ? 'Includes the informative broadcast pattern rule. This is separate from WCAG.' : 'This profile does not assess regular patterns.'}</Text>
        <Text style={styles.line}>HDR is unsupported. Fine balanced pattern exceptions are not implemented.</Text>
      </View>;
    })}
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
