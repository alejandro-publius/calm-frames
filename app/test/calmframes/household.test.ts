/**
 * The household setting, the per-title status and the parent area's pieces.
 *
 * The rule under test everywhere here is the one from CLAUDE.md: a room
 * setting can only add hides, never remove them, and nothing is ever weaker
 * than WCAG.
 */

import fs from 'fs';
import path from 'path';
import {
  buildCoverIntervals,
  DEFAULT_GUARD_BAND_MS,
  DEFAULT_MIN_COVER_MS,
  FlashSegment,
  totalCoveredMs,
} from '../../src/calmframes/coverSchedule';
import {
  clampSettings,
  coverOptionsFor,
  DEFAULT_SETTINGS,
  describeRoom,
  displayWidthIn,
  fieldInches,
  HouseholdSettings,
  mapCoversRoom,
  PRESET_NAMES,
  PRESETS,
  roomFieldFraction,
  SEAT_DISTANCE_CHOICES_IN,
  TV_DIAGONAL_CHOICES_IN,
  unionSegments,
} from '../../src/calmframes/household';
import {
  addHideEntry,
  describeHideEntry,
  emptyHideLog,
  formatDuration,
  formatPosition,
  HIDE_LOG_LIMIT,
  HideLogEntry,
  totalHiddenMs,
} from '../../src/calmframes/hideLog';
import {
  attemptPin,
  emptyPinGate,
  hashPin,
  isValidPin,
  LOCKOUT_MS,
  MAX_ATTEMPTS,
  setPin,
} from '../../src/calmframes/parentGate';
import {
  badgeLabel,
  CatalogTitle,
  checkTitles,
  kidModeTitles,
} from '../../src/calmframes/titleStatus';

const burstsMapText = fs.readFileSync(
  path.join(__dirname, 'fixtures', 'bursts.flashmap.json'),
  'utf8',
);
const BURSTS = JSON.parse(burstsMapText);
const KEY = '533gF/bCDXyQppRnqiiT41+JwyyUYRN8P4YVZnCbKLQ=';
const NOW = Date.parse(BURSTS.created_utc) + 1000;

describe('presets', () => {
  it('every preset keeps the WCAG map, it never swaps it out', () => {
    for (const name of PRESET_NAMES) {
      expect(PRESETS[name].mapProfiles).toContain('wcag');
    }
  });

  it('no preset can produce a shorter guard band or cover than the default', () => {
    for (const name of PRESET_NAMES) {
      const options = coverOptionsFor({ ...DEFAULT_SETTINGS, preset: name });
      expect(options.guardBandMs).toBeGreaterThanOrEqual(DEFAULT_GUARD_BAND_MS);
      expect(options.minCoverMs).toBeGreaterThanOrEqual(DEFAULT_MIN_COVER_MS);
    }
  });

  it('covers at least as much as the standard preset, whatever is chosen', () => {
    const segments: FlashSegment[] = [
      { startMs: 1_000, endMs: 1_400 },
      { startMs: 9_000, endMs: 12_000 },
      { startMs: 12_100, endMs: 12_300, reason: 'red' },
      { startMs: 40_000, endMs: 41_000 },
    ];
    const baseline = buildCoverIntervals(
      segments,
      coverOptionsFor({ ...DEFAULT_SETTINGS, preset: 'wcag' }),
    );

    for (const name of PRESET_NAMES) {
      const chosen = buildCoverIntervals(
        segments,
        coverOptionsFor({ ...DEFAULT_SETTINGS, preset: name }),
      );
      expect(totalCoveredMs(chosen)).toBeGreaterThanOrEqual(
        totalCoveredMs(baseline),
      );
      // And not only in total: every millisecond the baseline hides is hidden.
      for (const interval of baseline) {
        for (const at of [interval.startMs, (interval.startMs + interval.endMs) / 2, interval.endMs - 1]) {
          const stillHidden = chosen.some(
            (one) => at >= one.startMs && at < one.endMs,
          );
          expect(stillHidden).toBe(true);
        }
      }
    }
  });

  it('keeps a red segment red through the union', () => {
    const merged = buildCoverIntervals(
      unionSegments([
        { segments: [{ startMs: 1_000, endMs: 2_000, reason: 'general' }] },
        { segments: [{ startMs: 1_500, endMs: 2_500, reason: 'red' }] },
      ]),
      { guardBandMs: 0 },
    );
    expect(merged).toHaveLength(1);
    expect(merged[0].reason).toBe('red');
  });
});

