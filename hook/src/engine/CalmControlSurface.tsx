/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Reviewed materials, enabled by the application root; false supports legacy comparisons. */
import React from 'react';
import { CoastalAppearance } from './CoastalAppearance';
import { StyleSheet, View } from 'react-native';
import LinearGradient from '@amazon-devices/react-linear-gradient';
import { CALM_COLORS, COASTAL_COLORS, CALM_CONTROL, scale } from './calmStyles';

export const CalmControlAppearance = React.createContext(false);
export type ControlSurfaceKind = 'primary' | 'secondary' | 'tertiary' | 'keypad';
export const CONTROL_MATERIAL = {
  primary: ['#F0F2EF', '#DCE2E2'], primaryPressed: ['#DCE2E2', '#E8EDEC'],
  secondary: ['#263641', '#202D37'], secondaryPressed: ['#1D2932', '#2B3B47'],
  selected: ['#2B3B47', '#22303B'], disabled: ['#22303B', '#22303B'],
} as const;
export const COASTAL_MATERIAL = CONTROL_MATERIAL;

/** All paint stays inside the existing target. No blur, elevation, motion or external shadow. */
export function CalmControlSurface({ kind, focused, pressed, disabled, selected }: {
  kind: ControlSurfaceKind; focused: boolean; pressed: boolean; disabled: boolean; selected: boolean;
}) {
  const coastal = React.useContext(CoastalAppearance);
  const material = coastal ? COASTAL_MATERIAL : CONTROL_MATERIAL;
  const styles = coastal ? coastalStyles : darkStyles;
  if (kind === 'tertiary' && !focused && !pressed) return null;
  const primary = kind === 'primary' && !disabled;
  const colors = disabled ? material.disabled : primary
    ? (pressed ? material.primaryPressed : material.primary)
    : pressed ? material.secondaryPressed : selected ? material.selected : material.secondary;
  return <View pointerEvents="none" accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[styles.paint, coastal && primary ? { borderRadius: scale(58) } : null]}>
    <View style={[styles.depth, disabled || kind === 'tertiary' ? styles.noDepth : null]} />
    <View style={[styles.foot, coastal && primary ? { borderRadius: scale(58) } : null, primary ? styles.primaryFoot : null]} />
    <View style={[styles.face, coastal && primary ? { borderRadius: scale(58) } : null, primary || focused ? styles.darkContour : disabled ? styles.disabledContour : null, { top: scale(pressed ? 2 : 0), bottom: scale(pressed || disabled || kind === 'tertiary' ? 2 : 5) }]}>
      <LinearGradient colors={[...colors]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.gradient} />
      {!disabled && !pressed ? <View style={[styles.highlight, primary ? styles.primaryHighlight : null]} /> : null}
      {selected ? <View style={[styles.selectedEdge, disabled ? styles.disabledSelection : null]} /> : null}
    </View>
  </View>;
}

const makeStyles = (colors: Record<keyof typeof CALM_COLORS, string>) => StyleSheet.create({
  paint: { ...StyleSheet.absoluteFillObject, borderRadius: scale(CALM_CONTROL.RADIUS - 6), overflow: 'hidden' },
  noDepth: { backgroundColor: 'transparent' },
  primaryFoot: { backgroundColor: '#84949C' },
  darkContour: { borderColor: colors.INK },
  disabledContour: { borderColor: '#525D69' },
  primaryHighlight: { backgroundColor: '#FFFFFF' },
  depth: { backgroundColor: '#090E1670', position: 'absolute', left: 0, right: 0, top: scale(6), bottom: 0, borderRadius: scale(12) },
  foot: { bottom: scale(1), backgroundColor: '#090E16BB', position: 'absolute', left: scale(1), right: scale(1), top: scale(4), borderRadius: scale(12) },
  face: { borderColor: colors.BORDER, position: 'absolute', left: 0, right: 0, borderRadius: scale(12), borderWidth: scale(2), overflow: 'hidden' },
  gradient: { ...StyleSheet.absoluteFillObject },
  highlight: { backgroundColor: '#D1D3D62E', position: 'absolute', left: scale(10), right: scale(10), top: 0, height: Math.max(1, scale(1)), borderRadius: scale(1) },
  disabledSelection: { backgroundColor: '#8E98A5' },
  selectedEdge: { position: 'absolute', left: 0, top: scale(14), bottom: scale(14), width: scale(3), borderRadius: scale(2), backgroundColor: colors.VERIFIED },
});

const darkStyles = makeStyles(CALM_COLORS);
const coastalStyles = makeStyles(COASTAL_COLORS);
