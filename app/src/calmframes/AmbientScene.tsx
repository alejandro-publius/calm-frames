/** A stationary illustration, not a new video edition or a signed playback hold. */
import React from 'react';
import { Image, ImageSourcePropType, StyleSheet, Text, View } from 'react-native';
import { isContinuousScene } from './continuousScene';
import CalmButton from './CalmButton';
import { filmStill } from './HomeHarborScene';
import { CALM_SPACE, CALM_TEXT, CALM_WORLD, scale } from './calmStyles';
import { CheckedTitle } from './titleStatus';
import { titlePresentation } from './TitleArtwork';

export type AmbientArtwork = 'coastal' | 'sea-otters' | 'forest';
export function ambientArtworkFor(entry: CheckedTitle): AmbientArtwork | undefined {
  if (entry.status !== 'verified' || isContinuousScene(entry.title)) return undefined;
  const art = titlePresentation(entry.title);
  return art.menuArt ?? (art.art === 'coastal' ? 'coastal' : undefined);
}

export default function AmbientScene({ title, artwork, onBack, onPreview, previewSeconds, endingPicture, ended = false, testID = 'ambient-scene' }: {
  title: string; artwork: AmbientArtwork; onBack: () => void; onPreview?: () => void;
  previewSeconds?: number; ended?: boolean; testID?: string;
  endingPicture?: ImageSourcePropType;
}) {
  return <View testID={testID} style={styles.screen}>
    <Image testID={`${testID}-picture`} source={endingPicture ?? filmStill(artwork)} style={styles.picture} resizeMode="contain" fadeDuration={0} accessible={false} />
    <View style={styles.caption} accessible accessibilityLabel={`${title}. ${endingPicture ? 'Playback finished. Final frame.' : ended ? 'Preview finished.' : 'Still scene. No motion or audio.'}`}>
      <Text style={styles.title}>{title}</Text>
      {ended || endingPicture ? <Text style={styles.detail}>Finished</Text> : null}
    </View>
    <View style={styles.controls}>
      <CalmButton quiet sound={false} label="Back" testID={`${testID}-back`} hasTVPreferredFocus onPress={onBack} />
      {onPreview ? <CalmButton quiet sound={false} label={`Video preview · ${previewSeconds} sec`} accessibilityLabel={`Optional moving video preview, ${previewSeconds} seconds. May contain scene changes.`} testID={`${testID}-preview`} onPress={onPreview} /> : null}
    </View>
  </View>;
}
const styles = StyleSheet.create({
  // Kepler's bundled images retain their intrinsic size with edge constraints
  // alone. Explicit bounds keep the ending still aligned with the video.
  picture: { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%' },
  screen: { ...StyleSheet.absoluteFillObject, backgroundColor: '#193F3E', zIndex: 50 },
  caption: { position: 'absolute', top: scale(CALM_SPACE.SAFE_Y), left: scale(CALM_SPACE.SAFE_X), backgroundColor: CALM_WORLD.SURFACE, padding: scale(20), borderRadius: scale(12), maxWidth: scale(1500) },
  title: { ...CALM_TEXT.supporting, color: CALM_WORLD.TEXT },
  detail: { ...CALM_TEXT.supporting, color: CALM_WORLD.TEXT },
  controls: { position: 'absolute', bottom: scale(CALM_SPACE.SAFE_Y), left: scale(CALM_SPACE.SAFE_X), flexDirection: 'row', gap: scale(CALM_SPACE.ROW), backgroundColor: CALM_WORLD.SURFACE, padding: scale(12), borderRadius: scale(12) },
});
