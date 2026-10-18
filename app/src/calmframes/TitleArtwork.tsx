/** Presentation artwork from the approved design, never a signed playback still. */
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { isBundledBenignStory } from './benignStory';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import { ACADIA_SOURCE_SHA256, concernsPackagedLibrary } from './packagedLibrary';
import { CatalogTitle, CheckedTitle } from './titleStatus';
import { COASTAL_COLORS as CALM_COLORS, scale } from './calmStyles';
import { shelfLabel, shelfPoster } from './shelf';
import { trace } from './trace';

interface TitlePresentation {
  name: string;
  cardName?: string;
  kind?: string;
  action: string;
  description: string;
  runtime?: string;
  attribution?: string;
  /** Decorative menu scenery, independent of video or ambient playback. */
  menuArt?: 'coastal';
  art?: 'harbor' | 'harbor-cinematic' | 'gradient' | 'coastal';
}

export const OTTER_PREVIEW_SOURCE_SHA256 = '4e473dacc78c2a18c01e8fe030fc482da6b7845c326c2f36814b74d98ba454e4';

export function titlePresentation(title: CatalogTitle): TitlePresentation {
  if (concernsPackagedLibrary(title) && title.sha256 === OTTER_PREVIEW_SOURCE_SHA256 && title.durationMs === 4240) {
    return { name: 'Otters · short preview', cardName: 'Otters', kind: 'Short preview · 4.24 seconds',
      action: 'Watch preview', runtime: '4.24 seconds · Silent · Plays once', menuArt: 'coastal',
      description: 'A short excerpt of an otter grooming. Plays once, without sound.',
      attribution: 'Uusijani / Wikimedia Commons. Otter (Lutra lutra) grooming. CC0 1.0. Short excerpt. Source: https://commons.wikimedia.org/wiki/File:Otter_(Lutra_lutra)_grooming.webm' };
  }
  if (concernsPackagedLibrary(title) && title.sha256 === ACADIA_SOURCE_SHA256) {
    return { name: 'Acadia', kind: 'National Park Service', action: 'Watch now', art: 'coastal',
      description: 'Waves along the coast of Acadia National Park.' };
  }
  if (isBundledBenignStory(title)) {
    return { name: 'Harbor', cardName: 'Harbor demo', kind: 'Demo', action: 'Watch demo',
      description: 'A simulated demonstration with two picture pauses. No flashing.', art: 'harbor-cinematic' };
  }
  if (concernsPackagedLibrary(title) && title.title === 'Harbor story (prepared locally)') {
    return { name: 'Harbor', action: 'Watch now',
      description: '', art: 'harbor-cinematic' };
  }
  if (title.id === OFFLINE_TITLE_ID) {
    return { name: 'Calm gradient', kind: 'Playback check', action: 'Watch',
      description: 'A short gradient to check that video plays on this television.', art: 'gradient' };
  }
  const label = shelfLabel(title);
  return { name: label.name, kind: label.qualifier, action: 'Watch now', description: '', art: undefined };
}

export default function TitleArtwork({ entry, testID, compact = false, height, immersive = false, illustrated = false }: { entry: CheckedTitle; testID?: string; compact?: boolean; height?: number; immersive?: boolean; illustrated?: boolean }) {
  const presentation = titlePresentation(entry.title);
  const poster = shelfPoster(entry);
  const source = entry.status === 'verified' && presentation.art
    ? presentation.art === 'coastal' ? require('../../assets/image/tv/acadia-coast.png')
      : presentation.art === 'harbor-cinematic' && !illustrated ? require('../../assets/image/tv/harbor-cinematic.png')
      : (presentation.art === 'harbor' || presentation.art === 'harbor-cinematic') ? require('../../assets/image/tv/harbor-illustrated.png') : require('../../assets/image/tv/gradient.png')
    : poster ? { uri: poster } : undefined;
  const artworkStyle = [styles.art, { height: scale(height ?? (compact ? 220 : 380)) }, immersive ? { borderRadius: 0 } : null];
  return source ? <Image testID={testID} source={source} style={artworkStyle} resizeMode={presentation.art ? 'cover' : 'contain'} fadeDuration={0} accessible={false} onLoad={() => trace('image', `title ${presentation.art ?? 'poster'} loaded`)} onError={() => trace('image', `title ${presentation.art ?? 'poster'} error`)} />
    : <View style={artworkStyle} />;
}
const styles = StyleSheet.create({ art: { width: '100%', borderRadius: scale(20), backgroundColor: CALM_COLORS.SURFACE } });
