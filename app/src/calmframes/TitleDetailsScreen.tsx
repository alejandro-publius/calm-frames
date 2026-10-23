/** Viewing first; optional explanations and technical records use separate pages. */
import React from 'react';
import CoastalWorld, { WorldAppearance, WORLD } from './CoastalWorld';
import { DETAIL } from './homeIslands';
import { islandKind } from './CoastalIsland';
import { Image } from 'react-native';
import { BackHandler, ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import { EnvironmentMark } from './JourneyStatus';
import { filmStill } from './HomeHarborScene';
import { continuousScenePicture } from './continuousScene';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, CALM_FLOW, heroTitleTypography, scale } from './calmStyles';
import { coverLine, DETECTION_LIMITS_LINE, noticeForTitle, ONLY_IN_CALM_FRAMES_LINE, runtimeLabel, SAFETY_NOTE } from './copy';
import { buildCoverIntervals, totalCoveredMs } from './coverSchedule';
import CoveredSectionsStrip from './CoveredSectionsStrip';
import { coveredSections } from './coveredSections';
import { hasBakedOceanPresentation } from './titleCoverPresentation';
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
import PreparedVideoAnalysis from './PreparedVideoAnalysis';
import { concernsPackagedLibrary, packagedLibrary } from './packagedLibrary';
import {
  benignStorySettings,
  isBundledBenignStory,
} from './benignStory';

export interface TitleDetailsScreenProps {
  entry: CheckedTitle;
  settings?: HouseholdSettings;
  onPlay: (entry: CheckedTitle) => void;
  onAmbient?: (entry: CheckedTitle) => void;
  saving?: boolean;
  onBack?: () => void;
  testID?: string;
  interfaceMotionEnabled?: boolean;
  interfaceActive?: boolean;
  /** The optional simulated demo lives inside More info. */
  practice?: CheckedTitle;
  onOpenPractice?: (entry: CheckedTitle) => void;
  /** Back from the demo's own page puts focus on the control that opened it. */
  preferPracticeFocus?: boolean;
}

