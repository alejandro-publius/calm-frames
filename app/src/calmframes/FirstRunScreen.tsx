/**
 * The first run, for the parent.
 *
 * Four steps, in the order a person can answer them: the PIN, how strict, the
 * room, then twenty seconds on what gets hidden and why. Nothing is skippable
 * except by finishing it, and nothing plays until it is done, because the room
 * and the preset decide what the check has to cover before a title can be
 * called ready.
 *
 * Choices it makes, and why:
 *
 * - the PIN is typed twice. A mistyped PIN on a device with no account and no
 *   recovery locks the parent out of their own settings for good;
 * - the room asks for the television size and the sofa distance rather than
 *   working them out, because a wrong guess here can only ever hide less, and
 *   hiding less is the one thing the setting is not allowed to do;
 * - the explainer is the last step rather than the first. A parent who has
 *   just set a PIN is still reading. A parent who has not started yet is
 *   looking for the button;
 * - it carries the approved sentence about what this is and is not, word for
 *   word, from copy.ts.
 *
 * The PIN steps put the words on the left and the keypad on the right, the
 * way a television asks for a code, so the whole step fits on one screen with
 * nothing to scroll to. The other steps are the same page shape as parental
 * controls: a heading, a helper line, then rows and chips with the same quiet
 * resting look, the same chosen fill and the same focus ring, so a parent
 * meets each control here the way they will meet it again later.
 *
 * Setup remains still: the steps do not slide and nothing counts down on
 * screen. Optional artwork motion belongs to the library and title details.
 *
 * Each list of choices is a radio group and says so, labelled with the
 * question it is asking, and each choice carries `checked` rather than
 * `selected` alone, which is what a radio carries. Without the role a screen
 * reader read three questions as thirteen unrelated buttons. The two room
 * rows also say in words which chip is the chosen one, because a fill colour
 * is not a state everybody on the sofa can read.
 */

import React from 'react';
import TouchableOpacity from './CalmTouchable';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import {
  CALM_CONTROL,
  COASTAL_COLORS as CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
  CHOSEN_WORD,
  EXPLAINER_LINES,
  EXPLAINER_TARGET_SECONDS,
  EXPLAINER_TITLE,
  Notice,
  ROOM_ONLY_ADDS,
  SEAT_DISTANCE_TITLE,
  seatChosen,
  televisionChosen,
  TV_SIZE_TITLE,
} from './copy';
import {
  DEFAULT_SETTINGS,
  describeRoom,
  HouseholdSettings,
  PRESET_NAMES,
  PresetName,
  PRESETS,
  SEAT_DISTANCE_CHOICES_IN,
  TV_DIAGONAL_CHOICES_IN,
} from './household';
import {
  emptyPinGate,
  isValidPin,
  PIN_LENGTH,
  PIN_ROUNDS,
  PinGateState,
  setPin,
} from './parentGate';
import PinKeypad from './PinKeypad';
import StatusNotice from './StatusNotice';
import { useUiCapture } from './uiCapture';
import {
  FIRST_RUN_EXPLAINER_FRAME,
  FIRST_RUN_PIN_FRAME,
  FIRST_RUN_PRESET_FRAME,
  FIRST_RUN_ROOM_FRAME,
} from './uiFrames';

export type FirstRunStep = 'pin' | 'confirm' | 'preset' | 'room' | 'explainer';

export interface FirstRunResult {
  gate: PinGateState;
  settings: HouseholdSettings;
}

export interface FirstRunScreenProps {
  /** Called once, with the PIN set and the settings chosen. */
  onDone: (result: FirstRunResult) => void;
  /**
   * A fresh salt for the PIN.
   *
   * The caller owns this because where random bytes come from is the app's
   * business, not this screen's, and a screen that invented its own would be
   * the wrong place to look for it later.
   */
  newSalt: () => string;
  /** Hash rounds. Tests use a small number; the app uses the default. */
  rounds?: number;
  settings?: HouseholdSettings;
  testID?: string;
}

