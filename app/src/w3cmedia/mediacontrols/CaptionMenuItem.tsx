import React from 'react';
import { StyleSheet, Text } from 'react-native';
import FocusableElement from '../../components/FocusableElement';
import { CALM_COLORS, CALM_TEXT, FOCUS_RING_WIDTH } from '../../calmframes/calmStyles';
import { COLORS } from '../../styles/Colors';
import { areComponentPropsEqual } from '../../utils/lodashHelper';
import { scaleUxToDp } from '../../utils/pixelUtils';
import { CaptionMenuItemProps } from './types/Captions';

export const areCaptionMenuItemPropsEqual = (
  prevProps: CaptionMenuItemProps,
  nextProps: CaptionMenuItemProps,
) => {
  const excludedProps = ['onPress', 'testID'];
  return areComponentPropsEqual(prevProps, nextProps, excludedProps);
};

export const CaptionMenuItem = React.memo(
  ({ text, selected, onPress, testID }: CaptionMenuItemProps) => {
    return (
      <FocusableElement
        onPress={onPress}
        accessibilityRole="radio"
        accessibilityLabel={text}
        accessibilityState={{ checked: selected }}
        hasTVPreferredFocus={selected}
        style={[styles.menuItem, selected && styles.selectedMenuItem]}
        onFocusOverrideStyle={styles.focusedMenuItem}
        testID={testID}>
        <Text style={styles.menuItemText} testID={'video-player-caption-menu'}>
          {text}
        </Text>
      </FocusableElement>
    );
  },
  areCaptionMenuItemPropsEqual,
);

const styles = StyleSheet.create({
  menuItemText: {
    color: COLORS.WHITE,
    ...CALM_TEXT.supporting,
    marginVertical: scaleUxToDp(4),
    padding: scaleUxToDp(20),
  },
  menuItem: { borderWidth: scaleUxToDp(FOCUS_RING_WIDTH), borderColor: 'transparent' },
  focusedMenuItem: { backgroundColor: CALM_COLORS.SURFACE_FOCUSED, borderColor: CALM_COLORS.FOCUS_RING },
  selectedMenuItem: { backgroundColor: COLORS.GRAY + '66' },
});
