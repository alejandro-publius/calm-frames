/**
 * The details page, with the still flash map strip.
 *
 * It says what the check found before anything plays: how many parts will be
 * hidden, how long they add up to and where they fall. No video preview.
 *
 * A title that did not verify gets this page too, and that is the point of it.
 * Instead of the strip and a summary it shows one notice saying what happened
 * and that the picture stays hidden, with a focused way back to the library.
 * No playback action is offered for an unchecked title. There is no state
 * of this screen where an unverified title can be started.
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import HomeHarborScene from './HomeHarborScene';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { noticeForTitle } from './copy';
import { buildCoverIntervals, totalCoveredMs } from './coverSchedule';
import FlashMapStrip from './FlashMapStrip';
import {
  coverOptionsFor,
  DEFAULT_SETTINGS,
  HouseholdSettings,
} from './household';
import { titlePresentation } from './TitleArtwork';
import StatusNotice from './StatusNotice';
import { CheckedTitle } from './titleStatus';
import { useUiCapture } from './uiCapture';
import { TITLE_DETAILS_BLOCKED_FRAME, TITLE_DETAILS_FRAME, TITLE_DETAILS_HARBOR_FRAME, TITLE_DETAILS_DEMO_FRAME } from './uiFrames';
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
  const presentation = titlePresentation(entry.title);
  const demo = isBundledBenignStory(entry.title);
  const notice = noticeForTitle(entry);
  const playable = notice === null;
  useUiCapture(
    playable ? (presentation.art === 'harbor-cinematic' ? (demo ? TITLE_DETAILS_DEMO_FRAME : TITLE_DETAILS_HARBOR_FRAME) : TITLE_DETAILS_FRAME) : TITLE_DETAILS_BLOCKED_FRAME,
    playable ? 'title details' : 'title details, not ready',
  );

  const hiddenSeconds = Math.round(totalCoveredMs(intervals) / 1000);
  const scrollRef = React.useRef<ScrollView>(null);
  const infoTop = React.useRef(0);

  if (notice) {
    // Remove only an exact repeated heading, never a distinct rejection reason.
    const repeatedHeading = `${notice.title}. `;
    const displayNotice = notice.detail.startsWith(repeatedHeading)
      ? { ...notice, detail: notice.detail.slice(repeatedHeading.length) }
      : notice;
    return (
      <ScrollView testID={testID} style={styles.screen}
        contentContainerStyle={[styles.content, styles.unavailableContent]}>
        <CalmPageHeader onBack={onBack} backTestID={`${testID}-back`} preferredBack />
        <View style={styles.unavailableBody}>
          <Text style={styles.title} accessibilityRole="header" testID={`${testID}-title`}>
            {presentation.name}
          </Text>
          <StatusNotice testID={`${testID}-notice`} notice={displayNotice} />

        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      ref={scrollRef}
      testID={testID}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      {presentation.art === 'harbor-cinematic' || presentation.art === 'harbor' ? <HomeHarborScene immersive enabled={interfaceMotionEnabled} active={interfaceActive} /> : null}
      <CalmPageHeader onBack={onBack} backTestID={`${testID}-back`} />
      <View style={styles.hero}>
        <View style={styles.heroCopy}>
          <View style={styles.kicker}><Text style={styles.eyebrow}>{demo ? 'Optional demo' : presentation.art === 'harbor-cinematic' ? 'A Calm Frames original' : 'About this story'}{durationMs > 0 ? ` · ${Math.round(durationMs / 1000)} sec` : ''}</Text></View>
          <Text style={[styles.title, styles.heroTitle, presentation.name.length > 20 ? styles.longTitle : null]} testID={`${testID}-title`}>{presentation.name}</Text>
          {presentation.description ? <Text style={styles.synopsis} testID={demo ? `${testID}-demo-label` : `${testID}-description`}>{presentation.description}</Text> : null}
          </View>
        <View style={styles.actionRail}>
          <View style={styles.buttons}>
            <CalmButton primary sound={false} testID={`${testID}-play`} label={saving ? 'Saving your changes...' : presentation.action}
              accessibilityLabel={saving ? 'Saving your changes...' : `${presentation.action}: ${presentation.name}`}
              disabled={saving} hasTVPreferredFocus onPress={() => onPlay(entry)} />
          </View>
          <Text style={styles.quickSummary}>{intervals.length === 0 ? 'No picture holds in this story. Some flashing may still go undetected.' : `${intervals.length} ${demo ? 'practice holds' : 'parts covered'}. Sound and captions continue.`}</Text>
        </View>
      </View>

      {playable ? (
        <View testID={`${testID}-info`} style={styles.infoAnchor}
          onLayout={({ nativeEvent }) => { infoTop.current = nativeEvent.layout.y; }}>
          <View>
            <CalmButton quiet testID={`${testID}-show-info`} label="Viewing details ↓"
              accessibilityLabel="Picture holds and viewing settings. Scroll down to read more."
              onPress={() => scrollRef.current?.scrollTo({
                // Keep this same focused control in view above the explanation.
                y: Math.max(0, infoTop.current - scale(CALM_SPACE.SAFE_Y)),
                animated: false,
              })} />
          </View>
        </View>
      ) : null}

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
                    showKey
                    holdLabel={demo ? 'Practice hold' : 'Picture covered'}
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

      {onBack ? <View style={styles.footer}><View><CalmButton quiet testID={`${testID}-back-bottom`} label="Back to library" onPress={onBack} /></View></View> : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND },
  content: { paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y), alignItems: 'flex-start' },
  navigation: { width: '100%', maxWidth: scale(1728), alignItems: 'flex-start', marginBottom: scale(16) },
  hero: { width: '100%', minHeight: scale(670), alignItems: 'flex-start', justifyContent: 'flex-end' },
  heroCopy: { width: '100%', maxWidth: scale(1000), alignItems: 'flex-start', paddingTop: scale(220) },
  actionRail: { width: '100%', flexDirection: 'row', alignItems: 'center', gap: scale(48), marginTop: scale(40), paddingTop: scale(24), borderTopWidth: scale(1), borderTopColor: CALM_COLORS.BORDER },
  quickSummary: { ...CALM_TEXT.supporting, maxWidth: scale(850), color: CALM_COLORS.TEXT_DIM },
  heroArt: { width: '100%', maxWidth: scale(1120) },
  artSky: { position: 'absolute', top: 0, left: 0, right: 0, height: scale(56) },
  artFloor: { position: 'absolute', bottom: 0, left: 0, right: 0, height: scale(160) },
  artEdge: { position: 'absolute', top: 0, bottom: 0, right: 0, width: scale(120) },
  kicker: { alignItems: 'flex-start', marginBottom: scale(8) },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT, marginBottom: scale(16), textAlign: 'left' },
  heroTitle: { fontSize: scale(144), lineHeight: scale(162) },
  longTitle: { fontSize: scale(64), lineHeight: scale(76) },
  synopsis: { ...CALM_TEXT.body, fontSize: scale(32), lineHeight: scale(44), color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
  summary: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
  section: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT, textAlign: 'left' },
  infoAnchor: { width: '100%', maxWidth: scale(1040), alignItems: 'flex-start', marginTop: scale(12) },
  checkSummary: { width: '100%', maxWidth: scale(1040), gap: scale(20), marginTop: scale(32) },
  chapterHeading: { alignItems: 'flex-start' },
  chapterContent: { gap: scale(24) },
  timeline: { marginTop: scale(8) },
  timelineLabel: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, marginBottom: scale(12), textAlign: 'left' },
  viewingChapter: { width: '100%', maxWidth: scale(1040), marginTop: scale(56) },
  unavailableContent: { flexGrow: 1, justifyContent: 'flex-start' },
  unavailableBody: { width: '100%', maxWidth: scale(1040), alignItems: 'flex-start', gap: scale(24) },
  unavailableAction: { marginTop: scale(16) },
  buttons: { flexDirection: 'row', justifyContent: 'flex-start', marginTop: 0 },
  footer: { width: '100%', maxWidth: scale(1040), alignItems: 'flex-start', marginTop: scale(40), paddingTop: scale(24), borderTopWidth: scale(1), borderTopColor: CALM_COLORS.SURFACE_FOCUSED },
});
export default TitleDetailsScreen;
