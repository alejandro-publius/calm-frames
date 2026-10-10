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
  CALM_TYPE,
  FOCUS_RING_WIDTH,
  scale,
} from './calmStyles';
import {
  CHECKED_TITLES_TITLE,
  CHIME_NOTE,
  CHIME_OFF_LABEL,
  CHIME_ON_LABEL,
  CHIME_SECTION_TITLE,
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
  PARENT_AREA_TITLE,
  PIN_LOCKED_TITLE,
  PIN_NOT_SET,
  PIN_PROMPT,
  PIN_WRONG_TITLE,
  PROFILE_ONLY_ADDS,
  PROFILES_FULL,
  PROFILES_PARENT_TITLE,
  removeKidLabel,
  removeKidPrompt,
  ROOM_ONLY_ADDS,
  ROOM_TITLE,
  seatChosen,
  SEAT_DISTANCE_TITLE,
  sectionFor,
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
      change.then(finish).catch(() => {
        setNotice({ title: 'The parent area stays locked',
          detail: 'Your PIN settings could not be saved. Try again.', tone: 'blocked' });
      }).finally(() => {
        savingPinRef.current = false;
        setSavingPin(false);
      });
    } else {
      finish();
    }
  };

  if (!unlocked) {
    return (
      <View testID={testID} style={styles.screen}>
        <Text style={styles.title} accessibilityRole="header">
          {PARENT_AREA_TITLE}
        </Text>
        <View style={styles.block}>
          <StatusNotice testID={`${testID}-message`} notice={notice} />
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
        <View style={styles.buttons}>
          {!gate.record && onSetPin ? (
            <CalmButton
              disabled={saving || undefined}
              testID={`${testID}-set-pin`}
              label="Set a PIN"
              onPress={onSetPin}
              hasTVPreferredFocus
            />
          ) : null}
          {onBack ? (
            <View style={styles.secondButton}>
              <CalmButton disabled={saving || undefined} testID={`${testID}-back`} label="Back" onPress={onBack} />
            </View>
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

  return (
    <ScrollView
      testID={`${testID}-open`}
      style={styles.screen}
      contentContainerStyle={styles.content}>
      <Text style={styles.title} accessibilityRole="header">
        {PARENT_AREA_TITLE}
      </Text>

      {saving ? (
        <Text style={styles.note} accessibilityLiveRegion="polite" testID={`${testID}-saving`}>
          Saving your household settings
        </Text>
      ) : null}

      {family && onFamilyChange ? (
        <>
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
          <Text style={styles.note} testID={`${testID}-profile-rule`}>
            {PROFILE_ONLY_ADDS}
          </Text>
          {floorEffect ? (
            <Text style={styles.note} testID={`${testID}-floor-effect`}>
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
                  <CalmButton
                    disabled={saving || undefined}
                    testID={`${testID}-remove-keep`}
                    label={keepKidLabel(editingProfile.name)}
                    onPress={() => setAskedToRemove(null)}
                    hasTVPreferredFocus
                  />
                  <View style={styles.secondButton}>
                    <CalmButton
                      disabled={saving || undefined}
                      testID={`${testID}-remove-confirm`}
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
                <CalmButton
                  disabled={saving || undefined}
                  testID={`${testID}-add-profile`}
                  label="Add a kid"
                  // Named apart from the start. Two chips both reading Kid is
                  // a picker nobody can use, and there is no keyboard here to
                  // rename one with.
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
              ) : (
                <Text style={styles.note} testID={`${testID}-profiles-full`}>
                  {PROFILES_FULL}
                </Text>
              )}
              {editingProfile && removable ? (
                <View style={styles.secondButton}>
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
        </>
      ) : null}

      <Text style={styles.section} accessibilityRole="header">
        {sectionFor(STRICTNESS_TITLE, whose)}
      </Text>
      {PRESET_NAMES.map((name: PresetName) => {
        const chosen = shown.preset === name;
        return (
          <TouchableOpacity
            disabled={saving || undefined}
            key={name}
            testID={`${testID}-preset-${name}`}
            accessibilityRole="radio"
            accessibilityState={{ checked: chosen, selected: chosen, ...(saving ? { disabled: true } : {}) }}
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

      <Text style={styles.section} accessibilityRole="header">
        {sectionFor(ROOM_TITLE, whose)}
      </Text>
      <Text style={styles.rowDetail} testID={`${testID}-room`}>
        {describeRoom(shown)}
      </Text>
      <Text style={styles.note}>{ROOM_ONLY_ADDS}</Text>
      <Text style={styles.rowTitle} accessibilityRole="header">
        {TV_SIZE_TITLE}
      </Text>
      <View
        style={styles.choices}
        accessibilityRole="radiogroup"
        accessibilityLabel={TV_SIZE_TITLE}
        aria-label={TV_SIZE_TITLE}>
        {TV_DIAGONAL_CHOICES_IN.map((inches) => {
          const chosen = shown.tvDiagonalIn === inches;
          return (
            <TouchableOpacity
              disabled={saving || undefined}
              key={`tv-${inches}`}
              testID={`${testID}-tv-${inches}`}
              accessibilityRole="radio"
              accessibilityState={{ checked: chosen, selected: chosen, ...(saving ? { disabled: true } : {}) }}
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
        {televisionChosen(shown.tvDiagonalIn)}
      </Text>
      <Text style={styles.rowTitle} accessibilityRole="header">
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
          return (
            <TouchableOpacity
              disabled={saving || undefined}
              key={`seat-${inches}`}
              testID={`${testID}-seat-${inches}`}
              accessibilityRole="radio"
              accessibilityState={{ checked: chosen, selected: chosen, ...(saving ? { disabled: true } : {}) }}
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
        {seatChosen(shown.seatDistanceIn)}
      </Text>

      <Text style={styles.section} accessibilityRole="header">
        {sectionFor(HIDDEN_TITLE, whose)}
      </Text>
      <Text style={styles.total} testID={`${testID}-total`}>
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

      {family && onFamilyChange ? (
        <>
          <Text style={styles.section} accessibilityRole="header">
            {CHIME_SECTION_TITLE}
          </Text>
          <Text style={styles.note} testID={`${testID}-chime-note`}>
            {CHIME_NOTE}
          </Text>
          <View style={styles.buttons}>
            <CalmButton
              disabled={saving || undefined}
              testID={`${testID}-chime`}
              label={family.chimeEnabled ? CHIME_ON_LABEL : CHIME_OFF_LABEL}
              accessibilityLabel={`${
                family.chimeEnabled ? CHIME_ON_LABEL : CHIME_OFF_LABEL
              }. Press to turn it ${family.chimeEnabled ? 'off' : 'on'}.`}
              onPress={() => onFamilyChange(setChimeEnabled(family, !family.chimeEnabled))}
            />
          </View>
        </>
      ) : null}

      <Text style={styles.section} accessibilityRole="header">
        {CHECKED_TITLES_TITLE}
      </Text>
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

      {onBack || onCredits ? (
        <View style={styles.buttons}>
          {onBack ? (
            <CalmButton disabled={saving || undefined} testID={`${testID}-back`} label="Back" onPress={onBack} />
          ) : null}
          {onCredits ? (
            <CalmButton
              disabled={saving || undefined}
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
  /**
   * Which chip in the row above is the chosen one, in words.
   *
   * The same shape the profile picker uses, and for the same two reasons: a
   * fill colour is not a state everybody can read, and a word drawn on the
   * chosen chip would make that chip wider than its neighbours and slide the
   * rest of the row along when a parent presses one.
   */
  chosenLine: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  /**
   * The record reads as the evidence it is.
   *
   * These lines were the dimmest and smallest thing on the screen, in the same
   * style as the asides beside them, which put the one proof a household has
   * that any of this works below the notes about it. They are body text on the
   * ground now, cream on teal at 7.60 to 1, and the asides stay dim so the two
   * are still told apart.
   */
  total: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  logDay: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.SMALL),
    fontWeight: '600',
    marginTop: scale(CALM_SPACE.ROW),
    marginBottom: scale(CALM_SPACE.TIGHT),
  },
  logLine: {
    color: CALM_COLORS.TEXT,
    fontSize: scale(CALM_TYPE.BODY),
    marginBottom: scale(CALM_SPACE.TIGHT),
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
