/** How it works, in plain words, with the practice demo one press away. No household writes. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { COASTAL_COLORS as CALM_COLORS, CALM_TEXT, scale } from './calmStyles';
import { SAFETY_NOTE } from './copy';

export default function PictureHoldIntroduction({ onStart, onPlaybackCheck, onDemoDetails, disabled = false }: { onDemoDetails?: () => void; onPlaybackCheck?: () => void; onStart?: () => void; disabled?: boolean }) {
  return <View testID="picture-hold-introduction" style={styles.content}>
    <Text style={styles.title} accessibilityRole="header">How it works</Text>
    <Text style={styles.body}>Calm Frames is for families with photosensitive epilepsy. Every video is checked for flashing, frame by frame, before it can play.</Text>
    <Text style={styles.body}>When flashing is found, the picture holds on a calm still while the sound and captions continue. A card says when a hold is coming, and Skip jumps past it.</Text>
    <Text style={styles.detail}>The practice version of Harbor has two scheduled practice holds, so you can see one.</Text>
    <View style={styles.actions}>
      {onStart ? <CalmButton testID="picture-hold-start" primary label="Play the demo" sound={false} hasTVPreferredFocus disabled={disabled} onPress={onStart} /> : null}
      {onDemoDetails ? <CalmButton quiet testID="picture-hold-demo-details" label="About the demo" disabled={disabled} onPress={onDemoDetails} /> : null}
    </View>
    <Text style={styles.detail}>{`Detection can miss flashing. ${SAFETY_NOTE}`}</Text>
    {onPlaybackCheck ? <View style={styles.tools}><CalmButton quiet compact testID="picture-hold-playback-check" label="Check playback" disabled={disabled} onPress={onPlaybackCheck} /></View> : null}
  </View>;
}
const styles = StyleSheet.create({
  tools: { marginTop: scale(12), alignItems: 'flex-start' },
  content: { maxWidth: scale(920), paddingTop: scale(40), gap: scale(24) },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT },
  body: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT },
  detail: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20), marginTop: scale(12) },
});
