import { ambientArtworkFor } from './AmbientScene';
import React from 'react';
import Svg, { Path } from '@amazon-devices/react-native-svg';
import CoastalWorld, { WorldAppearance, WORLD } from './CoastalWorld';
import { islandKind } from './CoastalIsland';
import { ENVIRONMENTS, environmentHeadingBox, HOME_ISLANDS, ISLAND_ORDER, IslandSlotKind, islandChoiceBox, ScreenBox } from './homeIslands';
import { continuousScenePicture } from './continuousScene';
import TouchableOpacity from './CalmTouchable';
import {
  BackHandler,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import { EnvironmentMark } from './JourneyStatus';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import HomeHarborScene, { filmStill } from './HomeHarborScene';
import PictureHoldIntroduction from './PictureHoldIntroduction';
import { isBundledBenignStory } from './benignStory';
import {
  COASTAL_COLORS as CALM_COLORS,
  CALM_FLOW,
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
  runtimeLabel,
  WATCHING_STATE_WORD,
  whoIsWatching,
} from './copy';
import ProfilePicker from './ProfilePicker';
import { Profile } from './profiles';
import { shelfPoster } from './shelf';
import { titlePresentation } from './TitleArtwork';
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

/** A block placed on the screen at a homeIslands.ts box, scaled from 1080p units. */
const placed = (box: ScreenBox) => ({ position: 'absolute' as const, left: scale(box.left), top: scale(box.top), width: scale(box.width), height: scale(box.height) });

/** The shelf control to restore after leaving a title or the parent area. */
export type ReturnFocusControl = 'watch' | 'details' | 'poster' | 'parent';

export interface KidHomeScreenProps {
  /** Every title that has been checked, in any state. */
  titles: CheckedTitle[];
  onOpen: (entry: CheckedTitle) => void;
  onPlay?: (entry: CheckedTitle) => void;
  onAmbient?: (entry: CheckedTitle) => void;
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
  onSelectTitle?: (id: string) => void;
  selectedTitleId?: string | null;
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
  onAmbient,
  returnFocusId,
  returnFocusControl,
  onLaunchControl,
  onOpenParentArea,
  onSelectTitle,
  selectedTitleId,
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
  // The header control to put the remote's focus back on after a panel it
  // opened is dismissed: How it works after the explanation, the profile
  // button after the picker. One value, so the latest dismissal wins.
  const [returnToHeader, setReturnToHeader] = React.useState<'learn' | 'profile' | null>(null);
  const demo = listed.find((entry) => isBundledBenignStory(entry.title));
  const closeIntroduction = () => { setShowIntroduction(false); setReturnToHeader('learn'); };
  React.useEffect(() => {
    if (!showIntroduction || !interfaceActive) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { closeIntroduction(); return true; });
    return () => subscription.remove();
  }, [showIntroduction, interfaceActive]);
  const [choosingProfile, setChoosingProfile] = React.useState(false);
  // A choice or Back asks the picker to close. It closes once nothing is being
  // saved: the button it hands focus back to is disabled during a save, and a
  // picker that closed then would leave the remote with nothing focused. Until
  // then the chips stay focusable and ignore presses.
  const [closingPicker, setClosingPicker] = React.useState(false);
  React.useEffect(() => {
    if (closingPicker && !saving) {
      setClosingPicker(false);
      setChoosingProfile(false);
      setReturnToHeader('profile');
    }
  }, [closingPicker, saving]);
  // The picker is one level above the shelf, so Back closes it rather than
  // falling through to the shelf's handler and leaving the app. The chips go
  // with it, so focus is put back on the control that opened them.
  React.useEffect(() => {
    if (!choosingProfile || !interfaceActive) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      setClosingPicker(true);
      return true;
    });
    return () => subscription.remove();
  }, [choosingProfile, interfaceActive]);
  const [selectedId, setSelectedId] = React.useState(selectedTitleId ?? returnFocusId);
  const featured = listed.find((entry) => entry.title.id === selectedId && !isBundledBenignStory(entry.title) && entry.title.id !== OFFLINE_TITLE_ID) ?? listed.find((entry) => titlePresentation(entry.title).action === 'Watch now') ?? listed[0];
  const mainStories = listed.filter((entry) => !isBundledBenignStory(entry.title) && entry.title.id !== OFFLINE_TITLE_ID);
  // Keep the playable island order aligned with the map: Ocean (Acadia, Sea Otters), then Forest.
  const islandOrder = (entry: CheckedTitle) => {
    const art = titlePresentation(entry.title);
    return ISLAND_ORDER.indexOf(art.menuArt ?? 'coastal');
  };
  mainStories.sort((a, b) => islandOrder(a) - islandOrder(b));
  const hasMainStory = mainStories.length > 0;
  const playbackCheck = listed.find((entry) => entry.title.id === OFFLINE_TITLE_ID);
  const feature = featured ? titlePresentation(featured.title) : null;
  // The rail chooses between videos. With one featured video whose scene the
  // hero already shows there is nothing to choose, so the hero stands alone.
  // With two or more, every one is a card; a lone title without hero art keeps
  // its poster, which is the only place its own picture appears; and a shelf
  // with no main video keeps its legacy posters for what it does hold.
  const otherStories = !hasMainStory ? listed
    : mainStories.length > 1 || !feature?.art ? mainStories : [];
  // Every main video with an island of its own gets the island map, where
  // each card stands on its island and every position comes from
  // homeIslands.ts. Anything else keeps the flowing shelf.
  const islandOf = (entry: CheckedTitle): IslandSlotKind | undefined => {
    const art = titlePresentation(entry.title);
    return art.menuArt ?? (art.art === 'coastal' ? 'coastal' : undefined);
  };
  const islandKinds = mainStories.map(islandOf);
  const islandHome = !showIntroduction && hasMainStory && islandKinds.every(Boolean) &&
    islandKinds.every(kind => islandKinds.filter(candidate => candidate === kind).length <= (kind === 'coastal' ? 2 : 1));
  // Watching is the primary action. Unavailable titles stay in Parents.
  const ambient = Boolean(onAmbient && featured && ambientArtworkFor(featured));
  const featuredAction = ambient ? 'Settle in' : feature?.action === 'Watch now' ? 'Watch' : feature?.action;
  const preferredId = listed.some((entry) => entry.title.id === returnFocusId)
    ? returnFocusId
    : listed[0]?.title.id;
  // Exactly one control takes the remote's focus when the shelf comes back:
  // the one that was pressed, or, for a press from the introduction, which
  // reports none, How it works.
  const returningToFeatured = Boolean(featured) && returnFocusId === (listed.find((entry) => titlePresentation(entry.title).action === 'Watch now') ?? listed[0])?.title.id;
  const fromIntroduction = returnFocusId === demo?.title.id || returnFocusId === playbackCheck?.title.id;
  // While the picker is open its active chip is the one control asking.
  const requested: ReturnFocusControl | 'learn' | 'profile' | null = saving || choosingProfile ? null
    : returnToHeader ? returnToHeader
    : returnFocusControl === 'parent' ? 'parent'
    : !returnFocusId ? 'watch'
    : returnFocusControl ?? (fromIntroduction ? 'learn' : returningToFeatured ? 'details' : 'poster');
  // A poster that is no longer on the rail cannot take focus; Watch does.
  const returnTo = requested === 'poster' && !otherStories.some((entry) => entry.title.id === preferredId)
    ? 'watch' : requested;
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

  // With cards on the map, each card already names its video, so the sand
  // below holds only what to do with the chosen one.
  const cardsNameIt = islandHome && otherStories.length > 0;
  const cardKinds = islandHome ? [...new Set(otherStories.map((entry) => islandOf(entry)!))] : [];
  const flowing = !islandHome;
  // On the island map the picker takes the row of cards while it is open, so
  // nothing it says sits under a card; the cards come back when it closes.
  const picker = choosingProfile && picking && profiles && onChooseProfile ? (
    <ProfilePicker focusActive disabled={saving || undefined} testID={`${testID}-profiles`} title={PROFILES_KID_TITLE}
      chosenWord={WATCHING_STATE_WORD} chosenLine={whoIsWatching((profiles.find((one) => one.id === activeProfileId) ?? profiles[0]).name)}
      profiles={profiles} activeProfileId={activeProfileId ?? profiles[0].id} onChoose={(profile) => {
        onChooseProfile(profile); setClosingPicker(true);
      }} />
  ) : null;
  const hero = featured && feature ? <View testID={`${testID}-hero`} style={islandHome ? [styles.islandHero, placed(cardsNameIt ? HOME_ISLANDS.ACTIONS : HOME_ISLANDS.HERO)] : styles.hero}>
              <View style={styles.heroCopy}>
                {cardsNameIt ? null : <>
                <Text accessibilityRole="header" numberOfLines={1} style={[styles.featureTitle, CALM_TEXT.section]} testID={`${testID}-video-title`}>{feature.name}</Text>
                <Text style={styles.videoMeta} testID={`${testID}-video-meta`}>{[feature.runtime ?? runtimeLabel(featured.title.durationMs), isBundledBenignStory(featured.title) ? 'Simulated demo' : null].filter(Boolean).join(' · ')}</Text>
                </>}
                <View style={styles.actions}>
                  <CalmButton primary playIcon={!ambient} sound={false} onFocus={() => setFocusedId('watch')} onBlur={() => setFocusedId(null)} testID={`${testID}-watch`} label={featuredAction!} accessibilityLabel={`${featuredAction}: ${feature.name}`}
                    disabled={saving} hasTVPreferredFocus={returnTo === 'watch'} onPress={() => { onLaunchControl?.('watch'); (ambient ? onAmbient! : (onPlay ?? onOpen))(featured); }} />
                  <CalmButton quiet tertiary compact onFocus={() => setFocusedId('details')} onBlur={() => setFocusedId(null)} testID={`${testID}-more-info`} label="Details" accessibilityLabel={`Details: ${feature.name}`} hasTVPreferredFocus={returnTo === 'details'} onPress={() => { onLaunchControl?.('details'); onOpen(featured); }} disabled={saving} />
                </View>
              </View>
            </View> : null;
  const heading = <View testID={`${testID}-heading`} style={styles.sectionHeading}><Text accessibilityRole="header" testID={`${testID}-title`} style={styles.section}>Choose an island</Text></View>;
  // On the map, each environment is named once, over its own cards.
  const environmentHeadings = ENVIRONMENTS.map(({ name, kinds }) => {
    const present = kinds.filter((kind) => cardKinds.includes(kind));
    if (!present.length) return null;
    const id = name.toLowerCase();
    return <View key={id} testID={`${testID}-environment-${id}`} style={[styles.islandHeading, placed(environmentHeadingBox(present))]}>
      <EnvironmentMark forest={name === 'Forest'} />
      <Text accessibilityRole="header" numberOfLines={1} testID={`${testID}-environment-${id}-name`} style={styles.section}>{name}</Text>
    </View>;
  });
  const poster = (entry: CheckedTitle) => {
                const siblings = otherStories.filter(candidate => islandOf(candidate) === islandOf(entry));
                const split = islandHome && siblings.length === 2;
                const focused = focusedId === entry.title.id;
                const selected = featured?.title.id === entry.title.id;
                const label = titlePresentation(entry.title);
                return <TouchableOpacity surfaceKind="tertiary" disabled={saving || undefined} accessibilityState={{ disabled: saving, selected }}
                  key={entry.title.id} testID={`${testID}-poster-${entry.title.id}`} accessibilityRole="button"
                  accessibilityLabel={[label.cardName ?? label.name, label.kind].filter(Boolean).join(', ')} activeOpacity={1}
                  hasTVPreferredFocus={returnTo === 'poster' && entry.title.id === preferredId}
                  onFocus={() => { setFocusedId(entry.title.id); setSelectedId(entry.title.id); onSelectTitle?.(entry.title.id); }} onBlur={() => setFocusedId(null)} onPress={() => {
                    if (!saving) {
                      // Activation can arrive without a native focus event.
                      // Keep Watch and the restored shelf on the opened title.
                      setSelectedId(entry.title.id);
                      onSelectTitle?.(entry.title.id);
                      onLaunchControl?.('poster');
                      onOpen(entry);
                      feedback.confirm();
                    }
                  }}
                  style={[styles.poster, islandHome ? [styles.islandCard, placed(islandChoiceBox(islandOf(entry)!, siblings.indexOf(entry), siblings.length))] : null, split ? styles.splitCard : null, selected ? styles.posterSelected : null, focused ? styles.posterFocused : null]}>
                  <Image source={continuousScenePicture(entry.title) ?? (!label.menuArt && !label.art && shelfPoster(entry) ? { uri: shelfPoster(entry) } : filmStill(label.menuArt ?? label.art))} style={[styles.filmStill, split ? styles.splitPicture : null]} resizeMode="cover" fadeDuration={0} testID={`${testID}-poster-image-${entry.title.id}`} accessible={false} />
                  {selected && !split ? <View testID={`${testID}-selected-${entry.title.id}`} style={styles.selectionMark} pointerEvents="none" accessible={false}><Svg width={scale(32)} height={scale(32)} viewBox="0 0 32 32"><Path d="M6 16L13 23L27 8" fill="none" stroke={WORLD.TEXT} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" /></Svg></View> : null}
                  <View style={[styles.posterCopy, split ? styles.splitCopy : null]}>
                  <Text style={[styles.posterTitle, split ? styles.splitTitle : null, focused ? styles.focusedLabel : null]} numberOfLines={1} testID={`${testID}-poster-title-${entry.title.id}`}>{label.cardName ?? label.name}</Text>
                  {label.kind ? <Text style={[styles.posterQualifier, split ? styles.splitQualifier : null]} numberOfLines={1} testID={`${testID}-poster-qualifier-${entry.title.id}`}>{onAmbient && ambientArtworkFor(entry) ? 'Still scene' : label.selectorMeta ?? label.kind}</Text> : null}
                  </View>
                </TouchableOpacity>;
              };

  return (
    <WorldAppearance.Provider value={!empty && !showIntroduction}><View testID={testID} style={[styles.screen, !empty && !showIntroduction && { backgroundColor: WORLD.BACKGROUND }]}>
      {!empty && !showIntroduction ? <CoastalWorld destination={islandKind(feature?.menuArt ?? feature?.art)} cardKinds={cardKinds} showBoat={feature?.art === 'coastal' || Boolean(feature?.menuArt)} motionEnabled={interfaceMotionEnabled} active={interfaceActive && !choosingProfile} /> : <HomeHarborScene variant={feature?.menuArt ?? feature?.art} immersive={!empty} wideReading={showIntroduction} enabled={interfaceMotionEnabled} active={interfaceActive && !showIntroduction} />}
      <CalmPageHeader wordmark onBack={showIntroduction ? closeIntroduction : undefined} backTestID="picture-hold-dismiss" preferredBack={showIntroduction && !demo}>
          {picking && profiles ? <CalmButton quiet tertiary compact testID={`${testID}-choose-profile`} label={saving ? 'Saving your changes...' : (profiles.find((p) => p.id === activeProfileId) ?? profiles[0]).name}
            disabled={saving} accessibilityLabel="Choose who is watching" hasTVPreferredFocus={!showIntroduction && returnTo === 'profile'}
            onPress={() => { setReturnToHeader(null); setChoosingProfile(!choosingProfile); }} /> : null}
          {!showIntroduction && !empty ? <View style={styles.navigationLink}><CalmButton quiet tertiary compact testID={`${testID}-learn`} label="How it works" accessibilityLabel="How it works" hasTVPreferredFocus={returnTo === 'learn'}
            disabled={saving} onPress={() => { setChoosingProfile(false); setReturnToHeader(null); setShowIntroduction(true); }} /></View> : null}
          {onOpenParentArea ? <View style={styles.navigationLink}><CalmButton quiet tertiary compact testID={`${testID}-parent-area`} label="Parents" accessibilityLabel="Parents: parental controls, needs a PIN" hasTVPreferredFocus={(empty || returnTo === 'parent') && !saving && !showIntroduction} onPress={onOpenParentArea} /></View> : null}
      </CalmPageHeader>
      {flowing ? picker : null}
      {showIntroduction ? <ScrollView style={styles.libraryScroll} showsVerticalScrollIndicator={false}><PictureHoldIntroduction disabled={saving} onDemoDetails={demo ? () => onOpen(demo) : undefined} onPlaybackCheck={playbackCheck ? () => onOpen(playbackCheck) : undefined} onStart={demo ? () => {
        if (!saving) { setShowIntroduction(false); setReturnToHeader('learn'); (onPlay ?? onOpen)(demo); }
      } : undefined} /></ScrollView> : empty ? (
        <StatusNotice
          testID={`${testID}-empty`}
          notice={offline ? BACKEND_UNREACHABLE_EMPTY : NO_TITLES}
        />
      ) : (
        <>
          {offline && flowing ? (
            <View style={styles.banner}>
              <StatusNotice testID={`${testID}-offline`} notice={BACKEND_UNREACHABLE} />
            </View>
          ) : null}
          {flowing ? <ScrollView style={styles.libraryScroll} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
            {hero}
            {otherStories.length > 0 ? heading : null}
            <View style={styles.grid}>
              {otherStories.map(poster)}
            </View>
          </ScrollView> : <View testID={`${testID}-islands`} style={styles.islandLayer} pointerEvents="box-none">
            {picker ? <View testID={`${testID}-picker-panel`} style={[styles.pickerPanel, placed(HOME_ISLANDS.PICKER), { height: undefined, minHeight: scale(HOME_ISLANDS.PICKER.height) }]}>{picker}</View> : <>
              {environmentHeadings}
              {otherStories.map(poster)}
            </>}
            {hero}
            {offline ? <View testID={`${testID}-notice-slot`} style={placed(HOME_ISLANDS.NOTICE)}>
              <StatusNotice testID={`${testID}-offline`} notice={BACKEND_UNREACHABLE} />
            </View> : null}
          </View>}
        </>
      )}
    </View></WorldAppearance.Provider>
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
  scrollContent: { minHeight: scale(820), paddingBottom: scale(12) },
  hero: { position: 'absolute', bottom: 0, width: '100%', minHeight: scale(180), alignItems: 'flex-start', paddingBottom: scale(36) },
  heroCopy: { width: scale(CALM_FLOW.HERO_TITLE_WIDTH), paddingTop: 0, alignItems: 'flex-start' },
  featureTitle: { ...CALM_TEXT.feature, color: WORLD.TEXT, marginTop: scale(0), marginBottom: scale(CALM_SPACE.TIGHT) },
  videoMeta: { ...CALM_TEXT.supporting, color: WORLD.TEXT_DIM, marginBottom: scale(CALM_SPACE.BLOCK) },
  actions: { flexDirection: 'row', alignItems: 'center', gap: scale(20) },
  learn: { flexDirection: 'row', marginTop: scale(8) },
  sectionHeading: { alignItems: 'center', marginTop: scale(16), marginBottom: scale(12) },
  section: { ...CALM_TEXT.section, color: WORLD.TEXT },
  banner: { marginBottom: scale(20) },
  grid: { width: '100%', flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: scale(180), marginTop: scale(100), gap: scale(40) },
  poster: { width: scale(400), minHeight: scale(280), flexDirection: 'column', justifyContent: 'center', padding: scale(12), borderRadius: scale(20), borderWidth: scale(FOCUS_RING_WIDTH), borderColor: WORLD.BORDER, borderBottomWidth: scale(12), backgroundColor: WORLD.SURFACE },
  posterSelected: { borderBottomColor: WORLD.FOCUS_RING },
  posterFocused: { borderColor: WORLD.FOCUS_RING, backgroundColor: WORLD.SURFACE_FOCUSED },
  filmStill: { width: '100%', height: scale(164), borderRadius: scale(10) },
  selectionMark: { position: 'absolute', right: scale(24), top: scale(24), width: scale(44), height: scale(44), borderRadius: scale(22), backgroundColor: WORLD.SURFACE, alignItems: 'center', justifyContent: 'center' },
  posterCopy: { paddingHorizontal: scale(4), paddingTop: scale(8) },
  islandLayer: { ...StyleSheet.absoluteFillObject },
  islandHeading: { flexDirection: 'row', gap: scale(CALM_SPACE.TIGHT), alignItems: 'center', justifyContent: 'center' },
  islandHero: { alignItems: 'flex-start', justifyContent: 'flex-end' },
  islandCard: { minHeight: undefined, justifyContent: 'flex-start' },
  splitCard: { flexDirection: 'row', alignItems: 'center', gap: scale(12) },
  splitPicture: { width: scale(80), height: scale(90) },
  splitCopy: { flex: 1, paddingTop: 0 },
  splitTitle: { fontSize: scale(32), lineHeight: scale(40) },
  splitQualifier: { fontSize: scale(26), lineHeight: scale(34) },
  pickerPanel: { padding: scale(24), paddingBottom: 0, borderRadius: scale(20), borderWidth: scale(FOCUS_RING_WIDTH), borderColor: WORLD.BORDER, backgroundColor: WORLD.SURFACE },
  posterTitle: { ...CALM_TEXT.section, color: WORLD.TEXT },
  posterQualifier: { ...CALM_TEXT.supporting, color: WORLD.TEXT_DIM },
});
export default KidHomeScreen;
