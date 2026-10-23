import React from 'react';
import { StyleSheet, Text } from 'react-native';
import FocusableElement from '../../components/FocusableElement';
import { CALM_CONTROL, CALM_COLORS, CALM_TEXT, FOCUS_RING_WIDTH } from '../../calmframes/calmStyles';
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
        <Text accessible={false} style={styles.check}>{selected ? '✓' : ''}</Text>
        <Text numberOfLines={2} style={styles.menuItemText} testID={'video-player-caption-menu'}>
          {text}
        </Text>
      </FocusableElement>
    );
  },
  areCaptionMenuItemPropsEqual,
);

const styles = StyleSheet.create({
  menuItemText: {
    color: CALM_COLORS.TEXT,
    ...CALM_TEXT.supporting,
    marginVertical: scaleUxToDp(4),
    paddingVertical: scaleUxToDp(20),
    paddingHorizontal: scaleUxToDp(12),
    flex: 1,
    flexShrink: 1,
  },
  check: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT, width: scaleUxToDp(42), textAlign: 'center' },
  menuItem: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: scaleUxToDp(12), borderRadius: scaleUxToDp(CALM_CONTROL.RADIUS), borderWidth: scaleUxToDp(FOCUS_RING_WIDTH), borderColor: 'transparent' },
  focusedMenuItem: { backgroundColor: CALM_COLORS.SURFACE_FOCUSED, borderColor: CALM_COLORS.FOCUS_RING },
  selectedMenuItem: { backgroundColor: CALM_COLORS.SURFACE_FOCUSED },
});
