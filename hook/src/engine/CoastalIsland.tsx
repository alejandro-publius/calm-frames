/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Original layered vector scenery, shared by the map, Details and loading. */
import React from 'react';
import { G, Path, Ellipse, Rect } from '@amazon-devices/react-native-svg';
export type IslandKind = 'coastal' | 'sea-otters' | 'forest';
export const islandKind = (art?: string): IslandKind => art === 'sea-otters' || art === 'forest' ? art : 'coastal';
const shores: Record<IslandKind, string> = {
  coastal: 'M-330 0L-285-65L-205-80L-155-120L-45-110L15-135L120-100L195-75L270-80L335-20L310 42L235 68L130 60L40 92L-65 80L-155 95L-245 60L-305 45Z',
  'sea-otters': 'M-330-5Q-305-86-205-85Q-130-125-45-100Q65-130 145-90Q265-100 322-25Q350 30 285 65Q195 105 100 75Q20 110-75 85Q-175 110-250 60Q-340 50-330-5Z',
  forest: 'M-310 0Q-330-65-225-85Q-170-130-70-110Q20-150 100-105Q210-120 245-65Q330-55 305 20Q280 100 160 85Q40 120-55 95Q-180 120-215 75Q-300 80-310 0Z',
};
function Pine({ x, y, size = 1 }: { x: number; y: number; size?: number }) {
  return <G transform={`translate(${x} ${y}) scale(${size})`}>
    <Path d="M0-140V8" stroke="#705A43" strokeWidth="14" strokeLinecap="round" />
    <Path d="M0-180L-40-100H-25L-60-30H60L25-100H40Z" fill="#356A57" stroke="#234E49" strokeWidth="6" strokeLinejoin="round" />
    <Path d="M0-166V-45L42-45L15-101H25Z" fill="#4E8166" />
  </G>;
}
/**
 * The landmarks for an island a Home card stands on, in island units.
 *
 * The card covers the middle of the island (homeIslands.ts), so what says
 * which island it is stands on the two strips either side of it, at least 262
 * units from the centre, and the front beach below it. Nothing here is drawn
 * where the card will be.
 */
function Flanks({ kind }: { kind: IslandKind }) {
  if (kind === 'coastal') return <G testID="island-landmarks-coastal">
    <Pine x={-300} y={-28} size={0.5} />
    <Path d="M-336 28Q-346-6-320-24Q-296-40-274-20Q-264-2-268 24Q-300 40-336 28Z" fill="#9CA99C" stroke="#385C59" strokeWidth="6" strokeLinejoin="round" />
    <Path d="M-318-14Q-300-24-284-12" fill="none" stroke="#DCE0C9" strokeWidth="6" strokeLinecap="round" />
    <Path d="M272-30L281-188H307L316-30Z" fill="#FFF8E7" stroke="#385C59" strokeWidth="6" />
    <Rect x="281" y="-168" width="26" height="22" fill="#BB5944" />
    <Path d="M274-188L294-214L314-188Z" fill="#BB5944" stroke="#385C59" strokeWidth="6" strokeLinejoin="round" />
  </G>;
  if (kind === 'sea-otters') return <G testID="island-landmarks-sea-otters">
    {[[-300, 30], [-322, 60], [300, 30], [322, 60]].map(([left, top]) => <G key={left} transform={`translate(${left} ${top}) scale(0.7)`}>
      <Path d="M0 50Q-30 5-4-24Q20-55 0-90" fill="none" stroke="#315F4D" strokeWidth="9" strokeLinecap="round" />
      <Path d="M-5 5Q-55-20-35-40Q-5-33-5 5 M3-28Q42-38 35-64Q5-62 3-28" fill="#4F7D58" stroke="#315F4D" strokeWidth="4" />
    </G>)}
    <Ellipse cx="300" cy="-44" rx="30" ry="18" fill="#A9B2A1" stroke="#385C59" strokeWidth="5" />
    <Path d="M-150 100Q-60 114 20 100 M70 100Q130 112 170 100" fill="none" stroke="#FFF8E7" strokeWidth="8" strokeLinecap="round" />
  </G>;
  return <G testID="island-landmarks-forest">
    <Pine x={-318} y={4} size={0.4} /><Pine x={-290} y={-16} size={0.45} />
    <Pine x={300} y={-12} size={0.55} />
    <Ellipse cx="-180" cy="110" rx="34" ry="18" fill="#B8BBA5" stroke="#385C59" strokeWidth="5" />
  </G>;
}