describe('the room', () => {
  it('matches the trigonometry flashmap uses', () => {
    // A 10 degree field at 96 inches spans 2 * 96 * tan(5 degrees).
    expect(fieldInches(96)).toBeCloseTo(2 * 96 * Math.tan((Math.PI / 180) * 5), 6);
    // A 55 inch 16 by 9 screen is about 47.9 inches across.
    expect(displayWidthIn(55)).toBeCloseTo(47.94, 1);
  });

  it('gets stricter as the television grows or the sofa comes closer', () => {
    const base = DEFAULT_SETTINGS;
    const bigger = { ...base, tvDiagonalIn: 85 };
    const closer = { ...base, seatDistanceIn: 48 };
    expect(roomFieldFraction(bigger)).toBeLessThan(roomFieldFraction(base));
    expect(roomFieldFraction(closer)).toBeLessThan(roomFieldFraction(base));
  });

  it('says a map does not answer for a room stricter than it measured', () => {
    // The WCAG window is 341 of 1024 across, a third of the picture.
    const map = { windows: [{ name: 'wcag-10deg', widthFraction: 341 / 1024 }] };
    expect(mapCoversRoom(map, { preset: 'wcag', tvDiagonalIn: 43, seatDistanceIn: 120 })).toBe(
      true,
    );
    expect(mapCoversRoom(map, { preset: 'wcag', tvDiagonalIn: 85, seatDistanceIn: 48 })).toBe(
      false,
    );
  });

  it('refuses a map with no windows at all', () => {
    expect(mapCoversRoom({ windows: [] }, DEFAULT_SETTINGS)).toBe(false);
  });

  it('falls back to the default for a setting that makes no sense', () => {
    expect(clampSettings(null)).toEqual(DEFAULT_SETTINGS);
    expect(
      clampSettings({ preset: 'whatever' as never, tvDiagonalIn: -5, seatDistanceIn: 0 }),
    ).toEqual(DEFAULT_SETTINGS);
    expect(clampSettings({ preset: 'broadcast', tvDiagonalIn: 65, seatDistanceIn: 72 })).toEqual(
      { preset: 'broadcast', tvDiagonalIn: 65, seatDistanceIn: 72 },
    );
  });

  it('offers only sizes and distances a household would recognise', () => {
    expect(TV_DIAGONAL_CHOICES_IN).toContain(DEFAULT_SETTINGS.tvDiagonalIn);
    expect(SEAT_DISTANCE_CHOICES_IN).toContain(DEFAULT_SETTINGS.seatDistanceIn);
    expect(describeRoom(DEFAULT_SETTINGS)).toBe(
      '55 inch television, seats about 8 feet away',
    );
  });
});

describe('per title status', () => {
  const settings: HouseholdSettings = {
    preset: 'wcag',
    tvDiagonalIn: 43,
    seatDistanceIn: 120,
  };

  const titles: CatalogTitle[] = [
    {
      id: 'checked',
      title: 'Checked title',
      uri: 'https://example.invalid/a.m3u8',
      sha256: BURSTS.source.sha256,
      maps: { wcag: burstsMapText },
    },
    {
      id: 'waiting',
      title: 'Not checked yet',
      uri: 'https://example.invalid/b.m3u8',
      sha256: 'b'.repeat(64),
      maps: {},
    },
    {
      id: 'broken',
      title: 'Check failed',
      uri: 'https://example.invalid/c.m3u8',
      sha256: 'c'.repeat(64),
      maps: { wcag: burstsMapText },
    },
  ];

  it('sorts titles into checked, waiting and failed', () => {
    const checked = checkTitles(titles, {
      publicKeyBase64: KEY,
      nowMs: NOW,
      settings,
    });
    expect(checked.map((one) => one.status)).toEqual([
      'verified',
      'pending',
      'failed',
    ]);
    expect(checked[1].rejection).toBe('missing');
    // The third title's map is real, but it describes a different file.
    expect(checked[2].rejection).toBe('wrong-file');
    expect(checked[0].segments).toHaveLength(3);
    expect(checked[0].hiddenMs).toBe(10_200);
  });

  it('never lists an unchecked title in kid mode', () => {
    const checked = checkTitles(titles, {
      publicKeyBase64: KEY,
      nowMs: NOW,
      settings,
    });
    const listed = kidModeTitles(checked);
    expect(listed.map((one) => one.title.id)).toEqual(['checked']);
  });

  it('makes a checked title pending again when the room gets stricter', () => {
    const strict: HouseholdSettings = {
      preset: 'wcag',
      tvDiagonalIn: 85,
      seatDistanceIn: 48,
    };
    const checked = checkTitles([titles[0]], {
      publicKeyBase64: KEY,
      nowMs: NOW,
      settings: strict,
    });
    expect(checked[0].status).toBe('pending');
    expect(checked[0].reason).toMatch(/stricter than the check/);
    expect(kidModeTitles(checked)).toHaveLength(0);
  });

  it('is pending when the preset asks for a map the title does not have', () => {
    const checked = checkTitles([titles[0]], {
      publicKeyBase64: KEY,
      nowMs: NOW,
      settings: { ...settings, preset: 'broadcast' },
    });
    expect(checked[0].status).toBe('pending');
    expect(checked[0].verifiedProfiles).toEqual(['wcag']);
  });

  it('has a plain badge for each status', () => {
    expect(badgeLabel('verified')).toBe('Checked');
    expect(badgeLabel('pending')).toBe('Needs check');
    expect(badgeLabel('failed')).toBe('Check failed');
  });
});

