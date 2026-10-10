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
 *
 * Reached from parental controls, behind the PIN: "Credits and licences" in
 * ParentAreaScreen, routed by KidModeScreen's 'credits' view. Behind the PIN
 * rather than in kid mode, because this is a screen for the adult.
 *
 * That route is the point of it. NOTICE ships with the source, which is no use
 * to somebody holding a remote, and CC BY asks for attribution where a person
 * can actually read it. screens.test.tsx has the reachability test, and it was
 * seen red with the button removed.
 *
 * Each entry is a quiet card: the title, the collection it came from, the
 * licence, the credit line, then any condition under those. The one control
 * is the shared button, so its ring is the same ring as everywhere else.
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { CALM_COLORS, CALM_SPACE, CALM_TEXT, scale } from './calmStyles';
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
  useUiCapture(CREDITS_FRAME, 'credits');

  return (
    <ScrollView
      testID={testID}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title} testID={`${testID}-title`}>
          {CREDITS_TITLE}
        </Text>
        <Text style={styles.intro} testID={`${testID}-intro`}>
          {CREDITS_INTRO}
        </Text>
        <Text style={styles.count} testID={`${testID}-count`}>
          {entries.length} {entries.length === 1 ? 'title' : 'titles'}
        </Text>
      </View>

      {entries.map((entry) => (
        <CreditRow
          key={entry.title}
          entry={entry}
          testID={`${testID}-entry-${entry.title}`}
        />
      ))}

      {onBack ? (
        <View style={styles.buttons}>
          <CalmButton
            testID={`${testID}-back`}
            label="Back"
            onPress={onBack}
            hasTVPreferredFocus
          />
        </View>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: CALM_COLORS.BACKGROUND,
    paddingHorizontal: scale(CALM_SPACE.SAFE_X),
    paddingVertical: scale(CALM_SPACE.SAFE_Y),
  },
  content: {
    paddingBottom: scale(CALM_SPACE.SAFE_Y),
  },
  header: {
    marginBottom: scale(CALM_SPACE.BLOCK),
  },
  title: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
  },
  intro: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
    marginTop: scale(CALM_SPACE.TIGHT),
    maxWidth: scale(1500),
  },
  count: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  entry: {
    alignSelf: 'stretch',
    maxWidth: scale(1500),
    marginBottom: scale(CALM_SPACE.TIGHT),
    paddingVertical: scale(CALM_SPACE.ROW),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  entryTitle: {
    ...CALM_TEXT.card,
    color: CALM_COLORS.TEXT,
  },
  collection: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
  },
  license: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  credit: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  condition: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
});

export default CreditsScreen;
