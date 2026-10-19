/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Original coastal map, with static shore depth and optional selection movement. */
import React from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Path, Rect } from '@amazon-devices/react-native-svg';
import CoastalIsland, { IslandKind } from './CoastalIsland';
import CoastalBoat from './CoastalBoat';
import { HOME_ISLANDS, shoreline } from './homeIslands';
const ROUTE_Y = HOME_ISLANDS.BOAT.top + HOME_ISLANDS.BOAT.height / 2;
/** The dashed route the boat follows, through the open water in front of the islands. */
const ROUTE = `M${HOME_ISLANDS.CENTERS.coastal} ${ROUTE_Y}Q${(HOME_ISLANDS.CENTERS.coastal + HOME_ISLANDS.CENTERS.forest) / 2} ${ROUTE_Y + 16} ${HOME_ISLANDS.CENTERS.forest} ${ROUTE_Y}T${HOME_ISLANDS.CENTERS['sea-otters']} ${ROUTE_Y}`;
/** Small waves in open water: past the outer islands, and in front of them clear of the route. */
const WATER_RIPPLES = [[16, 470], [1808, 470], [150, 700], [1660, 700]];
export const WorldAppearance = React.createContext(false);
export const WORLD = { BACKGROUND:'#F7EACF', SURFACE:'#FFF8E7', SURFACE_FOCUSED:'#FFE1A9', BORDER:'#385C59', FOCUS_RING:'#A44132', PRIMARY:'#F7B37A', TEXT:'#193F3E', TEXT_DIM:'#193F3E', TEXT_DISABLED:'#526A63', INK:'#193F3E' };
export default function CoastalWorld({ detail = false, destination = 'coastal', showBoat = false, motionEnabled = false, active = true, cardKinds = [] }: { detail?: boolean; destination?: IslandKind; showBoat?: boolean; motionEnabled?: boolean; active?: boolean; /** Islands a Home card stands on; their landmarks stand beside the card. */ cardKinds?: IslandKind[] }) {
  return <View testID="coastal-world" pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={StyleSheet.absoluteFill}>
    <Svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
      <Rect width="1920" height="1080" fill="#6FB4B1" />
      {detail ? <>
        <Path d="M0 0H1920V190Q1690 130 1530 210T1140 170T720 210T300 170T0 210Z" fill="#F7EACF" />
        <Path d="M0 900Q180 800 400 870T850 875T1310 865T1920 840V1080H0Z" fill="#D2B47D" />
        <Path d="M0 926Q180 826 400 896T850 901T1310 891T1920 866V1080H0Z" fill="#F7EACF" />
        <CoastalIsland kind={destination} x={1430} y={700} size={1.12} />
        {[[100,730],[880,680],[1770,800],[1260,270]].map(([x,y],i)=><Path key={i} d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
        <Rect x="90" y="200" width="900" height="700" rx="36" fill="#FFF8E7" stroke="#385C59" strokeWidth="8" />
      </> : <>
        {/* Positions come from homeIslands.ts, which the cards and the hero read too. */}
        <Path testID="home-sky" d={shoreline(HOME_ISLANDS.SKY_EDGE, false)} fill="#F7EACF" />
        <Path testID="home-sand-edge" d={shoreline(HOME_ISLANDS.SAND_EDGE, true)} fill="#D2B47D" />
        <Path testID="home-sand" d={shoreline(HOME_ISLANDS.SAND_EDGE + HOME_ISLANDS.SAND_STEP, true)} fill="#F7EACF" />
        <Path testID="home-route" d={ROUTE} fill="none" stroke="#386F70" strokeWidth="24" strokeLinecap="round" />
        <Path d={ROUTE} fill="none" stroke="#F7EACF" strokeWidth="9" strokeDasharray="5 30" strokeLinecap="round" />
        {(['forest', 'coastal', 'sea-otters'] as const).map(kind => <CoastalIsland key={kind} kind={kind} x={HOME_ISLANDS.CENTERS[kind]} y={HOME_ISLANDS.ISLAND_Y} size={HOME_ISLANDS.ISLAND_SCALE} onMap underCard={cardKinds.includes(kind)} />)}
        {WATER_RIPPLES.map(([x, y]) => <Path key={x} testID="home-ripple" d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
      </>}
    </Svg>
    {!detail && showBoat ? <CoastalBoat destination={destination} enabled={motionEnabled} active={active} /> : null}
  </View>;
}
