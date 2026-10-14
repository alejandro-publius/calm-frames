// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import MaterialIcons from '@amazon-devices/react-native-vector-icons/MaterialIcons';
import React from 'react';
import { StyleProp, StyleSheet, Text, ViewStyle } from 'react-native';
import { CALM_COLORS, FOCUS_RING_WIDTH } from '../calmframes/calmStyles';
import { COLORS } from '../styles/Colors';
import { areComponentPropsEqual } from '../utils/lodashHelper';
import { scaleUxToDp } from '../utils/pixelUtils';
import FocusableElement from './FocusableElement';

interface BackButtonProps {
  onPress: () => void;
  overrideStyle?: StyleProp<ViewStyle>;
  hasTVPreferredFocus: boolean;
}

const BackButton = ({
  onPress,
  overrideStyle,
  hasTVPreferredFocus,
}: BackButtonProps) => {
  return (
    <FocusableElement
      accessibilityRole="button"
      accessibilityLabel="Back"
      hasTVPreferredFocus={hasTVPreferredFocus}
      style={[styles.backButtonContainer, overrideStyle]}
      onFocusOverrideStyle={styles.backButtonFocus}
      onPress={onPress}>
      <Text testID={'header_back_icon'}>
        <MaterialIcons name={'chevron-left'} size={scaleUxToDp(48)} color={COLORS.WHITE} />
      </Text>
    </FocusableElement>
  );
};

const areBackButtonPropsEqual = (
  prevProps: BackButtonProps,
  nextProps: BackButtonProps,
) => {
  const excludedProps = ['onPress'];
  return areComponentPropsEqual(prevProps, nextProps, excludedProps);
};

export default React.memo(BackButton, areBackButtonPropsEqual);

const styles = StyleSheet.create({
  backButtonImage: {
    height: scaleUxToDp(70),
    width: scaleUxToDp(70),
    resizeMode: 'contain',
    tintColor: COLORS.WHITE,
  },
  backButtonContainer: {
    padding: scaleUxToDp(12),
    alignItems: 'center',
    flexDirection: 'row',
    borderWidth: scaleUxToDp(FOCUS_RING_WIDTH),
    borderColor: 'transparent',
    borderRadius: scaleUxToDp(42),
  },
  backButtonFocus: {
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
    borderColor: CALM_COLORS.FOCUS_RING,
    borderRadius: scaleUxToDp(70),
  },
});
