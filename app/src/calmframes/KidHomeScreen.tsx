/**
 * Kid mode: the shelf.
 *
 * What it does not do matters as much as what it does:
 *
 * - it never lists a title whose map did not verify. The list it renders comes
 *   from kidModeTitles, so an unchecked title cannot reach the grid by any
 *   route;
 * - nothing plays a preview. There is no autoplaying video and no motion
 *   anywhere on this screen;
 * - a poster's picture is a still: one the catalog published, or Harbor's own
 *   signed scene still (shelf.ts). No title borrows another title's picture,
 *   and a title with none keeps a plain block;
 * - every poster carries the shield, and focus is a thick ring rather than a
 *   colour change or a wobble.
 *
 * When there is nothing to show it says so rather than showing an empty room.
 * The two ways that happens read differently, because they are different: no
 * title has finished being checked yet, or the service that publishes checks
 * cannot be reached. The second one is not a reason to show anything
 * unchecked, so the shelf keeps whatever already carries its own check, which
 * is the title bundled inside the app.
 */

import React from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import CalmButton from './CalmButton';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
  BACKEND_UNREACHABLE,
  BACKEND_UNREACHABLE_EMPTY,
  KID_HOME_SUBTITLE,
  KID_HOME_TITLE,
  NO_TITLES,
  PROFILES_KID_TITLE,
  WATCHING_STATE_WORD,
  whoIsWatching,
} from './copy';
import ProfilePicker from './ProfilePicker';
import { Profile } from './profiles';
import { shelfLabel, shelfPoster, spokenShelfLabel } from './shelf';
import ShieldBadge from './ShieldBadge';
import StatusNotice from './StatusNotice';
import { CheckedTitle, kidModeTitles } from './titleStatus';
import { useUiCapture } from './uiCapture';
import {
  KID_HOME_EMPTY_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_FRAME,
  KID_HOME_OFFLINE_FRAME,
  KID_HOME_PROFILES_FRAME,
} from './uiFrames';

export interface KidHomeScreenProps {
  /** Every title that has been checked, in any state. */
  titles: CheckedTitle[];
  onOpen: (entry: CheckedTitle) => void;
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
}

const KidHomeScreen = ({
  titles,
  onOpen,
  onOpenParentArea,
  offline = false,
  profiles,
  activeProfileId,
  onChooseProfile,
  testID = 'kid-home',
  saving = false,
}: KidHomeScreenProps) => {
  const listed = kidModeTitles(titles);
  const hiddenCount = titles.length - listed.length;
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
    frame = KID_HOME_PROFILES_FRAME;
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
      <View style={styles.header}>
        <Text style={styles.title} testID={`${testID}-title`}>
          {KID_HOME_TITLE}
        </Text>
        {empty ? null : (
          <Text style={styles.subtitle} testID={`${testID}-subtitle`}>
            {saving ? 'Saving who is watching' : KID_HOME_SUBTITLE}
          </Text>
        )}
      </View>

      {picking && profiles && onChooseProfile ? (
        <ProfilePicker
          disabled={saving || undefined}
          testID={`${testID}-profiles`}
          title={PROFILES_KID_TITLE}
          chosenWord={WATCHING_STATE_WORD}
          chosenLine={whoIsWatching(
            (profiles.find((one) => one.id === activeProfileId) ?? profiles[0]).name,
          )}
          profiles={profiles}
          activeProfileId={activeProfileId ?? profiles[0].id}
          onChoose={onChooseProfile}
        />
      ) : null}

      {empty ? (
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
          <ScrollView
            contentContainerStyle={styles.grid}
            horizontal={false}
            showsVerticalScrollIndicator={false}>
            {listed.map((entry, index) => {
              const focused = focusedId === entry.title.id;
              const poster = shelfPoster(entry);
              const label = shelfLabel(entry.title);
              return (
                <TouchableOpacity
                  disabled={saving || undefined}
                  accessibilityState={saving ? { disabled: true } : undefined}
                  key={entry.title.id}
                  testID={`${testID}-poster-${entry.title.id}`}
                  accessibilityRole="button"
                  accessibilityLabel={`${spokenShelfLabel(label)}, checked`}
                  activeOpacity={1}
                  hasTVPreferredFocus={index === 0}
                  onFocus={() => setFocusedId(entry.title.id)}
                  onBlur={() => setFocusedId(null)}
                  onPress={() => onOpen(entry)}
                  style={[styles.poster, focused ? styles.posterFocused : null]}>
                  {poster ? (
                    <Image
                      source={{ uri: poster }}
                      style={styles.posterImage}
                      // A still, never cropped, so a burned-in label stays
                      // whole, and drawn without a fade: nothing on this
                      // screen moves by itself.
                      resizeMode="contain"
                      fadeDuration={0}
                      accessible={false}
                      testID={`${testID}-poster-image-${entry.title.id}`}
                    />
                  ) : (
                    <View style={styles.posterImage} />
                  )}
                  <View style={styles.posterText}>
                    <Text
                      style={styles.posterTitle}
                      numberOfLines={2}
                      testID={`${testID}-poster-title-${entry.title.id}`}>
                      {label.name}
                    </Text>
                    {label.qualifier ? (
                      <Text
                        style={styles.posterQualifier}
                        numberOfLines={2}
                        testID={`${testID}-poster-qualifier-${entry.title.id}`}>
                        {label.qualifier}
                      </Text>
                    ) : null}
                  </View>
                  <ShieldBadge
                    status={entry.status}
                    testID={`${testID}-badge-${entry.title.id}`}
                  />
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </>
      )}

      <View style={styles.footer}>
        {hiddenCount > 0 ? (
          <Text style={styles.footerText} testID={`${testID}-hidden-count`}>
            {hiddenCount} more {hiddenCount === 1 ? 'title is' : 'titles are'} still
            being checked.
          </Text>
        ) : null}
        {onOpenParentArea ? (
          <CalmButton
            testID={`${testID}-parent-area`}
            label="Parent area"
            accessibilityLabel="Parent area, needs a PIN"
            onPress={onOpenParentArea}
          />
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: CALM_COLORS.BACKGROUND,
    paddingHorizontal: scale(CALM_SPACE.SAFE_X),
    paddingTop: scale(CALM_SPACE.SAFE_Y),
    paddingBottom: scale(CALM_SPACE.SAFE_Y),
  },
  header: { marginBottom: scale(CALM_SPACE.BLOCK) },
  title: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SCREEN_TITLE),
    fontWeight: '700',
  },
  subtitle: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  banner: { marginBottom: scale(CALM_SPACE.BLOCK) },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  poster: {
    width: scale(320),
    marginRight: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(CALM_SPACE.BLOCK),
    padding: scale(CALM_SPACE.TIGHT),
    borderRadius: scale(14),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  posterFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  posterImage: {
    width: '100%',
    // The signed stills are 16:9, so the block is too and nothing letterboxes.
    aspectRatio: 16 / 9,
    borderRadius: scale(8),
    // The block a poster sits in before its picture is there, and the whole
    // picture for a title with no still. uiFrames.ts counts it either way.
    backgroundColor: CALM_COLORS.BORDER,
  },
  posterText: { marginVertical: scale(CALM_SPACE.TIGHT) },
  posterTitle: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    fontWeight: '600',
  },
  // The second line. TEXT_DIM holds the text floor on the resting card and
  // on the focused one; shelf.test.tsx measures both.
  posterQualifier: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
  },
  footer: {
    paddingTop: scale(CALM_SPACE.ROW),
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  footerText: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
  },
});

export default KidHomeScreen;
