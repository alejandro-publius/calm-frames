import React from 'react';
import TouchableOpacity from './CalmTouchable';
import {
  BackHandler,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import HomeHarborScene from './HomeHarborScene';
import PictureHoldIntroduction from './PictureHoldIntroduction';
import { isBundledBenignStory } from './benignStory';
import {
  CALM_CONTROL,
  COASTAL_COLORS as CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
  BACKEND_UNREACHABLE,
  BACKEND_UNREACHABLE_EMPTY,
  NO_TITLES,
  PROFILES_KID_TITLE,
  WATCHING_STATE_WORD,
  whoIsWatching,
} from './copy';
import ProfilePicker from './ProfilePicker';
import { Profile } from './profiles';
import TitleArtwork, { titlePresentation } from './TitleArtwork';
import StatusNotice from './StatusNotice';
import { CheckedTitle, kidModeTitles } from './titleStatus';
import { useUiCapture } from './uiCapture';
import { useInterfaceFeedback } from './useInterfaceSound';
import {
  KID_HOME_EMPTY_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_FRAME,
  KID_HOME_STORY_FRAME, KID_HOME_STORY_FOCUSED_FRAME, KID_HOME_STORY_WATCH_FRAME,
  KID_HOME_OFFLINE_FRAME,
  KID_HOME_PROFILES_FRAME,
  KID_HOME_PROFILES_OFFLINE_FRAME,
  KID_HOME_PROFILES_FOCUSED_FRAME,
  KID_HOME_PICKER_FRAME,
} from './uiFrames';

/** The shelf control to restore after leaving a title or the parent area. */
export type ReturnFocusControl = 'watch' | 'details' | 'poster' | 'parent';

export interface KidHomeScreenProps {
  /** Every title that has been checked, in any state. */
  titles: CheckedTitle[];
  onOpen: (entry: CheckedTitle) => void;
  onPlay?: (entry: CheckedTitle) => void;
  /**
   * Called with the shelf control just pressed, right before onOpen or onPlay,
   * so the route can bring focus back to that control afterwards.
   */
  onLaunchControl?: (control: ReturnFocusControl) => void;
  /** Last opened title, retained by the route while this shelf is unmounted. */
  returnFocusId?: string | null;
  /**
   * Which control opened it. The featured title has Watch and Details side by
   * side, so the id alone cannot say which one to return to; without this,
   * Back from playback started with Watch put focus on Details.
   */
  returnFocusControl?: ReturnFocusControl;
  onOpenParentArea?: () => void;
  /**
   * The service that publishes checks could not be reached.
   *
   * The shelf still shows whatever verified, because a verified title carries
   * its own signed check and does not need the service to play.
   */
  offline?: boolean;
  /**
   * The kids in this household.
   *
   * Left out, the shelf is what it always was. Given, it asks who is watching
   * first, because the shelf a kid is looking at is the one their own settings
   * produced and they have to be able to tell it is theirs.
   */
  profiles?: Profile[];
  activeProfileId?: string;
  onChooseProfile?: (profile: Profile) => void;
  testID?: string;
  saving?: boolean;
  interfaceMotionEnabled?: boolean;
  interfaceActive?: boolean;
}

const KidHomeScreen = ({
  titles,
  onOpen,
  onPlay,
  returnFocusId,
  returnFocusControl,
  onLaunchControl,
  onOpenParentArea,
  offline = false,
  profiles,
  activeProfileId,
  onChooseProfile,
  testID = 'kid-home',
  saving = false,
  interfaceMotionEnabled = false,
  interfaceActive = true,
}: KidHomeScreenProps) => {
  const feedback = useInterfaceFeedback();
  const listed = kidModeTitles(titles);
  const [showIntroduction, setShowIntroduction] = React.useState(false);
  const [returnToIntroduction, setReturnToIntroduction] = React.useState(false);
  const demo = listed.find((entry) => isBundledBenignStory(entry.title));
  const closeIntroduction = () => { setShowIntroduction(false); setReturnToIntroduction(true); };
  React.useEffect(() => {
    if (!showIntroduction || !interfaceActive) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { closeIntroduction(); return true; });
    return () => subscription.remove();
  }, [showIntroduction, interfaceActive]);
  const [choosingProfile, setChoosingProfile] = React.useState(false);
  // The picker is one level above the shelf, so Back closes it rather than
  // falling through to the shelf's handler and leaving the app.
  React.useEffect(() => {
    if (!choosingProfile || !interfaceActive) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { setChoosingProfile(false); return true; });
    return () => subscription.remove();
  }, [choosingProfile, interfaceActive]);
  const featured = listed.find((entry) => titlePresentation(entry.title).action === 'Watch now') ?? listed[0];
  const hasMainStory = listed.some((entry) => !isBundledBenignStory(entry.title) && entry.title.id !== OFFLINE_TITLE_ID);
  const otherStories = listed.filter((entry) => (!hasMainStory || (!isBundledBenignStory(entry.title) && entry.title.id !== OFFLINE_TITLE_ID)) && (entry !== featured || !titlePresentation(entry.title).art || !hasMainStory));
  const playbackCheck = listed.find((entry) => entry.title.id === OFFLINE_TITLE_ID);
  const feature = featured ? titlePresentation(featured.title) : null;
  // The hero names the app, not the title. The title's length and hold count
  // are on Details, and Play's spoken label still says which title it starts.
  // Titles held back by the household's settings are listed in the parent
  // area, not announced here.
  const featuredAction = feature?.action === 'Watch now' ? 'Play' : feature?.action;
  const preferredId = listed.some((entry) => entry.title.id === returnFocusId)
    ? returnFocusId
    : listed[0]?.title.id;
  // Exactly one control takes the remote's focus when the shelf comes back:
  // the one that was pressed, or, for a press from the introduction, which
  // reports none, How it works.
  const returningToFeatured = Boolean(featured) && returnFocusId === featured?.title.id;
  const fromIntroduction = returnFocusId === demo?.title.id || returnFocusId === playbackCheck?.title.id;
  const returnTo: ReturnFocusControl | 'learn' | null = saving ? null
    : returnToIntroduction ? 'learn'
    : returnFocusControl === 'parent' ? 'parent'
    : !returnFocusId ? 'watch'
    : returnFocusControl ?? (fromIntroduction ? 'learn' : returningToFeatured ? 'details' : 'poster');
  const [focusedId, setFocusedId] = React.useState<string | null>(null);
  const empty = listed.length === 0;
  // With nothing to watch, the shelf does not ask who is watching: there is
  // nothing for the answer to change, and one fewer thing to read.
  const picking = Boolean(profiles && profiles.length > 0 && onChooseProfile) && !empty;

  // The app records what it paints, because Vega gives it no way to read its
  // own pixels. See uiCapture.ts.
  //
  // The picker is checked before the other two states on purpose. Its chips
  // paint the chosen fill, which neither the offline shelf nor a focused
  // poster adds on its own, so a shelf with a picker on it paints the same
  // colours whichever of those it is in, and that is the frame it reports.
  let frame = KID_HOME_FRAME;
  let reason = 'kid home';
  if (empty) {
    frame = KID_HOME_EMPTY_FRAME;
    reason = offline ? 'shelf empty, service unreachable' : 'shelf empty';
  } else if (picking) {
    frame = choosingProfile ? KID_HOME_PICKER_FRAME : focusedId ? KID_HOME_PROFILES_FOCUSED_FRAME : offline ? KID_HOME_PROFILES_OFFLINE_FRAME : KID_HOME_PROFILES_FRAME;
    reason = offline
      ? 'shelf with profiles, service unreachable'
      : focusedId
        ? 'profiles, poster focused'
        : 'shelf, with the profiles';
  } else if (offline) {
    frame = KID_HOME_OFFLINE_FRAME;
    reason = 'shelf, service unreachable';
  } else if (focusedId) {
    frame = KID_HOME_FOCUSED_FRAME;
    reason = 'poster focused';
  }
  if (!empty && !otherStories.length && !choosingProfile && !offline) {
    frame = focusedId === 'watch' ? KID_HOME_STORY_WATCH_FRAME : focusedId === 'details' ? KID_HOME_STORY_FOCUSED_FRAME : KID_HOME_STORY_FRAME;
    reason = frame.screen;
  }
  useUiCapture(frame, reason);

  return (
    <View testID={testID} style={styles.screen}>
      <HomeHarborScene immersive={!showIntroduction && !empty} enabled={interfaceMotionEnabled} active={interfaceActive && !showIntroduction} />
      <CalmPageHeader wordmark={false} onBack={showIntroduction ? closeIntroduction : undefined} backTestID="picture-hold-dismiss" preferredBack={showIntroduction && !demo}>
          {picking && profiles ? <CalmButton quiet compact testID={`${testID}-choose-profile`} label={saving ? 'Saving your changes...' : (profiles.find((p) => p.id === activeProfileId) ?? profiles[0]).name}
            disabled={saving} accessibilityLabel="Choose who is watching" onPress={() => setChoosingProfile(!choosingProfile)} /> : null}
          {!showIntroduction && !empty ? <View style={styles.navigationLink}><CalmButton quiet compact testID={`${testID}-learn`} label="How it works" accessibilityLabel="How it works" hasTVPreferredFocus={returnTo === 'learn'}
            disabled={saving} onPress={() => { setChoosingProfile(false); setShowIntroduction(true); }} /></View> : null}
          {onOpenParentArea ? <View style={styles.navigationLink}><CalmButton quiet tertiary compact testID={`${testID}-parent-area`} label="Parents" accessibilityLabel="Parents: parental controls, needs a PIN" hasTVPreferredFocus={(empty || returnTo === 'parent') && !saving} onPress={onOpenParentArea} /></View> : null}
      </CalmPageHeader>
      {choosingProfile && picking && profiles && onChooseProfile ? (
        <ProfilePicker disabled={saving || undefined} testID={`${testID}-profiles`} title={PROFILES_KID_TITLE}
          chosenWord={WATCHING_STATE_WORD} chosenLine={whoIsWatching((profiles.find((one) => one.id === activeProfileId) ?? profiles[0]).name)}
          profiles={profiles} activeProfileId={activeProfileId ?? profiles[0].id} onChoose={onChooseProfile} />
      ) : null}
      {showIntroduction ? <PictureHoldIntroduction disabled={saving} onDemoDetails={demo ? () => onOpen(demo) : undefined} onPlaybackCheck={playbackCheck ? () => onOpen(playbackCheck) : undefined} onStart={demo ? () => {
        if (!saving) { setShowIntroduction(false); setReturnToIntroduction(true); (onPlay ?? onOpen)(demo); }
      } : undefined} /> : empty ? (
        <StatusNotice
          testID={`${testID}-empty`}
          notice={offline ? BACKEND_UNREACHABLE_EMPTY : NO_TITLES}
        />
      ) : (
        <>
          {offline ? (
            <View style={styles.banner}>
              <StatusNotice testID={`${testID}-offline`} notice={BACKEND_UNREACHABLE} />
            </View>
          ) : null}
          <ScrollView style={styles.libraryScroll} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
            {featured && feature ? <View style={styles.hero}>
              <View style={styles.heroCopy}>
                <Text accessibilityRole="header" testID={`${testID}-title`} style={styles.featureTitle}>Calm Frames</Text>
                <View style={styles.actions}>
                  <CalmButton primary playIcon sound={false} onFocus={() => setFocusedId('watch')} onBlur={() => setFocusedId(null)} testID={`${testID}-watch`} label={featuredAction!} accessibilityLabel={`${featuredAction}: ${feature.name}`}
                    disabled={saving} hasTVPreferredFocus={returnTo === 'watch'} onPress={() => { onLaunchControl?.('watch'); (onPlay ?? onOpen)(featured); }} />
                  <CalmButton quiet onFocus={() => setFocusedId('details')} onBlur={() => setFocusedId(null)} testID={`${testID}-more-info`} label="Details" accessibilityLabel={`Details: ${feature.name}`} hasTVPreferredFocus={returnTo === 'details'} onPress={() => { onLaunchControl?.('details'); onOpen(featured); }} disabled={saving} />
                </View>
              </View>
            </View> : null}
            {otherStories.length > 0 ? <View style={styles.sectionHeading}><Text style={styles.section}>More to watch</Text></View> : null}
            <View style={styles.grid}>
              {otherStories.map((entry) => {
                const focused = focusedId === entry.title.id;
                const label = titlePresentation(entry.title);
                return <TouchableOpacity disabled={saving || undefined} accessibilityState={saving ? { disabled: true } : undefined}
                  key={entry.title.id} testID={`${testID}-poster-${entry.title.id}`} accessibilityRole="button"
                  accessibilityLabel={[label.cardName ?? label.name, label.kind].filter(Boolean).join(', ')} activeOpacity={1}
                  hasTVPreferredFocus={returnTo === 'poster' && entry.title.id === preferredId}
                  onFocus={() => setFocusedId(entry.title.id)} onBlur={() => setFocusedId(null)} onPress={() => {
                    if (!saving) { onLaunchControl?.('poster'); onOpen(entry); feedback.confirm(); }
                  }}
                  style={[styles.poster, focused ? styles.posterFocused : null]}>
                  <View style={styles.posterArt}><TitleArtwork illustrated compact height={116} entry={entry} testID={`${testID}-poster-image-${entry.title.id}`} /></View>
                  <View style={styles.posterCopy}>
                  <Text style={[styles.posterTitle, focused ? styles.focusedLabel : null]} numberOfLines={2} testID={`${testID}-poster-title-${entry.title.id}`}>{label.cardName ?? label.name}</Text>
                  {label.kind ? <Text style={styles.posterQualifier} testID={`${testID}-poster-qualifier-${entry.title.id}`}>{label.kind}</Text> : null}
                  </View>
                </TouchableOpacity>;
              })}
            </View>
          </ScrollView>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  focusedLabel: { textDecorationLine: 'underline' },
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND, paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y) },
  header: { width: '100%', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: scale(24) },
  brand: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
  mark: { width: scale(80), height: scale(80) },
  wordmark: { ...CALM_TEXT.control, color: CALM_COLORS.TEXT },
  navigation: { flexDirection: 'row', gap: scale(20) },
  navigationLink: { alignSelf: 'center' },
  libraryScroll: { flex: 1 },
  scrollContent: { paddingBottom: scale(12) },
  hero: { width: '100%', minHeight: scale(810), alignItems: 'flex-start', paddingBottom: scale(36) },
  heroCopy: { width: scale(840), paddingTop: scale(70), alignItems: 'flex-start' },
  // One line at 120: "Calm Frames" measures 755 units in the display face,
  // which ends before the island's tree at about 900. At 184 it would run to
  // 1158 and under the lighthouse.
  featureTitle: { ...CALM_TEXT.screen, fontSize: scale(120), lineHeight: scale(136), color: CALM_COLORS.TEXT, marginBottom: scale(36) },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
  learn: { flexDirection: 'row', marginTop: scale(8) },
  sectionHeading: { alignItems: 'flex-start', marginBottom: scale(24) },
  section: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT },
  banner: { marginBottom: scale(20) },
  grid: { width: '100%', flexDirection: 'row', flexWrap: 'wrap', gap: scale(20) },
  poster: { width: scale(540), flexDirection: 'row', alignItems: 'center', gap: scale(20), padding: scale(6), borderRadius: scale(CALM_CONTROL.RADIUS), borderWidth: scale(FOCUS_RING_WIDTH), borderColor: CALM_COLORS.BACKGROUND, backgroundColor: CALM_COLORS.BACKGROUND },
  posterFocused: { borderColor: CALM_COLORS.FOCUS_RING, backgroundColor: CALM_COLORS.SURFACE_FOCUSED },
  posterArt: { width: scale(190), borderRadius: scale(CALM_CONTROL.RADIUS), overflow: 'hidden' },
  posterCopy: { flex: 1 },
  posterTitle: { ...CALM_TEXT.card, color: CALM_COLORS.TEXT },
  posterQualifier: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM },
});
export default KidHomeScreen;