describe('the hide log', () => {
  const entry = (overrides: Partial<HideLogEntry> = {}): HideLogEntry => ({
    atMs: new Date(2026, 8, 17, 19, 5).getTime(),
    titleId: 'a',
    titleName: 'Sintel',
    positionMs: 65_000,
    durationMs: 4_000,
    cause: 'schedule',
    ...overrides,
  });

  it('keeps the newest first and stops growing', () => {
    let log = emptyHideLog();
    for (let index = 0; index < HIDE_LOG_LIMIT + 10; index += 1) {
      log = addHideEntry(log, entry({ positionMs: index }));
    }
    expect(log.entries).toHaveLength(HIDE_LOG_LIMIT);
    expect(log.entries[0].positionMs).toBe(HIDE_LOG_LIMIT + 9);
  });

  it('adds up what was hidden', () => {
    const log = addHideEntry(
      addHideEntry(emptyHideLog(), entry()),
      entry({ durationMs: 1_500 }),
    );
    expect(totalHiddenMs(log)).toBe(5_500);
  });

  it('writes a line a parent can read', () => {
    expect(formatPosition(65_000)).toBe('1:05');
    expect(formatPosition(0)).toBe('0:00');
    expect(formatDuration(1_000)).toBe('1 second');
    expect(formatDuration(4_400)).toBe('4 seconds');
    expect(describeHideEntry(entry())).toBe(
      '19:05 Sintel: hid 4 seconds at 1:05',
    );
    expect(describeHideEntry(entry({ cause: 'seek' }))).toMatch(
      /after moving the playhead$/,
    );
    expect(describeHideEntry(entry({ cause: 'unverified' }))).toBe(
      '19:05 Sintel: kept the picture hidden, title not checked',
    );
  });
});

describe('the parent PIN', () => {
  const salt = 'a1b2c3d4';
  const rounds = 4; // The real count is slow on purpose. Four is enough to test.

  it('only takes four digits', () => {
    expect(isValidPin('1234')).toBe(true);
    expect(isValidPin('12345')).toBe(false);
    expect(isValidPin('12a4')).toBe(false);
    expect(() => setPin(emptyPinGate(), 'abcd', salt, rounds)).toThrow();
  });

  it('never stores the PIN itself', () => {
    const state = setPin(emptyPinGate(), '1234', salt, rounds);
    expect(JSON.stringify(state)).not.toContain('1234');
    expect(state.record?.hash).toBe(hashPin('1234', salt, rounds));
  });

  it('gives a different hash for the same PIN under a different salt', () => {
    expect(hashPin('1234', 'one', rounds)).not.toBe(hashPin('1234', 'two', rounds));
  });

  it('opens on the right PIN and not on a wrong one', () => {
    const state = setPin(emptyPinGate(), '1234', salt, rounds);
    expect(attemptPin(state, '1234', 0).ok).toBe(true);
    const wrong = attemptPin(state, '4321', 0);
    expect(wrong.ok).toBe(false);
    expect(wrong.message).toMatch(/4 tries left/);
  });

  it('locks for a minute after five wrong tries', () => {
    let state = setPin(emptyPinGate(), '1234', salt, rounds);
    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt += 1) {
      state = attemptPin(state, '0000', 1_000).state;
    }
    expect(state.lockedUntilMs).toBe(1_000 + LOCKOUT_MS);
    const duringLockout = attemptPin(state, '1234', 2_000);
    expect(duringLockout.ok).toBe(false);
    expect(duringLockout.message).toMatch(/Wait \d+ seconds/);
    // And the right PIN works again once the lockout is over.
    expect(attemptPin(state, '1234', 1_000 + LOCKOUT_MS + 1).ok).toBe(true);
  });

  it('says so when no PIN has been set', () => {
    const result = attemptPin(emptyPinGate(), '1234', 0);
    expect(result.ok).toBe(false);
    expect(result.message).toMatch(/No PIN is set/);
  });
});
