/** Immediate pressed feedback, shared by selectors and controls; never scales or fades. */
import { WorldAppearance, WORLD } from './CoastalWorld';
import React from 'react';
import { CoastalAppearance } from './CoastalAppearance';
import { TouchableOpacity, TouchableOpacityProps, StyleSheet } from 'react-native';
import { CALM_COLORS, COASTAL_COLORS, COASTAL_PRIMARY_FOCUS } from './calmStyles';
import { CalmControlSurface, ControlSurfaceKind, CalmControlAppearance } from './CalmControlSurface';
import { trace } from './trace';

type Props = TouchableOpacityProps & { surfaceKind?: ControlSurfaceKind };
const CalmTouchable = React.forwardRef<React.ComponentRef<typeof TouchableOpacity>, Props>(
  ({ style, onPressIn, onPressOut, onFocus, onBlur, children, surfaceKind = 'secondary', ...props }, ref) => {
    const coastal = React.useContext(CoastalAppearance);
    const world = React.useContext(WorldAppearance);
    const colors = world ? WORLD : coastal ? COASTAL_COLORS : CALM_COLORS;
    const [pressed, setPressed] = React.useState(false);
    const [focused, setFocused] = React.useState(false);
    const material = React.useContext(CalmControlAppearance);
    const study = material && !world;
    const blocked = props.disabled || props.accessibilityState?.disabled;
    const cornerRadius = StyleSheet.flatten(style)?.borderRadius;
    return <TouchableOpacity {...props} ref={ref} activeOpacity={1}
      onPressIn={(event) => { if (!blocked) setPressed(true); onPressIn?.(event); }}
      onPressOut={(event) => { setPressed(false); onPressOut?.(event); }}
      onFocus={(event) => { setFocused(true); trace('focus', props.testID); onFocus?.(event); }}
      onBlur={(event) => { setFocused(false); setPressed(false); onBlur?.(event); }}
      style={[style, pressed && !blocked ? { backgroundColor: surfaceKind === 'primary' ? colors.PRIMARY : colors.SURFACE_FOCUSED } : null, study ? styles.study : null, study && focused && !blocked ? { borderColor: surfaceKind === 'primary' ? COASTAL_PRIMARY_FOCUS : colors.FOCUS_RING } : null]}>
      {study ? <CalmControlSurface cornerRadius={typeof cornerRadius === 'number' ? cornerRadius : undefined} kind={surfaceKind} focused={focused} pressed={pressed && !blocked} disabled={!!blocked} selected={!!(props.accessibilityState?.selected || props.accessibilityState?.checked === true)} /> : null}
      {children}
    </TouchableOpacity>;
  },
);
const styles = StyleSheet.create({
  study: { backgroundColor: 'transparent', borderColor: 'transparent' },
  focus: { borderColor: CALM_COLORS.FOCUS_RING },
});
export default CalmTouchable;
