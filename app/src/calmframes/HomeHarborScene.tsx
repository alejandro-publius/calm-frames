/** Decorative home scenery only. Playback and signed hold images never use it. */
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import LinearGradient from '@amazon-devices/react-linear-gradient';
import React from 'react';
import { AccessibilityInfo, Animated, Easing, Image, StyleSheet, View } from 'react-native';
import { COASTAL_COLORS as CALM_COLORS, scale } from './calmStyles';
import { trace } from './trace';

export default function HomeHarborScene({ enabled = false, active = true, immersive = false }: { enabled?: boolean; active?: boolean; immersive?: boolean }) {
  const manager = useKeplerAppStateManager();
  const drift = React.useRef(new Animated.Value(0)).current;
  React.useEffect(() => {
    let alive = true;
    let generation = 0;
    let animation: Animated.CompositeAnimation | undefined;
    const stop = () => { generation += 1; animation?.stop(); animation = undefined; drift.setValue(0); };
    const start = async () => {
      stop();
      const request = generation;
      if (!enabled || !active) return;
      try {
        if (manager.getCurrentState() !== 'active') return;
        const [reduced, spoken] = await Promise.all([
          AccessibilityInfo.isReduceMotionEnabled(), AccessibilityInfo.isScreenReaderEnabled(),
        ]);
        if (!alive || request !== generation || reduced !== false || spoken !== false) return;
        // Begin and end at rest so loop reset cannot jump a ripple.
        animation = Animated.loop(Animated.sequence([4, 0, -4, 0].map((offset) =>
          Animated.timing(drift, { toValue: scale(offset), duration: 4000,
            easing: Easing.inOut(Easing.sin), useNativeDriver: true, isInteraction: false }),
        )));
        animation.start();
      } catch { if (alive && request === generation) stop(); }
    };
    let lifecycle: { remove(): void } | undefined;
    let reduction: { remove(): void } | undefined;
    let reader: { remove(): void } | undefined;
    try {
      lifecycle = manager.addAppStateListener('change', (state) => { if (state === 'active') start(); else stop(); });
      reduction = AccessibilityInfo.addEventListener('reduceMotionChanged', (value) => { if (value !== false) stop(); else start(); });
      reader = AccessibilityInfo.addEventListener('screenReaderChanged', (value) => { if (value !== false) stop(); else start(); });
      start();
    } catch { stop(); }
    return () => { alive = false; stop(); lifecycle?.remove(); reduction?.remove(); reader?.remove(); };
  }, [active, enabled, drift, manager]);
  return <View testID="home-harbor-scene" style={styles.scene} pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Image source={require('../../assets/image/tv/coastal-zen.png')} style={[styles.art, immersive ? styles.immersiveArt : null]} resizeMode="cover" fadeDuration={0} onLoad={() => trace('image', 'scene loaded')} onError={() => trace('image', 'scene error')} />
    <Animated.View testID="home-water-ripples" style={[styles.ripples, { transform: [{ translateX: drift }, { translateY: drift.interpolate({ inputRange: [scale(-4), scale(4)], outputRange: [scale(-1), scale(1)] }) }] }]}>
      <View style={[styles.ripple, styles.first]} /><View style={[styles.ripple, styles.second]} /><View style={[styles.ripple, styles.third]} />
    </Animated.View>
    {immersive ? <LinearGradient colors={[CALM_COLORS.BACKGROUND, CALM_COLORS.BACKGROUND, `${CALM_COLORS.BACKGROUND}00`]} locations={[0, 0.76, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.readingEdge} /> : null}
    {!immersive ? <LinearGradient colors={[`${CALM_COLORS.BACKGROUND}F5`, `${CALM_COLORS.BACKGROUND}EB`, `${CALM_COLORS.BACKGROUND}75`]} locations={[0, 0.55, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} /> : null}
  </View>;
}
const styles = StyleSheet.create({
  scene: { ...StyleSheet.absoluteFillObject, backgroundColor: CALM_COLORS.BACKGROUND, overflow: 'hidden' },
  readingEdge: { position: 'absolute', left: 0, top: scale(770), width: scale(820), height: scale(310) },
  immersiveArt: { opacity: 1 },
  art: { position: 'absolute', left: 0, top: 0, width: scale(1920), height: scale(1080) },
  ripples: { position: 'absolute', top: scale(690), left: scale(1050), width: scale(720), height: scale(120) },
  ripple: { position: 'absolute', height: scale(2), borderRadius: scale(2), backgroundColor: '#77A19E', opacity: 0.22 },
  first: { top: 0, left: scale(80), width: scale(130) },
  second: { top: scale(42), left: scale(330), width: scale(170) },
  third: { top: scale(95), left: scale(190), width: scale(110) },
});
