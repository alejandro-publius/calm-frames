import MaterialIcons from '@amazon-devices/react-native-vector-icons/MaterialIcons';
import React, { RefObject } from 'react';
import {
  StyleProp,
  StyleSheet,
  Text,
  TouchableOpacity,
  ViewStyle,
  AccessibilityState,
} from 'react-native';
import { CALM_COLORS, FOCUS_RING_WIDTH } from '../../calmframes/calmStyles';
import FocusableElement from '../../components/FocusableElement';
import { COLORS } from '../../styles/Colors';
import { scaleUxToDp } from '../../utils/pixelUtils';

export interface PlayerButtonProps {
  onPress: () => void;
  accessibilityLabel: string;
  accessibilityState?: AccessibilityState;
  icon: string;
  size: number;
  overrideStyle?: StyleProp<ViewStyle>;
  onBlur?: () => void;
  testID?: string;
  hasTVPreferredFocus?: boolean;
}

export const PlayerButton = React.forwardRef(
  (
    {
      onPress,
      accessibilityLabel,
      accessibilityState,
      icon,
      size,
      overrideStyle,
      onBlur,
      testID,
      hasTVPreferredFocus,
    }: PlayerButtonProps,
    ref: React.ForwardedRef<React.ComponentRef<typeof TouchableOpacity>>,
  ) => {
    return (
      <FocusableElement
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        accessibilityState={accessibilityState}
        onBlur={onBlur}
        focusableElementRef={ref as RefObject<React.ComponentRef<typeof TouchableOpacity>> | null}
        style={[styles.buttonContainer, overrideStyle]}
        onFocusOverrideStyle={[styles.buttonFocus, { borderRadius: scaleUxToDp(size) }]}
        onPress={onPress}
        hasTVPreferredFocus={hasTVPreferredFocus}
        testID={testID}>
        <Text>
          <MaterialIcons name={icon} size={scaleUxToDp(size)} color={COLORS.WHITE} />
        </Text>
      </FocusableElement>
    );
  },
);

const styles = StyleSheet.create({
  buttonContainer: {
    padding: scaleUxToDp(18),
    borderWidth: scaleUxToDp(FOCUS_RING_WIDTH),
    borderColor: 'transparent',
    borderRadius: scaleUxToDp(40),
    alignItems: 'center',
    flexDirection: 'row',
  },
  button: {
    resizeMode: 'contain',
    tintColor: COLORS.WHITE,
  },
  buttonFocus: {
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
    borderColor: CALM_COLORS.FOCUS_RING,
  },
});

export default PlayerButton;
