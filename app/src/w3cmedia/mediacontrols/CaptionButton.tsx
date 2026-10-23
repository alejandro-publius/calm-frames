import { TVFocusGuideView } from '@amazon-devices/react-native-kepler';
import React, { useEffect, useRef } from 'react';
import { StyleSheet } from 'react-native';
import { DPADEventType } from '../../constants';
import { CALM_COLORS } from '../../calmframes/calmStyles';
import { areComponentPropsEqual } from '../../utils/lodashHelper';
import PlayerButton from './PlayerButton';
import { CaptionButtonProps } from './types/Captions';

const CaptionEnabledIcon = 'closed-caption';
const CaptionDisabledIcon = 'closed-caption-disabled';
const CaptionUnavailableIcon = 'closed-caption-off';

const CaptionButton = ({
  onPress,
  video,
  captionMenuVisibility,
  testID,
  playerControlType,
  isCaptionButtonFocused,
}: CaptionButtonProps) => {
  const captionsExist = video?.textTracks?.length > 0 ? true : false;
  const captionButtonRef = useRef<any>(null);
  const onBlurCaptionButton = () => {
    captionButtonRef?.current?.blur();
  };
  let CaptionIcon = CaptionUnavailableIcon;
  if (captionsExist) {
    CaptionIcon = CaptionEnabledIcon;
  } else {
    CaptionIcon = CaptionDisabledIcon;
  }
  useEffect(() => {
    if (
      playerControlType === DPADEventType.BACK &&
      !captionMenuVisibility &&
      isCaptionButtonFocused
    ) {
      captionButtonRef.current?.requestTVFocus();
    }
  }, [playerControlType, captionMenuVisibility, isCaptionButtonFocused]);

  return (
    <TVFocusGuideView trapFocusLeft={captionMenuVisibility}>
      <PlayerButton
        accessibilityLabel={captionsExist ? 'Captions' : 'Captions unavailable'}
        accessibilityState={{ expanded: captionMenuVisibility }}
        ref={captionButtonRef}
        onBlur={onBlurCaptionButton}
        onPress={onPress}
        icon={CaptionIcon}
        size={48}
        overrideStyle={
          captionMenuVisibility ? styles.captionSelected : undefined
        }
        testID={testID}
      />
    </TVFocusGuideView>
  );
};
export const areCaptionButtonPropsEqual = (
  prevProps: CaptionButtonProps,
  nextProps: CaptionButtonProps,
) => {
  const excludedProps = ['onPress', 'testID'];
  return areComponentPropsEqual(prevProps, nextProps, excludedProps);
};
export default React.memo(CaptionButton, areCaptionButtonPropsEqual);

const styles = StyleSheet.create({
  captionSelected: {
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
});
