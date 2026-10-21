import React from 'react';
import { CoastalAppearance } from './CoastalAppearance';
import { StyleSheet, Text, View } from 'react-native';
import CoastalWorld, { WorldAppearance, WORLD } from './CoastalWorld';
import { islandKind } from './CoastalIsland';
import CalmPageHeader from './CalmPageHeader';
import JourneyStatus from './JourneyStatus';
import { CALM_FLOW, CALM_SPACE, CALM_TEXT, heroTitleTypography, scale } from './calmStyles';
/**
 * liveStatus is false only for the route's loading stand-in
 * (playerRouteFallback.tsx), so the status is announced once, by the player.
 *
 * The title sits where the Details title sits, so Watch does not move the
 * words on screen: the eyebrow above it takes its own line height and margin
 * out of the hero offset.
 */
const EYEBROW_MARGIN = 12;
/** CALM_TEXT.supporting's line height in 1080p units; test/calmframes/openingAlignment.test.tsx pins it. */
export const EYEBROW_LINE_HEIGHT = 42;
export const OPENING_COPY_TOP = CALM_FLOW.HERO_TOP - (EYEBROW_LINE_HEIGHT + EYEBROW_MARGIN);
export default function PlayerOpening({ menuArt, title, onBack, returning = false, liveStatus = true, checking = false, motionEnabled = false }: { menuArt?: string; title: string; onBack: () => void; returning?: boolean; liveStatus?: boolean; checking?: boolean; motionEnabled?: boolean }) {
  return <CoastalAppearance.Provider value><WorldAppearance.Provider value><View testID="player-home-opening" style={styles.screen}>
    <CoastalWorld detail destination={islandKind(menuArt)} />
    <CalmPageHeader onBack={!returning ? onBack : undefined} backLabel="Back" backTestID="player-opening-back" preferredBack />
    <View style={styles.copy}>
      <Text style={styles.eyebrow}>{menuArt === 'forest' ? 'Forest' : menuArt === 'coastal' || menuArt === 'sea-otters' ? 'Ocean' : 'Calm Frames'}</Text>
      <Text style={[styles.title, heroTitleTypography(title)]}>{title}</Text>
      <JourneyStatus forest={islandKind(menuArt) === 'forest'} motionEnabled={motionEnabled && !returning} liveStatus={liveStatus}
        status={returning ? 'Going back...' : checking ? 'Checking this video...' : 'Opening your video...'} />

    </View>
  </View></WorldAppearance.Provider></CoastalAppearance.Provider>;
}
const styles = StyleSheet.create({
  screen: { ...StyleSheet.absoluteFillObject, zIndex: 30, backgroundColor: WORLD.BACKGROUND, paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y) },
  brand: { flexDirection: 'row', gap: scale(20), alignItems: 'center', height: scale(80) },
  mark: { width: scale(80), height: scale(80) }, wordmark: { ...CALM_TEXT.control, color: WORLD.TEXT },
  copy: { marginLeft: scale(40), paddingTop: scale(OPENING_COPY_TOP), width: scale(CALM_FLOW.HERO_TITLE_WIDTH) },
  eyebrow: { ...CALM_TEXT.supporting, color: WORLD.TEXT_DIM, marginBottom: scale(EYEBROW_MARGIN) },
  title: { color: WORLD.TEXT, marginBottom: scale(12) },
  detail: { ...CALM_TEXT.supporting, color: WORLD.TEXT_DIM, minHeight: scale(84), marginBottom: scale(24) },
  actions: { flexDirection: 'row', gap: scale(20), alignItems: 'center' },
});
