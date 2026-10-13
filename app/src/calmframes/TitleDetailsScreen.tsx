/**
 * The details page, with the still flash map strip.
 *
 * It says what the check found before anything plays: how many parts will be
 * hidden, how long they add up to and where they fall. No video preview.
 *
 * A title that did not verify gets this page too, and that is the point of it.
 * Instead of the strip and a summary it shows one notice saying what happened
 * and that the picture stays hidden, and the play control is drawn as
 * unavailable rather than left out, so nobody hunts for it. There is no state
 * of this screen where an unverified title can be started.
 */

import LinearGradient from '@amazon-devices/react-linear-gradient';
import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import CalmArtworkMotion from './CalmArtworkMotion';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { noticeForTitle } from './copy';
import { buildCoverIntervals, totalCoveredMs } from './coverSchedule';
import FlashMapStrip from './FlashMapStrip';
import {
  coverOptionsFor,
  DEFAULT_SETTINGS,
  HouseholdSettings,
} from './household';
import TitleArtwork, { titlePresentation } from './TitleArtwork';
import StatusNotice from './StatusNotice';
import { CheckedTitle } from './titleStatus';
import { useUiCapture } from './uiCapture';
import { TITLE_DETAILS_BLOCKED_FRAME, TITLE_DETAILS_FRAME } from './uiFrames';
import ViewingPlan from './ViewingPlan';
import {
  benignStorySettings,
  isBundledBenignStory,
} from './benignStory';

export interface TitleDetailsScreenProps {
  entry: CheckedTitle;
  settings?: HouseholdSettings;
  onPlay: (entry: CheckedTitle) => void;
  saving?: boolean;
  onBack?: () => void;
  testID?: string;
  interfaceMotionEnabled?: boolean;
  interfaceActive?: boolean;
}

