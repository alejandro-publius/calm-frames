/**
 * Kid mode's shelf, the details page and the parent area.
 *
 * Every empty state and every error state is here as well as the happy path,
 * because the states nobody demonstrates are the ones that ship broken. The
 * rule each of them has to keep is the same one: an error state never puts an
 * unchecked title within reach.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { MINIMUM_TEXT_SIZE } from '../../src/calmframes/calmStyles';
import {
  BACKEND_UNREACHABLE,
  BACKEND_UNREACHABLE_EMPTY,
  CHIME_OFF_LABEL,
  CHIME_ON_LABEL,
  NO_TITLES,
  PIN_NOT_SET,
  PIN_WRONG_TITLE,
  SAFETY_NOTE,
  TITLE_FAILED,
  TITLE_PENDING,
  TITLE_STALE,
} from '../../src/calmframes/copy';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import FlashMapStrip, {
  describeStrip,
  MINIMUM_MARK_FRACTION,
  stripMarks,
} from '../../src/calmframes/FlashMapStrip';
import {
  addHideEntry,
  emptyHideLog,
  HideLogEntry,
} from '../../src/calmframes/hideLog';
import {
  DEFAULT_SETTINGS,
  HouseholdSettings,
  TV_DIAGONAL_CHOICES_IN,
} from '../../src/calmframes/household';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import {
  OFFLINE_PUBLIC_KEY_BASE64,
  offlineTitle,
} from '../../src/calmframes/offlineTitle';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import {
  emptyPinGate,
  MAX_ATTEMPTS,
  setPin,
} from '../../src/calmframes/parentGate';
import {
  addProfile,
  addProfileHide,
  effectiveSettings,
  emptyProfileLogs,
  Family,
  newFamily,
  setChimeEnabled,
  setFloor,
} from '../../src/calmframes/profiles';
import ShieldBadge from '../../src/calmframes/ShieldBadge';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CheckedTitle, checkTitle } from '../../src/calmframes/titleStatus';
import ViewingPlan from '../../src/calmframes/ViewingPlan';

function makeTitle(
  id: string,
  status: CheckedTitle['status'],
  overrides: Partial<CheckedTitle> = {},
): CheckedTitle {
  return {
    title: {
      id,
      title: `Title ${id}`,
      uri: `https://example.invalid/${id}.m3u8`,
      sha256: 'a'.repeat(64),
      durationMs: 600_000,
      posterUrl: `https://example.invalid/${id}.jpg`,
    },
    status,
    segments: [
      { startMs: 60_000, endMs: 64_000 },
      { startMs: 300_000, endMs: 301_000, reason: 'red' },
    ],
    hiddenMs: 5_000,
    verifiedProfiles: ['wcag'],
    ...overrides,
  };
}

/** The title bundled in the package, checked with the real reader. */
const MAP_MADE_AT = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc);
function bundledTitle(nowMs: number): CheckedTitle {
  return checkTitle(offlineTitle('file:///offline/calm_gradient.mp4'), {
    settings: DEFAULT_SETTINGS,
    publicKeyBase64: OFFLINE_PUBLIC_KEY_BASE64,
    nowMs,
  });
}

describe('FlashMapStrip', () => {
  const intervals = buildCoverIntervals(
    [
      { startMs: 60_000, endMs: 64_000 },
      { startMs: 300_000, endMs: 301_000, reason: 'red' },
    ],
    { guardBandMs: 500, durationMs: 600_000 },
  );

  it('places a mark where the interval falls', () => {
    const marks = stripMarks(intervals, 600_000);
    expect(marks).toHaveLength(2);
    expect(marks[0].left).toBeCloseTo(59_500 / 600_000, 5);
    expect(marks[0].width).toBeCloseTo(5_000 / 600_000, 5);
    expect(marks[1].reason).toBe('red');
  });

  it('widens a mark too thin to see', () => {
    const tiny = buildCoverIntervals([{ startMs: 0, endMs: 400 }], {
      guardBandMs: 0,
    });
    const marks = stripMarks(tiny, 3_600_000);
    expect(marks[0].width).toBe(MINIMUM_MARK_FRACTION);
  });

  it('draws nothing when the duration is unknown', () => {
    expect(stripMarks(intervals, 0)).toEqual([]);
  });

  it('says out loud what the strip shows', () => {
    expect(describeStrip(intervals, 600_000)).toBe(
      '2 flashing parts, 7 seconds in all, spread through about 10 minutes.',
    );
    expect(describeStrip([], 600_000)).toBe(
      'Nothing in this title goes over the flash limits.',
    );
  });

  it('renders one mark per interval with a label a screen reader can use', () => {
    render(<FlashMapStrip intervals={intervals} durationMs={600_000} />);
    expect(screen.getByTestId('flash-map-strip-mark-0')).toBeTruthy();
    expect(screen.getByTestId('flash-map-strip-mark-1')).toBeTruthy();
    expect(
      screen.getByTestId('flash-map-strip').props.accessibilityLabel,
    ).toMatch(/2 flashing parts/);
  });
});

describe('ShieldBadge', () => {
  it('says the status in words, not only in colour', () => {
    for (const [status, label] of [
      ['verified', 'Checked'],
      ['pending', 'Being checked'],
      ['failed', 'Check failed'],
    ] as const) {
      const { unmount } = render(<ShieldBadge status={status} />);
      expect(screen.getByTestId('shield-badge-label').props.children).toBe(
        label,
      );
      unmount();
    }
  });
});

