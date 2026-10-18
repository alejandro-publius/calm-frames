/** How it works, in plain words, with the practice demo one press away. No household writes. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { COASTAL_COLORS as CALM_COLORS, CALM_TEXT, CALM_FLOW, scale } from './calmStyles';
import { CAPTIONS_CONTINUE_LINE, CHECKED_BEFORE_ADDED_LINE, DETECTION_LIMITS_LINE, ONLY_IN_CALM_FRAMES_LINE, PURPOSE_LINE, SAFETY_NOTE } from './copy';

export default function PictureHoldIntroduction({ onStart, onPlaybackCheck, onDemoDetails, disabled = false }: { onDemoDetails?: () => void; onPlaybackCheck?: () => void; onStart?: () => void; disabled?: boolean }) {
  return <View testID="picture-hold-introduction" style={styles.content}>
    <Text style={styles.title} accessibilityRole="header">How it works</Text>
    <Text style={styles.body}>{PURPOSE_LINE}</Text>
    <Text style={styles.body}>{`${CAPTIONS_CONTINUE_LINE} ${CHECKED_BEFORE_ADDED_LINE}`}</Text>
    <Text style={styles.body}>{ONLY_IN_CALM_FRAMES_LINE}</Text>
    {onStart || onDemoDetails ? <Text style={styles.detail}>The demo has two simulated picture pauses and no flashing.</Text> : null}
    <View style={styles.actions}>
      {onStart ? <CalmButton testID="picture-hold-start" primary label="Watch demo" sound={false} hasTVPreferredFocus disabled={disabled} onPress={onStart} /> : null}
      {onDemoDetails ? <CalmButton quiet testID="picture-hold-demo-details" label="About the demo" disabled={disabled} onPress={onDemoDetails} /> : null}
    </View>
    <Text style={styles.detail}>{`${DETECTION_LIMITS_LINE} ${SAFETY_NOTE}`}</Text>
    {onPlaybackCheck ? <View style={styles.tools}><CalmButton quiet compact testID="picture-hold-playback-check" label="Check playback" disabled={disabled} onPress={onPlaybackCheck} /></View> : null}
  </View>;
}
const styles = StyleSheet.create({
  tools: { marginTop: scale(12), alignItems: 'flex-start' },
  content: { maxWidth: scale(CALM_FLOW.READING_WIDTH), paddingTop: scale(40), paddingBottom: scale(32), gap: scale(20) },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT },
  body: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT },
  detail: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20), marginTop: scale(12) },
});
