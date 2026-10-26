/** A quiet, read-only path from measured source to the selected prepared edition. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CALM_FLOW, CALM_SPACE, CALM_TEXT, COASTAL_COLORS as COLORS, scale } from './calmStyles';
import { CheckedTitle } from './titleStatus';
import { HouseholdSettings, PRESETS, coverOptionsFor } from './household';
import { buildCoverIntervals, totalCoveredMs } from './coverSchedule';
import { playbackProofFor } from './playbackProof';
import CalmButton from './CalmButton';

export default function PlaybackProofPanel({ entry, settings, testID = 'playback-proof' }: {
  entry: CheckedTitle; settings: HouseholdSettings; testID?: string;
}) {
  const [stage, setStage] = React.useState<'source' | 'prepared' | 'binding'>('source');
  const proof = playbackProofFor(entry, settings);
  if (!proof) return <View testID={`${testID}-unavailable`} style={styles.stage}>
    <Text accessibilityRole="header" style={styles.heading}>Playback proof unavailable</Text>
    <Text style={styles.line}>No matching report summary is available for this selection. This page cannot confirm its measurements.</Text>
  </View>;
  const findings = buildCoverIntervals(entry.segments, { guardBandMs: 0, minCoverMs: 0, durationMs: proof.durationMs });
  const covered = buildCoverIntervals(entry.segments, { ...coverOptionsFor(settings), durationMs: proof.durationMs });
  const profileLabel = (name: string) => name === 'wcag' ? 'WCAG' : name === 'broadcast' ? 'Broadcast' : 'Extra cautious';
  return <View testID={testID} style={styles.record}>
    <Text accessibilityRole="header" style={styles.heading}>Playback proof</Text>
    <Text style={styles.line}>{`${PRESETS[settings.preset].title} · ${(proof.durationMs / 1000).toFixed(1)} seconds · selected video edition`}</Text>
    <View style={styles.steps}>
      {(['source', 'prepared', 'binding'] as const).map((step, index) => <CalmButton key={step} quiet
        testID={`${testID}-step-${step}`} label={`${index + 1} · ${step === 'binding' ? 'Selection' : step === 'source' ? 'Source' : 'Prepared'}`}
        accessibilityLabel={`${step === 'binding' ? 'Selection' : step === 'source' ? 'Source' : 'Prepared'} evidence${stage === step ? ', selected' : ''}`}
        onPress={() => setStage(step)} />)}
    </View>
    {stage === 'source' ? <View style={styles.stage} testID={`${testID}-source`}>
      <Text style={styles.label}>1 · Source measured</Text>
      <Text style={styles.metric}>{`${findings.length} flagged period${findings.length === 1 ? '' : 's'}`}</Text>
      <Text style={styles.line}>Overlapping source findings are counted once. The original video is not played here.</Text>
      {proof.source.map(item => <Text key={item.profile} style={styles.line}>{`${profileLabel(item.profile)} map: ${item.findings} findings · ${item.analyzer ?? 'analyzer version not recorded'}`}</Text>)}
    </View> : stage === 'prepared' ? <View style={styles.stage} testID={`${testID}-prepared`}>
      <Text style={styles.label}>2 · Prepared file checked</Text>
      {proof.output.map(item => <Text key={item.profile} style={styles.metric}>{`${profileLabel(item.profile)}: ${item.findings === null ? 'finding count not recorded' : `${item.findings} output findings`}`}</Text>)}
      <Text style={styles.line}>{`${covered.length} covered period${covered.length === 1 ? '' : 's'} · ${(totalCoveredMs(covered) / 1000).toFixed(1)} seconds including margins`}</Text>
      <Text style={styles.line}>{proof.outcome === 'no flagged segments'
        ? 'Nothing was flagged, so this result does not demonstrate a cover working.'
        : proof.outcome === 'cover proven drawn' ? 'The report verifies that the replacement picture was drawn.' : 'The report does not prove that the cover was drawn.'}</Text>
      <Text style={styles.line}>{proof.timingPreserved && proof.frameCount !== null
        ? `${proof.frameCount} frames · frame timing checked against the source`
        : 'Complete frame-timing measurements are not recorded in this summary.'}</Text>
      {proof.output.map(item => <Text key={item.profile} style={styles.line}>{`${profileLabel(item.profile)} output analyzer: ${item.analyzer ?? 'version not recorded in this report'}`}</Text>)}
    </View> : <View style={styles.stage} testID={`${testID}-binding`}>
      <Text style={styles.label}>3 · Selection matches</Text>
      <Text style={styles.line}>The selected edition and signed timing maps match the approved file record. Media bytes are checked when the app is built; this page does not rescan the video.</Text>
      <Text style={styles.identifier}>{`Prepared file ${proof.renditionSha256.slice(0, 12)} · report ${proof.reportSha256.slice(0, 12)}`}</Text>
    </View>}
    <Text style={styles.line}>These checks do not establish personal comfort or medical safety. Detection can miss flashing. The full record below explains the limits.</Text>
  </View>;
}
const styles = StyleSheet.create({
  record: { width: '100%', maxWidth: scale(CALM_FLOW.READING_WIDTH), gap: scale(CALM_SPACE.ROW) },
  steps: { flexDirection: 'row', flexWrap: 'wrap', gap: scale(CALM_SPACE.TIGHT) },
  stage: { width: '100%', padding: scale(CALM_SPACE.BLOCK), gap: scale(CALM_SPACE.TIGHT), borderRadius: scale(18),
    backgroundColor: COLORS.BACKGROUND, borderWidth: scale(2), borderColor: COLORS.TEXT_DIM },
  heading: { ...CALM_TEXT.section, color: COLORS.TEXT },
  label: { ...CALM_TEXT.control, color: COLORS.TEXT },
  metric: { ...CALM_TEXT.section, color: COLORS.TEXT },
  line: { ...CALM_TEXT.supporting, color: COLORS.TEXT_DIM },
  identifier: { ...CALM_TEXT.supporting, color: COLORS.TEXT_DIM },
});
