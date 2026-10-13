/**
 * Parental controls, behind a local PIN.
 *
 * Five things live here and nothing else:
 *
 *   whose settings are being changed, when the household has kids in it;
 *   the preset, the television size and the seat distance, which can only add
 *   hides;
 *   what was hidden and when;
 *   interface preferences, the chime, and every title's status, including the
 *   ones kid mode will not list;
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
 * no PIN set is a fourth: the keypad is useless there, so it is not drawn. The
 * words sit on the left and the keypad on the right, the way a television
 * asks for a code, so the whole of it fits on one screen.
 *
 * The open state is a page: one heading, a line under it saying what the page
 * is for, then groups. Each group is a section heading over rows, and a row is
 * a primary label, a short helper line and, where there is a choice, the word
 * Chosen at its right edge. That word sits in a column of fixed width on every
 * row, so choosing another row changes which row carries the word and moves
 * nothing else.
 *
 * Controls are quiet at rest: a card with no visible outline. Focus is the
 * saffron ring and the lifted fill together, and the ring's width is reserved
 * on every control whether or not it has focus, so nothing moves when focus
 * moves. The colours each state paints are declared in uiFrames.ts and read
 * back off the rendered screen by test/calmframes/uiCapture.test.tsx, so the
 * fills here are the fills those frames expect, in the order they expect them.
 *
 * Removing a kid asks first, in that same notice block, because it takes their
 * settings and their record with it and neither comes back. It is two presses
 * on this screen rather than a dialog: CLAUDE.md rules out anything that
 * blocks events on Vega, and this app has no browser to put a modal in. While
 * the question is up it stands where the buttons were, so there is one thing
 * being asked and Add a kid is out of reach until it is answered.
 */

import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import CalmButton from './CalmButton';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
  ADD_KID_LABEL,
  BACK_TO_LIBRARY_LABEL,
  CHECKED_TITLES_TITLE,
  CHIME_NOTE,
  CHIME_OFF_LABEL,
  CHIME_ON_LABEL,
  CHIME_ROW_TITLE,
  CHIME_SECTION_TITLE,
  CHOSEN_WORD,
  CREDITS_LABEL,
  EVERYONE_LABEL,
  EXPLAINER_LINES,
  EXPLAINER_TITLE,
  HIDDEN_TITLE,
  hiddenSummary,
  hidesByDay,
  keepKidLabel,
  nextKidName,
  Notice,
  noticeForTitle,
  nothingHiddenFor,
  NOTHING_HIDDEN_YET,
  PARENTAL_CONTROLS_LEAD,
  PARENTAL_CONTROLS_TITLE,
  PIN_LOCKED_TITLE,
  PIN_NOT_SET,
  PIN_PROMPT,
  PIN_SAVE_FAILED,
  PIN_WRONG_TITLE,
  PROFILE_ONLY_ADDS,
  PROFILES_FULL,
  PROFILES_PARENT_TITLE,
  removeKidLabel,
  removeKidPrompt,
  ROOM_ONLY_ADDS,
  ROOM_TITLE,
  SAVING_CHANGES,
  seatChosen,
  SEAT_DISTANCE_TITLE,
  sectionFor,
  SET_PIN_LABEL,
  SETTINGS_STATE_WORD,
  STRICTNESS_TITLE,
  televisionChosen,
  TV_SIZE_TITLE,
  whoseSettingsThese,
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
import ProfilePicker from './ProfilePicker';
import {
  addProfile,
  allProfileHides,
  canAddProfile,
  DEFAULT_PROFILE_NAME,
  describeFloorEffect,
  emptyProfileLogs,
  EVERYONE_ID,
  Family,
  logForProfile,
  Profile,
  ProfileLogs,
  removeProfile,
  setChimeEnabled,
  setFloor,
  setProfileSettings,
} from './profiles';
import ShieldBadge from './ShieldBadge';
import { titlePresentation } from './TitleArtwork';
import StatusNotice from './StatusNotice';
import { CheckedTitle } from './titleStatus';
import { useUiCapture } from './uiCapture';
import {
  PARENT_LOCKED_FRAME,
  PARENT_OPEN_FRAME,
  PARENT_PROFILE_FRAME,
  PARENT_REMOVE_KID_FRAME,
  PARENT_WRONG_PIN_FRAME,
} from './uiFrames';

