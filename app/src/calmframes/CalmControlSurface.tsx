/** Opt-in material study. Production remains unchanged until visual review. */
import React from 'react';
import { StyleSheet, View } from 'react-native';
import LinearGradient from '@amazon-devices/react-linear-gradient';
import { CALM_COLORS, CALM_CONTROL, scale } from './calmStyles';

export const ControlSurfaceStudy = React.createContext(false);
export type ControlSurfaceKind = 'primary' | 'secondary' | 'tertiary' | 'keypad';
export const CONTROL_MATERIAL = {
  cream: ['#F8EFDE', '#E2D3B6'],
  creamPressed: ['#CFBF9F', '#E6D7BA'],
  teal: ['#294B54E8', '#16343DE8'],
  tealPressed: ['#142F39', '#26454D'],
  selected: ['#2D4C46EF', '#203F3FEF'],
  disabled: ['#263E43', '#263E43'],
} as const;

/** All paint stays inside the existing target. No blur, elevation, motion or external shadow. */
export function CalmControlSurface({ kind, focused, pressed, disabled, selected }: {
  kind: ControlSurfaceKind; focused: boolean; pressed: boolean; disabled: boolean; selected: boolean;
}) {
  if (kind === 'tertiary' && !focused && !pressed) return null;
  const primary = kind === 'primary' && !disabled;
  const colors = disabled ? CONTROL_MATERIAL.disabled : primary
    ? (pressed ? CONTROL_MATERIAL.creamPressed : CONTROL_MATERIAL.cream)
    : pressed ? CONTROL_MATERIAL.tealPressed : selected ? CONTROL_MATERIAL.selected : CONTROL_MATERIAL.teal;
  return <View pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.paint}>
    <View style={[styles.depth, disabled || kind === 'tertiary' ? styles.noDepth : null]} />
    <View style={[styles.foot, primary ? styles.creamFoot : null]} />
    <View style={[styles.face, primary || focused ? styles.darkContour : disabled ? styles.disabledContour : null, { top: scale(pressed ? 2 : 0), bottom: scale(pressed || disabled || kind === 'tertiary' ? 2 : 5) }]}>
      <LinearGradient colors={[...colors]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.gradient} />
      {!disabled && !pressed ? <View style={[styles.highlight, primary ? styles.creamHighlight : null]} /> : null}
      {selected ? <View style={styles.selectedEdge} /> : null}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  paint: { ...StyleSheet.absoluteFillObject, borderRadius: scale(CALM_CONTROL.RADIUS - 6), overflow: 'hidden' },
  noDepth: { backgroundColor: 'transparent' },
  creamFoot: { backgroundColor: '#887E6A' },
  darkContour: { borderColor: '#17323C' },
  disabledContour: { borderColor: '#42585D' },
  creamHighlight: { backgroundColor: '#FFF9EA' },
  depth: { backgroundColor: '#071D2670', position: 'absolute', left: 0, right: 0, top: scale(6), bottom: 0, borderRadius: scale(12) },
  foot: { bottom: scale(1), backgroundColor: '#0A252DBB', position: 'absolute', left: scale(1), right: scale(1), top: scale(4), borderRadius: scale(12) },
  face: { borderColor: '#48656B', position: 'absolute', left: 0, right: 0, borderRadius: scale(12), borderWidth: scale(2), overflow: 'hidden' },
  gradient: { ...StyleSheet.absoluteFillObject },
  highlight: { backgroundColor: '#AFC7C22E', position: 'absolute', left: scale(10), right: scale(10), top: 0, height: Math.max(1, scale(1)), borderRadius: scale(1) },
  selectedEdge: { position: 'absolute', left: 0, top: scale(14), bottom: scale(14), width: scale(3), borderRadius: scale(2), backgroundColor: CALM_COLORS.VERIFIED },
});
