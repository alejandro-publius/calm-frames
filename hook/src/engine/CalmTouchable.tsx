/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Immediate pressed feedback, shared by selectors and controls; never scales or fades. */
import React from 'react';
import { TouchableOpacity, TouchableOpacityProps, StyleSheet } from 'react-native';
import { CALM_COLORS } from './calmStyles';
import { CalmControlSurface, ControlSurfaceKind, CalmControlAppearance } from './CalmControlSurface';

type Props = TouchableOpacityProps & { surfaceKind?: ControlSurfaceKind };
const CalmTouchable = React.forwardRef<React.ComponentRef<typeof TouchableOpacity>, Props>(
  ({ style, onPressIn, onPressOut, onFocus, onBlur, children, surfaceKind = 'secondary', ...props }, ref) => {
    const [pressed, setPressed] = React.useState(false);
    const [focused, setFocused] = React.useState(false);
    const study = React.useContext(CalmControlAppearance);
    const blocked = props.disabled || props.accessibilityState?.disabled;
    return <TouchableOpacity {...props} ref={ref} activeOpacity={1}
      onPressIn={(event) => { if (!blocked) setPressed(true); onPressIn?.(event); }}
      onPressOut={(event) => { setPressed(false); onPressOut?.(event); }}
      onFocus={(event) => { setFocused(true); onFocus?.(event); }}
      onBlur={(event) => { setFocused(false); setPressed(false); onBlur?.(event); }}
      style={[style, pressed && !blocked ? { backgroundColor: CALM_COLORS.INK } : null, study ? styles.study : null, study && focused && !blocked ? styles.focus : null]}>
      {study ? <CalmControlSurface kind={surfaceKind} focused={focused} pressed={pressed && !blocked} disabled={!!blocked} selected={!!(props.accessibilityState?.selected || props.accessibilityState?.checked === true)} /> : null}
      {children}
    </TouchableOpacity>;
  },
);
const styles = StyleSheet.create({
  study: { backgroundColor: 'transparent', borderColor: 'transparent' },
  focus: { borderColor: CALM_COLORS.FOCUS_RING },
});
export default CalmTouchable;
