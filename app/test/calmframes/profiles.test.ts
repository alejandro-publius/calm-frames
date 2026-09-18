/**
 * Family profiles, and the rule that a profile can only ever add hides.
 *
 * The household setting was already floored at WCAG. Profiles put a second
 * layer over that, and a second layer is a second chance to get it wrong: a
 * kid set to Standard inside a household set to Extra cautious must still get
 * Extra cautious, and a kid sitting further from the television must not undo
 * a room the household set closer. So the tests here do not read the code,
 * they measure it: for every pair of floor and profile, every millisecond the
 * floor hides has to still be hidden, and the effective room has to be no
 * wider than either of the two it came from.
 *
 * Seen to fail, on purpose, in an isolated copy of the app rather than in this
 * tree, because other lanes are working in it:
 *
 * - `effectiveSettings` returning `chosen.preset` instead of
 *   `strictestPreset(floor.preset, chosen.preset)` turned five tests red. The
 *   first was "is never weaker than the household floor, whatever it picks",
 *   with `expect(received).toContain(expected) // indexOf`, Expected value:
 *   "broadcast", Received array: ["wcag"]: a kid on Standard inside a
 *   Broadcast household stopped unioning the broadcast map.
 * - the room comparison flipped from `<=` to `>` turned one test red, "the
 *   room a profile runs with is never wider than either room it came from",
 *   with `expect(received).toBeLessThanOrEqual(expected)`, Expected: <=
 *   0.11337023775422096, Received: 0.35041709851304664: the kid sitting four
 *   feet from an 85 inch television got the household's far sofa instead of
 *   their own close one.
 */

import {
  buildCoverIntervals,
  DEFAULT_GUARD_BAND_MS,
  DEFAULT_MIN_COVER_MS,
  FlashSegment,
  totalCoveredMs,
} from '../../src/calmframes/coverSchedule';
import {
  coverOptionsFor,
  DEFAULT_SETTINGS,
  HouseholdSettings,
  PRESET_NAMES,
  PRESETS,
  PresetName,
  roomFieldFraction,
} from '../../src/calmframes/household';
import { HideLogEntry } from '../../src/calmframes/hideLog';
import {
  activeProfile,
  addProfile,
  addProfileHide,
  allProfileHides,
  canAddProfile,
  clampFamily,
  describeFloorEffect,
  effectiveSettings,
  emptyProfileLogs,
  Family,
  logForProfile,
  makeProfile,
  MAX_PROFILE_NAME,
  MAX_PROFILES,
  newFamily,
  presetsByStrictness,
  PRESET_STRICTNESS,
  profileCoverOptions,
  Profile,
  removeProfile,
  renameProfile,
  selectProfile,
  setFloor,
  setProfileSettings,
  strictestPreset,
} from '../../src/calmframes/profiles';

const SEGMENTS: FlashSegment[] = [
  { startMs: 1_000, endMs: 1_400 },
  { startMs: 9_000, endMs: 12_000 },
  { startMs: 12_100, endMs: 12_300, reason: 'red' },
  { startMs: 40_000, endMs: 41_000 },
];

/** The rooms worth trying: the default, a stricter one, a laxer one. */
const ROOMS: Array<Pick<HouseholdSettings, 'tvDiagonalIn' | 'seatDistanceIn'>> = [
  { tvDiagonalIn: 55, seatDistanceIn: 96 },
  { tvDiagonalIn: 85, seatDistanceIn: 48 },
  { tvDiagonalIn: 32, seatDistanceIn: 144 },
];

function household(
  preset: PresetName,
  room: Pick<HouseholdSettings, 'tvDiagonalIn' | 'seatDistanceIn'>,
): HouseholdSettings {
  return { preset, ...room };
}

function familyWith(floor: HouseholdSettings, profile: HouseholdSettings): Family {
  return {
    floor,
    profiles: [makeProfile('profile-1', 'Robin', profile)],
    activeProfileId: 'profile-1',
    chimeEnabled: true,
  };
}

function scheduleFor(settings: HouseholdSettings) {
  return buildCoverIntervals(SEGMENTS, coverOptionsFor(settings));
}

