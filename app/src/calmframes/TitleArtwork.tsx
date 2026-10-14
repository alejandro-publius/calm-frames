/** Presentation artwork from the approved design, never a signed playback still. */
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { isBundledBenignStory } from './benignStory';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import { concernsPackagedLibrary } from './packagedLibrary';
import { CatalogTitle, CheckedTitle } from './titleStatus';
import { COASTAL_COLORS as CALM_COLORS, scale } from './calmStyles';
import { shelfLabel, shelfPoster } from './shelf';

interface TitlePresentation {
  name: string;
  cardName?: string;
  kind?: string;
  action: string;
  description: string;
  art?: 'harbor' | 'harbor-cinematic' | 'gradient';
}

export function titlePresentation(title: CatalogTitle): TitlePresentation {
  if (isBundledBenignStory(title)) {
    return { name: 'Harbor', cardName: 'Harbor demo', kind: 'Practice holds', action: 'Watch demo',
      description: 'Two scheduled practice holds show how the picture pauses while sound and captions continue.', art: 'harbor-cinematic' };
  }
  if (concernsPackagedLibrary(title) && title.title === 'Harbor story (prepared locally)') {
    return { name: 'Harbor', action: 'Watch now',
      description: '', art: 'harbor-cinematic' };
  }
  if (title.id === OFFLINE_TITLE_ID) {
    return { name: 'Calm gradient', kind: 'Playback test', action: 'Play',
      description: 'Use this short gradient clip to check picture playback and navigation.', art: 'gradient' };
  }
  const label = shelfLabel(title);
  return { name: label.name, kind: label.qualifier, action: 'Watch now', description: '', art: undefined };
}

export default function TitleArtwork({ entry, testID, compact = false, height, immersive = false, illustrated = false }: { entry: CheckedTitle; testID?: string; compact?: boolean; height?: number; immersive?: boolean; illustrated?: boolean }) {
  const presentation = titlePresentation(entry.title);
  const poster = shelfPoster(entry);
  const source = entry.status === 'verified' && presentation.art
    ? presentation.art === 'harbor-cinematic' && !illustrated ? require('../../assets/image/tv/harbor-cinematic.png')
      : (presentation.art === 'harbor' || presentation.art === 'harbor-cinematic') ? require('../../assets/image/tv/harbor-illustrated.png') : require('../../assets/image/tv/gradient.png')
    : poster ? { uri: poster } : undefined;
  const artworkStyle = [styles.art, { height: scale(height ?? (compact ? 220 : 380)) }, immersive ? { borderRadius: 0 } : null];
  return source ? <Image testID={testID} source={source} style={artworkStyle} resizeMode={presentation.art ? 'cover' : 'contain'} fadeDuration={0} accessible={false} />
    : <View style={artworkStyle} />;
}
const styles = StyleSheet.create({ art: { width: '100%', borderRadius: scale(20), backgroundColor: CALM_COLORS.SURFACE } });