const TitleDetailsScreen = ({
  entry,
  settings: householdSettings = DEFAULT_SETTINGS,
  onPlay,
  onAmbient,
  saving = false,
  onBack,
  testID = 'title-details',
  interfaceActive = true,
  practice,
  onOpenPractice,
  preferPracticeFocus = false,
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
        renditionStartOffsetMs: entry.title.renditionStartOffsetMs,
      }),
    [entry.segments, entry.title.renditionStartOffsetMs, settings, durationMs],
  );
  // The strip on the watch page: the same schedule, read once for the page.
  const covered = React.useMemo(
    () => coveredSections(entry, householdSettings),
    [entry, householdSettings],
  );
  const presentation = titlePresentation(entry.title);
  const ocean = hasBakedOceanPresentation(entry, settings, intervals);
  const demo = isBundledBenignStory(entry.title);
  const practiceOffered = practice && onOpenPractice && !demo ? practice : null;
  // Counted the way the demo's own page counts them: the merged schedule under
  // the demo's prepared settings, not the raw segments of each map.
  const practiceLine = React.useMemo(() => {
    if (!practiceOffered) return null;
    const runtime = runtimeLabel(practiceOffered.title.durationMs);
    const holds = buildCoverIntervals(practiceOffered.segments ?? [], {
      ...coverOptionsFor(benignStorySettings(practiceOffered.title, DEFAULT_SETTINGS)),
      durationMs: practiceOffered.title.durationMs,
    }).length;
    return runtime && holds > 0 ? `${runtime}, ${holds} picture pause${holds === 1 ? '' : 's'}` : null;
  }, [practiceOffered]);
  const playLabel = onAmbient ? 'Settle in' : demo ? 'Watch demo' : presentation.action === 'Watch preview' ? 'Watch preview' : 'Watch';
  const notice = noticeForTitle(entry) ?? (concernsPackagedLibrary(entry.title) && !packagedLibrary.evidenceFor(entry.title, settings) ? {
    title: 'This video is unavailable',
    detail: 'This version cannot play in Calm Frames. The picture stays hidden.',
    tone: 'blocked' as const,
  } : null);
  const playable = notice === null;
  useUiCapture(
    playable ? (presentation.art === 'harbor-cinematic' ? (demo ? TITLE_DETAILS_DEMO_FRAME : TITLE_DETAILS_HARBOR_FRAME) : TITLE_DETAILS_FRAME) : TITLE_DETAILS_BLOCKED_FRAME,
    playable ? 'title details' : 'title details, not ready',
  );

  const hiddenSeconds = Math.round(totalCoveredMs(intervals) / 1000);
  const meta = [demo ? 'Simulated demo' : null, presentation.runtime ?? runtimeLabel(durationMs)].filter(Boolean).join(' · ');
  const [page, setPage] = React.useState<'watch' | 'info' | 'technical'>(preferPracticeFocus ? 'info' : 'watch');
  const [returnFocus, setReturnFocus] = React.useState<'watch' | 'info' | 'technical'>('watch');
  const back = React.useCallback(() => {
    if (page === 'technical') { setPage('info'); setReturnFocus('technical'); }
    else if (page === 'info') { setPage('watch'); setReturnFocus('info'); }
    else onBack?.();
  }, [page, onBack]);
  React.useEffect(() => {
    if (!interfaceActive) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!playable) { onBack?.(); return Boolean(onBack); }
      if (page === 'watch' && !onBack) return false;
      back(); return true;
    });
    return () => subscription.remove();
  }, [back, interfaceActive, page, playable, onBack]);

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

  if (page !== 'watch') return (
    <ScrollView key={page} testID={`${testID}-${page}`} style={styles.screen} contentContainerStyle={styles.content}>
      <CalmPageHeader onBack={back} backTestID={`${testID}-info-back`} preferredBack={page === 'technical' || (!preferPracticeFocus && returnFocus !== 'technical')} />
      <View style={styles.reading}>
        <Text style={styles.title} accessibilityRole="header">{page === 'technical' ? 'Technical details' : 'More info'}</Text>
        {page === 'technical' ? <>
          <PreparedVideoAnalysis entry={entry} settings={settings} testID={`${testID}-record`} />
          {intervals.length > 0 && durationMs > 0 ? <View style={styles.checkSummary}>
            <Text style={styles.summary} testID={`${testID}-summary`}>
              {demo ? `Simulated demo: ${intervals.length} picture pauses, ${hiddenSeconds} seconds in total.`
                : `${intervals.length} scenes hidden, ${hiddenSeconds} seconds in total.`}
            </Text>
            <FlashMapStrip width={1040} showCaption={false} showKey holdLabel={demo ? 'Demo pause' : 'Picture hidden'}
              intervals={intervals} durationMs={durationMs} testID={`${testID}-strip`} />
          </View> : null}
          <ViewingPlan entry={entry} settings={settings} testID={`${testID}-plan`} />
        </> : <>
          <Text style={styles.section} accessibilityRole="header">{presentation.name}</Text>
          {demo ? <Text style={styles.summary}>This is a simulated demonstration. The pauses were added to show how the feature works, not because flashing was detected.</Text>
            : intervals.length > 0 ? <Text style={styles.summary} testID={`${testID}-cover-line`}>{coverLine(intervals.length, (entry.title.textTrack?.length ?? 0) > 0, ocean)}</Text> : null}
          <Text style={styles.summary}>{ONLY_IN_CALM_FRAMES_LINE}</Text>
          <Text style={styles.summary}>{`${DETECTION_LIMITS_LINE} ${SAFETY_NOTE}`}</Text>
          {presentation.art === 'coastal' ? <Text style={styles.summary}>Video: National Park Service, Acadia National Park. Public domain. No NPS endorsement is implied. The menu image is a still from the prepared video.</Text> : null}
          {presentation.attribution ? <Text style={styles.summary} testID={`${testID}-attribution`}>{presentation.attribution}</Text> : null}
          {practiceOffered ? <View style={styles.secondaryAction}><CalmButton quiet testID={`${testID}-practice`} label="Watch demo"
            accessibilityLabel={practiceLine ? `Watch simulated demo. ${practiceLine}` : 'Watch simulated demo'}
            disabled={saving} hasTVPreferredFocus={preferPracticeFocus && returnFocus !== 'technical'} onPress={() => onOpenPractice?.(practiceOffered)} /></View> : null}
          <View style={styles.secondaryAction}><CalmButton quiet testID={`${testID}-technical`} label={concernsPackagedLibrary(entry.title) ? 'Playback proof & details' : 'Technical details'}
            hasTVPreferredFocus={returnFocus === 'technical'} onPress={() => setPage('technical')} /></View>
        </>}
        <View style={styles.secondaryAction}><CalmButton quiet testID={`${testID}-back-bottom`} label="Back" onPress={back} /></View>
      </View>
    </ScrollView>
  );

  return (
    <WorldAppearance.Provider value><ScrollView key="watch" testID={testID} style={[styles.screen, { backgroundColor: WORLD.BACKGROUND }]} contentContainerStyle={[styles.content, { minHeight: scale(1080) }]}>
      <CoastalWorld detail destination={islandKind(presentation.menuArt ?? presentation.art)} cardKinds={[islandKind(presentation.menuArt ?? presentation.art)]} />
      <Image source={continuousScenePicture(entry.title) ?? filmStill(presentation.menuArt ?? presentation.art)} resizeMode="cover" fadeDuration={0} style={styles.destinationImage} testID={`${testID}-destination-image`} accessible={false} />
      <CalmPageHeader onBack={onBack} backTestID={`${testID}-back`}>
        {presentation.menuArt || presentation.art === 'coastal' ? <View style={styles.environment}><EnvironmentMark forest={presentation.menuArt === 'forest'} /><Text style={styles.environmentName}>{presentation.menuArt === 'forest' ? 'Forest' : 'Ocean'}</Text></View> : null}
      </CalmPageHeader>
      <View style={styles.hero}>
        <View style={styles.heroCopy}>
          <Text style={[styles.title, styles.heroTitle, heroTitleTypography(presentation.name), { color: WORLD.TEXT }]} testID={`${testID}-title`}>{presentation.name}</Text>
          <Text style={[styles.meta, { color: WORLD.TEXT_DIM }]} testID={`${testID}-meta`}>{onAmbient ? 'Still scene' : meta}</Text>
        </View>
        <View style={styles.actionRail}>
          <View style={styles.buttons}>
            <CalmButton primary playIcon={!onAmbient} sound={false} testID={`${testID}-play`} label={saving ? 'Saving your changes...' : playLabel}
              accessibilityLabel={saving ? 'Saving your changes...' : `${playLabel}: ${presentation.name}`}
              disabled={saving} hasTVPreferredFocus={returnFocus !== 'info'} onPress={() => (onAmbient ?? onPlay)(entry)} />
            <CalmButton quiet tertiary compact testID={`${testID}-show-info`} label="More info" hasTVPreferredFocus={returnFocus === 'info'}
              onPress={() => setPage('info')} />
          </View>
        </View>
          {presentation.description ? <Text style={[styles.synopsis, { color: WORLD.TEXT_DIM }]} testID={demo ? `${testID}-demo-label` : `${testID}-description`}>{presentation.description}</Text> : null}
        <CoveredSectionsStrip result={covered} ocean={ocean} testID={`${testID}-covered`} />
      </View>
    </ScrollView></WorldAppearance.Provider>
  );
};

