/**
 * Typing a kid's name with a remote.
 *
 * The parent area had no way to type, so a new kid was called Kid or Kid 2
 * and stayed that way. This is the keyboard: the letters in three rows, then
 * Shift, Space and Delete, with the name being typed above them and Save and
 * Cancel below. It is the PIN keypad's shape with more keys, and it keeps the
 * keypad's rules: quiet cards, the saffron ring and the lifted fill on the
 * one key with focus, and the ring's width reserved on every key so nothing
 * moves when focus moves.
 *
 * Why keys rather than the platform's text field. The Kepler fork of React
 * Native ships TextInput with options for a television keyboard, so the API
 * is installed. Nobody on this project has seen that keyboard appear on the
 * Vega Virtual Device, and this change could not be installed to find out.
 * The keypad has been pressed on that device many times, so a name typed on
 * keys built the same way is the path that is known to work. A text field can
 * sit beside these keys later, once the keyboard has been seen.
 *
 * Case takes care of itself. The first letter of each word is a capital and
 * the rest are small, which is how the names in a picker read. Shift turns
 * the next letter the other way, once, and every key shows the case it will
 * type, so the state is never a colour and never a guess.
 *
 * The editor holds the draft and nothing else. It says no to a blank, to a
 * name another chip already carries and to a character past the limit, in
 * words under the field, and hands a name to `onSave` only once none of that
 * is true. Whether the save committed is the caller's to know, so a failed
 * save comes back in as `failure`: the draft is still here, and the notice
 * offers Try again and Cancel. While a save is in flight the keys and both
 * buttons stay in the focus order and ignore presses, as the keypad does for
 * a pending PIN. The draft is never logged, never traced and never put in a
 * test id.
 */

