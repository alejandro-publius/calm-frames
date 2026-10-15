/**
 * The flash map, as a still strip.
 *
 * A child picking a title can see where the hidden parts are before it starts,
 * which is the difference between a surprise and something they already know
 * about. It is a still: no motion, no animation, nothing that plays.
 *
 * It draws the schedule, not the flashes. Each mark is an interval the player
 * will cover, which includes the guard band, so what the strip shows is what
 * the picture will actually do.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { CoverInterval, totalCoveredMs } from './coverSchedule';

export interface FlashMapStripProps {
  intervals: CoverInterval[];
  durationMs: number;
  /** Strip width in 1080p units. */
  width?: number;
  showCaption?: boolean;
  /** Readable time scale and key for the title-details page. */
  showKey?: boolean;
  holdLabel?: string;
  testID?: string;
}

/** A mark thinner than this is hard to see across a room, so it is widened. */
export const MINIMUM_MARK_FRACTION = 0.004;

function timelineTime(durationMs: number): string {
  const seconds = Math.floor(Math.max(0, durationMs) / 1000);
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}

export interface StripMark {
  /** Left edge as a fraction of the strip, 0 to 1. */
  left: number;
  /** Width as a fraction of the strip, 0 to 1. */
  width: number;
  reason: 'general' | 'red' | 'pattern';
}

/** Where the marks go. Pulled out so the arithmetic can be tested on its own. */
export function stripMarks(
  intervals: CoverInterval[],
  durationMs: number,
): StripMark[] {
  if (!(durationMs > 0)) {
    return [];
  }
  return intervals.map((interval) => {
    const left = Math.max(0, Math.min(1, interval.startMs / durationMs));
    const raw = (interval.endMs - interval.startMs) / durationMs;
    const width = Math.min(1 - left, Math.max(MINIMUM_MARK_FRACTION, raw));
    return { left, width, reason: interval.reason };
  });
}

/** Plain wording for a screen reader, since a strip says nothing out loud. */
export function describeStrip(
  intervals: CoverInterval[],
  durationMs: number,
): string {
  if (intervals.length === 0) {
    return 'Nothing above the flash limits was found.';
  }
  const seconds = Math.max(1, Math.round(totalCoveredMs(intervals) / 1000));
  const parts = intervals.length;
  const minutes = Math.max(1, Math.round(durationMs / 60_000));
  const duration = durationMs < 60_000 ? `${Math.round(durationMs / 1000)} seconds` : `about ${minutes} minute${minutes === 1 ? '' : 's'}`;
  return `${parts} scheduled cover${parts === 1 ? '' : 's'}, ${seconds} second${
    seconds === 1 ? '' : 's'
  } in all, spread through ${duration}.`;
}

const FlashMapStrip = ({
  intervals,
  durationMs,
  width = 1200,
  showCaption = true,
  showKey = false,
  holdLabel = 'Picture hold',
  testID = 'flash-map-strip',
}: FlashMapStripProps) => {
  const marks = stripMarks(intervals, durationMs);
  const stripWidth = scale(width);
  const description = describeStrip(intervals, durationMs);
  const hasRedHold = marks.some(mark => mark.reason === 'red');
  const hasOtherHold = marks.some(mark => mark.reason !== 'red');
  const keyDescription = marks.length > 0
    ? `${hasOtherHold ? `${holdLabel} marks show when the picture holds. ` : ''}${hasRedHold ? 'Red flash hold marks show holds for red flashes. ' : ''}Sound and captions continue.`
    : 'There are no scheduled picture holds.';

  return (
    <View testID={testID} accessible accessibilityLabel={showKey
      ? `${description} From 0:00 to ${timelineTime(durationMs)}. ${keyDescription}`
      : description}>
      <View style={[styles.track, { width: stripWidth }]}>
        {marks.map((mark, index) => (
          <View
            key={`${mark.left}-${index}`}
            testID={`${testID}-mark-${index}`}
            style={[
              styles.mark,
              {
                left: mark.left * stripWidth,
                width: mark.width * stripWidth,
                backgroundColor:
                  mark.reason === 'red' ? CALM_COLORS.FAILED : CALM_COLORS.PENDING,
              },
            ]}
          />
        ))}
      </View>
      {showKey ? (
        <>
          <View style={styles.scale}>
            <Text style={styles.time} testID={`${testID}-start`}>0:00</Text>
            <Text style={styles.time} testID={`${testID}-middle`}>{timelineTime(durationMs / 2)}</Text>
            <Text style={styles.time} testID={`${testID}-end`}>{timelineTime(durationMs)}</Text>
          </View>
          <View style={styles.key}>
            <View style={styles.keyItem}><View style={styles.visibleSwatch} />
              <Text style={styles.time}>{marks.length === 0 ? 'No scheduled holds' : 'Picture visible'}</Text></View>
            {hasOtherHold ? <View style={styles.keyItem}>
              <View style={[styles.holdSwatch, { backgroundColor: CALM_COLORS.PENDING }]} />
              <Text style={styles.time}>{holdLabel}</Text></View> : null}
            {hasRedHold ? <View style={styles.keyItem}>
              <View style={[styles.holdSwatch, { backgroundColor: CALM_COLORS.FAILED }]} />
              <Text style={styles.time}>Red flash hold</Text></View> : null}
          </View>
          {marks.length > 0 ? <Text style={styles.keyNote}>Sound and captions continue during every hold.</Text> : null}
        </>
      ) : null}
      {showCaption ? <Text style={styles.caption} testID={`${testID}-caption`}>
        {description}
      </Text> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  scale: { flexDirection: 'row', justifyContent: 'space-between', marginTop: scale(12) },
  time: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM },
  key: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'flex-start', gap: scale(32), marginTop: scale(24) },
  keyItem: { flexDirection: 'row', alignItems: 'center', gap: scale(12) },
  visibleSwatch: { width: scale(28), height: scale(28), borderRadius: scale(6), borderWidth: scale(2), borderColor: CALM_COLORS.BORDER, backgroundColor: CALM_COLORS.SURFACE },
  holdSwatch: { width: scale(28), height: scale(28), borderRadius: scale(3) },
  keyNote: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left', marginTop: scale(20) },
  track: {
    height: scale(28),
    borderRadius: scale(6),
    backgroundColor: CALM_COLORS.SURFACE,
    borderColor: CALM_COLORS.BORDER,
    borderWidth: scale(2),
    overflow: 'hidden',
  },
  mark: {
    position: 'absolute',
    top: 0,
    bottom: 0,
  },
  caption: {
    marginTop: scale(CALM_SPACE.TIGHT),
    color: CALM_COLORS.TEXT_DIM,
    ...CALM_TEXT.supporting, },
});

export default FlashMapStrip;
