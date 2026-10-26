import { TVFocusGuideView } from '@amazon-devices/react-native-kepler';
import React, { useCallback, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CAPTION_DISABLE_ID, CAPTION_DISABLE_TEXT } from '../../constants';
import { CALM_COLORS, CALM_TEXT } from '../../calmframes/calmStyles';
import { areComponentPropsEqual } from '../../utils/lodashHelper';
import { scaleUxToDp } from '../../utils/pixelUtils';
import { CaptionMenuItem } from './CaptionMenuItem';
import { CaptionOptions } from './CaptionOptions';
import { CaptionMenuProps } from './types/Captions';

export const areCaptionMenuPropsEqual = (
  prevProps: CaptionMenuProps,
  nextProps: CaptionMenuProps,
) => {
  const excludedProps = ['setSelectedCaption', 'setCaptionMenuVisibility'];
  return areComponentPropsEqual(prevProps, nextProps, excludedProps);
};

export const CaptionMenu = React.memo(
  ({
    captionMenuVisibility,
    video,
    setSelectedCaption,
    setCaptionMenuVisibility,
    selectedCaptionId,
  }: CaptionMenuProps) => {
    const [ownCaptionID, setCaptionID] = useState<string>(CAPTION_DISABLE_ID);
    // Calm Frames: the player turns a title's captions on by itself, so the
    // id it passes down is the one showing. Starting from the menu's own Off
    // instead would mark Off as chosen while a track played, and Off would
    // then leave that track running.
    const captionID = selectedCaptionId ?? ownCaptionID;

    const removeCurrentCaption = useCallback(() => {
      if (captionID !== CAPTION_DISABLE_ID) {
        console.log('Disabling Captions');
        const current = video?.textTracks?.getTrackById(captionID);
        if (current) {
          current.mode = 'hidden';
        }
      }
      setCaptionID(CAPTION_DISABLE_ID);
    }, [captionID, video]);

    const enableCaption = useCallback(
      (id: string) => {
        if (id === captionID) {
          setCaptionMenuVisibility(false);
          return;
        }
        removeCurrentCaption();
        if (video && video.textTracks) {
          video.textTracks.getTrackById(id)!.mode = 'showing';
          setCaptionID(id);
          setSelectedCaption(id);
        }
        setCaptionID(id);
        setSelectedCaption(id);
        setCaptionMenuVisibility(false);
      },
      [
        captionID,
        removeCurrentCaption,
        video,
        setSelectedCaption,
        setCaptionMenuVisibility,
      ],
    );

    const turnOffCaptions = useCallback(() => {
      setSelectedCaption(CAPTION_DISABLE_ID);
      removeCurrentCaption();
      setCaptionMenuVisibility(false);
    }, [setSelectedCaption, removeCurrentCaption, setCaptionMenuVisibility]);

    return (
      <TVFocusGuideView trapFocusLeft trapFocusRight trapFocusUp>
        {captionMenuVisibility ? (
          <View style={styles.menu}><Text style={styles.heading} accessibilityRole="header">Captions</Text>
            <CaptionOptions
              video={video}
              enableCaption={enableCaption}
              selectedCaptionId={captionID}
            />
            <CaptionMenuItem
              key={CAPTION_DISABLE_TEXT}
              text={CAPTION_DISABLE_TEXT}
              onPress={turnOffCaptions}
              selected={captionID === CAPTION_DISABLE_ID}
              testID={'caption-menu-focus-element'}
            />
          </View>
        ) : null}
      </TVFocusGuideView>
    );
  },
  areCaptionMenuPropsEqual,
);

const styles = StyleSheet.create({
  menu: {
    backgroundColor: CALM_COLORS.SURFACE,
    width: scaleUxToDp(480),
    justifyContent: 'center',
    zIndex: 30,
    borderRadius: scaleUxToDp(24),
    padding: scaleUxToDp(12),
    overflow: 'hidden',
  },
  heading: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, padding: scaleUxToDp(20) },
});
