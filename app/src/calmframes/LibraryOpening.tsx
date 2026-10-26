/** The real boot and household wait share the same map as the destination shelf. */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import CoastalWorld, { WorldAppearance } from './CoastalWorld';
import CalmPageHeader from './CalmPageHeader';
import JourneyStatus from './JourneyStatus';
import { CALM_FLOW, CALM_SPACE, CALM_TEXT, CALM_WORLD, scale } from './calmStyles';
export default function LibraryOpening({ status, testID }: { status: string; testID: string }) {
  return <WorldAppearance.Provider value><View testID={testID} style={styles.screen}>
    <CoastalWorld detail />
    <CalmPageHeader />
    <View style={styles.copy} accessible accessibilityRole="progressbar" accessibilityLabel={`Calm Frames is opening. ${status}`} accessibilityLiveRegion="polite">
      <Text style={styles.eyebrow}>Ocean & Forest</Text>
      <Text style={styles.heading}>Opening Calm Frames</Text>
      <JourneyStatus status={status} liveStatus={false} />
    </View>
  </View></WorldAppearance.Provider>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_WORLD.BACKGROUND, paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y), overflow: 'hidden' },
  copy: { marginLeft: scale(40), paddingTop: scale(CALM_FLOW.HERO_TOP - 54), width: scale(760) },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_WORLD.TEXT, marginBottom: scale(CALM_SPACE.TIGHT) },
  heading: { ...CALM_TEXT.screen, color: CALM_WORLD.TEXT },
});