function hiddenAt(intervals: ReturnType<typeof scheduleFor>, atMs: number): boolean {
  return intervals.some((one) => atMs >= one.startMs && atMs < one.endMs);
}

function entry(atMs: number, titleName: string): HideLogEntry {
  return {
    atMs,
    titleId: 'one',
    titleName,
    positionMs: 10_000,
    durationMs: 4_000,
    cause: 'schedule',
  };
}

describe('the strictness order', () => {
  it('agrees with what the presets actually do', () => {
    // A rank that lied would be the one way a profile could come out weaker,
    // because effectiveSettings picks by rank. So the rank is checked against
    // the presets rather than trusted: anything ranked above another has to
    // keep its maps and hold a guard band and a minimum cover at least as
    // long.
    const order = presetsByStrictness();
    expect(order).toHaveLength(PRESET_NAMES.length);
    for (let index = 1; index < order.length; index += 1) {
      const gentler = PRESETS[order[index - 1]];
      const stricter = PRESETS[order[index]];
      for (const profile of gentler.mapProfiles) {
        expect(stricter.mapProfiles).toContain(profile);
      }
      expect(stricter.guardBandMs).toBeGreaterThanOrEqual(gentler.guardBandMs);
      expect(stricter.minCoverMs).toBeGreaterThanOrEqual(gentler.minCoverMs);
    }
  });

  it('puts WCAG at the bottom, because nothing is allowed under it', () => {
    expect(PRESET_STRICTNESS.wcag).toBe(0);
    for (const name of PRESET_NAMES) {
      expect(strictestPreset('wcag', name)).toBe(name === 'wcag' ? 'wcag' : name);
    }
  });

  it('keeps the stricter of two presets whichever way round they come', () => {
    expect(strictestPreset('wcag', 'extra-cautious')).toBe('extra-cautious');
    expect(strictestPreset('extra-cautious', 'wcag')).toBe('extra-cautious');
    expect(strictestPreset('broadcast', 'broadcast')).toBe('broadcast');
  });
});

