/** Shared profile choices: stable checkmark, radio semantics and visible focus. */

import React from 'react';
import { WorldAppearance, WORLD } from './CoastalWorld';
import TouchableOpacity from './CalmTouchable';
import { StyleSheet, Text, View } from 'react-native';
import {
  CALM_CONTROL,
  COASTAL_COLORS as CALM_COLORS,
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
  /** Legacy caller context; selected state is conveyed by the chip itself. */
  chosenLine?: string;
  /** Move focus into a newly opened chooser, without stealing settings focus. */
  focusActive?: boolean;
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
  focusActive = false,
  chosenWord = 'watching',
  testID = 'profile-picker',
  disabled = false,
}: ProfilePickerProps) => {
  const styles = React.useContext(WorldAppearance) ? worldStyles : darkStyles;
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
              // Keep the chip in the remote focus order while its choice is
              // being saved, as the PIN keypad does for a pending attempt.
              accessibilityState={{ checked: chosen, selected: chosen, ...(disabled ? { disabled: true } : {}) }}
              accessibilityLabel={`${profile.name}${chosen ? `, ${chosenWord}` : ''}`}
              hasTVPreferredFocus={focusActive && chosen}
              activeOpacity={1}
              onFocus={() => setFocusedId(profile.id)}
              onBlur={() => setFocusedId(null)}
              onPress={() => {
                if (!disabled) {
                  onChoose(profile);
                }
              }}
              style={[
                styles.chip,
                chosen ? styles.chipChosen : null,
                focused ? styles.chipFocused : null,
              ]}>
              <Text accessible={false} style={styles.selectionMark}>{chosen ? '✓' : ''}</Text>
              <Text style={[styles.name, focused ? styles.focusedLabel : null]} testID={`${testID}-${profile.id}-name`}>
                {profile.name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const makeStyles = (colors: Record<keyof typeof CALM_COLORS, string>) => StyleSheet.create({
  focusedLabel: { textDecorationLine: 'underline' },
  block: { marginBottom: scale(CALM_SPACE.BLOCK) },
  title: {
    ...CALM_TEXT.section,
    color: colors.TEXT,
    marginBottom: scale(CALM_SPACE.ROW),
  },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
  /** Quiet at rest: the ring is there, in the card's own colour. */
  selectionMark: { ...CALM_TEXT.supporting, color: colors.TEXT, width: scale(42) },
  chip: {
    flexDirection: 'row', alignItems: 'center',
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: colors.SURFACE,
    backgroundColor: colors.SURFACE,
  },
  /** Chosen is a fill and a word. Focus is the ring. They stack. */
  chipChosen: {
    borderColor: colors.SURFACE_FOCUSED,
    backgroundColor: colors.SURFACE_FOCUSED,
  },
  chipFocused: {
    borderColor: colors.FOCUS_RING,
    backgroundColor: colors.SURFACE_FOCUSED,
  },
  name: {
    ...CALM_TEXT.control,
    color: colors.TEXT,
  },
  /** The word half of "a fill and a word", where it cannot move a control. */
  chosenLine: {
    ...CALM_TEXT.body,
    color: colors.TEXT,
  },
});

const darkStyles = makeStyles(CALM_COLORS);
const worldStyles = makeStyles({ ...CALM_COLORS, ...WORLD });
export default ProfilePicker;