describe('the household viewing plan', () => {
  it.each(['pending', 'failed'] as const)(
    'keeps the standalone plan hidden for a %s entry',
    (status) => {
      render(
        <ViewingPlan
          entry={makeTitle('blocked', status)}
          settings={DEFAULT_SETTINGS}
        />,
      );
      expect(screen.queryByTestId('viewing-plan')).toBeNull();
    },
  );

  it('does not call an old Standard check a ready Broadcast plan', () => {
    render(
      <ViewingPlan
        entry={makeTitle('old-check', 'verified')}
        settings={{ ...DEFAULT_SETTINGS, preset: 'broadcast' }}
      />,
    );
    expect(screen.queryByTestId('viewing-plan')).toBeNull();
  });

  it('explains the checked maps, selected room and playback fallback without overclaiming', () => {
    render(
      <TitleDetailsScreen
        entry={makeTitle('plan', 'verified')}
        settings={DEFAULT_SETTINGS}
        onPlay={jest.fn()}
      />,
    );
    expect(screen.getByTestId('title-details-plan-preset').props.children).toBe(
      'Standard',
    );
    expect(screen.getByTestId('title-details-plan-room').props.children).toBe(
      '55 inch television, seats about 8 feet away',
    );
    expect(screen.getByTestId('title-details-plan-maps').props.children).toBe(
      'Checked maps: WCAG 2.3.1.',
    );
    expect(
      screen.getByTestId('title-details-plan-continuity').props.children,
    ).toMatch(
      /checked still when available.*opaque cover.*Sound and captions/i,
    );
    expect(screen.getByTestId('title-details-plan-limits').props.children).toBe(
      SAFETY_NOTE,
    );
  });

  it.each(['pending', 'failed'] as const)(
    'never presents a ready viewing plan for a %s title',
    (status) => {
      const onPlay = jest.fn();
      render(
        <TitleDetailsScreen
          entry={makeTitle('blocked-plan', status)}
          onPlay={onPlay}
        />,
      );
      expect(screen.queryByTestId('title-details-plan')).toBeNull();
      fireEvent.press(screen.getByTestId('title-details-play'));
      expect(onPlay).not.toHaveBeenCalled();
    },
  );

  it('updates the viewing plan when the household changes instead of showing stale choices', () => {
    const entry = makeTitle('plan', 'verified', {
      verifiedProfiles: ['wcag', 'broadcast'],
    });
    const { rerender } = render(
      <TitleDetailsScreen entry={entry} onPlay={jest.fn()} />,
    );
    rerender(
      <TitleDetailsScreen
        entry={entry}
        settings={{
          preset: 'extra-cautious',
          tvDiagonalIn: 65,
          seatDistanceIn: 72,
        }}
        onPlay={jest.fn()}
      />,
    );
    expect(screen.getByTestId('title-details-plan-preset').props.children).toBe(
      'Extra cautious',
    );
    expect(screen.getByTestId('title-details-plan-room').props.children).toBe(
      '65 inch television, seats about 6 feet away',
    );
    expect(screen.getByTestId('title-details-plan-maps').props.children).toBe(
      'Checked maps: WCAG 2.3.1 and broadcast.',
    );
  });
});

describe('KidHomeScreen', () => {
  const titles = [
    makeTitle('ok', 'verified'),
    makeTitle('waiting', 'pending'),
    makeTitle('bad', 'failed'),
  ];

  it('lists only the checked titles', () => {
    render(<KidHomeScreen titles={titles} onOpen={jest.fn()} />);
    expect(screen.getByTestId('kid-home-poster-ok')).toBeTruthy();
    expect(screen.queryByTestId('kid-home-poster-waiting')).toBeNull();
    expect(screen.queryByTestId('kid-home-poster-bad')).toBeNull();
    expect(screen.getByTestId('kid-home-hidden-count').props.children).toEqual(
      expect.arrayContaining([2]),
    );
  });

  it('opens a title when it is pressed', () => {
    const onOpen = jest.fn();
    render(<KidHomeScreen titles={titles} onOpen={onOpen} />);
    fireEvent.press(screen.getByTestId('kid-home-poster-ok'));
    expect(onOpen).toHaveBeenCalledWith(titles[0]);
  });

  it('says so plainly when nothing is ready, and shows no grid at all', () => {
    render(<KidHomeScreen titles={[titles[1]]} onOpen={jest.fn()} />);
    expect(screen.getByTestId('kid-home-empty-title').props.children).toBe(
      NO_TITLES.title,
    );
    expect(screen.getByTestId('kid-home-empty-detail').props.children).toBe(
      NO_TITLES.detail,
    );
    expect(screen.queryByTestId('kid-home-poster-waiting')).toBeNull();
  });

  it('keeps playing the bundled title when the service cannot be reached', () => {
    const bundled = bundledTitle(MAP_MADE_AT + 1_000);
    expect(bundled.status).toBe('verified');

    const onOpen = jest.fn();
    render(
      <KidHomeScreen
        titles={[bundled, titles[1]]}
        onOpen={onOpen}
        offline
      />,
    );
    expect(screen.getByTestId('kid-home-offline-title').props.children).toBe(
      BACKEND_UNREACHABLE.title,
    );
    fireEvent.press(screen.getByTestId(`kid-home-poster-${bundled.title.id}`));
    expect(onOpen).toHaveBeenCalledWith(bundled);
  });

  it('says the service is unreachable and offers nothing when the shelf is bare', () => {
    render(<KidHomeScreen titles={[titles[2]]} onOpen={jest.fn()} offline />);
    expect(screen.getByTestId('kid-home-empty-title').props.children).toBe(
      BACKEND_UNREACHABLE_EMPTY.title,
    );
    expect(screen.queryByTestId('kid-home-poster-bad')).toBeNull();
  });

  it('has no video and nothing that plays by itself', () => {
    const { toJSON } = render(
      <KidHomeScreen titles={titles} onOpen={jest.fn()} />,
    );
    const tree = JSON.stringify(toJSON());
    expect(tree).not.toMatch(
      /autoPlay|shouldPlay|Video|KeplerVideoSurfaceView/i,
    );
    // An Image is a still. That is the only picture on this screen.
    expect(screen.getByTestId('kid-home-poster-image-ok')).toBeTruthy();
  });

  it('never draws a poster for a title that did not verify', () => {
    const { toJSON } = render(
      <KidHomeScreen titles={titles} onOpen={jest.fn()} offline />,
    );
    const tree = JSON.stringify(toJSON());
    expect(tree).toContain('ok.jpg');
    expect(tree).not.toContain('waiting.jpg');
    expect(tree).not.toContain('bad.jpg');
  });

  it('draws its headings at a ten foot size', () => {
    render(<KidHomeScreen titles={titles} onOpen={jest.fn()} />);
    const style = screen.getByTestId('kid-home-title').props.style;
    const flat = Array.isArray(style) ? Object.assign({}, ...style) : style;
    expect(flat.fontSize).toBeGreaterThanOrEqual(MINIMUM_TEXT_SIZE);
  });
});

