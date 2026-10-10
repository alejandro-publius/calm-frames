/** Presentation artwork from the approved design, never a signed playback still. */
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { isBundledBenignStory } from './benignStory';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import { concernsPackagedLibrary } from './packagedLibrary';
import { CatalogTitle, CheckedTitle } from './titleStatus';
import { CALM_COLORS, scale } from './calmStyles';
import { shelfLabel, shelfPoster } from './shelf';

export function titlePresentation(title: CatalogTitle) {
  if (isBundledBenignStory(title)) {
    return { name: 'Harbor: Scene hold demo', kind: 'Scheduled scene holds', action: 'Watch demo',
      description: 'This version adds scheduled scene holds to Harbor so you can see how they work during playback.', art: 'harbor' };
  }
  if (concernsPackagedLibrary(title) && title.title === 'Harbor story (prepared locally)') {
    return { name: 'Harbor', kind: 'Original story', action: 'Watch now',
      description: 'A small boat makes its way through a quiet harbor and carries on toward home.', art: 'harbor' };
  }
  if (title.id === OFFLINE_TITLE_ID) {
    return { name: 'Calm gradient', kind: 'Playback test', action: 'Play',
      description: 'Use this short gradient clip to check picture playback and navigation.', art: 'gradient' };
  }
  const label = shelfLabel(title);
  return { name: label.name, kind: label.qualifier, action: 'Watch now', description: '', art: undefined };
}

export default function TitleArtwork({ entry, testID, compact = false }: { entry: CheckedTitle; testID?: string; compact?: boolean }) {
  const presentation = titlePresentation(entry.title);
  const poster = shelfPoster(entry);
  const source = entry.status === 'verified' && presentation.art
    ? presentation.art === 'harbor' ? require('../../assets/image/tv/harbor.png') : require('../../assets/image/tv/gradient.png')
    : poster ? { uri: poster } : undefined;
  return source ? <Image testID={testID} source={source} style={[styles.art, { height: scale(compact ? 160 : 380) }]} resizeMode={presentation.art ? 'cover' : 'contain'} fadeDuration={0} accessible={false} />
    : <View style={[styles.art, { height: scale(compact ? 160 : 380) }]} />;
}
const styles = StyleSheet.create({ art: { width: '100%', borderRadius: scale(20), backgroundColor: CALM_COLORS.SURFACE } });
