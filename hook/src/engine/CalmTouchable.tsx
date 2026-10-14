/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Immediate pressed feedback, shared by selectors and controls; never scales or fades. */
import React from 'react';
import { TouchableOpacity, TouchableOpacityProps } from 'react-native';
import { CALM_COLORS } from './calmStyles';
const CalmTouchable = React.forwardRef<React.ComponentRef<typeof TouchableOpacity>, TouchableOpacityProps>(
  ({ style, onPressIn, onPressOut, onBlur, ...props }, ref) => {
    const [pressed, setPressed] = React.useState(false);
    const blocked = props.disabled || props.accessibilityState?.disabled;
    return <TouchableOpacity {...props} ref={ref} activeOpacity={1}
      onPressIn={(event) => { if (!blocked) setPressed(true); onPressIn?.(event); }}
      onPressOut={(event) => { setPressed(false); onPressOut?.(event); }}
      onBlur={(event) => { setPressed(false); onBlur?.(event); }}
      style={[style, pressed && !blocked ? { backgroundColor: CALM_COLORS.INK } : null]} />;
  },
);
export default CalmTouchable;