const STEP_TITLES: Record<FirstRunStep, string> = {
  pin: 'Choose a PIN',
  confirm: 'Confirm your PIN',
  preset: 'Choose a viewing preset',
  room: 'Your TV and seating',
  explainer: EXPLAINER_TITLE,
};

/** The four steps a person counts. Typing the PIN twice is one step. */
const STEP_NUMBER: Record<FirstRunStep, number> = {
  pin: 1,
  confirm: 1,
  preset: 2,
  room: 3,
  explainer: 4,
};
export const FIRST_RUN_STEPS = 4;

/** Under the heading on the strictness step. The same rows are in parental controls. */
const PRESET_STEP_NOTE = 'You can change this later in parental controls.';

/** Under the review of the household, before the library opens. */
const REVIEW_NOTE =
  'Your library shows the titles available with these viewing settings.';

/**
 * The notice beside the keypad.
 *
 * The heading already says what to do, so the notice says why and what to
 * watch out for rather than saying the heading again.
 */
const PIN_NOTICES: Record<'pin' | 'confirm' | 'mismatch', Notice> = {
  pin: {
    title: 'Your PIN keeps parental controls locked',
    detail:
      'Choose four digits you will remember. The PIN stays on this television and is never sent anywhere.',
    tone: 'calm',
  },
  confirm: {
    title: 'Keep your PIN somewhere secure',
    detail:
      'Enter the same four digits again. Your PIN cannot be recovered if you forget it.',
    tone: 'calm',
  },
  mismatch: {
    title: 'Those two did not match',
    detail: 'Start again and enter the same four digits both times.',
    tone: 'blocked',
  },
};

