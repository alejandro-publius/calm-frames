import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import HomeHarborScene from './HomeHarborScene';
import CalmButton from './CalmButton';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
export default function PlayerOpening({ title, onBack, returning = false }: { title: string; onBack: () => void; returning?: boolean }) {
  return <View testID="player-home-opening" style={styles.screen}>
    <HomeHarborScene />
    <View style={styles.brand}><Image source={require('../../assets/image/CalmFrames.png')} style={styles.mark} fadeDuration={0} accessible={false} /><Text style={styles.wordmark}>Calm Frames</Text></View>
    <View style={styles.copy}>
      <Text style={styles.eyebrow}>A calmer way to watch</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.detail} accessibilityLiveRegion="polite">{returning ? 'Returning to your library.' : 'Opening your checked title...'}</Text>
      <View style={styles.actions}>
        <CalmButton primary disabled label={returning ? 'Returning...' : 'Opening...'} />
        {!returning ? <CalmButton quiet testID="player-opening-back" label="Back to library" hasTVPreferredFocus onPress={onBack} /> : null}
      </View>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  screen: { ...StyleSheet.absoluteFillObject, zIndex: 30, backgroundColor: CALM_COLORS.BACKGROUND, paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y) },
  brand: { flexDirection: 'row', gap: scale(20), alignItems: 'center', height: scale(80) },
  mark: { width: scale(80), height: scale(80) }, wordmark: { ...CALM_TEXT.control, color: CALM_COLORS.TEXT },
  copy: { paddingTop: scale(80), width: scale(800) },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.FOCUS_RING, marginBottom: scale(12) },
  title: { ...CALM_TEXT.feature, color: CALM_COLORS.TEXT, marginBottom: scale(12) },
  detail: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, minHeight: scale(84), marginBottom: scale(24) },
  actions: { flexDirection: 'row', gap: scale(20), alignItems: 'center' },
});