/**
 * How many lines of the record the screen draws.
 *
 * The store keeps two hundred. Twenty is as many as reads as a list rather
 * than a wall from across a room, and the summary above them says so when
 * there are more, because a count that does not match the lines under it is
 * the kind of quiet untruth this record cannot carry.
 */
const LOG_LINES_SHOWN = 20;

export interface ParentAreaScreenProps {
  gate: PinGateState;
  onGateChange: (state: PinGateState) => void | Promise<void>;
  settings: HouseholdSettings;
  onSettingsChange: (settings: HouseholdSettings) => void;
  log: HideLogStore;
  /**
   * The kids, when this household has made any.
   *
   * Left out, this screen is what it always was: one household setting and one
   * log. Given, the picker at the top decides whose settings the sections
   * under it are changing, and the household itself is the first choice in
   * that picker because what it is set to is the floor under every kid.
   *
   * The PIN is not in here. There is one for the household, and this screen is
   * already behind it.
   */
  family?: Family;
  onFamilyChange?: (family: Family) => void;
  /** One hide log per profile id. */
  profileLogs?: ProfileLogs;
  titles: CheckedTitle[];
  nowMs?: () => number;
  onBack?: () => void;
  /** Offered only when no PIN exists, to send the parent to the first run. */
  onSetPin?: () => void;
  /** Opens the credits. Behind the PIN, because it is a parent's screen. */
  onCredits?: () => void;
  testID?: string;
  saving?: boolean;
}

