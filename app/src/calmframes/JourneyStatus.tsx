/** Decorative route, never a progress meter. Text follows real application state. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from '@amazon-devices/react-native-svg';
import CalmArtworkMotion from './CalmArtworkMotion';
import { CALM_JOURNEY, CALM_SPACE, CALM_TEXT, CALM_WORLD, scale } from './calmStyles';

export function EnvironmentMark({ forest = false, size = 40 }: { forest?: boolean; size?: number }) {
  return <Svg width={scale(size)} height={scale(size)} viewBox="0 0 48 48" accessible={false}>
    {forest ? <Path d="M24 4L10 24H17L7 36H41L31 24H38ZM24 36V44" fill="none" stroke={CALM_WORLD.TEXT} strokeWidth="3" strokeLinejoin="round" />
      : <Path d="M3 15Q10 5 17 15T31 15T45 15M3 29Q10 19 17 29T31 29T45 29M9 41H39" fill="none" stroke={CALM_WORLD.TEXT} strokeWidth="3" strokeLinecap="round" />}
  </Svg>;
}

export default function JourneyStatus({ status, forest = false, motionEnabled = false, active = true, liveStatus = true, testID = 'journey-status' }: {
  status: string; forest?: boolean; motionEnabled?: boolean; active?: boolean; liveStatus?: boolean; testID?: string;
}) {
  return <View testID={testID} style={styles.status}>
    <View pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <CalmArtworkMotion gentle enabled={motionEnabled} active={active} testID={`${testID}-art`}>
        <Svg width={scale(CALM_JOURNEY.WIDTH)} height={scale(CALM_JOURNEY.HEIGHT)} viewBox="0 0 700 144">
          <Path d="M4 106Q95 106 150 76T310 80T480 74H566" fill="none" stroke={CALM_WORLD.BORDER} strokeWidth="3" strokeDasharray="5 12" strokeLinecap="round" />
          <Circle cx="626" cy="74" r="56" fill={CALM_WORLD.BACKGROUND} stroke={CALM_WORLD.BORDER} strokeWidth="3" />
          <Circle cx="626" cy="74" r="46" fill="none" stroke={CALM_WORLD.BORDER} strokeWidth="1" />
          {forest ? <Path d="M626 40L605 70H614L598 93H654L638 70H647ZM626 94V108" fill={CALM_WORLD.SURFACE_FOCUSED} stroke={CALM_WORLD.TEXT} strokeWidth="3" strokeLinejoin="round" />
            : <Path d="M598 65Q607 53 616 65T634 65T652 65M598 82Q607 70 616 82T634 82T652 82M609 99H643" fill="none" stroke={CALM_WORLD.TEXT} strokeWidth="4" strokeLinecap="round" />}
          <Path d="M29 61H101L87 79H43ZM63 17V59M57 24L37 52H57ZM70 28L90 52H70Z" fill={CALM_WORLD.PRIMARY} stroke={CALM_WORLD.TEXT} strokeWidth="3" strokeLinejoin="round" />
        </Svg>
      </CalmArtworkMotion>
    </View>
    <Text testID={`${testID}-message`} style={styles.message} accessibilityLiveRegion={liveStatus ? 'polite' : 'none'}>{status}</Text>
  </View>;
}
const styles = StyleSheet.create({
  status: { width: scale(CALM_JOURNEY.WIDTH), gap: scale(CALM_SPACE.ROW), marginTop: scale(CALM_SPACE.ROW) },
  message: { ...CALM_TEXT.body, color: CALM_WORLD.TEXT, minHeight: scale(96) },
});
