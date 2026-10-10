/**
 * Who is watching.
 *
 * One row of large targets, used in two places: on the shelf so a kid can say
 * it is them, and in parental controls so a grown up can pick whose settings
 * and whose record they are looking at.
 *
 * The rules it follows are the ones every control in this app follows. Chosen
 * is a fill and a word, focus is the ring, and the two stack rather than
 * fighting: a chosen profile that also has focus shows the chosen fill inside
 * the focus ring, so nobody has to tell two shades of the same colour apart
 * from the sofa. The chips are quiet at rest, a card with no visible outline,
 * and nothing moves when focus moves, because the ring's width is reserved
 * whether or not a chip has focus.
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
 * parental controls, not on a shelf a child is reading.
 */

import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
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
   * The shelf says watching, because that is what the row is asking. Parental
   * controls say showing, because nobody is watching a settings page and what
   * the chip does there is decide what the page below it shows.
   */
  chosenWord?: string;
  testID?: string;
  disabled?: boolean;
}

const ProfilePicker = ({
  profiles,
  activeProfileId,
  onChoose,
  title,
  chosenLine,
  chosenWord = 'watching',
  testID = 'profile-picker',
  disabled = false,
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
              disabled={disabled || undefined}
              key={profile.id}
              testID={`${testID}-${profile.id}`}
              accessibilityRole="radio"
              // checked is what a radio carries. selected stays beside it
              // because the rest of the app reads that way today.
              accessibilityState={{ checked: chosen, selected: chosen, ...(disabled ? { disabled: true } : {}) }}
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
              <Text style={[styles.name, focused ? styles.focusedLabel : null]} testID={`${testID}-${profile.id}-name`}>
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
  focusedLabel: { textDecorationLine: 'underline' },
  block: { marginBottom: scale(CALM_SPACE.BLOCK) },
  title: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(CALM_SPACE.ROW),
  },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
  /** Quiet at rest: the ring is there, in the card's own colour. */
  chip: {
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.SURFACE,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  /** Chosen is a fill and a word. Focus is the ring. They stack. */
  chipChosen: {
    borderColor: CALM_COLORS.SURFACE_FOCUSED,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  chipFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  name: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
  },
  /** The word half of "a fill and a word", where it cannot move a control. */
  chosenLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
  },
});

export default ProfilePicker;
