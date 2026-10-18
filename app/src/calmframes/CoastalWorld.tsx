/** Original coastal map, with static shore depth and optional selection movement. */
import React from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Path, Rect } from '@amazon-devices/react-native-svg';
import CoastalIsland, { IslandKind } from './CoastalIsland';
import CoastalBoat from './CoastalBoat';
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
        <Path d="M476 704Q720 728 960 704T1444 704" fill="none" stroke="#386F70" strokeWidth="24" strokeLinecap="round" />
        <Path d="M476 698Q720 722 960 698T1444 698" fill="none" stroke="#F7EACF" strokeWidth="9" strokeDasharray="5 30" strokeLinecap="round" />
        <CoastalIsland kind="forest" x={960} y={620} size={0.86} />
        <CoastalIsland kind="coastal" x={476} y={620} size={0.86} />
        <CoastalIsland kind="sea-otters" x={1444} y={620} size={0.86} />
      </>}
      {[[100,730],[880,680],[1770,800],[1260,270]].map(([x,y],i)=><Path key={i} d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
      {detail ? <Rect x="90" y="200" width="900" height="700" rx="36" fill="#FFF8E7" stroke="#385C59" strokeWidth="8" /> : null}
    </Svg>
    {!detail && showBoat ? <CoastalBoat destination={destination} enabled={motionEnabled} active={active} /> : null}
  </View>;
}
