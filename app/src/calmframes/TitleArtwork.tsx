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
  selectorMeta?: string;
  action: string;
  description: string;
  runtime?: string;
  attribution?: string;
  /** Decorative menu scenery, independent of video or ambient playback. */
  menuArt?: 'coastal' | 'sea-otters' | 'forest';
  art?: 'harbor' | 'harbor-cinematic' | 'gradient' | 'coastal';
}

export const SEA_OTTER_SOURCE_SHA256 = '02c2b0c0674262862ad9d02a7107e421c398aac0b06bfc4fff04098d32ebe4d6';
export const FOREST_SOURCE_SHA256 = '63432b83ef15c0614d1fd80b4a899d4227a6703a0b847cb194f7ba6725b8454c';

export function titlePresentation(title: CatalogTitle): TitlePresentation {
  if (concernsPackagedLibrary(title) && title.sha256 === FOREST_SOURCE_SHA256 && title.durationMs === 12000) {
    return { name: 'Forest creek at Redwood', cardName: 'Forest', kind: 'Redwood creek · 12 seconds',
      selectorMeta: 'Nature audio · 12 sec', action: 'Watch now', runtime: '12 seconds · Nature sounds · Plays once', menuArt: 'forest',
      description: 'A redwood tree beside a quiet creek in Redwood National and State Parks.',
      attribution: 'NPS: G Litten. Prairie Creek and Redwood. Public-domain footage; 12-second excerpt with original nature audio, plays once. No NPS endorsement implied. Source: https://www.nps.gov/media/video/view.htm?id=F2E1744E-F295-B2E5-52AF33C2205A8C9E' };
  }
  if (concernsPackagedLibrary(title) && title.sha256 === SEA_OTTER_SOURCE_SHA256 && title.durationMs === 19986.633) {
    return { name: 'Sea otters in Alaska', cardName: 'Sea otters', kind: 'Ocean wildlife · 20 seconds',
      selectorMeta: 'Silent · 20 seconds', action: 'Watch now', runtime: '20 seconds · Silent · Plays once', menuArt: 'sea-otters',
      description: 'Sea otters float together in the ocean at Unalaska, Alaska.',
      attribution: 'NOAA Fisheries. Sea otters at Unalaska/Dutch Harbor, Alaska. Public-domain B-roll; 19.987-second silent excerpt, plays once. Source: https://videos.fisheries.noaa.gov/detail/video/2789953172001/b-roll%3A-sea-otters' };
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