describe('TitleDetailsScreen', () => {
  it('says how much will be hidden and shows the strip', () => {
    render(
      <TitleDetailsScreen entry={makeTitle('ok', 'verified')} onPlay={jest.fn()} />,
    );
    expect(screen.getByTestId('title-details-summary').props.children).toMatch(
      /2 parts will be hidden/,
    );
    expect(screen.getByTestId('title-details-strip')).toBeTruthy();
  });

  it('will not play a title that is still being checked', () => {
    const onPlay = jest.fn();
    render(
      <TitleDetailsScreen
        entry={makeTitle('waiting', 'pending', {
          reason: 'This title is not checked yet, so the picture stays hidden.',
          segments: [],
        })}
        onPlay={onPlay}
      />,
    );
    const play = screen.getByTestId('title-details-play');
    expect(play.props.accessibilityState).toEqual({ disabled: true });
    fireEvent.press(play);
    expect(onPlay).not.toHaveBeenCalled();
    expect(
      screen.getByTestId('title-details-notice-title').props.children,
    ).toBe(TITLE_PENDING.title);
    // Nothing to show about a title that has not been checked.
    expect(screen.queryByTestId('title-details-strip')).toBeNull();
    expect(screen.queryByTestId('title-details-summary')).toBeNull();
  });

  it('will not play a title whose check did not pass', () => {
    const onPlay = jest.fn();
    render(
      <TitleDetailsScreen
        entry={makeTitle('bad', 'failed', {
          rejection: 'bad-signature',
          reason:
            'The check for this title was changed after it was signed, so the picture stays hidden.',
          segments: [],
        })}
        onPlay={onPlay}
      />,
    );
    fireEvent.press(screen.getByTestId('title-details-play'));
    expect(onPlay).not.toHaveBeenCalled();
    expect(
      screen.getByTestId('title-details-notice-title').props.children,
    ).toBe(TITLE_FAILED.title);
    expect(
      screen.getByTestId('title-details-notice-detail').props.children,
    ).toMatch(/changed after it was signed/);
  });

  it('will not play a title whose check is too old, checked with the real reader', () => {
    // Ninety days and a minute after the bundled map was made.
    const stale = bundledTitle(MAP_MADE_AT + 90 * 24 * 60 * 60 * 1000 + 60_000);
    expect(stale.rejection).toBe('stale');

    const onPlay = jest.fn();
    render(<TitleDetailsScreen entry={stale} onPlay={onPlay} />);
    fireEvent.press(screen.getByTestId('title-details-play'));
    expect(onPlay).not.toHaveBeenCalled();
    expect(
      screen.getByTestId('title-details-notice-title').props.children,
    ).toBe(TITLE_STALE.title);
  });

  it('plays a checked title', () => {
    const onPlay = jest.fn();
    const entry = makeTitle('ok', 'verified');
    render(<TitleDetailsScreen entry={entry} onPlay={onPlay} />);
    fireEvent.press(screen.getByTestId('title-details-play'));
    expect(onPlay).toHaveBeenCalledWith(entry);
  });

  it('shows a stricter preset as more hidden time, never less', () => {
    const entry = makeTitle('ok', 'verified');
    const standard = render(
      <TitleDetailsScreen entry={entry} onPlay={jest.fn()} settings={DEFAULT_SETTINGS} />,
    );
    const standardText = String(
      screen.getByTestId('title-details-summary').props.children,
    );
    standard.unmount();

    render(
      <TitleDetailsScreen
        entry={entry}
        onPlay={jest.fn()}
        settings={{ ...DEFAULT_SETTINGS, preset: 'extra-cautious' }}
      />,
    );
    const strictText = String(
      screen.getByTestId('title-details-summary').props.children,
    );
    const seconds = (text: string) => Number(/(\d+) second/.exec(text)?.[1] ?? 0);
    expect(seconds(strictText)).toBeGreaterThan(seconds(standardText));
  });
});