const TitleDetailsScreen = ({
  entry,
  settings: householdSettings = DEFAULT_SETTINGS,
  onPlay,
  saving = false,
  onBack,
  testID = 'title-details',
  interfaceMotionEnabled = false,
  interfaceActive = true,
}: TitleDetailsScreenProps) => {
  const settings = React.useMemo(
    () => benignStorySettings(entry.title, householdSettings),
    [entry.title, householdSettings],
  );
  const durationMs = entry.title.durationMs ?? 0;
  const intervals = React.useMemo(
    () =>
      buildCoverIntervals(entry.segments, {
        ...coverOptionsFor(settings),
        durationMs: durationMs > 0 ? durationMs : undefined,
      }),
    [entry.segments, settings, durationMs],
  );
  const notice = noticeForTitle(entry);
  const playable = notice === null;
  useUiCapture(
    playable ? TITLE_DETAILS_FRAME : TITLE_DETAILS_BLOCKED_FRAME,
    playable ? 'title details' : 'title details, not ready',
  );

  const presentation = titlePresentation(entry.title);
  const demo = isBundledBenignStory(entry.title);
  const hiddenSeconds = Math.round(totalCoveredMs(intervals) / 1000);

  return (
    <ScrollView
      testID={testID}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      {onBack ? <View style={styles.navigation}><CalmButton quiet testID={`${testID}-back`} label="Back to library" onPress={onBack} /></View> : null}
      <View style={styles.hero}>
        <View style={styles.heroArt} pointerEvents="none">
          <CalmArtworkMotion enabled={interfaceMotionEnabled} active={interfaceActive} testID={`${testID}-hero-motion`}>
            <TitleArtwork immersive entry={entry} height={480} testID={`${testID}-artwork`} />
          </CalmArtworkMotion>
          <LinearGradient pointerEvents="none" colors={[CALM_COLORS.BACKGROUND, '#102F3A00']}
            start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.artSky} />
          <LinearGradient pointerEvents="none" colors={['#102F3A00', CALM_COLORS.BACKGROUND]}
            start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.artFloor} />
          <LinearGradient pointerEvents="none" colors={['#102F3A00', CALM_COLORS.BACKGROUND]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.artEdge} />
        </View>
        <View style={styles.heroCopy}>
          <View style={styles.kicker}>
            <Text style={styles.eyebrow}>{presentation.kind}</Text>
          </View>
          <Text style={[styles.title, presentation.name.length > 20 ? styles.longTitle : null]} testID={`${testID}-title`}>{presentation.name}</Text>
          {presentation.description ? <Text style={styles.synopsis} testID={demo ? `${testID}-demo-label` : `${testID}-description`}>{presentation.description}</Text> : null}
          <View style={styles.buttons}>
            <CalmButton primary sound={false} testID={`${testID}-play`} label={saving ? 'Saving your changes...' : playable ? presentation.action : 'Unavailable'}
              accessibilityLabel={saving ? 'Saving your changes...' : playable ? `${presentation.action}: ${presentation.name}` : `${presentation.name} is unavailable. ${notice?.detail ?? ''}`}
              disabled={!playable || saving} hasTVPreferredFocus onPress={() => onPlay(entry)} />
          </View>
        </View>
      </View>

      {notice ? (
        <View style={styles.block}>
          <StatusNotice testID={`${testID}-notice`} notice={notice} />
        </View>
      ) : (
        <>
          <View style={styles.checkSummary}>
            <View style={styles.chapterHeading}>
              <Text style={styles.section} accessibilityRole="header">{demo ? 'About this demo' : 'Before you watch'}</Text>
            </View>
            <View style={styles.chapterContent}>
              {demo ? <Text style={styles.summary}>Harbor was created without flashing effects. The two picture holds are scheduled demonstrations.</Text> : null}
              <Text style={styles.summary} testID={`${testID}-summary`}>
                {intervals.length === 0
                  ? 'This story plays without picture holds. Some flashing may still go undetected.'
                  : `${intervals.length} ${demo ? 'scheduled hold' : 'part'}${
                      intervals.length === 1 ? '' : 's'
                    } ${demo ? (intervals.length === 1 ? 'is included' : 'are included') : 'will be hidden'}, ${hiddenSeconds} second${
                      hiddenSeconds === 1 ? '' : 's'
                    } in all.${demo ? '' : ' Sound and captions keep playing.'}`}
              </Text>

              {durationMs > 0 ? (
                <View style={styles.timeline}>
                  <Text style={styles.timelineLabel}>Picture timeline</Text>
                  <FlashMapStrip
                    width={1040}
                    showCaption={false}
                    intervals={intervals}
                    durationMs={durationMs}
                    testID={`${testID}-strip`}
                  />
                </View>
              ) : null}
            </View>
          </View>

          <View style={styles.viewingChapter}>
            <ViewingPlan
              entry={entry}
              settings={settings}
              testID={`${testID}-plan`}
            />
          </View>
        </>
      )}

      {onBack ? <View style={styles.footer}><CalmButton quiet testID={`${testID}-back-bottom`} label="Back to library" onPress={onBack} /></View> : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND },
  content: { paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y), alignItems: 'center' },
  navigation: { width: '100%', maxWidth: scale(1440), alignItems: 'flex-start', marginBottom: scale(16) },
  hero: { width: '100%', maxWidth: scale(1440), alignItems: 'center', overflow: 'hidden' },
  heroCopy: { width: '100%', maxWidth: scale(1000), alignItems: 'center', paddingTop: scale(12) },
  heroArt: { width: '100%', maxWidth: scale(1280) },
  artSky: { position: 'absolute', top: 0, left: 0, right: 0, height: scale(56) },
  artFloor: { position: 'absolute', bottom: 0, left: 0, right: 0, height: scale(160) },
  artEdge: { position: 'absolute', top: 0, bottom: 0, right: 0, width: scale(120) },
  kicker: { alignItems: 'center', marginBottom: scale(8) },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.FOCUS_RING, textAlign: 'center' },
  title: { ...CALM_TEXT.feature, fontSize: scale(84), lineHeight: scale(96), color: CALM_COLORS.TEXT, marginBottom: scale(16), textAlign: 'center' },
  longTitle: { fontSize: scale(72), lineHeight: scale(84) },
  synopsis: { ...CALM_TEXT.body, fontSize: scale(32), lineHeight: scale(44), color: CALM_COLORS.TEXT_DIM, textAlign: 'center' },
  summary: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM, textAlign: 'center' },
  section: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT, textAlign: 'center' },
  checkSummary: { width: '100%', maxWidth: scale(1040), gap: scale(24), marginTop: scale(72) },
  chapterHeading: { alignItems: 'center' },
  chapterContent: { gap: scale(24) },
  timeline: { marginTop: scale(8) },
  timelineLabel: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, marginBottom: scale(12), textAlign: 'center' },
  viewingChapter: { width: '100%', maxWidth: scale(1040), marginTop: scale(56) },
  block: { width: '100%', maxWidth: scale(1040), marginTop: scale(CALM_SPACE.BLOCK) },
  buttons: { flexDirection: 'row', justifyContent: 'center', marginTop: scale(24) },
  footer: { width: '100%', maxWidth: scale(1040), alignItems: 'center', marginTop: scale(40), paddingTop: scale(24), borderTopWidth: scale(1), borderTopColor: CALM_COLORS.SURFACE_FOCUSED },
});
export default TitleDetailsScreen;
