/**
 * The details page, with the still flash map strip.
 *
 * It says what the check found before anything plays: how many parts will be
 * hidden, how long they add up to and where they fall. No preview, no motion.
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TYPE, scale } from './calmStyles';
import { buildCoverIntervals, totalCoveredMs } from './coverSchedule';
import FlashMapStrip from './FlashMapStrip';
import { coverOptionsFor, DEFAULT_SETTINGS, HouseholdSettings } from './household';
import ShieldBadge from './ShieldBadge';
import { CheckedTitle } from './titleStatus';

export interface TitleDetailsScreenProps {
  entry: CheckedTitle;
  settings?: HouseholdSettings;
  onPlay: (entry: CheckedTitle) => void;
  onBack?: () => void;
  testID?: string;
}

const TitleDetailsScreen = ({
  entry,
  settings = DEFAULT_SETTINGS,
  onPlay,
  onBack,
  testID = 'title-details',
}: TitleDetailsScreenProps) => {
  const durationMs = entry.title.durationMs ?? 0;
  const intervals = React.useMemo(
    () =>
      buildCoverIntervals(entry.segments, {
        ...coverOptionsFor(settings),
        durationMs: durationMs > 0 ? durationMs : undefined,
      }),
    [entry.segments, settings, durationMs],
  );
  const [focused, setFocused] = React.useState<string | null>(null);

  const hiddenSeconds = Math.round(totalCoveredMs(intervals) / 1000);

  return (
    <ScrollView
      testID={testID}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      <Text style={styles.title} testID={`${testID}-title`}>
        {entry.title.title}
      </Text>
      <ShieldBadge status={entry.status} testID={`${testID}-badge`} />

      <Text style={styles.summary} testID={`${testID}-summary`}>
        {intervals.length === 0
          ? 'The check found nothing over the flash limits in this title.'
          : `${intervals.length} part${
              intervals.length === 1 ? '' : 's'
            } will be hidden, ${hiddenSeconds} second${
              hiddenSeconds === 1 ? '' : 's'
            } in all. Sound and captions keep playing.`}
      </Text>

      {durationMs > 0 ? (
        <View style={styles.strip}>
          <FlashMapStrip
            intervals={intervals}
            durationMs={durationMs}
            testID={`${testID}-strip`}
          />
        </View>
      ) : null}

      {entry.reason ? (
        <Text style={styles.reason} testID={`${testID}-reason`}>
          {entry.reason}
        </Text>
      ) : null}

      <View style={styles.buttons}>
        <TouchableOpacity
          testID={`${testID}-play`}
          accessibilityRole="button"
          accessibilityLabel={
            entry.status === 'verified'
              ? `Play ${entry.title.title}`
              : 'This title is not checked yet'
          }
          accessibilityState={{ disabled: entry.status !== 'verified' }}
          activeOpacity={1}
          hasTVPreferredFocus
          disabled={entry.status !== 'verified'}
          onFocus={() => setFocused('play')}
          onBlur={() => setFocused(null)}
          onPress={() => onPlay(entry)}
          style={[
            styles.button,
            focused === 'play' ? styles.buttonFocused : null,
            entry.status !== 'verified' ? styles.buttonDisabled : null,
          ]}>
          <Text style={styles.buttonLabel}>
            {entry.status === 'verified' ? 'Play' : 'Not ready'}
          </Text>
        </TouchableOpacity>

        {onBack ? (
          <TouchableOpacity
            testID={`${testID}-back`}
            accessibilityRole="button"
            accessibilityLabel="Back"
            activeOpacity={1}
            onFocus={() => setFocused('back')}
            onBlur={() => setFocused(null)}
            onPress={onBack}
            style={[styles.button, focused === 'back' ? styles.buttonFocused : null]}>
            <Text style={styles.buttonLabel}>Back</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND },
  content: {
    padding: scale(CALM_SPACE.EDGE),
  },
  title: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SCREEN_TITLE),
    fontWeight: '700',
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  summary: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.BLOCK),
  },
  strip: { marginTop: scale(CALM_SPACE.BLOCK) },
  reason: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.ROW),
  },
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
  button: {
    marginRight: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    borderWidth: scale(4),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  buttonFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonLabel: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BUTTON),
    fontWeight: '600',
  },
});

export default TitleDetailsScreen;
