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
  /** The line above the row. */
  title: string;
  /**
   * The word in brackets on the chosen chip.
   *
   * The shelf says watching, because that is what the row is asking. The
   * parent area says chosen, the same word the preset rows on that screen
   * already use, because nobody is watching a settings page.
   */
  chosenWord?: string;
  /** True on the shelf, where the first chip should take focus on arrival. */
  preferFocus?: boolean;
  testID?: string;
}

const ProfilePicker = ({
  profiles,
  activeProfileId,
  onChoose,
  title,
  chosenWord = 'watching',
  preferFocus = false,
  testID = 'profile-picker',
}: ProfilePickerProps) => {
  const [focusedId, setFocusedId] = React.useState<string | null>(null);

  return (
    <View testID={testID} style={styles.block}>
      <Text style={styles.title} testID={`${testID}-title`}>
        {title}
      </Text>
      <View style={styles.row}>
        {profiles.map((profile, index) => {
          const chosen = profile.id === activeProfileId;
          const focused = focusedId === profile.id;
          return (
            <TouchableOpacity
              key={profile.id}
              testID={`${testID}-${profile.id}`}
              accessibilityRole="radio"
              accessibilityState={{ selected: chosen }}
              accessibilityLabel={`${profile.name}${chosen ? `, ${chosenWord}` : ''}`}
              activeOpacity={1}
              hasTVPreferredFocus={preferFocus && index === 0}
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
                {chosen ? ` (${chosenWord})` : ''}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
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
});

export default ProfilePicker;