const FirstRunScreen = ({
  onDone,
  newSalt,
  rounds = PIN_ROUNDS,
  settings: initialSettings = DEFAULT_SETTINGS,
  testID = 'first-run',
}: FirstRunScreenProps) => {
  const [step, setStep] = React.useState<FirstRunStep>('pin');
  const [entered, setEntered] = React.useState('');
  const [firstPin, setFirstPin] = React.useState('');
  const [mismatched, setMismatched] = React.useState(false);
  const [settings, setSettings] = React.useState<HouseholdSettings>(initialSettings);
  const [focusedRow, setFocusedRow] = React.useState<string | null>(null);

  const frames = {
    pin: FIRST_RUN_PIN_FRAME,
    confirm: FIRST_RUN_PIN_FRAME,
    preset: FIRST_RUN_PRESET_FRAME,
    room: FIRST_RUN_ROOM_FRAME,
    explainer: FIRST_RUN_EXPLAINER_FRAME,
  };
  useUiCapture(frames[step], `first run, ${step}`);

  const press = (digit: string) => {
    const next = `${entered}${digit}`;
    if (next.length < PIN_LENGTH) {
      setEntered(next);
      return;
    }
    setEntered('');
    if (step === 'pin') {
      setFirstPin(next);
      setMismatched(false);
      setStep('confirm');
      return;
    }
    if (next === firstPin && isValidPin(next)) {
      setMismatched(false);
      setStep('preset');
      return;
    }
    setFirstPin('');
    setMismatched(true);
    setStep('pin');
  };

  const finish = () => {
    onDone({
      gate: setPin(emptyPinGate(), firstPin, newSalt(), rounds),
      settings,
    });
  };

  const moveToStep = (next: 'preset' | 'room' | 'explainer') => {
    setFocusedRow(null);
    setStep(next);
  };

  const header = (
    <View style={styles.header}>
      <CalmPageHeader />
      <View style={styles.brandRow}>
        <Text
          style={styles.step}
          testID={`${testID}-step`}
          accessibilityLabel={`Step ${STEP_NUMBER[step]} of ${FIRST_RUN_STEPS}`}>
          Step {STEP_NUMBER[step]} of {FIRST_RUN_STEPS}
        </Text>
        <Text style={styles.step} testID={`${testID}-brand-line`}>
          A calmer way to watch
        </Text>
      </View>
      <View
        style={styles.progress}
        accessible={false}
        importantForAccessibility="no-hide-descendants">
        {Array.from({ length: FIRST_RUN_STEPS }, (_, index) => (
          <View
            key={index}
            style={[
              styles.progressSegment,
              index < STEP_NUMBER[step] ? styles.progressComplete : null,
            ]}
          />
        ))}
      </View>
      <Text style={styles.title} testID={`${testID}-title`} accessibilityRole="header">
        {STEP_TITLES[step]}
      </Text>
    </View>
  );

  if (step === 'pin' || step === 'confirm') {
    let notice = PIN_NOTICES[step];
    if (step === 'pin' && mismatched) {
      notice = PIN_NOTICES.mismatch;
    }
    return (
      <View testID={testID} style={styles.screen}>
        {header}
        <View style={styles.columns}>
          <View style={styles.aside}>
            <StatusNotice testID={`${testID}-notice`} notice={notice} />
          </View>
          <PinKeypad
            entered={entered.length}
            onDigit={press}
            onDelete={() => setEntered((value) => value.slice(0, -1))}
            idPrefix={testID}
          />
        </View>
      </View>
    );
  }

  if (step === 'preset') {
    return (
      <ScrollView
        testID={testID}
        style={styles.screen}
        contentContainerStyle={styles.content}>
        {header}
        <Text style={styles.helper}>{PRESET_STEP_NOTE}</Text>
        <View
          accessibilityRole="radiogroup"
          accessibilityLabel={STEP_TITLES.preset}
          aria-label={STEP_TITLES.preset}>
          {PRESET_NAMES.map((name: PresetName) => {
            const chosen = settings.preset === name;
            const key = `preset-${name}`;
            return (
              <TouchableOpacity
                key={name}
                testID={`${testID}-preset-${name}`}
                accessibilityRole="radio"
                // checked is what a radio carries. selected stays beside it
                // because the rest of the app reads that way today.
                accessibilityState={{ checked: chosen, selected: chosen }}
                accessibilityLabel={`${PRESETS[name].title}. ${PRESETS[name].description}`}
                activeOpacity={1}
                hasTVPreferredFocus={chosen}
                onFocus={() => setFocusedRow(key)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => setSettings({ ...settings, preset: name })}
                style={[
                  styles.row,
                  chosen ? styles.chosen : null,
                  focusedRow === key ? styles.focused : null,
                ]}>
                <View style={styles.rowText}>
                  <Text style={[styles.rowTitle, focusedRow === key ? styles.focusedLabel : null]}>{PRESETS[name].title}</Text>
                  <Text style={styles.rowDetail}>{PRESETS[name].description}</Text>
                </View>
                <View style={styles.rowState}>
                  {chosen ? (
                    <Text style={styles.rowStateWord}>{CHOSEN_WORD}</Text>
                  ) : null}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
        <View style={styles.buttons}>
          <CalmButton
            testID={`${testID}-next`}
            label="Next"
            onPress={() => moveToStep('room')}
          />
        </View>
      </ScrollView>
    );
  }

  if (step === 'room') {
    return (
      <ScrollView
        testID={testID}
        style={styles.screen}
        contentContainerStyle={styles.content}>
        {header}
        <Text style={styles.helper}>{ROOM_ONLY_ADDS}</Text>

        <Text style={styles.section} accessibilityRole="header">
          {TV_SIZE_TITLE}
        </Text>
        <View
          style={styles.choices}
          accessibilityRole="radiogroup"
          accessibilityLabel={TV_SIZE_TITLE}
          aria-label={TV_SIZE_TITLE}>
          {TV_DIAGONAL_CHOICES_IN.map((inches) => {
            const chosen = settings.tvDiagonalIn === inches;
            const key = `tv-${inches}`;
            return (
              <TouchableOpacity
                key={key}
                testID={`${testID}-tv-${inches}`}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen, selected: chosen }}
                accessibilityLabel={`${inches} inch television${chosen ? ', chosen' : ''}`}
                activeOpacity={1}
                hasTVPreferredFocus={chosen}
                onFocus={() => setFocusedRow(key)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => setSettings({ ...settings, tvDiagonalIn: inches })}
                style={[
                  styles.chip,
                  chosen ? styles.chosen : null,
                  focusedRow === key ? styles.focused : null,
                ]}>
                <Text accessible={false} style={styles.selectionMark}>{chosen ? '✓' : ''}</Text>
                <Text
                  style={[styles.chipLabel, focusedRow === key ? styles.focusedLabel : null]}
                  testID={`${testID}-tv-${inches}-label`}>
                  {inches} inch
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <Text style={styles.chosenLine} testID={`${testID}-tv-chosen`}>
          {televisionChosen(settings.tvDiagonalIn)}
        </Text>

        <Text style={styles.section} accessibilityRole="header">
          {SEAT_DISTANCE_TITLE}
        </Text>
        <View
          style={styles.choices}
          accessibilityRole="radiogroup"
          accessibilityLabel={SEAT_DISTANCE_TITLE}
          aria-label={SEAT_DISTANCE_TITLE}>
          {SEAT_DISTANCE_CHOICES_IN.map((inches) => {
            const chosen = settings.seatDistanceIn === inches;
            const feet = Math.round(inches / 12);
            const key = `seat-${inches}`;
            return (
              <TouchableOpacity
                key={key}
                testID={`${testID}-seat-${inches}`}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen, selected: chosen }}
                accessibilityLabel={`${feet} feet away${chosen ? ', chosen' : ''}`}
                activeOpacity={1}
                onFocus={() => setFocusedRow(key)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => setSettings({ ...settings, seatDistanceIn: inches })}
                style={[
                  styles.chip,
                  chosen ? styles.chosen : null,
                  focusedRow === key ? styles.focused : null,
                ]}>
                <Text accessible={false} style={styles.selectionMark}>{chosen ? '✓' : ''}</Text>
                <Text
                  style={[styles.chipLabel, focusedRow === key ? styles.focusedLabel : null]}
                  testID={`${testID}-seat-${inches}-label`}>
                  {feet} ft
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <Text style={styles.chosenLine} testID={`${testID}-seat-chosen`}>
          {seatChosen(settings.seatDistanceIn)}
        </Text>

        <View style={styles.buttons}>
          <CalmButton
            quiet
            testID={`${testID}-back`}
            label="Back"
            accessibilityLabel="Back to viewing preset"
            onPress={() => moveToStep('preset')}
          />
          <CalmButton
            testID={`${testID}-next`}
            label="Next"
            onPress={() => moveToStep('explainer')}
          />
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      testID={testID}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      {header}
      <View style={styles.review} testID={`${testID}-review`}>
        <Text style={styles.reviewTitle} accessibilityRole="header">
          Your household
        </Text>
        <Text style={styles.reviewLine} testID={`${testID}-review-preset`}>
          {PRESETS[settings.preset].title}
        </Text>
        <Text style={styles.reviewLine} testID={`${testID}-review-room`}>
          {describeRoom(settings)}
        </Text>
        <Text style={styles.reviewNote}>{REVIEW_NOTE}</Text>
      </View>
      <View style={styles.explainer} testID={`${testID}-explainer`}>
        {EXPLAINER_LINES.map((line, index) => (
          <Text
            key={line}
            testID={`${testID}-explainer-line-${index}`}
            style={styles.explainerLine}>
            {line}
          </Text>
        ))}
      </View>
      <Text style={styles.note} testID={`${testID}-reading-time`}>
        About {EXPLAINER_TARGET_SECONDS} seconds to read. You can find it again
        under parental controls.
      </Text>
      <View style={styles.buttons}>
        <CalmButton
          quiet
          testID={`${testID}-back`}
          label="Back"
          accessibilityLabel="Back to TV and seating"
          onPress={() => moveToStep('room')}
        />
        <CalmButton
          testID={`${testID}-done`}
          label="Open library"
          onPress={finish}
          hasTVPreferredFocus
        />
      </View>
    </ScrollView>
  );
};

/**
 * The column at the right edge of a row that holds the word Chosen, in 1080p
 * units. Every row reserves it, so the word moving from one row to another
 * re-wraps nothing and moves nothing.
 */
const STATE_COLUMN = 200;

const styles = StyleSheet.create({
  focusedLabel: { textDecorationLine: 'underline' },
  screen: {
    flex: 1,
    backgroundColor: CALM_COLORS.BACKGROUND,
    paddingHorizontal: scale(CALM_SPACE.SAFE_X),
    paddingVertical: scale(CALM_SPACE.SAFE_Y),
  },
  content: {
    width: '100%',
    maxWidth: scale(1400),
    paddingBottom: scale(CALM_SPACE.SAFE_Y),
  },
  header: { maxWidth: scale(1400), marginBottom: scale(16) },
  brandRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  step: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
  },
  progress: {
    flexDirection: 'row',
    gap: scale(12),
    marginTop: scale(8),
    marginBottom: scale(24),
  },
  progressSegment: {
    width: scale(72),
    borderTopWidth: scale(6),
    borderTopColor: CALM_COLORS.BORDER,
  },
  progressComplete: { borderTopColor: CALM_COLORS.TEXT },
  title: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
  },
  helper: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginBottom: scale(24),
    maxWidth: scale(1160),
  },
  /** The PIN steps: words on the left, the keypad on the right. */
  columns: { flexDirection: 'row', alignItems: 'flex-start' },
  aside: {
    flex: 1,
    maxWidth: scale(960),
    marginRight: scale(CALM_SPACE.EDGE),
  },
  section: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
    marginTop: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(CALM_SPACE.ROW),
  },
  /** A settings row. Quiet at rest: the ring is there, in the card's own colour. */
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: scale(24),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(16),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.SURFACE,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  /** Chosen is a fill and a word. Focus is the ring. They stack. */
  chosen: {
    borderColor: CALM_COLORS.SURFACE_FOCUSED,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  focused: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  rowText: { flex: 1 },
  rowTitle: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
  },
  rowDetail: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(8),
  },
  rowState: {
    width: scale(STATE_COLUMN),
    marginLeft: scale(CALM_SPACE.ROW),
    alignItems: 'flex-end',
  },
  rowStateWord: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT,
  },
  choices: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  selectionMark: { ...CALM_TEXT.supporting, color: CALM_COLORS.TEXT, width: scale(42) },
  chip: {
    flexDirection: 'row', alignItems: 'center',
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.SURFACE,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  chipLabel: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
  },
  /**
   * Which chip in the row above is the chosen one, in words.
   *
   * The same line parental controls draw under the same two rows, from the
   * same copy, because a parent meets these chips twice and they should read
   * the same way both times.
   */
  chosenLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
  },
  review: {
    alignSelf: 'stretch',
    maxWidth: scale(1400),
    padding: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(CALM_CONTROL.RADIUS),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  reviewTitle: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  reviewLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
  },
  reviewNote: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(20),
    maxWidth: scale(1160),
  },
  explainer: {
    marginTop: scale(CALM_SPACE.BLOCK),
    maxWidth: scale(1160),
  },
  explainerLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(20),
  },
  note: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(CALM_SPACE.ROW),
    maxWidth: scale(1160),
  },
  buttons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: scale(CALM_SPACE.ROW),
    marginTop: scale(CALM_SPACE.BLOCK),
  },
});

export default FirstRunScreen;
