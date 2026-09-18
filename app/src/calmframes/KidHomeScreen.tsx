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
} from './copy';
import ShieldBadge from './ShieldBadge';
import StatusNotice from './StatusNotice';
import { CheckedTitle, kidModeTitles } from './titleStatus';
import { useUiCapture } from './uiCapture';
import {
  KID_HOME_EMPTY_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_FRAME,
  KID_HOME_OFFLINE_FRAME,
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
  testID?: string;
}

const KidHomeScreen = ({
  titles,
  onOpen,
  onOpenParentArea,
  offline = false,
  testID = 'kid-home',
}: KidHomeScreenProps) => {
  const listed = kidModeTitles(titles);
  const hiddenCount = titles.length - listed.length;
  const [focusedId, setFocusedId] = React.useState<string | null>(null);
  const empty = listed.length === 0;

  // The app records what it paints, because Vega gives it no way to read its
  // own pixels. See uiCapture.ts.
  let frame = KID_HOME_FRAME;
  let reason = 'kid home';
  if (empty) {
    frame = KID_HOME_EMPTY_FRAME;
    reason = offline ? 'shelf empty, service unreachable' : 'shelf empty';
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
            {KID_HOME_SUBTITLE}
          </Text>
        )}
      </View>

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
              return (
                <TouchableOpacity
                  key={entry.title.id}
                  testID={`${testID}-poster-${entry.title.id}`}
                  accessibilityRole="button"
                  accessibilityLabel={`${entry.title.title}, checked`}
                  activeOpacity={1}
                  hasTVPreferredFocus={index === 0}
                  onFocus={() => setFocusedId(entry.title.id)}
                  onBlur={() => setFocusedId(null)}
                  onPress={() => onOpen(entry)}
                  style={[styles.poster, focused ? styles.posterFocused : null]}>
                  {entry.title.posterUrl ? (
                    <Image
                      source={{ uri: entry.title.posterUrl }}
                      style={styles.posterImage}
                      // A still. Nothing on this screen plays by itself.
                      testID={`${testID}-poster-image-${entry.title.id}`}
                    />
                  ) : (
                    <View style={[styles.posterImage, styles.posterBlank]} />
                  )}
                  <Text style={styles.posterTitle} numberOfLines={2}>
                    {entry.title.title}
                  </Text>
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
    height: scale(180),
    borderRadius: scale(8),
  },
  posterBlank: { backgroundColor: CALM_COLORS.BORDER },
  posterTitle: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginVertical: scale(CALM_SPACE.TIGHT),
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