const styles = StyleSheet.create({
  // The photograph stands on the island; homeIslands.ts DETAIL keeps the landmarks clear of it.
  destinationImage: { position: 'absolute', left: scale(DETAIL.PHOTO.left), top: scale(DETAIL.PHOTO.top), width: scale(DETAIL.PHOTO.width), height: scale(DETAIL.PHOTO.height), borderWidth: scale(10), borderColor: WORLD.SURFACE, borderRadius: scale(26) },
  environment: { flexDirection: 'row', alignItems: 'center', gap: scale(CALM_SPACE.TIGHT) },
  environmentName: { ...CALM_TEXT.supporting, color: WORLD.TEXT },
  reading: { width: '100%', maxWidth: scale(1040), gap: scale(24), paddingTop: scale(32) },
  secondaryAction: { alignItems: 'flex-start' },
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND },
  content: { paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y), alignItems: 'flex-start' },
  hero: { paddingLeft: scale(40), width: '100%', minHeight: scale(CALM_FLOW.HERO_HEIGHT), alignItems: 'flex-start', justifyContent: 'flex-start' },
  heroCopy: { width: '100%', maxWidth: scale(780), alignItems: 'flex-start', paddingTop: scale(CALM_FLOW.HERO_TOP) },
  actionRail: { width: '100%', alignItems: 'flex-start', gap: scale(26), marginTop: 0 },
  meta: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left', marginBottom: scale(16) },
  title: { ...CALM_TEXT.screen, color: CALM_COLORS.TEXT, marginBottom: scale(16), textAlign: 'left' },
  heroTitle: { marginBottom: scale(8) },
  synopsis: { ...CALM_TEXT.body, fontSize: scale(32), lineHeight: scale(44), color: CALM_COLORS.TEXT_DIM, textAlign: 'left', maxWidth: scale(700), marginTop: scale(28) },
  summary: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
  section: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT, textAlign: 'left' },
  checkSummary: { width: '100%', maxWidth: scale(1040), gap: scale(20), marginTop: scale(32) },
  unavailableContent: { flexGrow: 1, justifyContent: 'flex-start' },
  unavailableBody: { width: '100%', maxWidth: scale(1040), alignItems: 'flex-start', gap: scale(24) },
  buttons: { flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-start', gap: scale(20), marginTop: 0 },
});
export default TitleDetailsScreen;
