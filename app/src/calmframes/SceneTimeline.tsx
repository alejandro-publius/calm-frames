/** Read-only scene positions. This component cannot focus, seek or change a cover. */
import React from 'react';
import { StyleSheet, View } from 'react-native';
import { CoverInterval } from './coverSchedule';
import { stripMarks } from './FlashMapStrip';
import { CALM_COLORS, scale } from './calmStyles';

export default function SceneTimeline({ intervals, durationMs, width, currentMs, testID = 'scene-timeline' }: {
  intervals: CoverInterval[]; durationMs: number; width?: number; currentMs?: number; testID?: string;
}) {
  if (!Number.isFinite(durationMs) || durationMs <= 0) return null;
  const marks = stripMarks(intervals, durationMs);
  const trackWidth = width === undefined ? undefined : scale(width);
  const position = (fraction: number): number | `${number}%` => trackWidth === undefined ? `${fraction * 100}%` : fraction * trackWidth;
  return <View testID={`${testID}-track`} style={[styles.track, { width: trackWidth ?? '100%' }]}
    pointerEvents="none" focusable={false} accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    {marks.map((mark, index) => <View key={`${mark.left}-${index}`} testID={`${testID}-mark-${index}`}
      style={[styles.mark, { left: position(mark.left), width: position(mark.width),
        backgroundColor: mark.reason === 'red' ? CALM_COLORS.FAILED : CALM_COLORS.PENDING }]} />)}
    {currentMs !== undefined && Number.isFinite(currentMs) ? <View testID={`${testID}-position`}
      style={[styles.position, { left: position(Math.max(0, Math.min(1, currentMs / durationMs))) }]} /> : null}
  </View>;
}
const styles = StyleSheet.create({
  track: { height: scale(8), borderRadius: scale(4), backgroundColor: CALM_COLORS.SURFACE, overflow: 'hidden' },
  mark: { position: 'absolute', top: 0, bottom: 0 },
  position: { position: 'absolute', top: 0, bottom: 0, width: scale(4), marginLeft: scale(-2), backgroundColor: CALM_COLORS.TEXT },
});
