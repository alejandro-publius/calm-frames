/**
 * The parent area, behind a local PIN.
 *
 * Four things live here and nothing else:
 *
 *   the preset, the television size and the seat distance, which can only add
 *   hides;
 *   what was hidden and when;
 *   every title's status, including the ones kid mode will not list;
 *   the PIN itself.
 *
 * The screen renders the keypad until the gate is open. It never renders the
 * settings behind it in a way a child could reach by pressing back, because
 * the locked state does not mount them at all.
 *
 * The locked state has three readings, and they are different enough to say
 * differently: nothing typed yet, a wrong PIN with the tries left, and locked
 * out for a minute. All three are the same notice block as every other state
 * in the app, so a parent who has seen one has seen them all. A household with
 * no PIN set is a fourth: the keypad is useless there, so it is not drawn.
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
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
  EXPLAINER_TITLE,
  Notice,
  noticeForTitle,
  PARENT_AREA_TITLE,
  PIN_LOCKED_TITLE,
  PIN_NOT_SET,
  PIN_PROMPT,
  PIN_WRONG_TITLE,
  ROOM_ONLY_ADDS,
} from './copy';
import {
  describeRoom,
  HouseholdSettings,
  PRESET_NAMES,
  PRESETS,
  PresetName,
  SEAT_DISTANCE_CHOICES_IN,
  TV_DIAGONAL_CHOICES_IN,
} from './household';
import { describeHideEntry, HideLogStore, totalHiddenMs } from './hideLog';
import { attemptPin, PIN_LENGTH, PinGateState } from './parentGate';
import PinKeypad from './PinKeypad';
import ShieldBadge from './ShieldBadge';
import StatusNotice from './StatusNotice';
import { CheckedTitle } from './titleStatus';
import { useUiCapture } from './uiCapture';
import {
  PARENT_LOCKED_FRAME,
  PARENT_OPEN_FRAME,
  PARENT_WRONG_PIN_FRAME,
} from './uiFrames';

export interface ParentAreaScreenProps {
  gate: PinGateState;
  onGateChange: (state: PinGateState) => void;
  settings: HouseholdSettings;
  onSettingsChange: (settings: HouseholdSettings) => void;
  log: HideLogStore;
  titles: CheckedTitle[];
  nowMs?: () => number;
  onBack?: () => void;
  /** Offered only when no PIN exists, to send the parent to the first run. */
  onSetPin?: () => void;
  /** Opens the credits. Behind the PIN, because it is a parent's screen. */
  onCredits?: () => void;
  testID?: string;
}

