/**
 * Covered sections, drawn: a label, a still strip and one sentence.
 *
 * It sits on the Details page under the title's description, so a person sees
 * where the picture will be covered before pressing Watch. It is a picture of
 * the schedule and nothing more: it takes no focus, answers no press, and has
 * no way to seek, so it cannot become a path around the guarded seek. The
 * strip is still, with a fixed height, so the page does not move while it
 * loads. A state with nothing to draw says so in words instead of drawing an
 * empty bar.
 *
 * The marks use the same arithmetic as the technical page's strip, and the
 * same two colours: the ordinary cover and the red flash cover.
 *
 * Named Strip because this Mac's file system cannot tell CoveredSections.tsx
 * from coveredSections.ts, and the resolver then handed back the helper.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { CoveredSectionsResult } from './coveredSections';
import { stripMarks } from './FlashMapStrip';

export const COVERED_SECTIONS_HEADING = 'Covered sections';

export interface CoveredSectionsStripProps {
  result: CoveredSectionsResult;
  /** Strip width in 1080p units; the Details reading column by default. */
  width?: number;
  testID?: string;
}

const CoveredSectionsStrip = ({
  result,
  width = 620,
  testID = 'covered-sections',
}: CoveredSectionsStripProps) => {
  const trackWidth = scale(width);
  const marks = result.kind === 'ready' ? stripMarks(result.sections, result.durationMs) : [];
  return (
    <View
      testID={testID}
      style={[styles.block, { maxWidth: trackWidth }]}
      accessible
      accessibilityLabel={result.text}>
      <Text style={styles.heading} testID={`${testID}-heading`}>
        {COVERED_SECTIONS_HEADING}
      </Text>
      {result.kind === 'ready' ? (
        <View style={[styles.track, { width: trackWidth }]} testID={`${testID}-track`}>
          {marks.map((mark, index) => (
            <View
              key={`${mark.left}-${index}`}
              testID={`${testID}-mark-${index}`}
              style={[
                styles.mark,
                {
                  left: mark.left * trackWidth,
                  width: mark.width * trackWidth,
                  backgroundColor:
                    mark.reason === 'red' ? CALM_COLORS.FAILED : CALM_COLORS.PENDING,
                },
              ]}
            />
          ))}
        </View>
      ) : null}
      <Text style={styles.line} testID={`${testID}-line`}>
        {result.text}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  block: {
    width: '100%',
    alignItems: 'flex-start',
    marginTop: scale(CALM_SPACE.BLOCK),
    gap: scale(CALM_SPACE.TIGHT),
  },
  heading: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
  track: {
    height: scale(28),
    borderRadius: scale(6),
    backgroundColor: CALM_COLORS.SURFACE,
    borderColor: CALM_COLORS.BORDER,
    borderWidth: scale(2),
    overflow: 'hidden',
  },
  mark: { position: 'absolute', top: 0, bottom: 0 },
  line: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
});

export default CoveredSectionsStrip;
