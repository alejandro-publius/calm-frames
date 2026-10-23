/**
 * Family profiles: up to four kids, one PIN.
 *
 * A household is rarely one child. The younger one needs more hidden than the
 * older one, and the older one watches on the same television from the same
 * sofa. So each profile carries its own preset and its own room, and the
 * parent area shows each kid's own record of what was hidden for them.
 *
 * Two rules shape everything here, and both are enforced by the shape of the
 * module rather than by remembering:
 *
 * - One PIN for the household, never one per profile. A PIN per kid would read
 *   as four locks and be four chances to leave one unset, and the thing behind
 *   the lock is the same settings either way. `PinGateState` stays where it
 *   was, beside the family rather than inside a profile.
 *
 * - A profile can only ever add hides. The household setting is a floor, not a
 *   default: `effectiveSettings` takes the stricter of the floor and the
 *   profile on every axis, so a profile set to Standard inside a household set
 *   to Extra cautious still gets Extra cautious. Under that floor sits WCAG
 *   itself, because every preset keeps the WCAG map and `coverOptionsFor`
 *   floors the guard band and the minimum cover at the WCAG defaults. There is
 *   no arrangement of four profiles that hides less than WCAG asks.
 *
 * The strictness order is written down here rather than inferred, and
 * test/calmframes/profiles.test.ts checks the order against what the presets
 * actually do: a preset ranked above another has to include its maps and have
 * a guard band and a minimum cover at least as long. A rank that lied would be
 * the one way a profile could come out weaker.
 */

import {
  clampSettings,
  coverOptionsFor,
  DEFAULT_SETTINGS,
  HouseholdSettings,
  PRESET_NAMES,
  PRESETS,
  PresetName,
  roomFieldFraction,
} from './household';
import { CHIME_ON_BY_DEFAULT } from './chimeCue';
import {
  addHideEntry,
  emptyHideLog,
  HIDE_LOG_LIMIT,
  HideLogEntry,
  HideLogStore,
} from './hideLog';

/**
 * Four.
 *
 * Not a technical limit. A picker that stays one row of large targets on a
 * television is about four, and a household that needs more than four is a
 * household this app has not been designed for yet.
 */
export const MAX_PROFILES = 4;

/** The longest name that still fits one line of the picker at ten feet. */
export const MAX_PROFILE_NAME = 16;

/** What a profile is called before anyone names it. */
export const DEFAULT_PROFILE_NAME = 'Kid';

/** What the household floor is called on screen, beside the kids' names. */
export const EVERYONE_ID = 'everyone';

export interface Profile {
  /** Stable for the life of the profile. Hide log entries are keyed by it. */
  id: string;
  name: string;
  /** This kid's preset and this kid's room. Never weaker than the floor. */
  settings: HouseholdSettings;
}

export interface Family {
  /**
   * The household floor, set in the first run.
   *
   * Every profile is measured against this and the stricter one wins, so
   * raising the floor raises every kid at once and no kid can go under it.
   */
  floor: HouseholdSettings;
  profiles: Profile[];
  activeProfileId: string;
  /**
   * The soft chime a moment before the picture goes dark.
   *
   * One switch for the household rather than one per kid, because it is about
   * the room the television is in rather than about who is watching, and
   * because a chime that is on for one kid and off for another is a chime
   * nobody learns to read. On unless a household turns it off, and turning it
   * off changes nothing about what is hidden.
   */
  chimeEnabled: boolean;
  /** Optional for old records; only an explicit true enables an interface effect. */
  interfaceMotionEnabled?: boolean;
  interfaceSoundsEnabled?: boolean;
}

/**
 * How strict each preset is, highest hides most.
 *
 * Written out rather than derived, so adding a preset means saying where it
 * sits. profiles.test.ts then checks the claim against the presets themselves.
 */
export const PRESET_STRICTNESS: Record<PresetName, number> = {
  wcag: 0,
  broadcast: 1,
  'extra-cautious': 2,
};

/** The stricter of two presets. Ties keep the first. */
export function strictestPreset(left: PresetName, right: PresetName): PresetName {
  return PRESET_STRICTNESS[left] >= PRESET_STRICTNESS[right] ? left : right;
}

function cleanName(name: string | null | undefined): string {
  const trimmed = typeof name === 'string' ? name.trim() : '';
  if (trimmed.length === 0) {
    return DEFAULT_PROFILE_NAME;
  }
  return trimmed.slice(0, MAX_PROFILE_NAME);
}

export function makeProfile(
  id: string,
  name: string,
  settings: Partial<HouseholdSettings> = {},
): Profile {
  return {
    id,
    name: cleanName(name),
    settings: clampSettings({ ...DEFAULT_SETTINGS, ...settings }),
  };
}

export function clampProfile(profile: Profile): Profile {
  return makeProfile(profile.id, profile.name, profile.settings);
}