const ParentAreaScreen = ({
  gate,
  onGateChange,
  settings,
  onSettingsChange,
  log,
  titles,
  nowMs = Date.now,
  onBack,
  onSetPin,
  onCredits,
  testID = 'parent-area',
}: ParentAreaScreenProps) => {
  const [unlocked, setUnlocked] = React.useState(false);
  const [entered, setEntered] = React.useState('');
  const [notice, setNotice] = React.useState<Notice>(
    gate.record ? PIN_PROMPT : PIN_NOT_SET,
  );
  const [focusedRow, setFocusedRow] = React.useState<string | null>(null);
  const wrongPin = notice.tone === 'blocked';

  let frame = PARENT_LOCKED_FRAME;
  let reason = 'parent area locked';
  if (unlocked) {
    frame = PARENT_OPEN_FRAME;
    reason = 'parent area open';
  } else if (wrongPin) {
    frame = PARENT_WRONG_PIN_FRAME;
    reason = 'parent area, wrong PIN';
  }
  useUiCapture(frame, reason);

  const press = (digit: string) => {
    const next = `${entered}${digit}`;
    if (next.length < PIN_LENGTH) {
      setEntered(next);
      return;
    }
    const now = nowMs();
    const result = attemptPin(gate, next, now);
    onGateChange(result.state);
    setEntered('');
    if (result.ok) {
      setUnlocked(true);
      setNotice(PIN_PROMPT);
      return;
    }
    const lockedOut =
      result.state.lockedUntilMs !== null && now < result.state.lockedUntilMs;
    setNotice({
      title: lockedOut ? PIN_LOCKED_TITLE : PIN_WRONG_TITLE,
      detail: result.message,
      tone: 'blocked',
    });
  };

  if (!unlocked) {
    return (
      <View testID={testID} style={styles.screen}>
        <Text style={styles.title}>{PARENT_AREA_TITLE}</Text>
        <View style={styles.block}>
          <StatusNotice testID={`${testID}-message`} notice={notice} />
        </View>
        {gate.record ? (
          <PinKeypad entered={entered.length} onDigit={press} idPrefix={testID} />
        ) : null}
        <View style={styles.buttons}>
          {!gate.record && onSetPin ? (
            <CalmButton
              testID={`${testID}-set-pin`}
              label="Set a PIN"
              onPress={onSetPin}
              hasTVPreferredFocus
            />
          ) : null}
          {onBack ? (
            <View style={styles.secondButton}>
              <CalmButton testID={`${testID}-back`} label="Back" onPress={onBack} />
            </View>
          ) : null}
        </View>
      </View>
    );
  }

  const choose = (change: Partial<HouseholdSettings>) =>
    onSettingsChange({ ...settings, ...change });

  return (
    <ScrollView
      testID={`${testID}-open`}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      <Text style={styles.title}>{PARENT_AREA_TITLE}</Text>

      <Text style={styles.section}>How strict</Text>
      {PRESET_NAMES.map((name: PresetName) => {
        const chosen = settings.preset === name;
        return (
          <TouchableOpacity
            key={name}
            testID={`${testID}-preset-${name}`}
            accessibilityRole="radio"
            accessibilityState={{ selected: chosen }}
            accessibilityLabel={`${PRESETS[name].title}. ${PRESETS[name].description}`}
            activeOpacity={1}
            onFocus={() => setFocusedRow(`preset-${name}`)}
            onBlur={() => setFocusedRow(null)}
            onPress={() => choose({ preset: name })}
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

      <Text style={styles.section}>The room</Text>
      <Text style={styles.rowDetail} testID={`${testID}-room`}>
        {describeRoom(settings)}
      </Text>
      <Text style={styles.note}>{ROOM_ONLY_ADDS}</Text>
      <View style={styles.choices}>
        {TV_DIAGONAL_CHOICES_IN.map((inches) => {
          const chosen = settings.tvDiagonalIn === inches;
          return (
            <TouchableOpacity
              key={`tv-${inches}`}
              testID={`${testID}-tv-${inches}`}
              accessibilityRole="radio"
              accessibilityState={{ selected: chosen }}
              accessibilityLabel={`${inches} inch television${chosen ? ', chosen' : ''}`}
              activeOpacity={1}
              onFocus={() => setFocusedRow(`tv-${inches}`)}
              onBlur={() => setFocusedRow(null)}
              onPress={() => choose({ tvDiagonalIn: inches })}
              style={[
                styles.choice,
                chosen ? styles.rowSelected : null,
                focusedRow === `tv-${inches}` ? styles.rowFocused : null,
              ]}>
              <Text style={styles.choiceLabel}>{inches} inch</Text>
            </TouchableOpacity>
          );
        })}
      </View>
      <View style={styles.choices}>
        {SEAT_DISTANCE_CHOICES_IN.map((inches) => {
          const chosen = settings.seatDistanceIn === inches;
          const feet = Math.round(inches / 12);
          return (
            <TouchableOpacity
              key={`seat-${inches}`}
              testID={`${testID}-seat-${inches}`}
              accessibilityRole="radio"
              accessibilityState={{ selected: chosen }}
              accessibilityLabel={`${feet} feet away${chosen ? ', chosen' : ''}`}
              activeOpacity={1}
              onFocus={() => setFocusedRow(`seat-${inches}`)}
              onBlur={() => setFocusedRow(null)}
              onPress={() => choose({ seatDistanceIn: inches })}
              style={[
                styles.choice,
                chosen ? styles.rowSelected : null,
                focusedRow === `seat-${inches}` ? styles.rowFocused : null,
              ]}>
              <Text style={styles.choiceLabel}>{feet} ft</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <Text style={styles.section}>What was hidden</Text>
      <Text style={styles.rowDetail} testID={`${testID}-total`}>
        {log.entries.length === 0
          ? 'Nothing has been hidden yet.'
          : `${log.entries.length} part${
              log.entries.length === 1 ? '' : 's'
            }, ${Math.round(totalHiddenMs(log) / 1000)} seconds in all.`}
      </Text>
      {log.entries.slice(0, 20).map((entry, index) => (
        <Text
          key={`${entry.atMs}-${index}`}
          testID={`${testID}-log-${index}`}
          style={styles.logLine}>
          {describeHideEntry(entry)}
        </Text>
      ))}

      <Text style={styles.section}>Titles</Text>
      {titles.map((entry) => {
        const titleNotice = noticeForTitle(entry);
        return (
          <View
            key={entry.title.id}
            testID={`${testID}-title-${entry.title.id}`}
            style={styles.titleRow}>
            <Text style={styles.rowTitle}>{entry.title.title}</Text>
            <ShieldBadge
              status={entry.status}
              testID={`${testID}-status-${entry.title.id}`}
            />
            {titleNotice ? (
              <Text
                style={styles.rowDetail}
                testID={`${testID}-reason-${entry.title.id}`}>
                {titleNotice.detail}
              </Text>
            ) : null}
          </View>
        );
      })}

      <Text style={styles.section}>{EXPLAINER_TITLE}</Text>
      {EXPLAINER_LINES.map((line, index) => (
        <Text
          key={line}
          testID={`${testID}-explainer-line-${index}`}
          style={styles.explainerLine}>
          {line}
        </Text>
      ))}

      {onBack || onCredits ? (
        <View style={styles.buttons}>
          {onBack ? (
            <CalmButton testID={`${testID}-back`} label="Back" onPress={onBack} />
          ) : null}
          {onCredits ? (
            <CalmButton
              testID={`${testID}-credits`}
              label="Credits and licences"
              onPress={onCredits}
            />
          ) : null}
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
  content: { paddingBottom: scale(CALM_SPACE.SAFE_Y) },
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
  block: {
    marginTop: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.BLOCK),
  },
  row: {
    padding: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
    borderRadius: scale(12),
    borderWidth: scale(FOCUS_RING_WIDTH),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  /** Chosen is a fill and a word. Focus is the ring. They stack. */
  rowSelected: { backgroundColor: CALM_COLORS.SURFACE_FOCUSED },
  rowFocused: { borderColor: CALM_COLORS.FOCUS_RING },
  rowTitle: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    fontWeight: '600',
  },
  rowDetail: { color: CALM_COLORS.TEXT_DIM, fontSize: scale(CALM_TYPE.SMALL) },
  note: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
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
  logLine: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginBottom: scale(6),
  },
  explainerLine: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  titleRow: {
    marginBottom: scale(CALM_SPACE.ROW),
  },
  buttons: {
    flexDirection: 'row',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
  secondButton: { marginLeft: scale(CALM_SPACE.ROW) },
});

export default ParentAreaScreen;
