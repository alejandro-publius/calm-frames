/**
 * The cover: the view that hides the picture while sound and captions keep
 * going.
 *
 * It sits above the video surface (zIndex 0) and below the captions view
 * (zIndex 2), which is what lets a caption stay readable over a hidden
 * picture. It is driven by state, never by setNativeProps, which throws on
 * React Native 0.83.
 *
 * A reference patch can be left uncovered. The camera harness films that patch
 * to know, frame by frame, that the recording is of a running screen rather
 * than a frozen or blanked one, so the cover is drawn as four rectangles
 * around it rather than one full-screen rectangle.
 */

import React from 'react';
import { Image, StyleSheet, Text, View, ImageSourcePropType } from 'react-native';
import { trace } from './trace';
import { CALM_COLORS, CALM_TEXT, scale } from './calmStyles';

export interface ReferencePatch {
  /** Distance from the left edge of the screen, in pixels. */
  x: number;
  /** Distance from the top edge of the screen, in pixels. */
  y: number;
  width: number;
  height: number;
}

export interface CoverLayerProps {
  visible: boolean;
  /** Static opaque presentation for a scheduled cover with no signed still. */
  calmFallback?: boolean;
  /** Checked creator text for the current immutable base cover; never a new schedule. */
  sceneBridge?: { text: string; label: 'Creator note' | 'Scene bridge test' };
  /**
   * Opaque hides the picture completely. Dim is only ever allowed for general
   * (non-red) segments at 90% or darker, and the pipeline's verify step has to
   * model it, so the default is opaque.
   */
  mode?: 'opaque' | 'dim';
  /** Opacity for dim mode, 0.9 or higher. */
  dimOpacity?: number;
  /** A still from a verified signed scene hold, never an unchecked URL. */
  imageUri?: string;
  /** A bundled copy of exactly that still, for a device that cannot draw a data URI. */
  imageSource?: ImageSourcePropType;
  /** Screen area to leave uncovered for the camera harness. */
  referencePatch?: ReferencePatch;
  screenWidth?: number;
  screenHeight?: number;
  testID?: string;
}

export const COVER_Z_INDEX = 1;

const CoverLayer = ({
  visible,
  calmFallback = false,
  sceneBridge,
  mode = 'opaque',
  dimOpacity = 0.9,
  imageUri,
  imageSource,
  referencePatch,
  screenWidth,
  screenHeight,
  testID = 'calm-frames-cover',
}: CoverLayerProps) => {
  if (!visible) {
    return null;
  }

  const opacity = mode === 'dim' ? Math.max(0.9, dimOpacity) : 1;
  const showFallback = calmFallback && mode === 'opaque' && !imageUri && !referencePatch;
  const coverOpacity = imageUri ? 1 : opacity;
  const bridge = showFallback && sceneBridge &&
    (sceneBridge.label === 'Creator note' || sceneBridge.label === 'Scene bridge test') &&
    typeof sceneBridge.text === 'string' && sceneBridge.text.length > 0 && sceneBridge.text.length <= 120 &&
    sceneBridge.text === sceneBridge.text.trim() && sceneBridge.text.split(/\s+/u).length <= 20 &&
    !/[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u2028-\u202e\u2060-\u206f<>]/u.test(sceneBridge.text)
    ? sceneBridge : undefined;

  if (
    !referencePatch ||
    screenWidth === undefined ||
    screenHeight === undefined
  ) {
    return (
      <View
        testID={testID}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        style={[styles.fill, showFallback ? styles.calmFill : null, { opacity: coverOpacity }]} pointerEvents="none">
        {showFallback && bridge ? <View testID={`${testID}-fallback`} style={styles.message}>
          <Text style={styles.messageTitle}>{bridge ? bridge.label : 'This scene is covered'}</Text>
          {bridge ? <Text testID={`${testID}-bridge`} style={styles.bridgeText}>{bridge.text}</Text> : null}
          <Text style={styles.messageDetail}>You can wait or choose Skip.</Text>
        </View> : null}
        {imageUri && !referencePatch ? (
          <SceneStill
            key={imageUri}
            uri={imageUri}
            source={imageSource}
            testID={`${testID}-still`}
          />
        ) : null}
      </View>
    );
  }

  // Four rectangles around the patch: above, below, left of it and right of
  // it. Together they cover everything except the patch.
  const patchRight = referencePatch.x + referencePatch.width;
  const patchBottom = referencePatch.y + referencePatch.height;

  return (
    <View testID={testID} style={styles.container} pointerEvents="none">
      <View
        testID={`${testID}-top`}
        style={[
          styles.piece,
          {
            opacity,
            left: 0,
            top: 0,
            width: screenWidth,
            height: referencePatch.y,
          },
        ]}
      />
      <View
        testID={`${testID}-bottom`}
        style={[
          styles.piece,
          {
            opacity,
            left: 0,
            top: patchBottom,
            width: screenWidth,
            height: Math.max(0, screenHeight - patchBottom),
          },
        ]}
      />
      <View
        testID={`${testID}-left`}
        style={[
          styles.piece,
          {
            opacity,
            left: 0,
            top: referencePatch.y,
            width: referencePatch.x,
            height: referencePatch.height,
          },
        ]}
      />
      <View
        testID={`${testID}-right`}
        style={[
          styles.piece,
          {
            opacity,
            left: patchRight,
            top: referencePatch.y,
            width: Math.max(0, screenWidth - patchRight),
            height: referencePatch.height,
          },
        ]}
      />
    </View>
  );
};

/** A new URI mounts a fresh native image; failure leaves its black parent intact. */
const SceneStill = ({ uri, source, testID }: { uri: string; source?: ImageSourcePropType; testID: string }) => {
  const [failed, setFailed] = React.useState(false);
  if (failed) {
    return null;
  }
  return (
    <Image
      testID={testID}
      source={source ?? { uri }}
      style={StyleSheet.absoluteFill}
      resizeMode="contain"
      fadeDuration={0}
      accessible={false}
      onLoad={() => trace('still', 'loaded')}
      onError={() => { trace('still', 'error'); setFailed(true); }}
    />
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    top: 0,
    right: 0,
    bottom: 0,
    zIndex: COVER_Z_INDEX,
  },
  fill: {
    position: 'absolute',
    left: 0,
    top: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#000000',
    zIndex: COVER_Z_INDEX,
  },
  calmFill: { backgroundColor: CALM_COLORS.SURFACE },
  // Above the caption band and separate from the bottom-left Skip control.
  message: { position: 'absolute', top: scale(360), left: scale(96), right: scale(96), alignItems: 'center' },
  messageTitle: { ...CALM_TEXT.control, color: CALM_COLORS.TEXT, textAlign: 'center' },
  bridgeText: { ...CALM_TEXT.control, color: CALM_COLORS.TEXT, textAlign: 'center', maxWidth: scale(1000), marginTop: scale(16) },
  messageDetail: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'center', marginTop: scale(12) },
  piece: {
    position: 'absolute',
    backgroundColor: '#000000',
  },
});

export default CoverLayer;