/** A household that has just finished the first run: one profile, one floor. */
export function newFamily(
  floor: HouseholdSettings = DEFAULT_SETTINGS,
  firstName: string = DEFAULT_PROFILE_NAME,
): Family {
  const first = makeProfile('profile-1', firstName, floor);
  return {
    floor: clampSettings(floor),
    profiles: [first],
    activeProfileId: first.id,
    chimeEnabled: CHIME_ON_BY_DEFAULT,
    interfaceMotionEnabled: false,
    interfaceSoundsEnabled: false,
  };
}

/**
 * Put a family record back into a shape the rest of the app can rely on.
 *
 * Anything read back from storage goes through here: an empty profile list
 * becomes one profile, an unknown active id falls back to the first, extra
 * profiles past the fourth are dropped and every setting is clamped.
 */
export function clampFamily(family: Partial<Family> | null | undefined): Family {
  const floor = clampSettings(family?.floor);
  const profiles = (family?.profiles ?? [])
    .slice(0, MAX_PROFILES)
    .map((profile) => clampProfile(profile));
  if (profiles.length === 0) {
    return newFamily(floor);
  }
  const active = profiles.some((profile) => profile.id === family?.activeProfileId)
    ? (family?.activeProfileId as string)
    : profiles[0].id;
  // Anything but an explicit false leaves the chime on, so a record written
  // before the chime existed comes back with it on rather than silently off.
  return {
    floor,
    profiles,
    activeProfileId: active,
    chimeEnabled: family?.chimeEnabled !== false,
    interfaceMotionEnabled: family?.interfaceMotionEnabled === true,
    interfaceSoundsEnabled: family?.interfaceSoundsEnabled === true,
  };
}

/** Turn the chime on or off for the household. */
export function setChimeEnabled(family: Family, enabled: boolean): Family {
  return { ...family, chimeEnabled: enabled };
}

export function findProfile(family: Family, id: string): Profile | undefined {
  return family.profiles.find((profile) => profile.id === id);
}

/** Whoever the shelf is currently for. Never undefined: a family has one. */
export function activeProfile(family: Family): Profile {
  return findProfile(family, family.activeProfileId) ?? family.profiles[0];
}

export function canAddProfile(family: Family): boolean {
  return family.profiles.length < MAX_PROFILES;
}

/** An id nothing else in this family is using. */
export function nextProfileId(family: Family): string {
  let index = family.profiles.length + 1;
  while (family.profiles.some((profile) => profile.id === `profile-${index}`)) {
    index += 1;
  }
  return `profile-${index}`;
}

/** Add a kid. A full family is returned unchanged rather than growing. */
export function addProfile(family: Family, name: string): Family {
  if (!canAddProfile(family)) {
    return family;
  }
  const profile = makeProfile(nextProfileId(family), name, family.floor);
  return { ...family, profiles: [...family.profiles, profile] };
}

/** Remove a kid. The last one is never removed: a family has somebody in it. */
export function removeProfile(family: Family, id: string): Family {
  if (family.profiles.length <= 1) {
    return family;
  }
  const profiles = family.profiles.filter((profile) => profile.id !== id);
  if (profiles.length === family.profiles.length) {
    return family;
  }
  const activeProfileId = profiles.some(
    (profile) => profile.id === family.activeProfileId,
  )
    ? family.activeProfileId
    : profiles[0].id;
  return { ...family, profiles, activeProfileId };
}

export function renameProfile(family: Family, id: string, name: string): Family {
  return {
    ...family,
    profiles: family.profiles.map((profile) =>
      profile.id === id ? { ...profile, name: cleanName(name) } : profile,
    ),
  };
}

/**
 * Why a typed name cannot be saved, or null when it can.
 *
 * `renameProfile` repairs quietly: a blank becomes Kid and a long name is cut
 * short. That is right for a record read back from storage and wrong for a
 * parent's typing, so the editor asks here first, and nothing it saves is
 * changed on the way in. Names are compared trimmed and without regard to
 * case, because Robin and robin are two chips nobody can tell apart from a
 * sofa. `reserved` is for words the picker already uses beside the kids'
 * names, such as the household's own label.
 */
export type ProfileNameProblem = 'empty' | 'long' | 'taken';

export function nameProblem(
  draft: string,
  taken: string[],
  maxLength: number = MAX_PROFILE_NAME,
): ProfileNameProblem | null {
  const name = draft.trim();
  if (name.length === 0) {
    return 'empty';
  }
  if (name.length > maxLength) {
    return 'long';
  }
  const lower = name.toLowerCase();
  return taken.some((other) => other.trim().toLowerCase() === lower) ? 'taken' : null;
}

