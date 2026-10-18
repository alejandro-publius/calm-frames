/** Decorative fixed scenery. No playback media or unverified ambient loop is used. */
import LinearGradient from '@amazon-devices/react-linear-gradient';
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { COASTAL_COLORS as CALM_COLORS, scale } from './calmStyles';
import { trace } from './trace';

export function filmStill(variant?: string) {
  return variant === 'sea-otters' ? require('../../assets/image/tv/sea-otters-alaska.jpg')
    : variant === 'coastal' ? require('../../assets/image/tv/acadia-coast.png')
    : require('../../assets/image/tv/harbor-cinematic.png');
}

// Motion settings remain stored, but this scene stays still until a water-only
// loop has been prepared and verified on the native surface.
export default function HomeHarborScene({ immersive = false, wideReading = false, variant = 'harbor-cinematic' }: { enabled?: boolean; active?: boolean; immersive?: boolean; wideReading?: boolean; variant?: string }) {
  return <View testID="home-harbor-scene" style={styles.scene} pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Image source={filmStill(variant)} style={styles.art} resizeMode="cover" fadeDuration={0} onLoad={() => trace('image', `scene ${variant} loaded`)} onError={() => trace('image', 'scene error')} />
    <LinearGradient colors={[`${CALM_COLORS.BACKGROUND}E8`, `${CALM_COLORS.BACKGROUND}AE`, `${CALM_COLORS.BACKGROUND}00`]} locations={[0, wideReading || !immersive ? 0.65 : 0.30, 0.72]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={[`${CALM_COLORS.BACKGROUND}E8`, `${CALM_COLORS.BACKGROUND}E8`, `${CALM_COLORS.BACKGROUND}00`, `${CALM_COLORS.BACKGROUND}00`, `${CALM_COLORS.BACKGROUND}F2`]} locations={[0, 0.10, 0.22, 0.55, 1]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={StyleSheet.absoluteFill} />
  </View>;
}
const styles = StyleSheet.create({
  scene: { ...StyleSheet.absoluteFillObject, backgroundColor: CALM_COLORS.BACKGROUND, overflow: 'hidden' },
  art: { position: 'absolute', left: 0, top: 0, width: scale(1920), height: scale(1080) },
});
