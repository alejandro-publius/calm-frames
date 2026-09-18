/**
 * Who is watching.
 *
 * One row of large targets, used in two places: on the shelf so a kid can say
 * it is them, and in the parent area so a grown up can pick whose settings and
 * whose record they are looking at.
 *
 * The rules it follows are the ones every control in this app follows. Chosen
 * is a fill and a word, focus is the ring, and the two stack rather than
 * fighting: a chosen profile that also has focus shows the chosen fill inside
 * the focus ring, so nobody has to tell two shades of the same colour apart
 * from the sofa. Nothing moves when focus moves, because the border is the
 * same width in both states.
 *
 * Nothing moves when the choice moves either, and that took a change. The word
 * used to sit on the chosen chip, in brackets, which made that chip wider than
 * it was a moment earlier and slid every chip after it along the row. So the
 * chip carries the name and only the name, and the answer is a sentence under
 * the row where its length costs nobody anything. Every chip now renders the
 * same text whoever is chosen, and the test for that is the guard against the
 * word creeping back onto the chip.
 *
 * The chips are a radio group and say so, because a row of five things where
 * exactly one is true is a radio group whether or not it is built from radio
 * buttons, and a screen reader that is told this reads the row as one question
 * rather than five unrelated buttons.
 *
 * The name is the only thing on a chip. What a profile is set to belongs in
 * the parent area, not on a shelf a child is reading.
 */

import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import { Profile } from './profiles';

export interface ProfilePickerProps {
  profiles: Profile[];
  /** Which chip is drawn as chosen. */
  activeProfileId: string;
  onChoose: (profile: Profile) => void;
  /** The line above the row. The question. */
  title: string;
  /**
   * The line under the row. The answer, as a whole sentence.
   *
   * Required rather than optional: a picker whose answer is only a fill is the
   * thing this component exists not to be.
   */
  chosenLine: string;
  /**
   * The state word a screen reader hears on the chosen chip.
   *
   * The shelf says watching, because that is what the row is asking. The
   * parent area says showing, because nobody is watching a settings page and
   * what the chip does there is decide what the screen below it shows.
   */
  chosenWord?: string;
  testID?: string;
}

const ProfilePicker = ({
  profiles,
  activeProfileId,
  onChoose,
  title,
  chosenLine,
  chosenWord = 'watching',
  testID = 'profile-picker',
}: ProfilePickerProps) => {
  const [focusedId, setFocusedId] = React.useState<string | null>(null);

  return (
    <View testID={testID} style={styles.block}>
      <Text
        style={styles.title}
        testID={`${testID}-title`}
        accessibilityRole="header">
        {title}
      </Text>
      <View
        style={styles.row}
        accessibilityRole="radiogroup"
        accessibilityLabel={title}
        aria-label={title}>
        {profiles.map((profile) => {
          const chosen = profile.id === activeProfileId;
          const focused = focusedId === profile.id;
          return (
            <TouchableOpacity
              key={profile.id}
              testID={`${testID}-${profile.id}`}
              accessibilityRole="radio"
              // checked is what a radio carries. selected stays beside it
              // because the rest of the app reads that way today.
              accessibilityState={{ checked: chosen, selected: chosen }}
              accessibilityLabel={`${profile.name}${chosen ? `, ${chosenWord}` : ''}`}
              activeOpacity={1}
              onFocus={() => setFocusedId(profile.id)}
              onBlur={() => setFocusedId(null)}
              onPress={() => onChoose(profile)}
              style={[
                styles.chip,
                chosen ? styles.chipChosen : null,
                focused ? styles.chipFocused : null,
              ]}>
              <Text style={styles.name} testID={`${testID}-${profile.id}-name`}>
                {profile.name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
      <Text style={styles.chosenLine} testID={`${testID}-chosen`}>
        {chosenLine}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  block: { marginBottom: scale(CALM_SPACE.BLOCK) },
  title: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SECTION),
    fontWeight: '600',
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: {
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.ROW),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  /** Chosen is a fill and a word. Focus is the ring. They stack. */
  chipChosen: { backgroundColor: CALM_COLORS.SURFACE_FOCUSED },
  chipFocused: { borderColor: CALM_COLORS.FOCUS_RING },
  name: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    fontWeight: '600',
  },
  /** The word half of "a fill and a word", where it cannot move a control. */
  chosenLine: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
});

export default ProfilePicker;
