/**
 * The details page, with the still flash map strip.
 *
 * It says what the check found before anything plays: how many parts will be
 * hidden, how long they add up to and where they fall. No preview, no motion.
 *
 * A title that did not verify gets this page too, and that is the point of it.
 * Instead of the strip and a summary it shows one notice saying what happened
 * and that the picture stays hidden, and the play control is drawn as
 * unavailable rather than left out, so nobody hunts for it. There is no state
 * of this screen where an unverified title can be started.
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
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
}

const TitleDetailsScreen = ({
  entry,
  settings: householdSettings = DEFAULT_SETTINGS,
  onPlay,
  saving = false,
  onBack,
  testID = 'title-details',
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
      {onBack ? <CalmButton quiet testID={`${testID}-back`} label="Back to library" onPress={onBack} /> : null}
      <View style={styles.hero}>
        <View style={styles.heroCopy}>
          <Text style={styles.eyebrow}>{presentation.kind}</Text>
          <Text style={styles.title} testID={`${testID}-title`}>{presentation.name}</Text>
          {presentation.description ? <Text style={styles.summary} testID={demo ? `${testID}-demo-label` : `${testID}-description`}>{presentation.description}</Text> : null}
          <View style={styles.buttons}>
            <CalmButton primary testID={`${testID}-play`} label={saving ? 'Saving your changes...' : playable ? presentation.action : 'Unavailable'}
              accessibilityLabel={saving ? 'Saving your changes...' : playable ? `${presentation.action}: ${presentation.name}` : `${presentation.name} is unavailable. ${notice?.detail ?? ''}`}
              disabled={!playable || saving} hasTVPreferredFocus onPress={() => onPlay(entry)} />
          </View>
        </View>
        <View style={styles.heroArt}><TitleArtwork entry={entry} testID={`${testID}-artwork`} /></View>
      </View>

      {notice ? (
        <View style={styles.block}>
          <StatusNotice testID={`${testID}-notice`} notice={notice} />
        </View>
      ) : (
        <>
          <View style={styles.checkSummary}>
            <Text style={styles.section} accessibilityRole="header">{demo ? 'About this demo' : 'Before you watch'}</Text>
            {demo ? <Text style={styles.summary}>The holds are added at set times to demonstrate how the picture changes while sound and captions continue. Harbor was created without flashing effects.</Text> : null}
            <Text style={styles.summary} testID={`${testID}-summary`}>
              {intervals.length === 0
                ? 'The check found no segments above the flash limits. Checks can miss hazards.'
                : `${intervals.length} ${demo ? 'scheduled hold' : 'part'}${
                    intervals.length === 1 ? '' : 's'
                  } ${demo ? (intervals.length === 1 ? 'is included' : 'are included') : 'will be hidden'}, ${hiddenSeconds} second${
                    hiddenSeconds === 1 ? '' : 's'
                  } in all.${demo ? '' : ' Sound and captions keep playing.'}`}
            </Text>

            {durationMs > 0 ? (
              <View style={styles.block}>
                <FlashMapStrip
                  showCaption={false}
                  intervals={intervals}
                  durationMs={durationMs}
                  testID={`${testID}-strip`}
                />
              </View>
            ) : null}
          </View>

          <View style={styles.block}>
            <ViewingPlan
              entry={entry}
              settings={settings}
              testID={`${testID}-plan`}
            />
          </View>
        </>
      )}

      {onBack ? <View style={styles.block}><CalmButton quiet testID={`${testID}-back-bottom`} label="Back to library" onPress={onBack} /></View> : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND },
  content: { paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y) },
  hero: { flexDirection: 'row', alignItems: 'center', gap: scale(64), marginVertical: scale(32) },
  heroCopy: { width: scale(850) },
  heroArt: { flex: 1 },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.FOCUS_RING },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT, marginVertical: scale(20) },
  summary: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM, marginTop: scale(20) },
  section: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT },
  checkSummary: { maxWidth: scale(1200), marginTop: scale(CALM_SPACE.TIGHT) },
  block: { marginTop: scale(CALM_SPACE.BLOCK) },
  buttons: { flexDirection: 'row', marginTop: scale(CALM_SPACE.BLOCK) },
});
export default TitleDetailsScreen;