/** The names one kid's new name may not match: every other kid's, then the reserved words. */
export function namesTakenFor(family: Family, id: string, reserved: string[] = []): string[] {
  return [
    ...family.profiles
      .filter((profile) => profile.id !== id)
      .map((profile) => profile.name),
    ...reserved,
  ];
}

export function profileNameProblem(
  family: Family,
  id: string,
  draft: string,
  reserved: string[] = [],
): ProfileNameProblem | null {
  return nameProblem(draft, namesTakenFor(family, id, reserved));
}

/** Change one kid's own preset or room. The floor still applies over it. */
export function setProfileSettings(
  family: Family,
  id: string,
  settings: Partial<HouseholdSettings>,
): Family {
  return {
    ...family,
    profiles: family.profiles.map((profile) =>
      profile.id === id
        ? { ...profile, settings: clampSettings({ ...profile.settings, ...settings }) }
        : profile,
    ),
  };
}

/** Raise or lower the household floor. Every profile moves with it. */
export function setFloor(family: Family, settings: Partial<HouseholdSettings>): Family {
  return { ...family, floor: clampSettings({ ...family.floor, ...settings }) };
}

/** Switch who the shelf is for. An unknown id changes nothing. */
export function selectProfile(family: Family, id: string): Family {
  return findProfile(family, id) ? { ...family, activeProfileId: id } : family;
}

/**
 * What the guard actually runs with for this kid.
 *
 * The stricter of the floor and the profile, axis by axis. This is the
 * function that makes "no profile can be weaker" true, so it is the one the
 * mutation gate attacks and the one profiles.test.ts measures rather than
 * reads.
 *
 * The room comparison is the part worth saying out loud. A smaller ten degree
 * field fraction is the stricter room, because a narrower window is filled by
 * a smaller patch of flashing, so more content crosses the area limit and more
 * titles are held back as pending for that room. household.ts says the same
 * thing beside roomFieldFraction. So the room that hides more is the one with
 * the smaller fraction, and that is the one every profile keeps.
 */
export function effectiveSettings(
  family: Family,
  profile: Profile,
): HouseholdSettings {
  const floor = clampSettings(family.floor);
  const chosen = clampSettings(profile.settings);
  const preset = strictestPreset(floor.preset, chosen.preset);
  const room = roomFieldFraction(chosen) <= roomFieldFraction(floor) ? chosen : floor;
  return {
    preset,
    tvDiagonalIn: room.tvDiagonalIn,
    seatDistanceIn: room.seatDistanceIn,
  };
}

/** The schedule options for one kid, floored twice over: by the household and by WCAG. */
export function profileCoverOptions(family: Family, profile: Profile) {
  return coverOptionsFor(effectiveSettings(family, profile));
}

/** Plain wording for the parent area, when a kid's own choice is not what runs. */
export function describeFloorEffect(family: Family, profile: Profile): string | null {
  const effective = effectiveSettings(family, profile);
  if (effective.preset === clampSettings(profile.settings).preset) {
    return null;
  }
  return `Everyone is set to ${PRESETS[effective.preset].title}, so ${profile.name} gets that.`;
}

/** Every preset, in the order they get stricter. For a picker that reads in order. */
export function presetsByStrictness(): PresetName[] {
  return [...PRESET_NAMES].sort(
    (left, right) => PRESET_STRICTNESS[left] - PRESET_STRICTNESS[right],
  );
}

/**
 * One hide log per profile.
 *
 * Keyed by profile id rather than by name, so renaming a kid keeps their
 * record. A profile with nothing hidden yet has no key at all, and reading it
 * gives an empty log rather than undefined.
 */
export type ProfileLogs = Record<string, HideLogStore>;

export function emptyProfileLogs(): ProfileLogs {
  return {};
}

export function logForProfile(logs: ProfileLogs, profileId: string): HideLogStore {
  return logs[profileId] ?? emptyHideLog();
}

/**
 * Record one hide against one kid.
 *
 * Nothing is shared between profiles: an entry written for one id can only
 * ever be read back under that id, which is what makes each kid's parent view
 * theirs.
 */
export function addProfileHide(
  logs: ProfileLogs,
  profileId: string,
  entry: HideLogEntry,
  limit = HIDE_LOG_LIMIT,
): ProfileLogs {
  return {
    ...logs,
    [profileId]: addHideEntry(logForProfile(logs, profileId), entry, limit),
  };
}

/**
 * Everything hidden on this device, whoever it was hidden for.
 *
 * What the parent area shows under Everyone. Newest first, the same order one
 * profile's log is in, so the two read the same way.
 */
export function allProfileHides(
  logs: ProfileLogs,
  limit = HIDE_LOG_LIMIT,
): HideLogStore {
  const entries = Object.values(logs)
    .flatMap((store) => store.entries)
    .sort((left, right) => right.atMs - left.atMs)
    .slice(0, limit);
  return { entries };
}