const ParentAreaScreen = ({
  gate,
  onGateChange,
  settings,
  onSettingsChange,
  log,
  family,
  onFamilyChange,
  profileLogs = emptyProfileLogs(),
  titles,
  nowMs = Date.now,
  onBack,
  onSetPin,
  onCredits,
  testID = 'parent-area',
  saving = false,
}: ParentAreaScreenProps) => {
  const [unlocked, setUnlocked] = React.useState(false);
  const [entered, setEntered] = React.useState('');
  const [savingPin, setSavingPin] = React.useState(false);
  const savingPinRef = React.useRef(false);
  // Whose settings the sections below are changing. The household first,
  // because it is the floor and a parent reads down from it.
  const [editingId, setEditingId] = React.useState<string>(EVERYONE_ID);
  const [notice, setNotice] = React.useState<Notice>(
    gate.record ? PIN_PROMPT : PIN_NOT_SET,
  );
  const [focusedRow, setFocusedRow] = React.useState<string | null>(null);
  // Which kid the screen has asked about removing, if it has asked. Held by
  // id rather than as a flag, so a question asked about Robin cannot be
  // answered about Sam if the picker moves underneath it.
  const [askedToRemove, setAskedToRemove] = React.useState<string | null>(null);
  const wrongPin = notice.tone === 'blocked';

  const editingKid = Boolean(
    family && family.profiles.some((profile) => profile.id === editingId),
  );
  // A family always has somebody in it, so the last kid has no Remove button
  // and so no question to ask about them either.
  const removable = Boolean(family && editingKid && family.profiles.length > 1);
  const confirmingRemoval = removable && askedToRemove === editingId;

  let frame = PARENT_LOCKED_FRAME;
  let reason = 'parent area locked';
  if (unlocked && confirmingRemoval) {
    frame = PARENT_REMOVE_KID_FRAME;
    reason = 'parent area, asking before removing a kid';
  } else if (unlocked && editingKid) {
    frame = PARENT_PROFILE_FRAME;
    reason = 'parent area, one kid';
  } else if (unlocked) {
    frame = PARENT_OPEN_FRAME;
    reason = 'parent area open';
  } else if (wrongPin) {
    frame = PARENT_WRONG_PIN_FRAME;
    reason = 'parent area, wrong PIN';
  }
  useUiCapture(frame, reason);

  const press = (digit: string) => {
    if (savingPinRef.current || saving) {
      return;
    }
    const next = `${entered}${digit}`;
    if (next.length < PIN_LENGTH) {
      setEntered(next);
      return;
    }
    const now = nowMs();
    const result = attemptPin(gate, next, now);
    setEntered('');
    const finish = () => {
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
    const change = onGateChange(result.state);
    if (change) {
      savingPinRef.current = true;
      setSavingPin(true);
      change
        .then(finish)
        .catch(() => {
          setNotice(PIN_SAVE_FAILED);
        })
        .finally(() => {
          savingPinRef.current = false;
          setSavingPin(false);
        });
    } else {
      finish();
    }
  };

  if (!unlocked) {
    const offersSetPin = !gate.record && Boolean(onSetPin);
    return (
      <View testID={testID} style={styles.screen}>
        <View style={styles.header}>
          <Text style={styles.title} accessibilityRole="header">
            {PARENTAL_CONTROLS_TITLE}
          </Text>
        </View>
        <View style={styles.columns}>
          <View style={styles.aside}>
            <StatusNotice testID={`${testID}-message`} notice={notice} />
            {offersSetPin || onBack ? (
              <View style={styles.buttons}>
                {offersSetPin ? (
                  <View style={styles.button}>
                    <CalmButton
                      disabled={saving || undefined}
                      testID={`${testID}-set-pin`}
                      label={SET_PIN_LABEL}
                      onPress={onSetPin}
                      hasTVPreferredFocus
                    />
                  </View>
                ) : null}
                {onBack ? (
                  <View style={styles.button}>
                    <CalmButton
                      disabled={saving || undefined}
                      testID={`${testID}-back`}
                      label={BACK_TO_LIBRARY_LABEL}
                      onPress={onBack}
                    />
                  </View>
                ) : null}
              </View>
            ) : null}
          </View>
          {gate.record ? (
            <PinKeypad
              entered={entered.length}
              onDigit={press}
              onDelete={() => {
                if (!savingPinRef.current && !saving) {
                  setEntered((value) => value.slice(0, -1));
                }
              }}
              idPrefix={testID}
              disabled={savingPin || saving}
            />
          ) : null}
        </View>
      </View>
    );
  }

  // Who is being edited, and what they are set to. With no family this is the
  // household and nothing else, which is what this screen was before profiles.
  const editingProfile: Profile | undefined = family
    ? family.profiles.find((profile) => profile.id === editingId)
    : undefined;
  const shown: HouseholdSettings = editingProfile
    ? editingProfile.settings
    : family?.floor ?? settings;

  const choose = (change: Partial<HouseholdSettings>) => {
    if (saving) { return; }
    if (family && onFamilyChange) {
      onFamilyChange(
        editingProfile
          ? setProfileSettings(family, editingProfile.id, change)
          : setFloor(family, change),
      );
      return;
    }
    onSettingsChange({ ...settings, ...change });
  };

  // The picker's own list: the household, then the kids.
  const pickable: Profile[] = family
    ? [
        { id: EVERYONE_ID, name: EVERYONE_LABEL, settings: family.floor },
        ...family.profiles,
      ]
    : [];

  const shownLog: HideLogStore = family
    ? editingProfile
      ? logForProfile(profileLogs, editingProfile.id)
      : allProfileHides(profileLogs)
    : log;

  const floorEffect =
    family && editingProfile ? describeFloorEffect(family, editingProfile) : null;

  // Whose sections these are. Null with no picker on screen, so a household
  // that has never made a profile reads exactly what it read before.
  const whose = family && onFamilyChange ? editingProfile?.name ?? EVERYONE_LABEL : null;

  // The lines actually drawn, and the days they fall on.
  const shownEntries = shownLog.entries.slice(0, LOG_LINES_SHOWN);
  const days = hidesByDay(shownEntries, nowMs());

  // The state of every control is the accessibility state, so a screen reader
  // and the press handler agree about it while a save is in flight.
  const blocked = saving ? { disabled: true } : {};

  return (
    <ScrollView
      testID={`${testID}-open`}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={styles.headerTitleRow}>
          <Text style={[styles.title, styles.headerTitle]} accessibilityRole="header">
            {PARENTAL_CONTROLS_TITLE}
          </Text>
          <View style={styles.savingSlot} testID={`${testID}-saving-slot`}>
            {saving ? (
              <Text
                style={styles.saving}
                accessibilityLiveRegion="polite"
                testID={`${testID}-saving`}>
                {SAVING_CHANGES}
              </Text>
            ) : null}
          </View>
        </View>
        <Text style={styles.lead}>{PARENTAL_CONTROLS_LEAD}</Text>
      </View>

      {family && onFamilyChange ? (
        <View style={styles.group}>
          <ProfilePicker
            disabled={saving || undefined}
            testID={`${testID}-profiles`}
            title={PROFILES_PARENT_TITLE}
            chosenWord={SETTINGS_STATE_WORD}
            chosenLine={whoseSettingsThese(whose ?? EVERYONE_LABEL)}
            profiles={pickable}
            activeProfileId={editingId}
            onChoose={(profile) => {
              // Moving the picker takes the question with it. A parent who
              // answers by choosing somebody else has not said remove.
              setAskedToRemove(null);
              setEditingId(profile.id);
            }}
          />
          <Text style={styles.helper} testID={`${testID}-profile-rule`}>
            {PROFILE_ONLY_ADDS}
          </Text>
          {floorEffect ? (
            <Text style={styles.helper} testID={`${testID}-floor-effect`}>
              {floorEffect}
            </Text>
          ) : null}
          {confirmingRemoval && editingProfile ? (
            // The question stands in for the buttons rather than sitting
            // beside them, so the screen is asking one thing and Add a kid
            // cannot be pressed in the middle of it.
            <View style={styles.block}>
              <StatusNotice
                testID={`${testID}-remove-question`}
                notice={removeKidPrompt(editingProfile.name)}>
                <View style={styles.buttons}>
                  <View style={styles.button}>
                    <CalmButton
                      disabled={saving || undefined}
                      testID={`${testID}-remove-keep`}
                      label={keepKidLabel(editingProfile.name)}
                      onPress={() => setAskedToRemove(null)}
                      hasTVPreferredFocus
                    />
                  </View>
                  <View style={styles.button}>
                    <CalmButton
                      disabled={saving || undefined}
                      testID={`${testID}-remove-confirm`}
                      sound={false}
                      label={removeKidLabel(editingProfile.name)}
                      onPress={() => {
                        // The route forgets this profile's history after the
                        // household write commits, including a save retry.
                        onFamilyChange(removeProfile(family, editingProfile.id));
                        setAskedToRemove(null);
                        setEditingId(EVERYONE_ID);
                      }}
                    />
                  </View>
                </View>
              </StatusNotice>
            </View>
          ) : (
            <View style={styles.buttons}>
              {canAddProfile(family) ? (
                <View style={styles.button}>
                  <CalmButton
                    disabled={saving || undefined}
                    testID={`${testID}-add-profile`}
                    sound={false}
                    label={ADD_KID_LABEL}
                    // Named apart from the start. Two chips both reading Kid
                    // is a picker nobody can use, and there is no keyboard
                    // here to rename one with.
                    onPress={() =>
                      onFamilyChange(
                        addProfile(
                          family,
                          nextKidName(
                            DEFAULT_PROFILE_NAME,
                            family.profiles.map((one) => one.name),
                          ),
                        ),
                      )
                    }
                  />
                </View>
              ) : (
                <Text style={styles.helper} testID={`${testID}-profiles-full`}>
                  {PROFILES_FULL}
                </Text>
              )}
              {editingProfile && removable ? (
                <View style={styles.button}>
                  <CalmButton
                    disabled={saving || undefined}
                    testID={`${testID}-remove-profile`}
                    label={removeKidLabel(editingProfile.name)}
                    // Asks. Nothing is removed on this press, because what it
                    // removes does not come back.
                    onPress={() => setAskedToRemove(editingProfile.id)}
                  />
                </View>
              ) : null}
            </View>
          )}
        </View>
      ) : null}

      <View style={styles.group}>
        <Text style={styles.section} accessibilityRole="header">
          {sectionFor(STRICTNESS_TITLE, whose)}
        </Text>
        {PRESET_NAMES.map((name: PresetName) => {
          const chosen = shown.preset === name;
          const key = `preset-${name}`;
          return (
            <TouchableOpacity
              key={name}
              testID={`${testID}-preset-${name}`}
              accessibilityRole="radio"
              accessibilityState={{ checked: chosen, selected: chosen, ...blocked }}
              accessibilityLabel={`${PRESETS[name].title}. ${PRESETS[name].description}`}
              activeOpacity={1}
              onFocus={() => setFocusedRow(key)}
              onBlur={() => setFocusedRow(null)}
              onPress={() => choose({ preset: name })}
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

      <View style={styles.group}>
        <Text style={styles.section} accessibilityRole="header">
          {sectionFor(ROOM_TITLE, whose)}
        </Text>
        <Text style={styles.body} testID={`${testID}-room`}>
          {describeRoom(shown)}
        </Text>
        <Text style={styles.helper}>{ROOM_ONLY_ADDS}</Text>
        <Text style={styles.subheading} accessibilityRole="header">
          {TV_SIZE_TITLE}
        </Text>
        <View
          style={styles.choices}
          accessibilityRole="radiogroup"
          accessibilityLabel={TV_SIZE_TITLE}
          aria-label={TV_SIZE_TITLE}>
          {TV_DIAGONAL_CHOICES_IN.map((inches) => {
            const chosen = shown.tvDiagonalIn === inches;
            const key = `tv-${inches}`;
            return (
              <TouchableOpacity
                key={key}
                testID={`${testID}-tv-${inches}`}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen, selected: chosen, ...blocked }}
                accessibilityLabel={`${inches} inch television${chosen ? ', chosen' : ''}`}
                activeOpacity={1}
                onFocus={() => setFocusedRow(key)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => choose({ tvDiagonalIn: inches })}
                style={[
                  styles.chip,
                  chosen ? styles.chosen : null,
                  focusedRow === key ? styles.focused : null,
                ]}>
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
          {televisionChosen(shown.tvDiagonalIn)}
        </Text>
        <Text style={styles.subheading} accessibilityRole="header">
          {SEAT_DISTANCE_TITLE}
        </Text>
        <View
          style={styles.choices}
          accessibilityRole="radiogroup"
          accessibilityLabel={SEAT_DISTANCE_TITLE}
          aria-label={SEAT_DISTANCE_TITLE}>
          {SEAT_DISTANCE_CHOICES_IN.map((inches) => {
            const chosen = shown.seatDistanceIn === inches;
            const feet = Math.round(inches / 12);
            const key = `seat-${inches}`;
            return (
              <TouchableOpacity
                key={key}
                testID={`${testID}-seat-${inches}`}
                accessibilityRole="radio"
                accessibilityState={{ checked: chosen, selected: chosen, ...blocked }}
                accessibilityLabel={`${feet} feet away${chosen ? ', chosen' : ''}`}
                activeOpacity={1}
                onFocus={() => setFocusedRow(key)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => choose({ seatDistanceIn: inches })}
                style={[
                  styles.chip,
                  chosen ? styles.chosen : null,
                  focusedRow === key ? styles.focused : null,
                ]}>
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
          {seatChosen(shown.seatDistanceIn)}
        </Text>
      </View>

      <View style={styles.group}>
        <Text style={styles.section} accessibilityRole="header">
          {sectionFor(HIDDEN_TITLE, whose)}
        </Text>
        <Text style={styles.body} testID={`${testID}-total`}>
          {shownLog.entries.length === 0
            ? editingProfile
              ? nothingHiddenFor(editingProfile.name)
              : NOTHING_HIDDEN_YET
            : hiddenSummary(
                shownLog.entries.length,
                totalHiddenMs(shownLog),
                shownEntries.length,
              )}
        </Text>
        {days.map((day) => (
          <View key={day.key}>
            <Text
              testID={`${testID}-log-day-${day.key}`}
              style={styles.logDay}
              accessibilityRole="header">
              {day.heading}
            </Text>
            {day.lines.map((line) => (
              <Text
                key={`${line.entry.atMs}-${line.index}`}
                testID={`${testID}-log-${line.index}`}
                style={styles.logLine}>
                {describeHideEntry(line.entry)}
              </Text>
            ))}
          </View>
        ))}
      </View>

      {family && onFamilyChange ? (
        <View style={styles.group}>
          <Text style={styles.section} accessibilityRole="header">Interface</Text>
          {([
            {
              id: 'interface-motion',
              key: 'interfaceMotionEnabled',
              title: 'Gentle artwork motion',
              note: 'Artwork settles into place when you open the library or a title. Reduced motion keeps it still.',
            },
            {
              id: 'interface-sounds',
              key: 'interfaceSoundsEnabled',
              title: 'Selection sounds',
              note: 'A quiet tone confirms menu actions. Silent during playback and when a screen reader is active.',
            },
          ] as const).map((preference) => {
            const enabled = family[preference.key] === true;
            const focused = focusedRow === preference.id;
            return (
              <TouchableOpacity
                key={preference.id}
                testID={`${testID}-${preference.id}`}
                accessibilityRole="switch"
                accessibilityState={{ checked: enabled, disabled: saving }}
                accessibilityLabel={`${preference.title}. ${preference.note}`}
                activeOpacity={1}
                onFocus={() => setFocusedRow(preference.id)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => {
                  if (!saving) {
                    onFamilyChange({ ...family, [preference.key]: !enabled });
                  }
                }}
                style={[styles.row, focused ? styles.focused : null]}>
                <View style={styles.rowText}>
                  <Text style={[styles.rowTitle, focused ? styles.focusedLabel : null]}>{preference.title}</Text>
                  <Text style={styles.rowDetail}>{preference.note}</Text>
                </View>
                <View style={styles.rowState}>
                  <Text style={styles.rowStateWord}>{enabled ? 'On' : 'Off'}</Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      ) : null}

      {family && onFamilyChange ? (
        <View style={styles.group}>
          <Text style={styles.section} accessibilityRole="header">
            {CHIME_SECTION_TITLE}
          </Text>
          <TouchableOpacity
            testID={`${testID}-chime`}
            accessibilityRole="button"
            accessibilityState={{ disabled: saving }}
            accessibilityLabel={`${CHIME_ROW_TITLE}, ${
              family.chimeEnabled ? 'on' : 'off'
            }. Press to turn it ${family.chimeEnabled ? 'off' : 'on'}.`}
            activeOpacity={1}
            onFocus={() => setFocusedRow('chime')}
            onBlur={() => setFocusedRow(null)}
            onPress={() => {
              if (!saving) { onFamilyChange(setChimeEnabled(family, !family.chimeEnabled)); }
            }}
            style={[styles.row, focusedRow === 'chime' ? styles.focused : null]}>
            <View style={styles.rowText}>
              <Text style={[styles.rowTitle, focusedRow === 'chime' ? styles.focusedLabel : null]}>{CHIME_ROW_TITLE}</Text>
              <Text style={styles.rowDetail} testID={`${testID}-chime-note`}>
                {CHIME_NOTE}
              </Text>
            </View>
            <View style={styles.rowState}>
              <Text style={styles.rowStateWord} testID={`${testID}-chime-label`}>
                {family.chimeEnabled ? CHIME_ON_LABEL : CHIME_OFF_LABEL}
              </Text>
            </View>
          </TouchableOpacity>
        </View>
      ) : null}

      <View style={styles.group}>
        <Text style={styles.section} accessibilityRole="header">
          {CHECKED_TITLES_TITLE}
        </Text>
        {titles.map((entry) => {
          const titleNotice = noticeForTitle(entry);
          return (
            <View
              key={entry.title.id}
              testID={`${testID}-title-${entry.title.id}`}
              style={styles.card}>
              <View style={styles.cardHead}>
                <Text style={styles.cardTitle}>{titlePresentation(entry.title).name}</Text>
                <ShieldBadge
                  status={entry.status}
                  testID={`${testID}-status-${entry.title.id}`}
                />
              </View>
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
      </View>

      <View style={styles.group}>
        <Text style={styles.section} accessibilityRole="header">
          {EXPLAINER_TITLE}
        </Text>
        {EXPLAINER_LINES.map((line, index) => (
          <Text
            key={line}
            testID={`${testID}-explainer-line-${index}`}
            style={styles.explainerLine}>
            {line}
          </Text>
        ))}
      </View>

      {onBack || onCredits ? (
        <View style={styles.footer}>
          {onBack ? (
            <View style={styles.button}>
              <CalmButton
                disabled={saving || undefined}
                testID={`${testID}-back`}
                label={BACK_TO_LIBRARY_LABEL}
                onPress={onBack}
              />
            </View>
          ) : null}
          {onCredits ? (
            <View style={styles.button}>
              <CalmButton
                disabled={saving || undefined}
                testID={`${testID}-credits`}
                label={CREDITS_LABEL}
                onPress={onCredits}
              />
            </View>
          ) : null}
        </View>
      ) : null}
    </ScrollView>
  );
};

/** The gap between groups, in 1080p units: the larger step of the spacing scale. */
const GROUP_GAP = 56;

/**
 * The column at the right edge of a row that holds the word Chosen, or On and
 * Off, in 1080p units. Every row reserves it, so the word moving from one row
 * to another re-wraps nothing and moves nothing.
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
  header: { marginBottom: scale(GROUP_GAP) },
  headerTitleRow: { flexDirection: 'row', alignItems: 'center', gap: scale(CALM_SPACE.BLOCK) },
  headerTitle: { flex: 1 },
  title: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
  },
  lead: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(CALM_SPACE.TIGHT),
    maxWidth: scale(1160),
  },
  saving: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT,
    textAlign: 'right',
  },
  // Reserve the status beside the title so saving never moves the settings.
  savingSlot: { width: scale(400), height: scale(84), justifyContent: 'center' },
  /** The locked screen: words on the left, the keypad on the right. */
  columns: { flexDirection: 'row', alignItems: 'flex-start' },
  aside: {
    flex: 1,
    maxWidth: scale(960),
    marginRight: scale(CALM_SPACE.EDGE),
  },
  group: { marginBottom: scale(GROUP_GAP) },
  section: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(CALM_SPACE.ROW),
  },
  /** The two room questions, under the room's own heading. */
  subheading: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
    marginTop: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  body: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
  },
  helper: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(CALM_SPACE.TIGHT),
    maxWidth: scale(1160),
  },
  block: { marginTop: scale(CALM_SPACE.BLOCK) },
  /** A settings row. Quiet at rest: the ring is there, in the card's own colour. */
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: scale(24),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(16),
    borderRadius: scale(16),
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
  chipLabel: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
  },
  /**
   * Which chip in the row above is the chosen one, in words.
   *
   * The same shape the profile picker uses, and for the same two reasons: a
   * fill colour is not a state everybody can read, and a word drawn on the
   * chosen chip would make that chip wider than its neighbours and slide the
   * rest of the row along when a parent presses one.
   */
  chosenLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
  },
  /**
   * The record reads as the evidence it is: body text in the main colour,
   * with the day above each run of lines a step up from them.
   */
  logDay: {
    ...CALM_TEXT.card,
    color: CALM_COLORS.TEXT,
    marginTop: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  logLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  explainerLine: {
    ...CALM_TEXT.body,
    color: CALM_COLORS.TEXT,
    marginBottom: scale(CALM_SPACE.TIGHT),
    maxWidth: scale(1500),
  },
  /** A title's card: not a control, so no ring is reserved on it. */
  card: {
    paddingVertical: scale(CALM_SPACE.ROW),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
    marginBottom: scale(CALM_SPACE.TIGHT),
    borderRadius: scale(12),
    backgroundColor: CALM_COLORS.SURFACE,
  },
  cardHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardTitle: {
    ...CALM_TEXT.card,
    color: CALM_COLORS.TEXT,
    flex: 1,
    marginRight: scale(CALM_SPACE.ROW),
  },
  buttons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: scale(CALM_SPACE.BLOCK),
  },
  button: {
    marginRight: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  footer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
});

export default ParentAreaScreen;
