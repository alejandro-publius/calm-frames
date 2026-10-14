import React from 'react';
import { CoastalAppearance } from './CoastalAppearance';
import { StyleSheet, Text, View } from 'react-native';
import HomeHarborScene from './HomeHarborScene';
import CalmPageHeader from './CalmPageHeader';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
/**
 * liveStatus is false only for the route's loading stand-in
 * (playerRouteFallback.tsx), so the status is announced once, by the player.
 */
export default function PlayerOpening({ title, onBack, returning = false, liveStatus = true }: { title: string; onBack: () => void; returning?: boolean; liveStatus?: boolean }) {
  return <CoastalAppearance.Provider value><View testID="player-home-opening" style={styles.screen}>
    <HomeHarborScene />
    <CalmPageHeader onBack={!returning ? onBack : undefined} backLabel="Back" backTestID="player-opening-back" preferredBack />
    <View style={styles.copy}>
      <Text style={styles.eyebrow}>A calmer way to watch</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.detail} accessibilityLiveRegion={liveStatus ? 'polite' : 'none'}>{returning ? 'Going back...' : 'Opening your story...'}</Text>

    </View>
  </View></CoastalAppearance.Provider>;
}
const styles = StyleSheet.create({
  screen: { ...StyleSheet.absoluteFillObject, zIndex: 30, backgroundColor: CALM_COLORS.BACKGROUND, paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y) },
  brand: { flexDirection: 'row', gap: scale(20), alignItems: 'center', height: scale(80) },
  mark: { width: scale(80), height: scale(80) }, wordmark: { ...CALM_TEXT.control, color: CALM_COLORS.TEXT },
  copy: { paddingTop: scale(104), width: scale(800) },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, marginBottom: scale(12) },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT, marginBottom: scale(12) },
  detail: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, minHeight: scale(84), marginBottom: scale(24) },
  actions: { flexDirection: 'row', gap: scale(20), alignItems: 'center' },
});
