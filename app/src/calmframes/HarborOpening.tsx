/** A quiet sea at launch, followed by a single cut into the library. */
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import LinearGradient from '@amazon-devices/react-linear-gradient';
import React from 'react';
import { AccessibilityInfo, Animated, BackHandler, Easing, Image, StyleSheet, Text, View } from 'react-native';
import CalmPageHeader from './CalmPageHeader';
import HomeHarborScene from './HomeHarborScene';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { useUiCapture } from './uiCapture';
import { HARBOR_BOOTSTRAP_FRAME } from './uiFrames';

export const HARBOR_OPENING_MS = 1400;
export const HARBOR_WATER_DRIFT = { x: 16, y: -6 } as const;

export default function HarborOpening({
  motionEnabled = false,
  active = true,
  onFinish,
  testID = 'harbor-opening',
}: {
  motionEnabled?: boolean;
  active?: boolean;
  /** Omitted while real startup work is pending. No pretend progress or timer. */
  onFinish?: () => void;
  testID?: string;
}) {
  useUiCapture(onFinish ? { ...HARBOR_BOOTSTRAP_FRAME, surfaces: [] } : HARBOR_BOOTSTRAP_FRAME, 'harbor startup');
  const manager = useKeplerAppStateManager();
  const progress = React.useRef(new Animated.Value(0)).current;
  const finish = React.useRef(onFinish);
  finish.current = onFinish;
  const canFinish = Boolean(onFinish);

  React.useEffect(() => {
    // Household preferences are not available during storage/bootstrap loading.
    if (!canFinish) return;
    let alive = true;
    let done = false;
    let animation: Animated.CompositeAnimation | undefined;
    let lifecycle: { remove(): void } | undefined;
    let reduction: { remove(): void } | undefined;
    let screenReader: { remove(): void } | undefined;
    let back: { remove(): void } | undefined;
    const complete = () => {
      if (!alive || done) return;
      done = true;
      animation?.stop();
      finish.current?.();
    };
    // A missing system reply or animation callback must never strand a family.
    const timeout = setTimeout(complete, HARBOR_OPENING_MS + 600);
    const enter = async () => {
      if (!motionEnabled || !active) { complete(); return; }
      try {
        if (manager.getCurrentState() !== 'active') { complete(); return; }
        lifecycle = manager.addAppStateListener('change', (state) => {
          if (state !== 'active') complete();
        });
        reduction = AccessibilityInfo.addEventListener('reduceMotionChanged', (reduced) => {
          if (reduced !== false) complete();
        });
        screenReader = AccessibilityInfo.addEventListener('screenReaderChanged', (enabled) => {
          if (enabled !== false) complete();
        });
        back = BackHandler.addEventListener('hardwareBackPress', () => { complete(); return true; });
        const [reduced, spoken] = await Promise.all([
          AccessibilityInfo.isReduceMotionEnabled(),
          AccessibilityInfo.isScreenReaderEnabled(),
        ]);
        if (!alive || done) return;
        if (reduced !== false || spoken !== false) { complete(); return; }
        animation = Animated.timing(progress, {
          toValue: 1,
          duration: HARBOR_OPENING_MS,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
          isInteraction: false,
        });
        animation.start(complete);
      } catch {
        complete();
      }
    };
    void enter();
    return () => {
      alive = false;
      clearTimeout(timeout);
      animation?.stop();
      lifecycle?.remove();
      reduction?.remove();
      screenReader?.remove();
      back?.remove();
    };
  }, [active, canFinish, manager, motionEnabled, progress]);

  // Actual bootstrap callers have no onFinish: match the next loading/home
  // frame without introducing a timer or reading household preferences.
  if (!canFinish) return <View testID={testID} style={styles.screen} accessible accessibilityLabel="Calm Frames. Opening your library." accessibilityRole="progressbar">
    <HomeHarborScene />
    <CalmPageHeader />
    <View style={styles.loading}><Text style={styles.loadingTitle}>Opening Calm Frames</Text></View>
  </View>;

  return (
    <View testID={testID} style={styles.screen} accessible accessibilityLabel="Calm Frames. Opening your library." accessibilityRole="progressbar">
      <View style={styles.sea} pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <Animated.View testID={`${testID}-water`} style={[styles.wave, { transform: [
          { translateX: progress.interpolate({ inputRange: [0, 1], outputRange: [0, scale(HARBOR_WATER_DRIFT.x)] }) },
          { translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [0, scale(HARBOR_WATER_DRIFT.y)] }) },
        ] }]}>
          <Image source={require('../../assets/image/tv/harbor-water.png')} style={styles.image} resizeMode="cover" fadeDuration={0} />
        </Animated.View>
        <LinearGradient colors={[`${CALM_COLORS.BACKGROUND}00`, CALM_COLORS.BACKGROUND]} locations={[0, 0.85]}
          start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.shore} />
      </View>
      <View style={styles.copy}>
        <Image source={require('../../assets/image/CalmFrames.png')} style={styles.mark} fadeDuration={0} accessible={false} />
        <Text style={styles.title}>Calm Frames</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  loading: { paddingTop: scale(102), maxWidth: scale(750) },
  loadingTitle: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT },
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND, overflow: 'hidden', paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y) },
  sea: { ...StyleSheet.absoluteFillObject },
  wave: { position: 'absolute', top: scale(-20), bottom: scale(-20), left: scale(-24), right: scale(-24) },
  image: { width: '100%', height: '100%' },
  shore: { position: 'absolute', bottom: 0, left: 0, right: 0, height: scale(400) },
  copy: { position: 'absolute', bottom: scale(60), left: scale(CALM_SPACE.SAFE_X), right: scale(CALM_SPACE.SAFE_X), flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: scale(20) },
  mark: { width: scale(64), height: scale(64) },
  title: { ...CALM_TEXT.card, color: CALM_COLORS.TEXT },
});
