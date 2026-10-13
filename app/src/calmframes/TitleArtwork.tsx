/** Presentation artwork from the approved design, never a signed playback still. */
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { isBundledBenignStory } from './benignStory';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import { concernsPackagedLibrary } from './packagedLibrary';
import { CatalogTitle, CheckedTitle } from './titleStatus';
import { CALM_COLORS, scale } from './calmStyles';
import { shelfLabel, shelfPoster } from './shelf';

interface TitlePresentation {
  name: string;
  cardName?: string;
  kind?: string;
  action: string;
  description: string;
  /** Short introduction for browsing; details keep the full description. */
  browseSynopsis?: string;
  art?: 'harbor' | 'harbor-cinematic' | 'gradient';
}

export function titlePresentation(title: CatalogTitle): TitlePresentation {
  if (isBundledBenignStory(title)) {
    return { name: 'Harbor: Scene hold demo', cardName: 'Harbor demo', kind: 'Practice holds', action: 'Watch demo',
      description: 'This version adds practice holds to Harbor at set times so you can see how a hide works during playback. The holds are practice, not detected flashing.', art: 'harbor' };
  }
  if (concernsPackagedLibrary(title) && title.title === 'Harbor story (prepared locally)') {
    return { name: 'Harbor', kind: 'Checked story', action: 'Watch now',
      browseSynopsis: 'An original demo film following a small boat home through a quiet harbor.',
      description: 'A small boat finds its way home through a quiet harbor. Our own demo film, prepared and checked the way a real title is, with no practice holds.', art: 'harbor-cinematic' };
  }
  if (title.id === OFFLINE_TITLE_ID) {
    return { name: 'Calm gradient', kind: 'Playback test', action: 'Play',
      description: 'Use this short gradient clip to check picture playback and navigation.', art: 'gradient' };
  }
  const label = shelfLabel(title);
  return { name: label.name, kind: label.qualifier, action: 'Watch now', description: '', art: undefined };
}

export default function TitleArtwork({ entry, testID, compact = false, height, immersive = false }: { entry: CheckedTitle; testID?: string; compact?: boolean; height?: number; immersive?: boolean }) {
  const presentation = titlePresentation(entry.title);
  const poster = shelfPoster(entry);
  const source = entry.status === 'verified' && presentation.art
    ? presentation.art === 'harbor-cinematic' ? require('../../assets/image/tv/harbor-cinematic.png')
      : presentation.art === 'harbor' ? require('../../assets/image/tv/harbor.png') : require('../../assets/image/tv/gradient.png')
    : poster ? { uri: poster } : undefined;
  const artworkStyle = [styles.art, { height: scale(height ?? (compact ? 220 : 380)) }, immersive ? { borderRadius: 0 } : null];
  return source ? <Image testID={testID} source={source} style={artworkStyle} resizeMode={presentation.art ? 'cover' : 'contain'} fadeDuration={0} accessible={false} />
    : <View style={artworkStyle} />;
}
const styles = StyleSheet.create({ art: { width: '100%', borderRadius: scale(20), backgroundColor: CALM_COLORS.SURFACE } });