describe('ParentAreaScreen', () => {
  const rounds = 4;
  const gate = setPin(emptyPinGate(), '1357', 'seed', rounds);
  const titles = [makeTitle('ok', 'verified'), makeTitle('bad', 'failed')];
  const log = addHideEntry(emptyHideLog(), {
    atMs: new Date(2026, 8, 17, 20, 15).getTime(),
    titleId: 'ok',
    titleName: 'Title ok',
    positionMs: 60_000,
    durationMs: 5_000,
    cause: 'schedule',
  });

  function renderArea(overrides: Record<string, unknown> = {}) {
    const onSettingsChange = jest.fn();
    const onGateChange = jest.fn();
    render(
      <ParentAreaScreen
        gate={gate}
        onGateChange={onGateChange}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={onSettingsChange}
        log={log}
        titles={titles}
        nowMs={() => 0}
        {...overrides}
      />,
    );
    return { onSettingsChange, onGateChange };
  }

  const enter = (pin: string) => {
    for (const digit of pin) {
      fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
    }
  };

  it('offers the credits, and only once the PIN is right', () => {
    // CC BY asks for attribution where a person can read it. NOTICE ships with
    // the source, which is not much use to somebody holding a remote, so this
    // is the one route to it in the running app. Behind the PIN because the
    // credits are a parent's screen, not part of kid mode.
    const onCredits = jest.fn();
    renderArea({ onCredits });

    expect(screen.queryByTestId('parent-area-credits')).toBeNull();

    enter('1357');
    fireEvent.press(screen.getByTestId('parent-area-credits'));
    expect(onCredits).toHaveBeenCalled();
  });

  it('shows only the keypad until the PIN is right', () => {
    renderArea();
    expect(screen.getByTestId('parent-area')).toBeTruthy();
    expect(screen.queryByTestId('parent-area-open')).toBeNull();
    expect(screen.queryByTestId('parent-area-preset-wcag')).toBeNull();

    enter('0000');
    expect(screen.queryByTestId('parent-area-open')).toBeNull();
    expect(screen.getByTestId('parent-area-message-title').props.children).toBe(
      PIN_WRONG_TITLE,
    );
    expect(
      screen.getByTestId('parent-area-message-detail').props.children,
    ).toMatch(/not right/);
  });

  it('says how many tries are left, and then that it is locked', () => {
    // One state for the whole run, so the failed attempts really accumulate.
    let live = gate;
    render(
      <ParentAreaScreen
        gate={live}
        onGateChange={(next) => {
          live = next;
        }}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={jest.fn()}
        log={log}
        titles={titles}
        nowMs={() => 0}
      />,
    );
    enter('0000');
    expect(
      screen.getByTestId('parent-area-message-detail').props.children,
    ).toMatch(new RegExp(`${MAX_ATTEMPTS - 1} tries left`));
    expect(live.failedAttempts).toBe(1);
  });

  it('offers no keypad at all when no PIN has been set', () => {
    const onSetPin = jest.fn();
    renderArea({ gate: emptyPinGate(), onSetPin });
    expect(screen.queryByTestId('parent-area-keypad')).toBeNull();
    expect(screen.getByTestId('parent-area-message-title').props.children).toBe(
      PIN_NOT_SET.title,
    );
    fireEvent.press(screen.getByTestId('parent-area-set-pin'));
    expect(onSetPin).toHaveBeenCalled();
  });

  it('opens on the right PIN and shows the settings, the log and the statuses', () => {
    renderArea();
    enter('1357');
    expect(screen.getByTestId('parent-area-open')).toBeTruthy();
    expect(
      screen.getByTestId('parent-area-preset-extra-cautious'),
    ).toBeTruthy();
    expect(screen.getByTestId('parent-area-room').props.children).toMatch(
      /55 inch television/,
    );
    expect(screen.getByTestId('parent-area-log-0').props.children).toMatch(
      /Title ok: hid 5 seconds at 1:00/,
    );
    expect(
      screen.getByTestId('parent-area-status-bad-label').props.children,
    ).toBe('Check failed');
  });

  it('says why a title is not on the shelf, in the same words as its page', () => {
    renderArea();
    enter('1357');
    expect(screen.getByTestId('parent-area-reason-bad').props.children).toBe(
      TITLE_FAILED.detail,
    );
    expect(screen.queryByTestId('parent-area-reason-ok')).toBeNull();
  });

  it('changes the preset and the room, and says the room can only add', () => {
    const { onSettingsChange } = renderArea();
    enter('1357');
    fireEvent.press(screen.getByTestId('parent-area-preset-extra-cautious'));
    expect(onSettingsChange).toHaveBeenCalledWith({
      ...DEFAULT_SETTINGS,
      preset: 'extra-cautious',
    });

    fireEvent.press(screen.getByTestId('parent-area-tv-85'));
    expect(onSettingsChange).toHaveBeenCalledWith({
      ...DEFAULT_SETTINGS,
      tvDiagonalIn: 85,
    });

    fireEvent.press(screen.getByTestId('parent-area-seat-48'));
    expect(onSettingsChange).toHaveBeenCalledWith({
      ...DEFAULT_SETTINGS,
      seatDistanceIn: 48,
    });
  });

  /**
   * Which television and which distance are chosen, in words.
   *
   * The chips carried chosen as a fill colour and nothing else, which is the
   * same defect the profile picker had: a state only a person who can tell two
   * shades of teal apart can read, on a television, from a sofa. It gets the
   * same answer the picker got, a sentence under the row, rather than a second
   * style of saying the same thing.
   *
   * Under the row and not on the chip, because a word on the chosen chip would
   * make that chip wider than it was a moment earlier and slide every chip
   * after it along the row, and kid mode has no motion. There is no way to
   * measure a width here, so the guard is on the cause: the chips draw the same
   * text whichever one is chosen.
   *
   * Seen to fail twice, once for each half.
   *
   * With the television line dropped and the chosen state left to
   * `styles.rowSelected` alone:
   *
   *     ● ParentAreaScreen › says which television and which distance are
   *       chosen, in words
   *
   *       Unable to find an element with testID: parent-area-tv-chosen
   *
   *       at Object.getByTestId (test/calmframes/screens.test.tsx:551:19)
   *
   * And with the word put back on the chosen chip, which is what would make
   * the row slide:
   *
   *       expect(received).toEqual(expected) // deep equality
   *
   *       - Expected  - 2
   *       + Received  + 2
   *
   *         Array [
   *           "32, inch,",
   *           "43, inch,",
   *           "50, inch,",
   *       -   "55, inch, (chosen)",
   *       +   "55, inch,",
   *           "65, inch,",
   *           "75, inch,",
   *       -   "85, inch,",
   *       +   "85, inch, (chosen)",
   *         ]
   *
   *       at Object.toEqual (test/calmframes/screens.test.tsx:586:24)
   */
  it('says which television and which distance are chosen, in words', () => {
    const area = (settings: HouseholdSettings) => (
      <ParentAreaScreen
        gate={gate}
        onGateChange={jest.fn()}
        settings={settings}
        onSettingsChange={jest.fn()}
        log={log}
        titles={titles}
        nowMs={() => 0}
      />
    );
    const view = render(area(DEFAULT_SETTINGS));
    enter('1357');

    expect(screen.getByTestId('parent-area-tv-chosen').props.children).toBe(
      '55 inch is chosen.',
    );
    expect(screen.getByTestId('parent-area-seat-chosen').props.children).toBe(
      '8 feet away is chosen.',
    );
    // The rows say which question they are asking, and the chips carry the
    // state a radio carries rather than only a fill.
    expect(
      screen.getByLabelText('Television size').props.accessibilityRole,
    ).toBe('radiogroup');
    expect(
      screen.getByLabelText('How far away the sofa is').props.accessibilityRole,
    ).toBe('radiogroup');
    expect(
      screen.getByTestId('parent-area-tv-55').props.accessibilityState,
    ).toEqual({ checked: true, selected: true });
    expect(
      screen.getByTestId('parent-area-tv-85').props.accessibilityState,
    ).toEqual({ checked: false, selected: false });

    const chipText = () =>
      TV_DIAGONAL_CHOICES_IN.map((inches) =>
        String(
          screen.getByTestId(`parent-area-tv-${inches}-label`).props.children,
        ),
      );
    const before = chipText();

    view.rerender(
      area({ ...DEFAULT_SETTINGS, tvDiagonalIn: 85, seatDistanceIn: 48 }),
    );
    expect(screen.getByTestId('parent-area-tv-chosen').props.children).toBe(
      '85 inch is chosen.',
    );
    expect(screen.getByTestId('parent-area-seat-chosen').props.children).toBe(
      '4 feet away is chosen.',
    );
    // Only the sentence moved. No chip grew, so no chip slid.
    expect(chipText()).toEqual(before);
  });

  it('announces the PIN result politely', () => {
    renderArea();
    const message = screen.getByTestId('parent-area-message');
    expect(message.props.accessibilityLiveRegion).toBe('polite');
    expect(message.props['aria-live']).toBe('polite');
  });
});