import React from 'react';
import TouchableOpacity from './CalmTouchable';
import { StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import ReadingStop, { READING_STOP_ROOM } from './ReadingStop';
import {
  CALM_CONTROL,
  COASTAL_COLORS as CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
  CANCEL_NAME_LABEL,
  editNameTitle,
  NAME_DELETE_LABEL,
  NAME_EMPTY_HINT,
  nameLengthLine,
  nameProblemLine,
  NAME_SAVING,
  NAME_SHIFT_LABEL,
  NAME_SPACE_LABEL,
  Notice,
  SAVE_NAME_LABEL,
  shiftLabel,
  TRY_NAME_AGAIN_LABEL,
} from './copy';
import {
  MAX_PROFILE_NAME,
  nameProblem,
  Profile,
  ProfileNameProblem,
} from './profiles';
import StatusNotice from './StatusNotice';

export interface ProfileNameEditorProps {
  /** The kid whose name is being typed. The save is keyed by the id, never the name. */
  profile: Profile;
  /** Names the new one may not match: the other kids' and the household's own label. */
  taken: string[];
  /** Called with a trimmed, checked, changed name, and with nothing else. */
  onSave: (name: string) => void;
  onCancel: () => void;
  /** The caller is writing the name down. Keys and buttons ignore presses and keep focus. */
  saving?: boolean;
  /** The last save did not commit. The draft stays and the notice offers Try again. */
  failure?: Notice | null;
  maxLength?: number;
  testID?: string;
}

/** The letters, in the three rows a television keyboard uses. */
const LETTER_ROWS = ['ABCDEFGHIJ', 'KLMNOPQRST', 'UVWXYZ'];

type LetterCase = 'upper' | 'lower';

/** A capital at the start of each word, small letters after it. */
export function caseAt(draft: string): LetterCase {
  return draft.length === 0 || draft.endsWith(' ') ? 'upper' : 'lower';
}

/** The grid, in 1080p units. A letter key is as tall as every other control. */
const KEY_WIDTH = 108;
const KEY_WIDE = 216;
const KEY_GAP = CALM_SPACE.TIGHT;

const ProfileNameEditor = ({
  profile,
  taken,
  onSave,
  onCancel,
  saving = false,
  failure = null,
  maxLength = MAX_PROFILE_NAME,
  testID = 'profile-name',
}: ProfileNameEditorProps) => {
  const [draft, setDraft] = React.useState(profile.name);
  // One shot: the next letter takes the other case, then the rule takes over again.
  const [shifted, setShifted] = React.useState(false);
  // What the last Save press was refused for, cleared by the next key.
  const [problem, setProblem] = React.useState<ProfileNameProblem | null>(null);
  // A letter was refused because the name is as long as the picker can draw.
  const [full, setFull] = React.useState(false);
  const [focusedKey, setFocusedKey] = React.useState<string | null>(null);

  const ruleCase = caseAt(draft);
  const nextCase: LetterCase = shifted
    ? ruleCase === 'upper' ? 'lower' : 'upper'
    : ruleCase;

  const change = (next: string) => {
    setDraft(next);
    setShifted(false);
    setProblem(null);
    setFull(false);
  };

  const type = (letter: string) => {
    if (saving) {
      return;
    }
    if (draft.length >= maxLength) {
      setFull(true);
      return;
    }
    change(draft + (nextCase === 'upper' ? letter.toUpperCase() : letter.toLowerCase()));
  };

  const space = () => {
    if (saving) {
      return;
    }
    // No leading space and no second space in a row: trimming would only take
    // them back out, and a name that looks saved and is not is the one thing
    // this editor must not show.
    if (draft.length === 0 || draft.endsWith(' ')) {
      return;
    }
    if (draft.length >= maxLength) {
      setFull(true);
      return;
    }
    change(`${draft} `);
  };

  const erase = () => {
    if (!saving) {
      change(draft.slice(0, -1));
    }
  };

  const save = () => {
    if (saving) {
      return;
    }
    const name = draft.trim();
    if (name === profile.name) {
      // Nothing to write. Closing is the same as cancelling.
      onCancel();
      return;
    }
    const found = nameProblem(name, taken, maxLength);
    if (found) {
      setProblem(found);
      return;
    }
    onSave(name);
  };

  const cancel = () => {
    if (!saving) {
      onCancel();
    }
  };

  const shownProblem = problem
    ? nameProblemLine(problem, draft.trim(), maxLength)
    : full
      ? nameProblemLine('long', draft, maxLength)
      : null;

  const key = (
    id: string,
    label: string,
    accessibilityLabel: string,
    onPress: () => void,
    options: { wide?: boolean; selected?: boolean; preferred?: boolean } = {},
  ) => {
    const focused = focusedKey === id;
    return (
      <TouchableOpacity
        key={id}
        surfaceKind="keypad"
        traceFocus={false}
        testID={`${testID}-key-${id}`}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        // Not the `disabled` prop: that takes the key out of the focus order
        // at the moment a parent is pressing it. The state blocks the press.
        accessibilityState={{
          disabled: saving,
          ...(options.selected !== undefined ? { selected: options.selected } : {}),
        }}
        activeOpacity={1}
        hasTVPreferredFocus={options.preferred === true}
        onFocus={() => setFocusedKey(id)}
        onBlur={() => setFocusedKey(null)}
        onPress={onPress}
        style={[
          styles.key,
          options.wide ? styles.keyWide : null,
          focused ? styles.keyFocused : null,
        ]}>
        <Text
          testID={`${testID}-key-${id}-label`}
          style={[
            styles.keyLabel,
            focused ? styles.focusedLabel : null,
            saving ? styles.disabledLabel : null,
          ]}>
          {label}
        </Text>
      </TouchableOpacity>
    );
  };

  const letterKey = (letter: string, first: boolean) => {
    const shown = nextCase === 'upper' ? letter.toUpperCase() : letter.toLowerCase();
    return key(
      letter.toLowerCase(),
      shown,
      `${nextCase === 'upper' ? 'Capital' : 'Small'} ${letter}`,
      () => type(letter),
      { preferred: first && !failure },
    );
  };

  return (
    <View testID={testID} style={styles.editor}>
      <Text style={styles.title} accessibilityRole="header" testID={`${testID}-title`}>
        {editNameTitle(profile.name)}
      </Text>
      {/* The count sits at the field's right edge, and a refusal takes its
          place in the same slot, so a refusal moves nothing on the screen.
          The field is a stop the remote can land on, Up from the letters, so
          VoiceView reads the name as it stands; it speaks only what has focus.
          It still announces each change while focus is on a key. */}
      <ReadingStop
        flush
        style={styles.fieldStop}
        testID={`${testID}-field`}
        accessibilityLiveRegion="polite"
        accessibilityLabel={`${draft.length === 0 ? NAME_EMPTY_HINT : draft}. ${
          shownProblem ?? nameLengthLine(draft.length, maxLength)
        }`}>
      <View style={styles.field}>
        <Text
          style={[styles.draft, draft.length === 0 ? styles.hint : null]}
          testID={`${testID}-draft`}>
          {draft.length === 0 ? NAME_EMPTY_HINT : draft}
        </Text>
        <Text
          style={[styles.count, shownProblem ? styles.problem : null]}
          testID={shownProblem ? `${testID}-problem` : `${testID}-count`}>
          {shownProblem ?? nameLengthLine(draft.length, maxLength)}
        </Text>
      </View>
      </ReadingStop>
      <View testID={`${testID}-keys`}>
        {LETTER_ROWS.map((row, rowIndex) => (
          <View key={row} style={styles.row}>
            {[...row].map((letter, index) => letterKey(letter, rowIndex === 0 && index === 0))}
            {rowIndex === LETTER_ROWS.length - 1 ? (
              <>
                {key('shift', NAME_SHIFT_LABEL, shiftLabel(nextCase === 'upper'), () => {
                  if (!saving) {
                    setShifted((value) => !value);
                  }
                }, { wide: true, selected: shifted })}
                {key('space', NAME_SPACE_LABEL, NAME_SPACE_LABEL, space, { wide: true })}
                {key('delete', NAME_DELETE_LABEL, 'Delete the last character', erase, { wide: true })}
              </>
            ) : null}
          </View>
        ))}
      </View>
      {failure ? (
        <View style={styles.block}>
          <StatusNotice testID={`${testID}-failed`} notice={failure}>
            <View style={styles.buttons}>
              <View style={styles.button}>
                <CalmButton
                  testID={`${testID}-retry`}
                  label={saving ? NAME_SAVING : TRY_NAME_AGAIN_LABEL}
                  sound={false}
                  onPress={save}
                  hasTVPreferredFocus
                />
              </View>
              <View style={styles.button}>
                <CalmButton testID={`${testID}-cancel`} label={CANCEL_NAME_LABEL} onPress={cancel} />
              </View>
            </View>
          </StatusNotice>
        </View>
      ) : (
        <View style={styles.buttons}>
          <View style={styles.button}>
            <CalmButton
              testID={`${testID}-save`}
              label={saving ? NAME_SAVING : SAVE_NAME_LABEL}
              // The route confirms a committed change itself, as it does for
              // Add a kid, so the press makes no sound of its own.
              sound={false}
              onPress={save}
            />
          </View>
          <View style={styles.button}>
            <CalmButton testID={`${testID}-cancel`} label={CANCEL_NAME_LABEL} onPress={cancel} />
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  editor: { width: '100%' },
  title: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(CALM_SPACE.ROW),
  },
  /** The name being typed, on a card, with the count at its right edge. */
  field: {
    flexDirection: 'row',
    alignItems: 'baseline',
    paddingVertical: scale(16),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  /** The field's old gap below it, less the room its stop's ring takes. */
  fieldStop: { marginBottom: scale(CALM_SPACE.ROW - READING_STOP_ROOM) },
  draft: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
    flex: 1,
  },
  hint: { color: CALM_COLORS.TEXT_DIM },
  count: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginLeft: scale(CALM_SPACE.ROW),
    maxWidth: scale(960),
    textAlign: 'right',
  },
  /** A refusal, in the count's place and the main text colour. */
  problem: { color: CALM_COLORS.TEXT },
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: scale(KEY_GAP),
  },
  /** A key. Quiet at rest: the ring is there, in the card's own colour. */
  key: {
    width: scale(KEY_WIDTH),
    minHeight: scale(CALM_CONTROL.MIN_HEIGHT),
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: scale(KEY_GAP),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.SURFACE,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  keyWide: { width: scale(KEY_WIDE) },
  keyFocused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  keyLabel: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
  },
  focusedLabel: { textDecorationLine: 'underline' },
  disabledLabel: { color: CALM_COLORS.TEXT_DISABLED },
  block: { marginTop: scale(CALM_SPACE.BLOCK) },
  buttons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: scale(CALM_SPACE.ROW),
  },
  button: {
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
});

export default ProfileNameEditor;
