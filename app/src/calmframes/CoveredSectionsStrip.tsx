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
import { WorldAppearance, WORLD } from './CoastalWorld';
import { StyleSheet, Text, View } from 'react-native';
import { COASTAL_COLORS as CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { CoveredSectionsResult } from './coveredSections';
import SceneTimeline from './SceneTimeline';

export const COVERED_SECTIONS_HEADING = 'Scenes covered';

export interface CoveredSectionsStripProps {
  result: CoveredSectionsResult;
  /** Supplied only after the exact prepared ocean rendition has verified. */
  ocean?: boolean;
  /** Strip width in 1080p units; the Details reading column by default. */
  width?: number;
  testID?: string;
}

const CoveredSectionsStrip = ({
  result,
  ocean = false,
  width = 620,
  testID = 'covered-sections',
}: CoveredSectionsStripProps) => {
  const world = React.useContext(WorldAppearance);
  const trackWidth = scale(width);
  const heading = ocean && result.kind === 'ready' ? 'Scenes replaced' : COVERED_SECTIONS_HEADING;
  return (
    <View
      testID={testID}
      style={[styles.block, { maxWidth: trackWidth }]}
      accessible
      accessibilityLabel={`${heading}. ${result.text}`}>
      <View style={styles.summaryRow}>
        <Text style={[styles.heading, world && { color: WORLD.TEXT_DIM }]} testID={`${testID}-heading`}>{heading}</Text>
        <Text style={[styles.line, world && { color: WORLD.TEXT_DIM }]} testID={`${testID}-line`}>{result.text}</Text>
      </View>
      {result.kind === 'ready' ? <SceneTimeline intervals={result.sections} durationMs={result.durationMs} width={width} testID={testID} /> : null}
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
  summaryRow: { width: '100%', flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: scale(12) },
  heading: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
  line: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT_DIM, textAlign: 'left' },
});

export default CoveredSectionsStrip;