export default function CoastalIsland({ kind, x, y, size = 1, onMap = false, underCard = false }: { kind: IslandKind; x: number; y: number; size?: number; /** One of three on the Home map, where a narrower ring keeps neighbours apart. */ onMap?: boolean; /** A Home card stands on it, so landmarks move to the sides. */ underCard?: boolean }) {
  const shore = shores[kind];
  return <G testID={`island-${kind}`} transform={`translate(${x} ${y}) scale(${size})`}>
    <Ellipse cy="46" rx={onMap ? 340 : 360} ry={onMap ? 110 : 116} fill="none" stroke="#95C9C0" strokeWidth="9" />
    <Path d={shore} transform="translate(0 32)" fill="#3D8584" />
    <Path d={shore} transform="translate(0 18)" fill="#A99571" stroke="#385C59" strokeWidth="5" />
    <Path d={shore} fill={kind === 'forest' ? '#BDD09A' : '#F1DCA8'} stroke="#385C59" strokeWidth="5" strokeLinejoin="round" />
    {underCard ? <Flanks kind={kind} /> : kind === 'coastal' ? <>
      <Path d="M-295-20L-255-105L-195-120L-165-40L-95-75L-45-5L-90 38L-230 28Z M160 15L200-65L260-45L305 5L275 40Z" fill="#9CA99C" stroke="#385C59" strokeWidth="6" strokeLinejoin="round" />
      <Path d="M-255-105L-230-18L-165-40 M200-65L222 12L275 40" fill="none" stroke="#DCE0C9" strokeWidth="7" />
      <Pine x={-265} y={-45} size={0.7} />
      <Path d="M200-85L210-225H260L272-85Z" fill="#FFF8E7" stroke="#385C59" strokeWidth="6" />
      <Rect x="211" y="-205" width="48" height="28" fill="#BB5944" />
      <Path d="M200-225L235-260L270-225Z" fill="#BB5944" stroke="#385C59" strokeWidth="6" strokeLinejoin="round" />
    </> : kind === 'sea-otters' ? <>
      {[-280, -210, 230, 300].map((left, i) => <G key={left} transform={`translate(${left} ${i % 2 ? 28 : 65})`}>
        <Path d="M0 50Q-30 5-4-24Q20-55 0-90" fill="none" stroke="#315F4D" strokeWidth="9" strokeLinecap="round" />
        <Path d="M-5 5Q-55-20-35-40Q-5-33-5 5 M3-28Q42-38 35-64Q5-62 3-28" fill="#4F7D58" stroke="#315F4D" strokeWidth="4" />
      </G>)}
      <Ellipse cx="230" cy="-70" rx="54" ry="29" fill="#A9B2A1" stroke="#385C59" strokeWidth="5" />
      <Path d="M-160 67Q-60 93 20 65 M70 58Q130 77 170 63" fill="none" stroke="#FFF8E7" strokeWidth="8" strokeLinecap="round" />
    </> : <>
      <Path d="M-140 15Q-170-100-75-110Q-10-165 60-120Q155-130 155-20L105 30Z" fill="#9CA99C" stroke="#385C59" strokeWidth="6" />
      <Path d="M30-95Q55-70 38-25L25 20Q10 55 90 72" fill="none" stroke="#386F70" strokeWidth="35" strokeLinecap="round" />
      <Path d="M29-95Q51-70 34-25L23 20Q10 55 90 72" fill="none" stroke="#DCEFE0" strokeWidth="14" strokeLinecap="round" />
      <Pine x={-200} y={-20} size={0.95} /><Pine x={-110} y={-75} size={1.2} />
      <Pine x={95} y={-95} size={1.1} /><Pine x={205} y={-15} size={0.9} />
      <Ellipse cx="-190" cy="42" rx="52" ry="31" fill="#B8BBA5" stroke="#385C59" strokeWidth="5" />
    </>}
  </G>;
}