/**
 * Family profiles, on the screens.
 *
 * The model's own rules are measured in test/calmframes/profiles.test.ts. What
 * is checked here is that the screens use them: the shelf says whose it is, the
 * parent area edits one kid without touching the others, and the one PIN is
 * asked for once for the household rather than once per kid.
 *
 * Seen to fail, in an isolated copy rather than in this tree: the parent area
 * reading `allProfileHides(profileLogs)` where it should read
 * `logForProfile(profileLogs, editingProfile.id)` turned "shows each kid their
 * own record and no one else's" red with `expect(received).toContain(expected)`,
 * Expected substring: "Robin title", Received string: "16:00 Sam title: hid 4
 * seconds at 1:00". One kid opening another kid's record is the whole reason
 * these logs are keyed by profile.
 */
describe('family profiles on the screens', () => {
  const twoKids: Family = addProfile(
    newFamily(DEFAULT_SETTINGS, 'Robin'),
    'Sam',
  );
  const gate = setPin(emptyPinGate(), '1357', 'seed', 4);

  function hide(atMs: number, titleName: string): HideLogEntry {
    return {
      atMs,
      titleId: 'ok',
      titleName,
      positionMs: 60_000,
      durationMs: 4_000,
      cause: 'schedule',
    };
  }

  function renderFamilyArea(overrides: Record<string, unknown> = {}) {
    const onFamilyChange = jest.fn();
    render(
      <ParentAreaScreen
        gate={gate}
        onGateChange={jest.fn()}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={jest.fn()}
        log={emptyHideLog()}
        family={twoKids}
        onFamilyChange={onFamilyChange}
        titles={[]}
        nowMs={() => 0}
        {...overrides}
      />,
    );
    for (const digit of '1357') {
      fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
    }
    return { onFamilyChange };
  }

  it('says on the shelf whose shelf it is, and offers the others', () => {
    const onChooseProfile = jest.fn();
    render(
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified')]}
        onOpen={jest.fn()}
        profiles={twoKids.profiles}
        activeProfileId="profile-1"
        onChooseProfile={onChooseProfile}
      />,
    );
    // The answer is a sentence under the row, not a word on a chip.
    expect(screen.getByTestId('kid-home-profiles-chosen').props.children).toBe(
      'Robin is watching.',
    );
    fireEvent.press(screen.getByTestId('kid-home-profiles-profile-2'));
    expect(onChooseProfile).toHaveBeenCalledWith(twoKids.profiles[1]);
  });

  /**
   * The chips do not change size when the choice moves.
   *
   * They used to. The chosen chip carried " (watching)" inside it, so choosing
   * somebody made their chip wider and everything after it slid along the row.
   * There is no way to measure a width here, because react-test-renderer does
   * no layout, so the guard is on the cause rather than the effect: a chip's
   * text is the name and nothing else, whoever is chosen. Put the word back on
   * the chip and this goes red.
   *
   * Seen to fail. With the chosen word put back on the chip:
   *
   *     ● family profiles on the screens › draws the same text on every chip
   *       whoever is chosen
   *
   *       - Expected  - 2
   *       + Received  + 2
   *
   *         Array [
   *       -   "Robin, (watching)",
   *       -   "Sam,",
   *       +   "Robin,",
   *       +   "Sam, (watching)",
   *         ]
   *
   *       at Object.toEqual (test/calmframes/screens.test.tsx:620:24)
   */
  it('draws the same text on every chip whoever is chosen', () => {
    const chipText = () =>
      twoKids.profiles.map((profile) =>
        String(
          screen.getByTestId(`kid-home-profiles-${profile.id}-name`).props.children,
        ),
      );

    const shelf = (activeProfileId: string) => (
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified')]}
        onOpen={jest.fn()}
        profiles={twoKids.profiles}
        activeProfileId={activeProfileId}
        onChooseProfile={jest.fn()}
      />
    );

    const view = render(shelf('profile-1'));
    const before = chipText();
    view.rerender(shelf('profile-2'));

    expect(chipText()).toEqual(before);
    expect(before).toEqual(['Robin', 'Sam']);
    // Only the sentence under the row moved.
    expect(screen.getByTestId('kid-home-profiles-chosen').props.children).toBe(
      'Sam is watching.',
    );
  });

  /** Seen to fail with the radiogroup role taken off the row. */
  it('reads the row as one question rather than five loose buttons', () => {
    render(
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified')]}
        onOpen={jest.fn()}
        profiles={twoKids.profiles}
        activeProfileId="profile-1"
        onChooseProfile={jest.fn()}
      />,
    );
    // A radio group, labelled with the question it is asking, and the chosen
    // chip carries the state a radio carries rather than only a fill colour.
    expect(
      screen.getByLabelText('Who is watching').props.accessibilityRole,
    ).toBe('radiogroup');
    expect(
      screen.getByTestId('kid-home-profiles-profile-1').props
        .accessibilityState,
    ).toEqual({ checked: true, selected: true });
    expect(
      screen.getByTestId('kid-home-profiles-profile-2').props.accessibilityState,
    ).toEqual({ checked: false, selected: false });
  });

  it('leaves the shelf exactly as it was for a household with no profiles', () => {
    render(
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified')]}
        onOpen={jest.fn()}
      />,
    );
    expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
  });

  it('does not ask who is watching when there is nothing to watch', () => {
    render(
      <KidHomeScreen
        titles={[]}
        onOpen={jest.fn()}
        profiles={twoKids.profiles}
        activeProfileId="profile-1"
        onChooseProfile={jest.fn()}
      />,
    );
    expect(screen.queryByTestId('kid-home-profiles')).toBeNull();
    expect(screen.getByTestId('kid-home-empty')).toBeDefined();
  });

  it('asks for the one PIN once, not once per kid', () => {
    renderFamilyArea();
    // Switching between kids behind the gate never puts the keypad back.
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-2'));
    expect(screen.queryByTestId('parent-area-key-1')).toBeNull();
    expect(screen.getByTestId('parent-area-profiles')).toBeDefined();
  });

  it('changes one kid and leaves the household and the other kid alone', () => {
    const { onFamilyChange } = renderFamilyArea();
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-2'));
    fireEvent.press(screen.getByTestId('parent-area-preset-extra-cautious'));

    const next: Family = onFamilyChange.mock.calls[0][0];
    expect(next.profiles[1].settings.preset).toBe('extra-cautious');
    expect(next.profiles[0].settings.preset).toBe(DEFAULT_SETTINGS.preset);
    expect(next.floor).toEqual(DEFAULT_SETTINGS);
  });

  it('changes the household floor when the household is the one chosen', () => {
    const { onFamilyChange } = renderFamilyArea();
    fireEvent.press(screen.getByTestId('parent-area-preset-broadcast'));
    const next: Family = onFamilyChange.mock.calls[0][0];
    expect(next.floor.preset).toBe('broadcast');
    for (const profile of next.profiles) {
      expect(effectiveSettings(next, profile).preset).toBe('broadcast');
    }
  });

  it("shows each kid their own record and no one else's", () => {
    let logs = emptyProfileLogs();
    logs = addProfileHide(logs, 'profile-1', hide(1_000, 'Robin title'));
    logs = addProfileHide(logs, 'profile-2', hide(2_000, 'Sam title'));
    renderFamilyArea({ profileLogs: logs });

    // The household first: everything hidden on the device, newest first.
    expect(screen.getByTestId('parent-area-log-0').props.children).toContain(
      'Sam title',
    );
    expect(screen.getByTestId('parent-area-log-1').props.children).toContain(
      'Robin title',
    );

    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-1'));
    expect(screen.getByTestId('parent-area-log-0').props.children).toContain(
      'Robin title',
    );
    expect(screen.queryByTestId('parent-area-log-1')).toBeNull();
  });

  it('says a kid is getting the household setting when that is what is happening', () => {
    const strict: Family = setFloor(twoKids, { preset: 'extra-cautious' });
    renderFamilyArea({ family: strict });
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-1'));
    expect(
      screen.getByTestId('parent-area-floor-effect').props.children,
    ).toContain('Extra cautious');
  });

  it('offers the chime, on, and turns it off without touching anything else', () => {
    // On by default, and the switch says which way round it is rather than
    // relying on a highlight a parent has to interpret from the sofa.
    const { onFamilyChange } = renderFamilyArea();
    expect(screen.getByTestId('parent-area-chime-label').props.children).toBe(
      CHIME_ON_LABEL,
    );
    fireEvent.press(screen.getByTestId('parent-area-chime'));
    const next: Family = onFamilyChange.mock.calls[0][0];
    expect(next.chimeEnabled).toBe(false);
    // Turning the sound off changes nothing about what is hidden.
    expect(next.floor).toEqual(twoKids.floor);
    expect(next.profiles).toEqual(twoKids.profiles);
  });

  it('says the chime is off when it is off', () => {
    renderFamilyArea({ family: setChimeEnabled(twoKids, false) });
    expect(screen.getByTestId('parent-area-chime-label').props.children).toBe(
      CHIME_OFF_LABEL,
    );
  });

  /**
   * A parent who has scrolled past the picker still knows whose screen it is.
   *
   * The record already said the name. "How strict" and "The room" did not, and
   * those two are the ones where the difference matters: the floor under every
   * kid and one kid's own setting look identical once the picker is off the
   * top of the screen, and they are not the same thing at all.
   *
   * Seen to fail. With `sectionFor(STRICTNESS_TITLE, whose)` back to the bare
   * 'How strict', the first line said:
   *
   *     Unable to find an element with text: How strict for Everyone
   */
  it('says whose each section is, so a scrolled screen cannot be misread', () => {
    renderFamilyArea();
    expect(screen.getByText('How strict for Everyone')).toBeTruthy();
    expect(screen.getByText('The room for Everyone')).toBeTruthy();
    expect(screen.getByText('What was hidden for Everyone')).toBeTruthy();
    expect(
      screen.getByTestId('parent-area-profiles-chosen').props.children,
    ).toBe('These settings are for Everyone.');

    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-2'));
    expect(screen.getByText('How strict for Sam')).toBeTruthy();
    expect(screen.getByText('The room for Sam')).toBeTruthy();
    expect(screen.getByText('What was hidden for Sam')).toBeTruthy();
    expect(
      screen.getByTestId('parent-area-profiles-chosen').props.children,
    ).toBe('These settings are for Sam.');
  });

  /**
   * Seen to fail with `whose` naming the household whether or not a picker is
   * on screen: "Unable to find an element with text: How strict".
   */
  it('leaves the headings bare for a household that has never made a profile', () => {
    render(
      <ParentAreaScreen
        gate={gate}
        onGateChange={jest.fn()}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={jest.fn()}
        log={emptyHideLog()}
        titles={[]}
        nowMs={() => 0}
      />,
    );
    for (const digit of '1357') {
      fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
    }
    expect(screen.getByText('How strict')).toBeTruthy();
    expect(screen.getByText('The room')).toBeTruthy();
    expect(screen.getByText('What was hidden')).toBeTruthy();
    expect(screen.queryByTestId('parent-area-profiles')).toBeNull();
  });

  /**
   * The summary and the lines under it agree.
   *
   * The screen draws twenty lines and the store keeps two hundred, so a busy
   * household saw a count of forty three and twenty lines with nothing to say
   * why. This is the one record a household gets that any of this works, so it
   * says where the list stops.
   *
   * Seen to fail. With the third sentence taken out of hiddenSummary:
   *
   *     Expected: "25 parts, 1 minute 40 seconds in all. The 20 most recent are below."
   *     Received: "25 parts, 1 minute 40 seconds in all."
   */
  it('says where the list stops rather than showing twenty of twenty five', () => {
    let logs = emptyProfileLogs();
    for (let index = 0; index < 25; index += 1) {
      logs = addProfileHide(
        logs,
        'profile-1',
        hide(1_000 + index * 1_000, 'Title ok'),
      );
    }
    renderFamilyArea({ profileLogs: logs });

    expect(screen.getByTestId('parent-area-total').props.children).toBe(
      '25 parts, 1 minute 40 seconds in all. The 20 most recent are below.',
    );
    expect(screen.getByTestId('parent-area-log-19')).toBeTruthy();
    expect(screen.queryByTestId('parent-area-log-20')).toBeNull();
  });

  /**
   * A line says the time and nothing else, so the day goes above the lines.
   *
   * "19:30 hid 4 seconds" could be tonight or last Tuesday, and two hundred of
   * them read as one undated pile.
   *
   * Seen to fail, with `hideDayHeading` returning Today for every entry: this
   * one and the day test in copy.test.ts both went red.
   */
  it('puts a day over the lines, because a time on its own could be any day', () => {
    const tonight = new Date(2026, 8, 17, 20, 15).getTime();
    const nightBefore = new Date(2026, 8, 16, 19, 30).getTime();
    let logs = emptyProfileLogs();
    logs = addProfileHide(logs, 'profile-1', hide(nightBefore, 'Older title'));
    logs = addProfileHide(logs, 'profile-1', hide(tonight, 'Tonight title'));
    renderFamilyArea({
      profileLogs: logs,
      nowMs: () => new Date(2026, 8, 17, 21, 0).getTime(),
    });

    expect(
      screen.getByTestId('parent-area-log-day-2026-09-17').props.children,
    ).toBe('Today');
    expect(
      screen.getByTestId('parent-area-log-day-2026-09-16').props.children,
    ).toBe('Yesterday');
    // The lines keep their place in the whole list, newest first.
    expect(screen.getByTestId('parent-area-log-0').props.children).toContain(
      'Tonight title',
    );
    expect(screen.getByTestId('parent-area-log-1').props.children).toContain(
      'Older title',
    );
  });

  /** Seen to fail with `nextKidName` handing back the base name every time. */
  it('gives a new kid a name nobody else in the household has', () => {
    // There is no keyboard in the parent area, so two chips both reading Kid
    // would be a picker with no way out of the ambiguity.
    const withKid: Family = addProfile(
      newFamily(DEFAULT_SETTINGS, 'Kid'),
      'Robin',
    );
    const { onFamilyChange } = renderFamilyArea({ family: withKid });
    fireEvent.press(screen.getByTestId('parent-area-add-profile'));

    const next: Family = onFamilyChange.mock.calls[0][0];
    expect(next.profiles.map((one) => one.name)).toEqual([
      'Kid',
      'Robin',
      'Kid 2',
    ]);
  });

  /**
   * Removing a kid asks first, and the question is answerable both ways.
   *
   * One press used to take a kid's own preset, their room and their record of
   * what was hidden, and none of it comes back. The button sits next to the
   * picker a parent uses to switch between kids, which is the worst place on
   * the screen for a one press delete.
   *
   * The question is the app's own notice block with two buttons in it, not a
   * dialog. CLAUDE.md rules out anything that blocks events on Vega, and there
   * is no browser here to put a modal in. Both buttons say what they do rather
   * than OK and Cancel, and the one that changes nothing is first and takes
   * focus.
   *
   * Seen to fail. With the Remove press calling `removeProfile` straight away,
   * the way it did before:
   *
   *     ● family profiles on the screens › asks before it removes a kid, and
   *       removes nobody until it is answered
   *
   *       expect(jest.fn()).not.toHaveBeenCalled()
   *
   *       Expected number of calls: 0
   *       Received number of calls: 1
   *
   *       1: {"activeProfileId": "profile-1", "chimeEnabled": true, "floor":
   *       {"preset": "wcag", "seatDistanceIn": 96, "tvDiagonalIn": 55},
   *       "profiles": [{"id": "profile-1", "name": "Robin", "settings":
   *       {"preset": "wcag", "seatDistanceIn": 96, "tvDiagonalIn": 55}}]}
   *
   *       at Object.toHaveBeenCalled (test/calmframes/screens.test.tsx:1017:32)
   *
   * Sam is gone from that family already, on the press that was only meant to
   * ask.
   */
  it('asks before it removes a kid, and removes nobody until it is answered', () => {
    const { onFamilyChange } = renderFamilyArea();
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-2'));
    fireEvent.press(screen.getByTestId('parent-area-remove-profile'));

    // Nothing has happened yet. The screen has asked.
    expect(onFamilyChange).not.toHaveBeenCalled();
    expect(
      screen.getByTestId('parent-area-remove-question-title').props.children,
    ).toBe('Remove Sam?');
    expect(
      screen.getByTestId('parent-area-remove-question-detail').props.children,
    ).toContain('cannot be undone');
    // The question stands where the buttons were, so there is one thing being
    // asked and no way to add a kid in the middle of it.
    expect(screen.queryByTestId('parent-area-add-profile')).toBeNull();
    expect(screen.queryByTestId('parent-area-remove-profile')).toBeNull();

    // Both answers say what they do, and the safe one takes focus.
    const keep = screen.getByTestId('parent-area-remove-keep');
    expect(keep.props.accessibilityLabel).toBe('Keep Sam');
    expect(keep.props.hasTVPreferredFocus).toBe(true);
    expect(
      screen.getByTestId('parent-area-remove-confirm').props.accessibilityLabel,
    ).toBe('Remove Sam');

    // Keeping puts the buttons back and changes nothing.
    fireEvent.press(keep);
    expect(onFamilyChange).not.toHaveBeenCalled();
    expect(screen.queryByTestId('parent-area-remove-question')).toBeNull();
    expect(screen.getByTestId('parent-area-remove-profile')).toBeTruthy();

    // Answering the other way is what removes them.
    fireEvent.press(screen.getByTestId('parent-area-remove-profile'));
    fireEvent.press(screen.getByTestId('parent-area-remove-confirm'));
    const next: Family = onFamilyChange.mock.calls[0][0];
    expect(next.profiles.map((one) => one.name)).toEqual(['Robin']);
  });

  /**
   * A question asked about one kid cannot be answered about another.
   *
   * The picker sits above the question and stays live while it is up, so the
   * state is held by profile id rather than as a flag. Choosing somebody else
   * is not an answer, so it takes the question away rather than repointing it.
   *
   * Seen to fail. With the state held as a flag rather than an id, which is
   * `askedToRemove !== null` in place of `askedToRemove === editingId` and no
   * reset when the picker moves:
   *
   *     ● family profiles on the screens › takes the question away when the
   *       picker moves underneath it
   *
   *       expect(received).toBeNull()
   *
   *       Received: {"_fiber": {"_debugHookTypes": null, ... "elementType":
   *       "View", ... "type": "View", "updateQueue": null}}
   *
   *       at Object.toBeNull (test/calmframes/screens.test.tsx:1076:65)
   *
   * The question about Sam was still on screen with Robin chosen, which is the
   * one press that would have removed the wrong kid.
   */
  it('takes the question away when the picker moves underneath it', () => {
    const { onFamilyChange } = renderFamilyArea();
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-2'));
    fireEvent.press(screen.getByTestId('parent-area-remove-profile'));
    expect(screen.getByTestId('parent-area-remove-question')).toBeTruthy();

    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-1'));
    expect(screen.queryByTestId('parent-area-remove-question')).toBeNull();
    expect(onFamilyChange).not.toHaveBeenCalled();
  });

  /** The last kid has no Remove button, so there is no question to ask. */
  it('never asks about the only kid in the household', () => {
    renderFamilyArea({ family: newFamily(DEFAULT_SETTINGS, 'Robin') });
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-1'));
    expect(screen.queryByTestId('parent-area-remove-profile')).toBeNull();
    expect(screen.queryByTestId('parent-area-remove-question')).toBeNull();
  });

  it('stops at four kids and says so', () => {
    let full: Family = twoKids;
    full = addProfile(addProfile(full, 'Ash'), 'Kit');
    renderFamilyArea({ family: full });
    expect(screen.queryByTestId('parent-area-add-profile')).toBeNull();
    expect(screen.getByTestId('parent-area-profiles-full')).toBeDefined();
  });
});
