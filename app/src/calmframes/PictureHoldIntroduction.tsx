/** How it works, in plain words, with the practice demo one press away. No household writes. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { COASTAL_COLORS as CALM_COLORS, CALM_TEXT, CALM_FLOW, scale } from './calmStyles';
import { SAFETY_NOTE } from './copy';

export default function PictureHoldIntroduction({ onStart, onPlaybackCheck, onDemoDetails, disabled = false }: { onDemoDetails?: () => void; onPlaybackCheck?: () => void; onStart?: () => void; disabled?: boolean }) {
  return <View testID="picture-hold-introduction" style={styles.content}>
    <Text style={styles.title} accessibilityRole="header">How it works</Text>
    <Text style={styles.body}>Calm Frames replaces flashing scenes with a still picture. Sound and captions continue.</Text>
    <Text style={styles.body}>Videos are checked before they are added. This only works with videos in Calm Frames, not other apps or live TV.</Text>
    <Text style={styles.detail}>The demo has two simulated picture pauses and no flashing.</Text>
    <View style={styles.actions}>
      {onStart ? <CalmButton testID="picture-hold-start" primary label="Watch demo" sound={false} hasTVPreferredFocus disabled={disabled} onPress={onStart} /> : null}
      {onDemoDetails ? <CalmButton quiet testID="picture-hold-demo-details" label="About the demo" disabled={disabled} onPress={onDemoDetails} /> : null}
    </View>
    <Text style={styles.detail}>{`Detection can miss flashing. ${SAFETY_NOTE}`}</Text>
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
