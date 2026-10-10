/**
 * The block that says why there is nothing to watch, and every other state.
 *
 * Every empty state and every error state in Calm Frames is this one
 * component, so they are the same shape, the same size and the same distance
 * from the edge of the screen wherever they appear. A person who has read one
 * of them can read all of them.
 *
 * Three rules it keeps:
 *
 * - it announces itself. A state that arrives while someone is looking
 *   elsewhere is no use if it is silent, so the block is a polite live region
 *   and carries its own words as its label;
 * - colour is never the only signal. The tone sets the colour of the bar down
 *   the block's left edge, and the title says the same thing in words;
 * - it never offers a way past itself. A notice about a title that did not
 *   pass its check has no play button in it, because there is nothing to play.
 *   Whatever a caller puts in `children` sits below the words, and the screens
 *   only ever put a way back there.
 *
 * The tone used to be a ring all the way round the block, the same width as
 * the focus ring. That made a notice look like a control waiting for focus,
 * and on a page of quiet cards it was the one thing drawn in an outline. A
 * bar down one edge is the shape a television uses for a message, and it
 * paints no new colour: the fill is the card colour every other frame already
 * has, and uiFrames.ts counts fills, not borders.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
import { Notice, NoticeTone } from './copy';

export interface StatusNoticeProps {
  notice: Notice;
  /** A way back, or a way on. Never a way to play something unchecked. */
  children?: React.ReactNode;
  testID?: string;
}

const TONE_BAR: Record<NoticeTone, string> = {
  calm: CALM_COLORS.BORDER,
  waiting: CALM_COLORS.PENDING,
  blocked: CALM_COLORS.FAILED,
};

/**
 * The bar down the left edge, in 1080p units.
 *
 * A little wider than the focus ring, so it reads as a mark on the card rather
 * than as one side of an outline.
 */
const BAR_WIDTH = 8;

const StatusNotice = ({
  notice,
  children,
  testID = 'status-notice',
}: StatusNoticeProps) => (
  <View
    testID={testID}
    accessible
    accessibilityLiveRegion="polite"
    aria-live="polite"
    accessibilityLabel={`${notice.title}. ${notice.detail}`}
    aria-label={`${notice.title}. ${notice.detail}`}
    style={[styles.notice, { borderLeftColor: TONE_BAR[notice.tone] }]}>
    <Text style={styles.title} testID={`${testID}-title`}>
      {notice.title}
    </Text>
    <Text style={styles.detail} testID={`${testID}-detail`}>
      {notice.detail}
    </Text>
    {children}
  </View>
);

const styles = StyleSheet.create({
  notice: {
    alignSelf: 'stretch',
    maxWidth: scale(1500),
    paddingVertical: scale(CALM_SPACE.BLOCK),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(16),
    borderLeftWidth: scale(BAR_WIDTH),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  title: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
  },
  detail: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
});

export default StatusNotice;
