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
 * No motion anywhere, including here: the steps do not slide and nothing
 * counts down on screen.
 *
 * Each list of choices is a radio group and says so, labelled with the
 * question it is asking, and each choice carries `checked` rather than
 * `selected` alone, which is what a radio carries. Without the role a screen
 * reader read three questions as thirteen unrelated buttons. The two rooms
 * rows also say in words which chip is the chosen one, because a fill colour
 * is not a state everybody on the sofa can read.
 */

import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import CalmButton from './CalmButton';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
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
  confirm: 'Type the PIN again',
  preset: 'How strict should it be',
  room: 'Your television and your sofa',
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

const PIN_NOTICES: Record<'pin' | 'confirm' | 'mismatch', Notice> = {
  pin: {
    title: 'Choose a four digit PIN',
    detail:
      'This keeps the settings where a child cannot change them. It stays on this device and it is never sent anywhere.',
    tone: 'calm',
  },
  confirm: {
    title: 'Type it again',
    detail: 'There is no way to recover a PIN on this device, so it is worth checking.',
    tone: 'calm',
  },
  mismatch: {
    title: 'Those two did not match',
    detail: 'Start again and choose a four digit PIN.',
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

  const header = (
    <View style={styles.header}>
      <View style={styles.brandRow}>
        <Text style={styles.step} testID={`${testID}-step`}>
          Step {STEP_NUMBER[step]} of {FIRST_RUN_STEPS}
        </Text>
        <Text style={styles.step} testID={`${testID}-brand-line`}>
          A calmer way to watch
        </Text>
      </View>
      <Text style={styles.title} testID={`${testID}-title`}>
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
        <View style={styles.block}>
          <StatusNotice testID={`${testID}-notice`} notice={notice} />
        </View>
        <PinKeypad
          entered={entered.length}
          onDigit={press}
          onDelete={() => setEntered((value) => value.slice(0, -1))}
          idPrefix={testID}
        />
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
        <View
          accessibilityRole="radiogroup"
          accessibilityLabel={STEP_TITLES.preset}
          aria-label={STEP_TITLES.preset}>
          {PRESET_NAMES.map((name: PresetName, index) => {
            const chosen = settings.preset === name;
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
                hasTVPreferredFocus={index === 0}
                onFocus={() => setFocusedRow(`preset-${name}`)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => setSettings({ ...settings, preset: name })}
                style={[
                  styles.row,
                  chosen ? styles.rowSelected : null,
                  focusedRow === `preset-${name}` ? styles.rowFocused : null,
                ]}>
                <Text style={styles.rowTitle}>
                  {PRESETS[name].title}
                  {chosen ? ' (chosen)' : ''}
                </Text>
                <Text style={styles.rowDetail}>{PRESETS[name].description}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <View style={styles.buttons}>
          <CalmButton
            testID={`${testID}-next`}
            label="Next"
            onPress={() => setStep('room')}
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
        <Text style={styles.note}>{ROOM_ONLY_ADDS}</Text>

        <Text style={styles.section} accessibilityRole="header">
          {TV_SIZE_TITLE}
        </Text>
        <View
          style={styles.choices}
          accessibilityRole="radiogroup"
          accessibilityLabel={TV_SIZE_TITLE}
          aria-label={TV_SIZE_TITLE}>
          {TV_DIAGONAL_CHOICES_IN.map((inches, index) => {
            const chosen = settings.tvDiagonalIn === inches;
            return (
              <TouchableOpacity
                key={`tv-${inches}`}
                testID={`${testID}-tv-${inches}`}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen, selected: chosen }}
                accessibilityLabel={`${inches} inch television${chosen ? ', chosen' : ''}`}
                activeOpacity={1}
                hasTVPreferredFocus={index === 0}
                onFocus={() => setFocusedRow(`tv-${inches}`)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => setSettings({ ...settings, tvDiagonalIn: inches })}
                style={[
                  styles.choice,
                  chosen ? styles.rowSelected : null,
                  focusedRow === `tv-${inches}` ? styles.rowFocused : null,
                ]}>
                <Text
                  style={styles.choiceLabel}
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
            return (
              <TouchableOpacity
                key={`seat-${inches}`}
                testID={`${testID}-seat-${inches}`}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen, selected: chosen }}
                accessibilityLabel={`${feet} feet away${chosen ? ', chosen' : ''}`}
                activeOpacity={1}
                onFocus={() => setFocusedRow(`seat-${inches}`)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => setSettings({ ...settings, seatDistanceIn: inches })}
                style={[
                  styles.choice,
                  chosen ? styles.rowSelected : null,
                  focusedRow === `seat-${inches}` ? styles.rowFocused : null,
                ]}>
                <Text
                  style={styles.choiceLabel}
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
            testID={`${testID}-next`}
            label="Next"
            onPress={() => setStep('explainer')}
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
        <Text style={styles.section} accessibilityRole="header">
          Your household
        </Text>
        <Text style={styles.explainerLine} testID={`${testID}-review-preset`}>
          {PRESETS[settings.preset].title}
        </Text>
        <Text style={styles.explainerLine} testID={`${testID}-review-room`}>
          {describeRoom(settings)}
        </Text>
        <Text style={styles.note}>
          A title waits for a new check if this room needs a stricter map.
        </Text>
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
        About {EXPLAINER_TARGET_SECONDS} seconds to read. It is here in the parent
        area whenever you want it again.
      </Text>
      <View style={styles.buttons}>
        <CalmButton
          testID={`${testID}-done`}
          label="Open checked library"
          onPress={finish}
          hasTVPreferredFocus
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  review: {
    backgroundColor: CALM_COLORS.SURFACE,
    borderRadius: scale(12),
    padding: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(CALM_SPACE.BLOCK),
  },
  screen: {
    flex: 1,
    backgroundColor: CALM_COLORS.BACKGROUND,
    paddingHorizontal: scale(CALM_SPACE.SAFE_X),
    paddingVertical: scale(CALM_SPACE.SAFE_Y),
  },
  content: { paddingBottom: scale(CALM_SPACE.SAFE_Y) },
  header: { marginBottom: scale(CALM_SPACE.BLOCK) },
  brandRow: { flexDirection: 'row', justifyContent: 'space-between' },
  step: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  title: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SCREEN_TITLE),
    fontWeight: '700',
  },
  section: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SECTION),
    fontWeight: '600',
    marginTop: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  block: { marginBottom: scale(CALM_SPACE.BLOCK) },
  explainer: {
    alignSelf: 'stretch',
    maxWidth: scale(1500),
    padding: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(16),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  explainerLine: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginBottom: scale(CALM_SPACE.ROW),
  },
  note: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.ROW),
  },
  row: {
    padding: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  rowSelected: { backgroundColor: CALM_COLORS.SURFACE_FOCUSED },
  rowFocused: { borderColor: CALM_COLORS.FOCUS_RING },
  rowTitle: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    fontWeight: '600',
  },
  rowDetail: { color: CALM_COLORS.TEXT_DIM, fontSize: scale(CALM_TYPE.SMALL) },
  choices: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  choice: {
    marginRight: scale(CALM_SPACE.TIGHT),
    marginBottom: scale(CALM_SPACE.TIGHT),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.ROW),
    borderRadius: scale(10),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  choiceLabel: { color: CALM_COLORS.TEXT, fontSize: scale(CALM_TYPE.SMALL) },
  /**
   * Which chip in the row above is the chosen one, in words.
   *
   * The same line the parent area draws under the same two rows, from the same
   * copy, because a parent meets these chips twice and they should read the
   * same way both times.
   */
  chosenLine: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
});

export default FirstRunScreen;
