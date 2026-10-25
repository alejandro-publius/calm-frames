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
 *
 * Renaming a kid works the same way. Edit name sits beside Add a kid and
 * Remove, and pressing it puts the letter keys where the picker was, so one
 * name is being typed and nothing else in the group can move under it. The
 * editor holds the draft; this screen holds whether the write committed,
 * which it learns from `onRenameProfile` rather than assuming. Only a true
 * answer closes the editor. A false one keeps the draft on screen with Try
 * again and Cancel, and Back or Cancel put focus back on Edit name.
 */

import React from 'react';
import TouchableOpacity from './CalmTouchable';
import { BackHandler, ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import FocusRow from './FocusRow';
import HomeHarborScene from './HomeHarborScene';
import {
  CALM_CONTROL,
  COASTAL_COLORS as CALM_COLORS,
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
  CANCEL_NAME_LABEL,
  CHOSEN_WORD,
  CREDITS_LABEL,
  EDIT_NAME_LABEL,
  EVERYONE_LABEL,
  EXPLAINER_LINES,
  EXPLAINER_TITLE,
  HIDDEN_TITLE,
  hiddenSummary,
  hidesByDay,
  keepKidLabel,
  NAME_SAVE_FAILED,
  nextKidName,
  Notice,
  noticeForTitle,
  nothingHiddenFor,
  NOTHING_HIDDEN_YET,
  PARENTAL_CONTROLS_LEAD,
  PARENTAL_CONTROLS_TITLE,
  PIN_CHECKING,
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
  SEAT_DISTANCE_TITLE,
  sectionFor,
  SET_PIN_LABEL,
  SETTINGS_STATE_WORD,
  STRICTNESS_TITLE,
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
import ProfileNameEditor from './ProfileNameEditor';
import ProfilePicker from './ProfilePicker';
import ReadingStop from './ReadingStop';
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
  namesTakenFor,
  Profile,
  ProfileLogs,
  removeProfile,
  renameProfile,
  setProfileReadingComfort,
  setChimeEnabled,
  setFloor,
  setProfileSettings,
} from './profiles';
import ShieldBadge from './ShieldBadge';
import { titlePresentation } from './TitleArtwork';
import StatusNotice from './StatusNotice';
import { CheckedTitle } from './titleStatus';
import PersonalCoversScreen from './PersonalCoversScreen';
import { personalCoverAsset } from './personalCovers';
import { useUiCapture } from './uiCapture';
import {
  PARENT_EDIT_NAME_FRAME,
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
  /**
   * Saves a renamed family and says whether the write committed.
   *
   * Edit name is offered only when this is given. `onFamilyChange` returns
   * nothing, and an editor that closed because a callback returned would be
   * reporting a save it never saw. The route passes the household write's
   * own answer: true once the record holds the new name, false when it was
   * refused or failed, in which case the draft stays on screen.
   */
  onRenameProfile?: (family: Family) => Promise<boolean>;
  /** A preference is shown as saved only when the route commits its family. */
  onProfilePreferencesChange?: (family: Family) => Promise<boolean>;
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
  onRenameProfile,
  onProfilePreferencesChange,
  profileLogs = emptyProfileLogs(),
  titles,
  nowMs = Date.now,
  onBack,
  onSetPin,
  onCredits,
  testID = 'parent-area',
  saving: externalSaving = false,
}: ParentAreaScreenProps) => {
  const [comfortPending, setComfortPending] = React.useState(false);
  const comfortPendingRef = React.useRef(false);
  const comfortWantsFocusRef = React.useRef(false);
  const [comfortFailed, setComfortFailed] = React.useState(false);
  const [comfortReturnFocus, setComfortReturnFocus] = React.useState(false);
  const saving = externalSaving || comfortPending;
  const [unlocked, setUnlocked] = React.useState(false);
  const [extraReturnFocus, setExtraReturnFocus] = React.useState<string>();
  const [extraTitle, setExtraTitle] = React.useState<CheckedTitle>();
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
  // Which kid's name is being typed, by id for the same reason: a draft begun
  // for Robin cannot be saved onto Sam.
  const [renaming, setRenaming] = React.useState<string | null>(null);
  const [renamePending, setRenamePending] = React.useState(false);
  const renamePendingRef = React.useRef(false);
  // The last rename write came back false. The editor stays up with its draft.
  const [renameFailed, setRenameFailed] = React.useState(false);
  // Edit name takes focus back when the editor closes, whichever way it closed.
  const [renameReturnFocus, setRenameReturnFocus] = React.useState(false);
  const mounted = React.useRef(true);
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const shownNotice = savingPin ? PIN_CHECKING : notice;
  const wrongPin = shownNotice.tone === 'blocked';

  const editingKid = Boolean(
    family && family.profiles.some((profile) => profile.id === editingId),
  );
  // A family always has somebody in it, so the last kid has no Remove button
  // and so no question to ask about them either.
  const removable = Boolean(family && editingKid && family.profiles.length > 1);
  const confirmingRemoval = removable && askedToRemove === editingId;
  // The editor is open only for a kid who is still in the family, and only
  // when the route can say whether a save committed.
  const renamingProfile: Profile | undefined =
    family && renaming !== null
      ? family.profiles.find((profile) => profile.id === renaming)
      : undefined;
  const editingName = Boolean(renamingProfile && onRenameProfile);
  // Back closes the editor and nothing else, and while a write is in flight it
  // does nothing at all: the write cannot be taken back, so the screen waits
  // for its answer rather than showing the old name as if it were the answer.
  React.useEffect(() => {
    if (!editingName) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!renamePendingRef.current) {
        setRenaming(null);
        setRenameFailed(false);
        setRenameReturnFocus(true);
      }
      return true;
    });
    return () => subscription.remove();
  }, [editingName]);
  // While the screen is asking, Back answers the question with keeping the
  // kid. Falling through would leave the whole parent area instead.
  React.useEffect(() => {
    if (!confirmingRemoval) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { setAskedToRemove(null); return true; });
    return () => subscription.remove();
  }, [confirmingRemoval]);

  let frame = PARENT_LOCKED_FRAME;
  let reason = 'parent area locked';
  if (unlocked && editingName) {
    frame = PARENT_EDIT_NAME_FRAME;
    reason = 'parent area, typing a name';
  } else if (unlocked && confirmingRemoval) {
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
        <HomeHarborScene immersive wideReading />
        <CalmPageHeader onBack={onBack} backTestID={`${testID}-back`} backDisabled={saving} />
        <View style={styles.columns}>
          <View style={styles.aside}>
            <View style={styles.gateHeader}>
              <Text style={styles.title} accessibilityRole="header">
                {PARENTAL_CONTROLS_TITLE}
              </Text>
            </View>
            <StatusNotice testID={`${testID}-message`} notice={shownNotice} />
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

  const extraAsset = extraTitle ? personalCoverAsset(extraTitle.title) : undefined;
  if (extraTitle && extraAsset) {
    return <PersonalCoversScreen asset={extraAsset} title={extraTitle.title.title}
      onBack={() => { setExtraReturnFocus(extraTitle.title.id); setExtraTitle(undefined); }} />;
  }

  // Who is being edited, and what they are set to. With no family this is the
  // household and nothing else, which is what this screen was before profiles.
  const editingProfile: Profile | undefined = family
    ? family.profiles.find((profile) => profile.id === editingId)
    : undefined;
  // Only the selected kid's scrollable help changes. The profile panel,
  // name editor, PIN and approved explainer retain their existing geometry.
  const readingComfort = editingProfile?.readingComfortEnabled === true && !editingName && !confirmingRemoval;
  const helpText = readingComfort ? styles.comfortHelp : undefined;
  const bodyText = readingComfort ? styles.comfortBody : undefined;
  const helpRow = readingComfort ? styles.comfortRow : undefined;
  const shown: HouseholdSettings = editingProfile
    ? editingProfile.settings
    : family?.floor ?? settings;

  const saveReadingComfort = () => {
    if (!family || !editingProfile || !onProfilePreferencesChange || saving || comfortPendingRef.current) return;
    comfortPendingRef.current = true;
    comfortWantsFocusRef.current = true;
    setComfortPending(true);
    setComfortFailed(false);
    // Never flip local state optimistically: the stored family owns On/Off.
    // A synchronous throw is a failed save too, just like a rejected promise.
    (async () => {
      try {
        const accepted = await onProfilePreferencesChange(
          setProfileReadingComfort(family, editingProfile.id, editingProfile.readingComfortEnabled !== true),
        );
        if (mounted.current) setComfortFailed(!accepted);
      } catch {
        if (mounted.current) setComfortFailed(true);
      } finally {
        comfortPendingRef.current = false;
        if (mounted.current) {
          setComfortPending(false);
          setComfortReturnFocus(comfortWantsFocusRef.current);
        }
      }
    })();
  };

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

  const openRename = (profile: Profile) => {
    // One thing at a time: a question about removing the kid goes away.
    setAskedToRemove(null);
    setRenameFailed(false);
    setRenameReturnFocus(false);
    setRenaming(profile.id);
  };
  const closeRename = () => {
    setRenaming(null);
    setRenameFailed(false);
    setRenameReturnFocus(true);
  };
  const leaveParents = () => {
    if (editingName) {
      // Visible Back follows the same one-level cancellation as the remote.
      // The ref also covers a Save and Back arriving before the next render.
      if (!renamePendingRef.current && !saving) closeRename();
      return;
    }
    onBack?.();
  };
  const saveName = (name: string) => {
    if (
      !family ||
      !renamingProfile ||
      !onRenameProfile ||
      renamePendingRef.current ||
      saving
    ) {
      return;
    }
    renamePendingRef.current = true;
    setRenamePending(true);
    setRenameFailed(false);
    // The id is the key. Everything else about the kid, and everybody else
    // in the household, goes through untouched.
    onRenameProfile(renameProfile(family, renamingProfile.id, name))
      .then(
        (accepted) => {
          if (!mounted.current) return;
          if (accepted) {
            closeRename();
          } else {
            setRenameFailed(true);
          }
        },
        () => {
          if (mounted.current) setRenameFailed(true);
        },
      )
      .finally(() => {
        renamePendingRef.current = false;
        if (mounted.current) setRenamePending(false);
      });
  };

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
      <CalmPageHeader onBack={onBack ? leaveParents : undefined} backTestID={`${testID}-back-top`} preferredBack={!editingName && !extraReturnFocus && !renameReturnFocus && !comfortPending && !comfortReturnFocus} backDisabled={saving || renamePending} />
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

      {family && onFamilyChange && renamingProfile && onRenameProfile ? (
        // The keys stand where the picker and the buttons were, so one name is
        // being typed and nothing in the group can move under the draft.
        <View style={[styles.group, styles.profileGroup, styles.editorGroup]}>
          <ProfileNameEditor
            testID={`${testID}-name`}
            profile={renamingProfile}
            taken={namesTakenFor(family, renamingProfile.id, [EVERYONE_LABEL])}
            saving={saving || renamePending}
            failure={renameFailed ? NAME_SAVE_FAILED : null}
            onSave={saveName}
            onCancel={() => {
              if (!renamePendingRef.current) closeRename();
            }}
          />
        </View>
      ) : family && onFamilyChange ? (
        <View style={[styles.group, !confirmingRemoval ? styles.profileGroup : null]}>
          <View style={!confirmingRemoval ? styles.profileIdentity : undefined}>
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
              setRenameReturnFocus(false);
              setComfortReturnFocus(false);
              comfortWantsFocusRef.current = false;
              setComfortFailed(false);
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
          </View>
          <View style={!confirmingRemoval ? styles.profileManagement : undefined}>
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
                <Text style={[styles.helper, styles.managementNote]} testID={`${testID}-profiles-full`}>
                  {PROFILES_FULL}
                </Text>
              )}
              {editingProfile && onRenameProfile ? (
                <View style={styles.button}>
                  <CalmButton
                    disabled={saving || undefined}
                    testID={`${testID}-rename-profile`}
                    label={EDIT_NAME_LABEL}
                    // Focus comes back here when the editor closes, so Back
                    // and Cancel land where the parent left.
                    hasTVPreferredFocus={renameReturnFocus}
                    onPress={() => openRename(editingProfile)}
                  />
                </View>
              ) : null}
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
        </View>
      ) : null}

      <View
        style={styles.group}
        accessibilityRole="radiogroup"
        accessibilityLabel={sectionFor(STRICTNESS_TITLE, whose)}
        aria-label={sectionFor(STRICTNESS_TITLE, whose)}>
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
              // Name and state first, as the TV and seat chips say them; the
              // description follows as the hint. Read as one label, it came
              // first and a quick move cut the state off.
              accessibilityLabel={`${PRESETS[name].title}${chosen ? ', chosen' : ''}`}
              accessibilityHint={PRESETS[name].description}
              activeOpacity={1}
              onFocus={() => setFocusedRow(key)}
              onBlur={() => setFocusedRow(null)}
              onPress={() => choose({ preset: name })}
              style={[
                styles.row,
                helpRow,
                chosen ? styles.chosen : null,
                focusedRow === key ? styles.focused : null,
              ]}>
              <View style={styles.rowText}>
                <Text style={[styles.rowTitle, focusedRow === key ? styles.focusedLabel : null, saving ? styles.disabledRowText : null]}>{PRESETS[name].title}</Text>
                <Text style={[styles.rowDetail, helpText, saving ? styles.disabledRowText : null]}>{PRESETS[name].description}</Text>
              </View>
              <View style={styles.rowState}>
                {chosen ? (
                  <Text style={[styles.rowStateWord, saving ? styles.disabledRowText : null]}>✓ {CHOSEN_WORD}</Text>
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
        <Text style={[styles.body, bodyText]} testID={`${testID}-room`}>
          {describeRoom(shown)}
        </Text>
        <Text style={[styles.helper, helpText]}>{ROOM_ONLY_ADDS}</Text>
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
      </View>

      <View style={styles.group}>
        <Text style={styles.section} accessibilityRole="header">
          {sectionFor(HIDDEN_TITLE, whose)}
        </Text>
        {/* The record is one stop, so the remote can land on it and VoiceView reads it; ReadingStop.tsx says why. */}
        <ReadingStop testID={`${testID}-hidden-reading`} flush>
        <Text style={[styles.body, bodyText]} testID={`${testID}-total`}>
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
                style={[styles.logLine, helpText]}>
                {describeHideEntry(line.entry)}
              </Text>
            ))}
          </View>
        ))}
        </ReadingStop>
      </View>

      {family && editingProfile && onProfilePreferencesChange && !editingName && !confirmingRemoval ? (
        <View style={styles.group}>
          <Text style={styles.section} accessibilityRole="header">Reading for {editingProfile.name}</Text>
          <TouchableOpacity
            testID={`${testID}-reading-comfort`}
            focusable
            hasTVPreferredFocus={comfortReturnFocus}
            accessibilityRole="switch"
            accessibilityLabel={`Reading comfort, ${readingComfort ? 'on' : 'off'}`}
            accessibilityHint="Larger help text and more space in this kid's Parents settings and More info."
            accessibilityState={{ checked: readingComfort, disabled: saving }}
            activeOpacity={1}
            onFocus={() => { comfortWantsFocusRef.current = true; setFocusedRow('reading-comfort'); setRenameReturnFocus(false); }}
            onBlur={() => { comfortWantsFocusRef.current = false; setFocusedRow(null); setComfortReturnFocus(false); }}
            onPress={saveReadingComfort}
            style={[styles.row, helpRow, focusedRow === 'reading-comfort' ? styles.focused : null]}>
            <View style={styles.rowText}>
              <Text style={[styles.rowTitle, focusedRow === 'reading-comfort' ? styles.focusedLabel : null]}>Reading comfort</Text>
              <Text style={[styles.rowDetail, helpText]}>Larger help text and more space in Parents and More info. Other screens stay the same.</Text>
            </View>
            <View style={styles.rowState}><Text style={styles.rowStateWord}>{readingComfort ? 'On' : 'Off'}</Text></View>
          </TouchableOpacity>
          {comfortFailed ? <Text testID={`${testID}-reading-comfort-failure`} style={[styles.helper, helpText]} accessibilityLiveRegion="polite">
            Reading comfort was not saved. Choose it again to retry.
          </Text> : null}
        </View>
      ) : null}

      {family && onFamilyChange ? (
        <View style={styles.group}>
          <Text style={styles.section} accessibilityRole="header">Interface</Text>
          {([
            {
              id: 'interface-motion',
              key: 'interfaceMotionEnabled',
              title: 'Gentle artwork motion',
              note: 'Artwork eases into place when you open Home or a video. Reduced motion keeps it still.',
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
                // On or Off is drawn beside the name, so it is said with it,
                // before the note.
                accessibilityLabel={`${preference.title}, ${enabled ? 'on' : 'off'}`}
                accessibilityHint={preference.note}
                activeOpacity={1}
                onFocus={() => setFocusedRow(preference.id)}
                onBlur={() => setFocusedRow(null)}
                onPress={() => {
                  if (!saving) {
                    onFamilyChange({ ...family, [preference.key]: !enabled });
                  }
                }}
                style={[styles.row, helpRow, focused ? styles.focused : null]}>
                <View style={styles.rowText}>
                  <Text style={[styles.rowTitle, focused ? styles.focusedLabel : null]}>{preference.title}</Text>
                  <Text style={[styles.rowDetail, helpText]}>{preference.note}</Text>
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
            style={[styles.row, helpRow, focusedRow === 'chime' ? styles.focused : null]}>
            <View style={styles.rowText}>
              <Text style={[styles.rowTitle, focusedRow === 'chime' ? styles.focusedLabel : null]}>{CHIME_ROW_TITLE}</Text>
              <Text style={[styles.rowDetail, helpText]} testID={`${testID}-chime-note`}>
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
              {entry.status === 'verified' && personalCoverAsset(entry.title) ? (
                // Every verified title has one of these, so the title is in
                // what a screen reader says; the name beside it is only text.
                <CalmButton label="Extra picture covers" accessibilityLabel={`Extra picture covers: ${titlePresentation(entry.title).name}`} disabled={saving}
                  hasTVPreferredFocus={extraReturnFocus === entry.title.id}
                  onPress={() => { setExtraReturnFocus(undefined); setExtraTitle(entry); }} testID={`${testID}-extra-${entry.title.id}`} />
              ) : null}
              {titleNotice ? (
                <Text
                  style={[styles.rowDetail, helpText]}
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
        {/* The approved sentence is in here, so the lines are one stop the
            remote can land on and VoiceView reads; ReadingStop.tsx says why. */}
        <ReadingStop testID={`${testID}-explainer-reading`} flush>
        {EXPLAINER_LINES.map((line, index) => (
          <Text
            key={line}
            testID={`${testID}-explainer-line-${index}`}
            style={styles.explainerLine}>
            {line}
          </Text>
        ))}
        </ReadingStop>
      </View>

      {onBack || onCredits ? (
        // Right from the last of these went up the page to a seat chip.
        <FocusRow style={styles.footer} testID={`${testID}-footer`}>
          {onBack ? (
            <View style={styles.button}>
              <CalmButton
                disabled={saving || renamePending || undefined}
                testID={`${testID}-back`}
                label={editingName ? CANCEL_NAME_LABEL : BACK_TO_LIBRARY_LABEL}
                onPress={leaveParents}
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
        </FocusRow>
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
    maxWidth: scale(1560),
    alignSelf: 'center',
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
  gateHeader: { marginBottom: scale(32) },
  columns: { width: '100%', maxWidth: scale(1600), alignSelf: 'center', flexDirection: 'row', alignItems: 'flex-start', backgroundColor: CALM_COLORS.SURFACE, borderColor: CALM_COLORS.BORDER, borderWidth: scale(2), borderRadius: scale(28), padding: scale(48) },
  aside: {
    flex: 1,
    maxWidth: scale(960),
    marginRight: scale(CALM_SPACE.EDGE),
  },
  group: { width: '100%', marginBottom: scale(GROUP_GAP), maxWidth: scale(1560) },
  profileGroup: { flexDirection: 'row', gap: scale(40), marginBottom: scale(40), padding: scale(32), borderColor: CALM_COLORS.BORDER, borderWidth: scale(2), borderRadius: scale(24) },
  profileIdentity: { flex: 1 },
  profileManagement: { width: scale(360) },
  /** The editor takes the whole panel, one column, inside the same outline. */
  editorGroup: { flexDirection: 'column' },
  managementNote: { maxWidth: '100%' },
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
  disabledRowText: { color: CALM_COLORS.TEXT_DISABLED },
  rowTitle: {
    ...CALM_TEXT.control,
    color: CALM_COLORS.TEXT,
  },
  rowDetail: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT_DIM,
    marginTop: scale(8),
  },
  comfortHelp: { fontSize: scale(36), lineHeight: scale(52) },
  comfortBody: { fontSize: scale(40), lineHeight: scale(56) },
  comfortRow: { paddingVertical: scale(32), marginBottom: scale(24) },
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
    borderRadius: scale(CALM_CONTROL.RADIUS),
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