describe('a profile can only add hides', () => {
  it('is never weaker than the household floor, whatever it picks', () => {
    for (const floorPreset of PRESET_NAMES) {
      for (const floorRoom of ROOMS) {
        const floor = household(floorPreset, floorRoom);
        const baseline = scheduleFor(floor);
        for (const kidPreset of PRESET_NAMES) {
          for (const kidRoom of ROOMS) {
            const family = familyWith(floor, household(kidPreset, kidRoom));
            const effective = effectiveSettings(family, family.profiles[0]);
            const chosen = buildCoverIntervals(
              SEGMENTS,
              profileCoverOptions(family, family.profiles[0]),
            );

            expect(totalCoveredMs(chosen)).toBeGreaterThanOrEqual(
              totalCoveredMs(baseline),
            );
            // Not only in total. Every millisecond the floor hides is hidden.
            for (const interval of baseline) {
              for (const at of [
                interval.startMs,
                (interval.startMs + interval.endMs) / 2,
                interval.endMs - 1,
              ]) {
                expect(hiddenAt(chosen, at)).toBe(true);
              }
            }
            // And the maps the floor unions are all still unioned.
            for (const profile of PRESETS[floor.preset].mapProfiles) {
              expect(PRESETS[effective.preset].mapProfiles).toContain(profile);
            }
          }
        }
      }
    }
  });

  it('is never weaker than WCAG, which is the floor under the floor', () => {
    const wcag = scheduleFor({ ...DEFAULT_SETTINGS, preset: 'wcag' });
    for (const floorPreset of PRESET_NAMES) {
      for (const kidPreset of PRESET_NAMES) {
        const family = familyWith(
          household(floorPreset, ROOMS[0]),
          household(kidPreset, ROOMS[2]),
        );
        const options = profileCoverOptions(family, family.profiles[0]);
        expect(options.guardBandMs).toBeGreaterThanOrEqual(DEFAULT_GUARD_BAND_MS);
        expect(options.minCoverMs).toBeGreaterThanOrEqual(DEFAULT_MIN_COVER_MS);
        expect(
          totalCoveredMs(buildCoverIntervals(SEGMENTS, options)),
        ).toBeGreaterThanOrEqual(totalCoveredMs(wcag));
        expect(PRESETS[effectiveSettings(family, family.profiles[0]).preset].mapProfiles).toContain(
          'wcag',
        );
      }
    }
  });

  it('the room a profile runs with is never wider than either room it came from', () => {
    // A smaller ten degree fraction is the stricter room: more of what was
    // measured crosses the area limit, so more titles are held back. The
    // effective room therefore has to be no wider than either of the two.
    for (const floorRoom of ROOMS) {
      for (const kidRoom of ROOMS) {
        const floor = household('wcag', floorRoom);
        const family = familyWith(floor, household('wcag', kidRoom));
        const effective = effectiveSettings(family, family.profiles[0]);
        expect(roomFieldFraction(effective)).toBeLessThanOrEqual(
          roomFieldFraction(floor),
        );
        expect(roomFieldFraction(effective)).toBeLessThanOrEqual(
          roomFieldFraction(household('wcag', kidRoom)),
        );
      }
    }
  });

  it('gives a kid the gentler setting only when the floor allows it', () => {
    const family = familyWith(
      household('wcag', ROOMS[0]),
      household('extra-cautious', ROOMS[0]),
    );
    expect(effectiveSettings(family, family.profiles[0]).preset).toBe('extra-cautious');

    const strictHouse = familyWith(
      household('extra-cautious', ROOMS[0]),
      household('wcag', ROOMS[0]),
    );
    expect(effectiveSettings(strictHouse, strictHouse.profiles[0]).preset).toBe(
      'extra-cautious',
    );
  });

  it('says out loud when the floor is what a kid is actually getting', () => {
    const strictHouse = familyWith(
      household('extra-cautious', ROOMS[0]),
      household('wcag', ROOMS[0]),
    );
    expect(describeFloorEffect(strictHouse, strictHouse.profiles[0])).toContain(
      'Extra cautious',
    );
    const matched = familyWith(household('wcag', ROOMS[0]), household('wcag', ROOMS[0]));
    expect(describeFloorEffect(matched, matched.profiles[0])).toBeNull();
  });

  it('cannot be loosened by writing rubbish into a profile', () => {
    const family = familyWith(household('broadcast', ROOMS[0]), DEFAULT_SETTINGS);
    const wrecked = setProfileSettings(family, 'profile-1', {
      preset: 'anything-goes' as PresetName,
      tvDiagonalIn: Number.NaN,
      seatDistanceIn: -5,
    });
    const effective = effectiveSettings(wrecked, wrecked.profiles[0]);
    expect(effective.preset).toBe('broadcast');
    expect(effective.tvDiagonalIn).toBeGreaterThan(0);
    expect(effective.seatDistanceIn).toBeGreaterThan(0);
  });
});

