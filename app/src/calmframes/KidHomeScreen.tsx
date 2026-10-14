import React from 'react';
import {
  BackHandler,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import CalmButton from './CalmButton';
import HomeHarborScene from './HomeHarborScene';
import PictureHoldIntroduction from './PictureHoldIntroduction';
import { isBundledBenignStory } from './benignStory';
import {
  CALM_COLORS,
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
import { Image } from 'react-native';
import StatusNotice from './StatusNotice';
import { CheckedTitle, kidModeTitles } from './titleStatus';
import { useUiCapture } from './uiCapture';
import { useInterfaceFeedback } from './useInterfaceSound';
import {
  KID_HOME_EMPTY_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_FRAME,
  KID_HOME_OFFLINE_FRAME,
  KID_HOME_PROFILES_FRAME,
  KID_HOME_PROFILES_OFFLINE_FRAME,
  KID_HOME_PROFILES_FOCUSED_FRAME,
  KID_HOME_PICKER_FRAME,
} from './uiFrames';

export interface KidHomeScreenProps {
  /** Every title that has been checked, in any state. */
  titles: CheckedTitle[];
  onOpen: (entry: CheckedTitle) => void;
  onPlay?: (entry: CheckedTitle) => void;
  /** Last opened title, retained by the route while this shelf is unmounted. */
  returnFocusId?: string | null;
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
  const featured = listed.find((entry) => titlePresentation(entry.title).action === 'Watch now') ?? listed[0];
  const feature = featured ? titlePresentation(featured.title) : null;
  const hiddenCount = titles.length - listed.length;
  const preferredId = listed.some((entry) => entry.title.id === returnFocusId)
    ? returnFocusId
    : listed[0]?.title.id;
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
  useUiCapture(frame, reason);

  return (
    <View testID={testID} style={styles.screen}>
      <HomeHarborScene enabled={interfaceMotionEnabled} active={interfaceActive && !showIntroduction} />
      <View style={styles.header}>
        <View style={styles.brand}>
          <Image source={require('../../assets/image/CalmFrames.png')} style={styles.mark} fadeDuration={0} />
          <Text style={styles.wordmark}>Calm Frames</Text>
        </View>
        <View style={styles.navigation}>
          {picking && profiles ? <CalmButton quiet testID={`${testID}-choose-profile`} label={saving ? 'Saving your changes...' : (profiles.find((p) => p.id === activeProfileId) ?? profiles[0]).name}
            disabled={saving} accessibilityLabel="Choose who is watching" onPress={() => setChoosingProfile(!choosingProfile)} /> : null}
          {onOpenParentArea ? <View style={styles.navigationLink}><CalmButton quiet testID={`${testID}-parent-area`} label="Parental controls" accessibilityLabel="Parental controls, needs a PIN" hasTVPreferredFocus={empty && !saving} onPress={onOpenParentArea} /></View> : null}
        </View>
      </View>
      {choosingProfile && picking && profiles && onChooseProfile ? (
        <ProfilePicker disabled={saving || undefined} testID={`${testID}-profiles`} title={PROFILES_KID_TITLE}
          chosenWord={WATCHING_STATE_WORD} chosenLine={whoIsWatching((profiles.find((one) => one.id === activeProfileId) ?? profiles[0]).name)}
          profiles={profiles} activeProfileId={activeProfileId ?? profiles[0].id} onChoose={onChooseProfile} />
      ) : null}
      {showIntroduction ? <PictureHoldIntroduction disabled={saving} onBack={closeIntroduction} onStart={demo ? () => {
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
                <Text style={styles.eyebrow}>A calmer way to watch</Text>
                <Text style={[styles.featureTitle, feature.name.length > 18 ? styles.longFeatureTitle : null]}>{feature.name}</Text>
                <Text style={styles.description}>For fewer flashing pictures: prepared titles can hold the picture while sound continues.</Text>
                <View style={styles.actions}>
                  <CalmButton primary sound={false} testID={`${testID}-watch`} label={feature.action} accessibilityLabel={`${feature.action}: ${feature.name}`}
                    disabled={saving} hasTVPreferredFocus={!returnFocusId && !returnToIntroduction && !saving} onPress={() => (onPlay ?? onOpen)(featured)} />
                  {demo && featured !== demo ? <CalmButton quiet testID={`${testID}-try-demo`} label="Try the demo" sound={false} onPress={() => (onPlay ?? onOpen)(demo)} disabled={saving} /> : null}
                </View>
                <View style={styles.learn}><CalmButton quiet compact testID={`${testID}-learn`} label="How it works" hasTVPreferredFocus={returnToIntroduction && !saving}
                  disabled={saving} onPress={() => { setChoosingProfile(false); setShowIntroduction(true); }} />
                  <CalmButton quiet compact testID={`${testID}-more-info`} label="More info" onPress={() => onOpen(featured)} disabled={saving} /></View>
              </View>
            </View> : null}
            <View style={styles.sectionHeading}><Text style={styles.section} testID={`${testID}-title`}>Your library</Text></View>
            <View style={styles.grid}>
              {listed.map((entry) => {
                const focused = focusedId === entry.title.id;
                const label = titlePresentation(entry.title);
                return <TouchableOpacity disabled={saving || undefined} accessibilityState={saving ? { disabled: true } : undefined}
                  key={entry.title.id} testID={`${testID}-poster-${entry.title.id}`} accessibilityRole="button"
                  accessibilityLabel={[label.cardName ?? label.name, label.kind].filter(Boolean).join(', ')} activeOpacity={1}
                  hasTVPreferredFocus={!saving && !returnToIntroduction && Boolean(returnFocusId) && entry.title.id === preferredId}
                  onFocus={() => setFocusedId(entry.title.id)} onBlur={() => setFocusedId(null)} onPress={() => {
                    if (!saving) { onOpen(entry); feedback.confirm(); }
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

      <View style={styles.footer}>
        {!showIntroduction && hiddenCount > 0 ? (
          <Text style={styles.footerText} testID={`${testID}-hidden-count`}>
            {hiddenCount} more {hiddenCount === 1 ? 'title is' : 'titles are'} unavailable.
            Open Parental controls to see why.
          </Text>
        ) : null}

      </View>
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
  hero: { width: '100%', minHeight: scale(590), alignItems: 'flex-start' },
  heroCopy: { width: scale(800), paddingTop: scale(56), alignItems: 'flex-start' },
  eyebrow: { ...CALM_TEXT.supporting, color: CALM_COLORS.FOCUS_RING, marginBottom: scale(12) },
  featureTitle: { ...CALM_TEXT.feature, color: CALM_COLORS.TEXT, marginBottom: scale(12) },
  longFeatureTitle: { fontSize: scale(64), lineHeight: scale(76) },
  description: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, maxWidth: scale(780), marginBottom: scale(24) },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
  learn: { flexDirection: 'row', marginTop: scale(0) },
  sectionHeading: { alignItems: 'flex-start', marginBottom: scale(24) },
  section: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT },
  banner: { marginBottom: scale(20) },
  grid: { width: '100%', flexDirection: 'row', flexWrap: 'wrap', gap: scale(20) },
  poster: { width: scale(540), flexDirection: 'row', alignItems: 'center', gap: scale(20), padding: scale(6), borderRadius: scale(18), borderWidth: scale(FOCUS_RING_WIDTH), borderColor: CALM_COLORS.BACKGROUND, backgroundColor: CALM_COLORS.BACKGROUND },
  posterFocused: { borderColor: CALM_COLORS.FOCUS_RING, backgroundColor: CALM_COLORS.SURFACE_FOCUSED },
  posterArt: { width: scale(190), borderRadius: scale(12), overflow: 'hidden' },
  posterCopy: { flex: 1 },
  posterTitle: { ...CALM_TEXT.card, color: CALM_COLORS.TEXT },
  posterQualifier: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM },
  footer: { paddingTop: scale(12) },
  footerText: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM },
});
export default KidHomeScreen;
