/** Original static coastal map. No Nintendo assets, game engine or moving media. */
import React from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Path, Ellipse, Circle, Rect } from '@amazon-devices/react-native-svg';
export const WorldAppearance = React.createContext(false);
export const WORLD = { BACKGROUND:'#F7EACF', SURFACE:'#FFF8E7', SURFACE_FOCUSED:'#FFE1A9', BORDER:'#385C59', FOCUS_RING:'#A44132', PRIMARY:'#F7B37A', TEXT:'#193F3E', TEXT_DIM:'#193F3E', TEXT_DISABLED:'#526A63', INK:'#193F3E' };
export default function CoastalWorld({ detail = false }: { detail?: boolean }) {
  return <View testID="coastal-world" pointerEvents="none" accessible={false} accessibilityElementsHidden style={StyleSheet.absoluteFill}>
    <Svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
      <Rect width="1920" height="1080" fill="#6FB4B1" />
      <Path d="M0 0H1920V190Q1690 130 1530 210T1140 170T720 210T300 170T0 210Z" fill="#F7EACF" />
      <Path d="M0 900Q180 800 400 870T850 875T1310 865T1920 840V1080H0Z" fill="#D2B47D" />
      <Path d="M0 926Q180 826 400 896T850 901T1310 891T1920 866V1080H0Z" fill="#F7EACF" />
      <Path d="M300 670Q710 830 990 620T1620 650" fill="none" stroke="#386F70" strokeWidth="28" strokeLinecap="round" />
      <Path d="M300 662Q710 822 990 612T1620 642" fill="none" stroke="#F7EACF" strokeWidth="12" strokeDasharray="6 32" strokeLinecap="round" />
      <Ellipse cx="515" cy="612" rx="360" ry="145" fill="#3D8584" />
      <Ellipse cx="515" cy="578" rx="350" ry="145" fill="#D2B47D" />
      <Ellipse cx="515" cy="556" rx="338" ry="139" fill="#F1DCA8" />
      <Ellipse cx="1400" cy="630" rx="340" ry="140" fill="#3D8584" />
      <Ellipse cx="1400" cy="596" rx="328" ry="142" fill="#D2B47D" />
      <Ellipse cx="1400" cy="574" rx="318" ry="134" fill="#F1DCA8" />
      {/* Hand-built headland, lighthouse and quiet wave marks. */}
      <Path d="M170 490L225 365L280 490Z M245 498L300 390L350 498Z" fill="#356A57" stroke="#234E49" strokeWidth="7" strokeLinejoin="round" />
      <Path d="M1610 510L1625 340H1695L1710 510Z" fill="#FFF8E7" stroke="#385C59" strokeWidth="7" />
      <Rect x="1624" y="366" width="72" height="35" fill="#BB5944" />
      <Path d="M1608 340L1660 295L1712 340Z" fill="#BB5944" stroke="#385C59" strokeWidth="7" strokeLinejoin="round" />
      <Rect x="1645" y="320" width="30" height="28" rx="4" fill="#FFE1A9" />
      {[ [100,730],[850,330],[1040,780],[1770,740],[1160,270] ].map(([x,y],i)=><Path key={i} d={`M${x} ${y}q24 18 48 0t48 0`} fill="none" stroke="#CEE5D5" strokeWidth="7" strokeLinecap="round" />)}
      <Circle cx="935" cy="630" r="13" fill="#BB5944" stroke="#FFF8E7" strokeWidth="5" />
      {detail ? <Rect x="90" y="200" width="900" height="700" rx="36" fill="#FFF8E7" stroke="#385C59" strokeWidth="8" /> : null}
    </Svg>
  </View>;
}
