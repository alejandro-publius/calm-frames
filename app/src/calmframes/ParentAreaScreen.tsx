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
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { CALM_COLORS, CALM_SPACE, CALM_TYPE, scale } from './calmStyles';
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
import ShieldBadge from './ShieldBadge';
import { CheckedTitle } from './titleStatus';

export interface ParentAreaScreenProps {
  gate: PinGateState;
  onGateChange: (state: PinGateState) => void;
  settings: HouseholdSettings;
  onSettingsChange: (settings: HouseholdSettings) => void;
  log: HideLogStore;
  titles: CheckedTitle[];
  nowMs?: () => number;
  onBack?: () => void;
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
  testID = 'parent-area',
}: ParentAreaScreenProps) => {
  const [unlocked, setUnlocked] = React.useState(false);
  const [entered, setEntered] = React.useState('');
  const [message, setMessage] = React.useState('Enter the PIN to change settings.');

  const press = (digit: string) => {
    const next = `${entered}${digit}`;
    if (next.length < PIN_LENGTH) {
      setEntered(next);
      return;
    }
    const result = attemptPin(gate, next, nowMs());
    onGateChange(result.state);
    setEntered('');
    setMessage(result.message);
    if (result.ok) {
      setUnlocked(true);
    }
  };

  if (!unlocked) {
    return (
      <View testID={testID} style={styles.screen}>
        <Text style={styles.title}>Parent area</Text>
        <Text
          style={styles.message}
          testID={`${testID}-message`}
          accessibilityLiveRegion="polite"
          aria-live="polite">
          {message}
        </Text>
        <Text style={styles.entered} testID={`${testID}-entered`}>
          {'*'.repeat(entered.length)}
        </Text>
        <View style={styles.keypad}>
          {['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].map((digit) => (
            <TouchableOpacity
              key={digit}
              testID={`${testID}-key-${digit}`}
              accessibilityRole="button"
              accessibilityLabel={digit}
              activeOpacity={1}
              hasTVPreferredFocus={digit === '1'}
              onPress={() => press(digit)}
              style={styles.key}>
              <Text style={styles.keyLabel}>{digit}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {onBack ? (
          <TouchableOpacity
            testID={`${testID}-back`}
            accessibilityRole="button"
            accessibilityLabel="Back"
            activeOpacity={1}
            onPress={onBack}
            style={styles.button}>
            <Text style={styles.buttonLabel}>Back</Text>
          </TouchableOpacity>
        ) : null}
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
      <Text style={styles.title}>Parent area</Text>

      <Text style={styles.section}>How strict</Text>
      {PRESET_NAMES.map((name: PresetName) => (
        <TouchableOpacity
          key={name}
          testID={`${testID}-preset-${name}`}
          accessibilityRole="radio"
          accessibilityState={{ selected: settings.preset === name }}
          accessibilityLabel={`${PRESETS[name].title}. ${PRESETS[name].description}`}
          activeOpacity={1}
          onPress={() => choose({ preset: name })}
          style={[styles.row, settings.preset === name ? styles.rowSelected : null]}>
          <Text style={styles.rowTitle}>{PRESETS[name].title}</Text>
          <Text style={styles.rowDetail}>{PRESETS[name].description}</Text>
        </TouchableOpacity>
      ))}

      <Text style={styles.section}>The room</Text>
      <Text style={styles.rowDetail} testID={`${testID}-room`}>
        {describeRoom(settings)}
      </Text>
      <Text style={styles.note}>
        A bigger television or a closer sofa can only add hidden parts. It never
        takes any away.
      </Text>
      <View style={styles.choices}>
        {TV_DIAGONAL_CHOICES_IN.map((inches) => (
          <TouchableOpacity
            key={`tv-${inches}`}
            testID={`${testID}-tv-${inches}`}
            accessibilityRole="radio"
            accessibilityState={{ selected: settings.tvDiagonalIn === inches }}
            accessibilityLabel={`${inches} inch television`}
            activeOpacity={1}
            onPress={() => choose({ tvDiagonalIn: inches })}
            style={[
              styles.choice,
              settings.tvDiagonalIn === inches ? styles.rowSelected : null,
            ]}>
            <Text style={styles.choiceLabel}>{inches}"</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.choices}>
        {SEAT_DISTANCE_CHOICES_IN.map((inches) => (
          <TouchableOpacity
            key={`seat-${inches}`}
            testID={`${testID}-seat-${inches}`}
            accessibilityRole="radio"
            accessibilityState={{ selected: settings.seatDistanceIn === inches }}
            accessibilityLabel={`${Math.round(inches / 12)} feet away`}
            activeOpacity={1}
            onPress={() => choose({ seatDistanceIn: inches })}
            style={[
              styles.choice,
              settings.seatDistanceIn === inches ? styles.rowSelected : null,
            ]}>
            <Text style={styles.choiceLabel}>{Math.round(inches / 12)} ft</Text>
          </TouchableOpacity>
        ))}
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
      {titles.map((entry) => (
        <View
          key={entry.title.id}
          testID={`${testID}-title-${entry.title.id}`}
          style={styles.titleRow}>
          <Text style={styles.rowTitle}>{entry.title.title}</Text>
          <ShieldBadge
            status={entry.status}
            testID={`${testID}-status-${entry.title.id}`}
          />
          {entry.reason ? (
            <Text style={styles.rowDetail}>{entry.reason}</Text>
          ) : null}
        </View>
      ))}

      {onBack ? (
        <TouchableOpacity
          testID={`${testID}-back`}
          accessibilityRole="button"
          accessibilityLabel="Back"
          activeOpacity={1}
          onPress={onBack}
          style={styles.button}>
          <Text style={styles.buttonLabel}>Back</Text>
        </TouchableOpacity>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_COLORS.BACKGROUND, padding: scale(CALM_SPACE.EDGE) },
  content: { paddingBottom: scale(CALM_SPACE.EDGE) },
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
  message: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.BODY),
    marginTop: scale(CALM_SPACE.ROW),
  },
  entered: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SCREEN_TITLE),
    letterSpacing: scale(12),
    minHeight: scale(72),
  },
  keypad: { flexDirection: 'row', flexWrap: 'wrap', maxWidth: scale(600) },
  key: {
    width: scale(160),
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.ROW),
    paddingVertical: scale(CALM_SPACE.ROW),
    borderRadius: scale(12),
    borderWidth: scale(4),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
    alignItems: 'center',
  },
  keyLabel: { color: CALM_COLORS.TEXT, fontSize: scale(CALM_TYPE.SCREEN_TITLE) },
  row: {
    padding: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
    borderRadius: scale(12),
    borderWidth: scale(4),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  rowSelected: {
    borderColor: CALM_COLORS.FOCUS_RING,
    backgroundColor: CALM_COLORS.SURFACE_FOCUSED,
  },
  rowTitle: { color: CALM_COLORS.TEXT, fontSize: scale(CALM_TYPE.BODY), fontWeight: '600' },
  rowDetail: { color: CALM_COLORS.TEXT_DIM, fontSize: scale(CALM_TYPE.SMALL) },
  note: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginTop: scale(CALM_SPACE.TIGHT),
  },
  choices: { flexDirection: 'row', flexWrap: 'wrap', marginTop: scale(CALM_SPACE.TIGHT) },
  choice: {
    marginRight: scale(CALM_SPACE.TIGHT),
    marginBottom: scale(CALM_SPACE.TIGHT),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.ROW),
    borderRadius: scale(10),
    borderWidth: scale(3),
    borderColor: CALM_COLORS.BORDER,
    backgroundColor: CALM_COLORS.SURFACE,
  },
  choiceLabel: { color: CALM_COLORS.TEXT, fontSize: scale(CALM_TYPE.SMALL) },
  logLine: {
    color: CALM_COLORS.TEXT_DIM,
    fontSize: scale(CALM_TYPE.SMALL),
    marginBottom: scale(6),
  },
  titleRow: {
    marginBottom: scale(CALM_SPACE.ROW),
  },
  button: {
    marginTop: scale(CALM_SPACE.BLOCK),
    alignSelf: 'flex-start',
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    borderRadius: scale(12),
    borderWidth: scale(4),
    borderColor: CALM_COLORS.BORDER,
  },
  buttonLabel: { color: CALM_COLORS.TEXT, fontSize: scale(CALM_TYPE.BUTTON) },
});

export default ParentAreaScreen;