describe('the family record', () => {
  it('starts as one kid, watching, on the household floor', () => {
    const family = newFamily(DEFAULT_SETTINGS);
    expect(family.profiles).toHaveLength(1);
    expect(activeProfile(family).id).toBe(family.activeProfileId);
    expect(family.floor).toEqual(DEFAULT_SETTINGS);
  });

  it('holds four kids and no more', () => {
    let family = newFamily(DEFAULT_SETTINGS);
    for (let index = 0; index < 10; index += 1) {
      family = addProfile(family, `Kid ${index}`);
    }
    expect(family.profiles).toHaveLength(MAX_PROFILES);
    expect(canAddProfile(family)).toBe(false);
    expect(new Set(family.profiles.map((profile) => profile.id)).size).toBe(
      MAX_PROFILES,
    );
  });

  it('never removes the last profile, and never leaves nobody watching', () => {
    const one = newFamily(DEFAULT_SETTINGS);
    expect(removeProfile(one, one.profiles[0].id)).toEqual(one);

    const two = selectProfile(addProfile(one, 'Sam'), 'profile-2');
    const left = removeProfile(two, 'profile-2');
    expect(left.profiles).toHaveLength(1);
    expect(activeProfile(left).id).toBe('profile-1');
  });

  it('keeps a name a television can show, and keeps the id when it changes', () => {
    const family = renameProfile(
      newFamily(DEFAULT_SETTINGS),
      'profile-1',
      '   Alexandra Wilhelmina the Third   ',
    );
    expect(family.profiles[0].name.length).toBeLessThanOrEqual(MAX_PROFILE_NAME);
    expect(family.profiles[0].name.startsWith('Alexandra')).toBe(true);
    expect(family.profiles[0].id).toBe('profile-1');
    expect(renameProfile(family, 'profile-1', '   ').profiles[0].name).toBe('Kid');
  });

  it('ignores a switch to a profile that is not there', () => {
    const family = newFamily(DEFAULT_SETTINGS);
    expect(selectProfile(family, 'nobody')).toEqual(family);
  });

  it('puts a broken record back into a shape the app can use', () => {
    const family = clampFamily({
      floor: { preset: 'nonsense' as PresetName, tvDiagonalIn: 0, seatDistanceIn: 0 },
      profiles: [],
      activeProfileId: 'gone',
    });
    expect(family.profiles).toHaveLength(1);
    expect(family.floor).toEqual(DEFAULT_SETTINGS);
    expect(activeProfile(family)).toBeDefined();

    const crowded = clampFamily({
      floor: DEFAULT_SETTINGS,
      profiles: Array.from({ length: 9 }, (unused, index) =>
        makeProfile(`profile-${index}`, `Kid ${index}`),
      ) as Profile[],
      activeProfileId: 'profile-8',
    });
    expect(crowded.profiles).toHaveLength(MAX_PROFILES);
    expect(crowded.activeProfileId).toBe('profile-0');
  });

  it('moves every kid when the floor moves', () => {
    const family = setFloor(addProfile(newFamily(DEFAULT_SETTINGS), 'Sam'), {
      preset: 'extra-cautious',
    });
    for (const profile of family.profiles) {
      expect(effectiveSettings(family, profile).preset).toBe('extra-cautious');
    }
  });
});

describe('one log per kid', () => {
  it('keeps each kid reading only their own', () => {
    let logs = emptyProfileLogs();
    logs = addProfileHide(logs, 'profile-1', entry(1_000, 'One'));
    logs = addProfileHide(logs, 'profile-2', entry(2_000, 'Two'));
    logs = addProfileHide(logs, 'profile-1', entry(3_000, 'Three'));

    expect(logForProfile(logs, 'profile-1').entries.map((one) => one.titleName)).toEqual(
      ['Three', 'One'],
    );
    expect(logForProfile(logs, 'profile-2').entries.map((one) => one.titleName)).toEqual(
      ['Two'],
    );
    expect(logForProfile(logs, 'profile-3').entries).toEqual([]);
  });

  it('keeps a kid a record through a rename, because the key is the id', () => {
    const family = renameProfile(newFamily(DEFAULT_SETTINGS), 'profile-1', 'Robin');
    const logs = addProfileHide(emptyProfileLogs(), 'profile-1', entry(1_000, 'One'));
    expect(logForProfile(logs, family.profiles[0].id).entries).toHaveLength(1);
  });

  it('puts everything hidden on the device in one list, newest first', () => {
    let logs = emptyProfileLogs();
    logs = addProfileHide(logs, 'profile-1', entry(1_000, 'One'));
    logs = addProfileHide(logs, 'profile-2', entry(3_000, 'Three'));
    logs = addProfileHide(logs, 'profile-1', entry(2_000, 'Two'));
    expect(allProfileHides(logs).entries.map((one) => one.titleName)).toEqual([
      'Three',
      'Two',
      'One',
    ]);
  });

  it('holds each kid to the same limit as the household log', () => {
    let logs = emptyProfileLogs();
    for (let index = 0; index < 5; index += 1) {
      logs = addProfileHide(logs, 'profile-1', entry(index, `Title ${index}`), 3);
    }
    expect(logForProfile(logs, 'profile-1').entries).toHaveLength(3);
  });
});
