/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Decorative selection marker. Focus and playback never wait for this motion. */
import React from 'react';
import { AccessibilityInfo, Animated, Easing } from 'react-native';
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import Svg, { Path, Ellipse } from '@amazon-devices/react-native-svg';
import { scale } from './calmStyles';
import { IslandKind } from './CoastalIsland';
import { boatBox, HOME_ISLANDS } from './homeIslands';
export default function CoastalBoat({ destination, enabled = false, active = true }: { destination: IslandKind; enabled?: boolean; active?: boolean }) {
  const manager = useKeplerAppStateManager();
  // In open water in front of the chosen island; homeIslands.ts keeps it clear of the cards and the sand.
  const target = React.useMemo(() => ({ x: scale(boatBox(destination).left), y: scale(boatBox(destination).top) }), [destination]);
  const latest = React.useRef(target); latest.current = target;
  const previous = React.useRef(destination);
  const position = React.useRef(new Animated.ValueXY(target)).current;
  const animation = React.useRef<Animated.CompositeAnimation | undefined>(undefined);
  const [motionAllowed, setMotionAllowed] = React.useState(false);
  React.useEffect(() => {
    let alive = true, generation = 0, listenersAvailable = true;
    let lifecycle: { remove(): void } | undefined, reduction: { remove(): void } | undefined, reader: { remove(): void } | undefined;
    const settle = () => {
      generation += 1; setMotionAllowed(false); animation.current?.stop(); position.setValue(latest.current);
    };
    const query = async () => {
      if (!listenersAvailable) return;
      const request = ++generation;
      try {
        const [reduced, spoken] = await Promise.all([AccessibilityInfo.isReduceMotionEnabled(), AccessibilityInfo.isScreenReaderEnabled()]);
        if (!alive || !listenersAvailable || request !== generation) return;
        if (reduced === false && spoken === false && manager.getCurrentState() === 'active') setMotionAllowed(true);
        else settle();
      } catch { if (alive && request === generation) settle(); }
    };
    settle();
    if (enabled && active) {
      try {
        lifecycle = manager.addAppStateListener('change', state => { settle(); if (state === 'active') void query(); });
        reduction = AccessibilityInfo.addEventListener('reduceMotionChanged', reduced => { if (reduced !== false) settle(); else void query(); });
        reader = AccessibilityInfo.addEventListener('screenReaderChanged', spoken => { if (spoken !== false) settle(); else void query(); });
        if (manager.getCurrentState() === 'active') void query();
      } catch {
        listenersAvailable = false; lifecycle?.remove(); reduction?.remove(); reader?.remove();
        lifecycle = undefined; reduction = undefined; reader = undefined; settle();
      }
    }
    return () => { alive = false; generation += 1; animation.current?.stop(); position.setValue(latest.current); lifecycle?.remove(); reduction?.remove(); reader?.remove(); };
  }, [enabled, active, manager, position]);
  React.useLayoutEffect(() => {
    const changed = previous.current !== destination; previous.current = destination;
    animation.current?.stop();
    if (changed && enabled && active && motionAllowed) {
      animation.current = Animated.timing(position, { toValue: target, duration: 560, easing: Easing.inOut(Easing.cubic), useNativeDriver: true, isInteraction: false });
      animation.current.start();
    } else position.setValue(target);
  }, [destination, enabled, active, motionAllowed, position, target]);
  return <Animated.View testID={`coastal-boat-${destination}`} pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
    style={{ position: 'absolute', left: 0, top: 0, width: scale(HOME_ISLANDS.BOAT.width), height: scale(HOME_ISLANDS.BOAT.height), transform: position.getTranslateTransform() }}>
    <Svg width="100%" height="100%" viewBox="0 0 72 62">
      <Ellipse cx="36" cy="51" rx="34" ry="8" fill="#386F70" />
      <Path d="M5 35H67L55 51H19Z" fill="#BB5944" stroke="#193F3E" strokeWidth="4" strokeLinejoin="round" />
      <Path d="M34 5V36M31 8L10 30H31Z" fill="#FFF8E7" stroke="#193F3E" strokeWidth="4" strokeLinejoin="round" />
      <Path d="M40 11L58 30H40Z" fill="#FFE1A9" stroke="#193F3E" strokeWidth="4" strokeLinejoin="round" />
    </Svg>
  </Animated.View>;
}
