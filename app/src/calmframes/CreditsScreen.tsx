/**
 * The credits, on the television.
 *
 * Every video Calm Frames was built and measured with is listed here with its
 * licence, the credit line its source asks for, and anything we have to keep
 * doing to be allowed to use it: a share alike licence, the Blender logo
 * exclusion, the Tears of Steel credit scroll, the DVIDS non-endorsement
 * notice, the NASA credit line.
 *
 * Three things this screen will not do:
 *
 * - it will not summarise a credit line. The words are the ones the source
 *   asked for, taken from media/LICENSES.csv without being tidied up;
 * - it will not hide a condition behind a link or a second page. A condition
 *   nobody can see is a condition nobody keeps;
 * - it will not play anything. It is text on the same calm background as every
 *   other screen, so arriving here is a small step in brightness rather than a
 *   flash.
 *
 * The list itself is generated. `credits.ts` and the repository's NOTICE file
 * are both written from the ledger by eval/attribution.py, and CI fails if
 * either drifts, so what a parent reads here is what the repository says.
 */

import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TYPE, scale } from './calmStyles';
import { CREDIT_ENTRIES, CreditEntry } from './credits';
import { useUiCapture } from './uiCapture';
import { CREDITS_FRAME } from './uiFrames';

export const CREDITS_TITLE = 'Credits';

export const CREDITS_INTRO =
  'Calm Frames was built and measured with the videos below. Each one is used under the licence beside it, with the credit its source asks for. Anything we have to keep doing to use it is written under the credit.';

export interface CreditsScreenProps {
  entries?: CreditEntry[];
  onBack?: () => void;
  testID?: string;
}

const CreditRow = ({
  entry,
  testID,
}: {
  entry: CreditEntry;
  testID: string;
}) => (
  <View
    testID={testID}
    accessible
    accessibilityLabel={`${entry.title}. ${entry.license}. ${entry.credit}`}
    aria-label={`${entry.title}. ${entry.license}. ${entry.credit}`}
    style={styles.entry}>
    <Text style={styles.entryTitle} testID={`${testID}-title`}>
      {entry.title}
    </Text>
    <Text style={styles.collection} testID={`${testID}-collection`}>
      {entry.collection}
    </Text>
    <Text style={styles.license} testID={`${testID}-license`}>
      {entry.license}
    </Text>
    <Text style={styles.credit} testID={`${testID}-credit`}>
      {entry.credit}
    </Text>
    {entry.obligations.map((condition, index) => (
      <Text
        key={condition}
        style={styles.condition}
        testID={`${testID}-condition-${index}`}>
        {condition}
      </Text>
    ))}
  </View>
);

const CreditsScreen = ({
  entries = CREDIT_ENTRIES,
  onBack,
  testID = 'credits',
}: CreditsScreenProps) => {
  const [focused, setFocused] = React.useState(false);
  useUiCapture(CREDITS_FRAME, 'credits');

  return (
    <ScrollView
      testID={testID}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      <Text style={styles.title} testID={`${testID}-title`}>
        {CREDITS_TITLE}
      </Text>
      <Text style={styles.intro} testID={`${testID}-intro`}>
        {CREDITS_INTRO}
      </Text>
      <Text style={styles.count} testID={`${testID}-count`}>
        {entries.length} {entries.length === 1 ? 'title' : 'titles'}
      </Text>

      {entries.map(entry => (
        <CreditRow
          key={entry.title}
          entry={entry}
          testID={`${testID}-entry-${entry.title}`}
        />
      ))}

      {onBack ? (
        <View style={styles.buttons}>
          <TouchableOpacity
            testID={`${testID}-back`}
            accessibilityRole="button"
            accessibilityLabel="Back"
            activeOpacity={1}
            hasTVPreferredFocus
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onPress={onBack}
            style={[styles.button, focused ? styles.buttonFocused : null]}>
            <Text style={styles.buttonLabel}>Back</Text>
          </TouchableOpacity>
        </View>
      ) : null}
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
  },
  intro: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
    maxWidth: scale(1500),
  },
  count: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  entry: {
    alignSelf: 'stretch',
    maxWidth: scale(1500),
    marginTop: scale(CALM_SPACE.BLOCK),
    padding: scale(CALM_SPACE.ROW),
    borderRadius: scale(16),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  entryTitle: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.CARD_TITLE),
    fontWeight: '600',
  },
  collection: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  license: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  credit: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  condition: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
  button: {
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
  buttonLabel: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BUTTON),
    fontWeight: '600',
  },
});

export default CreditsScreen;
