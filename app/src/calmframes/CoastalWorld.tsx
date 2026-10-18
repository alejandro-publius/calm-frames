/** Original coastal map, with static shore depth and optional selection movement. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path, Rect } from '@amazon-devices/react-native-svg';
import CoastalIsland, { IslandKind } from './CoastalIsland';
import CoastalBoat from './CoastalBoat';
import { CALM_TEXT, scale } from './calmStyles';
export const WorldAppearance = React.createContext(false);
export const WORLD = { BACKGROUND:'#F7EACF', SURFACE:'#FFF8E7', SURFACE_FOCUSED:'#FFE1A9', BORDER:'#385C59', FOCUS_RING:'#A44132', PRIMARY:'#F7B37A', TEXT:'#193F3E', TEXT_DIM:'#193F3E', TEXT_DISABLED:'#526A63', INK:'#193F3E' };
export default function CoastalWorld({ detail = false, destination = 'coastal', showBoat = false, motionEnabled = false, active = true }: { detail?: boolean; destination?: IslandKind; showBoat?: boolean; motionEnabled?: boolean; active?: boolean }) {
  return <View testID="coastal-world" pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={StyleSheet.absoluteFill}>
    <Svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
      <Rect width="1920" height="1080" fill="#6FB4B1" />
      <Path d="M0 0H1920V190Q1690 130 1530 210T1140 170T720 210T300 170T0 210Z" fill="#F7EACF" />
      <Path d="M0 900Q180 800 400 870T850 875T1310 865T1920 840V1080H0Z" fill="#D2B47D" />
      <Path d="M0 926Q180 826 400 896T850 901T1310 891T1920 866V1080H0Z" fill="#F7EACF" />
      {detail ? <CoastalIsland kind={destination} x={1430} y={700} size={1.12} /> : <>
        <Path d="M515 750Q925 850 1400 768" fill="none" stroke="#386F70" strokeWidth="24" strokeLinecap="round" />
        <Path d="M515 744Q925 844 1400 762" fill="none" stroke="#F7EACF" strokeWidth="9" strokeDasharray="5 30" strokeLinecap="round" />
        <CoastalIsland kind="forest" x={960} y={474} size={0.66} />
        <CoastalIsland kind="coastal" x={515} y={578} />
        <CoastalIsland kind="sea-otters" x={1400} y={596} />
      </>}
      {[[100,730],[880,680],[1770,800],[1260,270]].map(([x,y],i)=><Path key={i} d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
      {detail ? <Rect x="90" y="200" width="900" height="700" rx="36" fill="#FFF8E7" stroke="#385C59" strokeWidth="8" /> : null}
    </Svg>
    {!detail ? <View testID="forest-preview-label" style={styles.forestLabel}>
      <Text style={styles.forestTitle}>Forest</Text><Text style={styles.forestStatus}>Not ready to watch</Text>
    </View> : null}
    {!detail && showBoat ? <CoastalBoat destination={destination} enabled={motionEnabled} active={active} /> : null}
  </View>;
}
const styles = StyleSheet.create({
  forestLabel: { position: 'absolute', left: scale(760), top: scale(564), width: scale(400), alignItems: 'center' },
  forestTitle: { ...CALM_TEXT.section, color: WORLD.TEXT },
  forestStatus: { ...CALM_TEXT.supporting, color: WORLD.TEXT },
});
