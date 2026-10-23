/** How it works, in plain words, with the practice demo one press away. No household writes. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { COASTAL_COLORS as CALM_COLORS, CALM_TEXT, CALM_FLOW, scale } from './calmStyles';
import { DETECTION_LIMITS_LINE, ONLY_IN_CALM_FRAMES_LINE, SAFETY_NOTE } from './copy';

export default function PictureHoldIntroduction({ onStart, onPlaybackCheck, onDemoDetails, onBridgeTest, preferBridgeTest = false, disabled = false }: { onBridgeTest?: () => void; preferBridgeTest?: boolean; onDemoDetails?: () => void; onPlaybackCheck?: () => void; onStart?: () => void; disabled?: boolean }) {
  return <View testID="picture-hold-introduction" style={styles.content}>
    <Text style={styles.title} accessibilityRole="header">How it works</Text>
    <Text testID="how-it-works-purpose" style={styles.body}>Calm Frames hides flagged flashing scenes in prepared videos.</Text>
    <Text style={styles.body}>Each one gets a plain cover or a still image from the same video. Original sound continues when present.</Text>
    <Text style={styles.body}>Choose a video, then press Watch. Press Back to return.</Text>
    <View testID="how-it-works-limits" style={styles.limits}>
      <Text style={styles.detail}>{ONLY_IN_CALM_FRAMES_LINE}</Text>
      {/* The approved sentence and its limit, word for word as More info says them. */}
      <Text style={styles.detail}>{`${DETECTION_LIMITS_LINE} ${SAFETY_NOTE}`}</Text>
    </View>
    {onStart || onDemoDetails ? <Text style={styles.detail}>The demo has two simulated picture pauses and no flashing.</Text> : null}
    <View style={styles.actions}>
      {onStart ? <CalmButton testID="picture-hold-start" primary label="Watch demo" sound={false} hasTVPreferredFocus={!preferBridgeTest} disabled={disabled} onPress={onStart} /> : null}
      {onDemoDetails ? <CalmButton quiet testID="picture-hold-demo-details" label="About the demo" disabled={disabled} onPress={onDemoDetails} /> : null}
    </View>
    {onPlaybackCheck || onBridgeTest ? <View style={styles.tools}>{typeof __DEV__ !== 'undefined' && __DEV__ && onBridgeTest ? <CalmButton quiet compact testID="picture-hold-bridge-test" sound={false} label="Scene bridge test" disabled={disabled} hasTVPreferredFocus={preferBridgeTest} onPress={onBridgeTest} /> : null}{onPlaybackCheck ? <CalmButton quiet compact testID="picture-hold-playback-check" label="Check playback" disabled={disabled} onPress={onPlaybackCheck} /> : null}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  tools: { marginTop: scale(12), alignItems: 'flex-start', flexDirection: 'row', gap: scale(20) },
  content: { maxWidth: scale(CALM_FLOW.READING_WIDTH), paddingTop: scale(40), paddingBottom: scale(32), gap: scale(20) },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT },
  body: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT },
  detail: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT },
  limits: { gap: scale(12), marginTop: scale(4) },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20), marginTop: scale(12) },
});
