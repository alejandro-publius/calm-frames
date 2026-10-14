/** Optional context before the real bundled practice film. No household writes. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { COASTAL_COLORS as CALM_COLORS, CALM_TEXT, scale } from './calmStyles';

export default function PictureHoldIntroduction({ onStart, onPlaybackCheck, onDemoDetails, disabled = false }: { onDemoDetails?: () => void; onPlaybackCheck?: () => void; onStart?: () => void; disabled?: boolean }) {
  return <View testID="picture-hold-introduction" style={styles.content}>
    <Text style={styles.eyebrow}>How it works</Text>
    <Text style={styles.title} accessibilityRole="header">Picture holds. The story keeps going.</Text>
    <Text style={styles.body}>Marked sections use a still picture. Sound continues, with optional captions.</Text>
    <Text style={styles.detail}>Try a 20-second Harbor demo with two scheduled practice holds. Skip moves past a hold; Back leaves the demo.</Text>
    <View style={styles.actions}>
      {onStart ? <CalmButton testID="picture-hold-start" primary label="Try the demo" sound={false} hasTVPreferredFocus disabled={disabled} onPress={onStart} /> : null}
      {onDemoDetails ? <CalmButton quiet testID="picture-hold-demo-details" label="About the demo" disabled={disabled} onPress={onDemoDetails} /> : null}
    </View>
    {onPlaybackCheck ? <View style={styles.tools}><Text style={styles.detail}>Need to check your screen?</Text><CalmButton quiet compact testID="picture-hold-playback-check" label="Playback check" disabled={disabled} onPress={onPlaybackCheck} /></View> : null}
  </View>;
}
const styles = StyleSheet.create({
  tools: { marginTop: scale(12), gap: scale(8), alignItems: 'flex-start' },
  content: { maxWidth: scale(920), paddingTop: scale(40), gap: scale(24) },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT },
  body: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT },
  detail: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20), marginTop: scale(12) },
});
