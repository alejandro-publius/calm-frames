/**
 * The block that says why there is nothing to watch.
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
 * - colour is never the only signal. The tone sets the border colour, and the
 *   title says the same thing in words;
 * - it never offers a way past itself. A notice about a title that did not
 *   pass its check has no play button in it, because there is nothing to play.
 *   Whatever a caller puts in `children` sits below the words, and the screens
 *   only ever put a way back there.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import { Notice, NoticeTone } from './copy';

export interface StatusNoticeProps {
  notice: Notice;
  /** A way back, or a way on. Never a way to play something unchecked. */
  children?: React.ReactNode;
  testID?: string;
}

const TONE_BORDER: Record<NoticeTone, string> = {
  calm: CALM_COLORS.BORDER,
  waiting: CALM_COLORS.PENDING,
  blocked: CALM_COLORS.FAILED,
};

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
    style={[styles.notice, { borderColor: TONE_BORDER[notice.tone] }]}>
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
    padding: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(16),
    borderWidth: scale(FOCUS_RING_WIDTH),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  title: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.CARD_TITLE),
    fontWeight: '600',
  },
  detail: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
});

export default StatusNotice;
