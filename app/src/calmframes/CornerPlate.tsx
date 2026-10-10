/**
 * A short label on a plate, in the top left corner of the safe area.
 *
 * The Harbor demo has to say what it is for as long as it plays: its holds
 * are practice and nothing in it flashes. That line used to run across the
 * top of the picture as bare text, 100 units down, which is where the card
 * now hangs, and bare cream text over a bright picture can fall below a
 * readable contrast. On a plate it carries its own background, so it reads
 * the same over any picture; in the corner it keeps to a row above the card
 * and well clear of the captions at the bottom.
 *
 * It is a label, not a control: it takes no focus and nothing about it moves.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  PLAYER_LAYOUT,
  scale,
} from './calmStyles';

/** Above the card, which is 3, and below the player's own controls. */
export const PLATE_Z_INDEX = 4;

export interface CornerPlateProps {
  label: string;
  /** The plate gets `${testID}-plate` and its text `${testID}-label`. */
  testID?: string;
}

const CornerPlate = ({ label, testID = 'corner' }: CornerPlateProps) => (
  <View style={styles.plate} pointerEvents="none" testID={`${testID}-plate`}>
    <Text style={styles.label} testID={`${testID}-label`}>
      {label}
    </Text>
  </View>
);

const styles = StyleSheet.create({
  plate: {
    position: 'absolute',
    top: scale(PLAYER_LAYOUT.PLATE_TOP),
    left: scale(PLAYER_LAYOUT.PLATE_LEFT),
    backgroundColor: CALM_COLORS.SURFACE,
    borderColor: CALM_COLORS.BORDER,
    borderWidth: scale(2),
    borderRadius: scale(12),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.ROW),
    zIndex: PLATE_Z_INDEX,
  },
  label: {
    color: CALM_COLORS.TEXT_DIM,
    ...CALM_TEXT.supporting, },
});

export default CornerPlate;
