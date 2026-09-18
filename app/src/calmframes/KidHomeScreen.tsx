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
import { CALM_COLORS, CALM_SPACE, CALM_TYPE, scale } from './calmStyles';
import ShieldBadge from './ShieldBadge';
import { CheckedTitle, kidModeTitles } from './titleStatus';
import { useUiCapture } from './uiCapture';
import { KID_HOME_FOCUSED_FRAME, KID_HOME_FRAME } from './uiFrames';

export interface KidHomeScreenProps {
  /** Every title that has been checked, in any state. */
  titles: CheckedTitle[];
  onOpen: (entry: CheckedTitle) => void;
  onOpenParentArea?: () => void;
  testID?: string;
}

const KidHomeScreen = ({
  titles,
  onOpen,
  onOpenParentArea,
  testID = 'kid-home',
}: KidHomeScreenProps) => {
  const listed = kidModeTitles(titles);
  const hiddenCount = titles.length - listed.length;
  const [focusedId, setFocusedId] = React.useState<string | null>(null);

  // The app records what it paints, because Vega gives it no way to read its
  // own pixels. See uiCapture.ts.
  useUiCapture(
    focusedId ? KID_HOME_FOCUSED_FRAME : KID_HOME_FRAME,
    focusedId ? 'poster focused' : 'kid home',
  );

  return (
    <View testID={testID} style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title} testID={`${testID}-title`}>
          Ready to watch
        </Text>
        <Text style={styles.subtitle} testID={`${testID}-subtitle`}>
          {listed.length === 0
            ? 'Nothing is ready yet. A grown up can see what is being checked in the parent area.'
            : 'Every title here has been checked frame by frame.'}
        </Text>
      </View>

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

      <View style={styles.footer}>
        {hiddenCount > 0 ? (
          <Text style={styles.footerText} testID={`${testID}-hidden-count`}>
            {hiddenCount} more {hiddenCount === 1 ? 'title is' : 'titles are'} still
            being checked.
          </Text>
        ) : null}
        {onOpenParentArea ? (
          <TouchableOpacity
            testID={`${testID}-parent-area`}
            accessibilityRole="button"
            accessibilityLabel="Parent area, needs a PIN"
            activeOpacity={1}
            onPress={onOpenParentArea}
            style={styles.parentButton}>
            <Text style={styles.parentLabel}>Parent area</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: CALM_COLORS.BACKGROUND,
    paddingHorizontal: scale(CALM_SPACE.EDGE),
    paddingTop: scale(CALM_SPACE.EDGE),
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
    borderWidth: scale(4),
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
    paddingVertical: scale(CALM_SPACE.ROW),
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  footerText: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
  },
  parentButton: {
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    borderWidth: scale(4),
    borderColor: CALM_COLORS.BORDER,
  },
  parentLabel: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BUTTON),
  },
});

export default KidHomeScreen;
