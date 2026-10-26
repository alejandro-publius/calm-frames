/** Original coastal map, with static shore depth and optional selection movement. */
import React from 'react';
import { CALM_WORLD } from './calmStyles';
import { StyleSheet, View } from 'react-native';
import Svg, { Path, Rect } from '@amazon-devices/react-native-svg';
import CoastalIsland, { IslandKind } from './CoastalIsland';
import CoastalBoat from './CoastalBoat';
import { DETAIL, HOME_ISLANDS, ISLAND_ORDER, shoreline } from './homeIslands';
const ROUTE_Y = HOME_ISLANDS.BOAT.top + HOME_ISLANDS.BOAT.height / 2;
/** The dashed route the boat follows, through the open water in front of the islands. */
const CENTERS = ISLAND_ORDER.map(kind => HOME_ISLANDS.CENTERS[kind]);
const ROUTE = `M${CENTERS[0]} ${ROUTE_Y}` + CENTERS.slice(1).map((x, i) => `Q${(CENTERS[i] + x) / 2} ${ROUTE_Y + (i % 2 ? -16 : 16)} ${x} ${ROUTE_Y}`).join('');
/** Small waves in open water: past the outer islands, and in front of them clear of the route. */
const WATER_RIPPLES = [[8, 450], [1816, 450], [64, 700], [1760, 700]];
export const WorldAppearance = React.createContext(false);
export const WORLD = CALM_WORLD;
export default function CoastalWorld({ detail = false, destination = 'coastal', showBoat = false, motionEnabled = false, active = true, cardKinds = [] }: { detail?: boolean; destination?: IslandKind; showBoat?: boolean; motionEnabled?: boolean; active?: boolean; /** Islands a card or photograph stands on; their landmarks stand beside it. */ cardKinds?: IslandKind[] }) {
  return <View testID="coastal-world" pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={StyleSheet.absoluteFill}>
    <Svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
      <Rect width="1920" height="1080" fill="#6FB4B1" />
      {detail ? <>
        {/* Positions come from homeIslands.ts DETAIL, which Details reads for its photograph too. */}
        <Path testID="home-sky" d={shoreline(HOME_ISLANDS.SKY_EDGE, false)} fill="#F7EACF" />
        <Path testID="home-sand-edge" d={shoreline(DETAIL.SAND_EDGE, true)} fill="#D2B47D" />
        <Path testID="home-sand" d={shoreline(DETAIL.SAND_EDGE + HOME_ISLANDS.SAND_STEP, true)} fill="#F7EACF" />
        <CoastalIsland kind={destination} x={DETAIL.ISLAND.x} y={DETAIL.ISLAND.y} size={DETAIL.ISLAND.scale} underCard={cardKinds.includes(destination)} />
        {DETAIL.RIPPLES.map(([x, y]) => <Path key={x} testID="home-ripple" d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
        <Rect testID="detail-panel" x={DETAIL.PANEL.left} y={DETAIL.PANEL.top} width={DETAIL.PANEL.width} height={DETAIL.PANEL.height} rx="28" fill="#FFF8E7" stroke="#385C59" strokeWidth="2" />
      </> : <>
        {/* Positions come from homeIslands.ts, which the cards and the hero read too. */}
        <Path testID="home-sky" d={shoreline(HOME_ISLANDS.SKY_EDGE, false)} fill="#F7EACF" />
        <Path testID="home-sand-edge" d={shoreline(HOME_ISLANDS.SAND_EDGE, true)} fill="#D2B47D" />
        <Path testID="home-sand" d={shoreline(HOME_ISLANDS.SAND_EDGE + HOME_ISLANDS.SAND_STEP, true)} fill="#F7EACF" />
        <Path testID="home-route" d={ROUTE} fill="none" stroke="#386F70" strokeWidth="24" strokeLinecap="round" />
        <Path d={ROUTE} fill="none" stroke="#F7EACF" strokeWidth="9" strokeDasharray="5 30" strokeLinecap="round" />
        {ISLAND_ORDER.map(kind => <CoastalIsland key={kind} kind={kind} x={HOME_ISLANDS.CENTERS[kind]} y={HOME_ISLANDS.ISLAND_Y} size={HOME_ISLANDS.ISLAND_SCALE} onMap underCard={cardKinds.includes(kind)} />)}
        {WATER_RIPPLES.map(([x, y]) => <Path key={x} testID="home-ripple" d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
      </>}
    </Svg>
    {!detail && showBoat ? <CoastalBoat destination={destination} enabled={motionEnabled} active={active} /> : null}
  </View>;
}
