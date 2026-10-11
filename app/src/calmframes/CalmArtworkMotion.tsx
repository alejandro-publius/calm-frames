/** Optional page-entry movement for decorative art, outside text and controls. */
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import React from 'react';
import { AccessibilityInfo, Animated, Easing, View } from 'react-native';
import { scale } from './calmStyles';

export interface CalmArtworkMotionProps {
  children: React.ReactNode;
  enabled?: boolean;
  active?: boolean;
  testID?: string;
}

export default function CalmArtworkMotion({
  children,
  enabled = false,
  active = true,
  testID = 'calm-artwork-motion',
}: CalmArtworkMotionProps) {
  const manager = useKeplerAppStateManager();
  const translation = React.useRef(new Animated.Value(0)).current;
  // Turning this on later never replays an entrance on an existing page.
  const consumed = React.useRef(!enabled || !active);
  const animatedOnEntry = React.useRef(enabled && active).current;

  React.useLayoutEffect(() => {
    let alive = true;
    let generation = 0;
    let foreground = false;
    let animation: Animated.CompositeAnimation | undefined;
    let lifecycle: { remove(): void } | undefined;
    let reduction: { remove(): void } | undefined;

    const settle = () => {
      consumed.current = true;
      generation += 1;
      animation?.stop();
      animation = undefined;
      translation.setValue(0);
    };
    const queryReduction = async (enter: boolean) => {
      const request = ++generation;
      try {
        const reduced = await AccessibilityInfo.isReduceMotionEnabled();
        if (!alive || request !== generation) return;
        if (reduced !== false) {
          settle();
          return;
        }
        if (!enter || consumed.current || !foreground || !enabled || !active) return;
        consumed.current = true;
        translation.setValue(scale(6));
        animation = Animated.timing(translation, {
          toValue: 0,
          duration: 240,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
          isInteraction: false,
        });
        animation.start(() => {
          if (alive) translation.setValue(0);
        });
      } catch {
        // An unavailable or failed preference query leaves the art still.
        if (alive && request === generation) settle();
      }
    };

    if (!enabled || !active) {
      settle();
    } else {
      try {
        foreground = manager.getCurrentState() === 'active';
        lifecycle = manager.addAppStateListener('change', (state) => {
          const wasForeground = foreground;
          foreground = state === 'active';
          if (!foreground) settle();
          else if (!wasForeground) queryReduction(false);
        });
        if (!foreground) settle();
        // Kepler currently returns a no-op subscription for this event. The
        // foreground query above also covers returning from system settings.
        try {
          reduction = AccessibilityInfo.addEventListener('reduceMotionChanged', (reduced) => {
            if (reduced !== false) settle();
          });
        } catch {
          // Older runtimes can omit the event; the explicit query remains.
        }
        queryReduction(!consumed.current);
      } catch {
        // Without lifecycle access, decorative movement stays disabled.
        settle();
      }
    }

    return () => {
      alive = false;
      settle();
      lifecycle?.remove();
      reduction?.remove();
    };
  }, [active, enabled, manager, translation]);

  return animatedOnEntry ? (
    <Animated.View testID={testID} accessible={false} pointerEvents="none"
      style={{ transform: [{ translateY: translation }] }}>
      {children}
    </Animated.View>
  ) : <View testID={testID} accessible={false} pointerEvents="none">{children}</View>;
}
