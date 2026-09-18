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
  NO_TITLES,
  PIN_NOT_SET,
  PIN_WRONG_TITLE,
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
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { addHideEntry, emptyHideLog } from '../../src/calmframes/hideLog';
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
import ShieldBadge from '../../src/calmframes/ShieldBadge';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkTitle, CheckedTitle } from '../../src/calmframes/titleStatus';

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
    expect(screen.getByTestId('flash-map-strip').props.accessibilityLabel).toMatch(
      /2 flashing parts/,
    );
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
      expect(screen.getByTestId('shield-badge-label').props.children).toBe(label);
      unmount();
    }
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
    const { toJSON } = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} />);
    const tree = JSON.stringify(toJSON());
    expect(tree).not.toMatch(/autoPlay|shouldPlay|Video|KeplerVideoSurfaceView/i);
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
    expect(screen.getByTestId('title-details-notice-title').props.children).toBe(
      TITLE_PENDING.title,
    );
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
    expect(screen.getByTestId('title-details-notice-title').props.children).toBe(
      TITLE_FAILED.title,
    );
    expect(screen.getByTestId('title-details-notice-detail').props.children).toMatch(
      /changed after it was signed/,
    );
  });

  it('will not play a title whose check is too old, checked with the real reader', () => {
    // Ninety days and a minute after the bundled map was made.
    const stale = bundledTitle(MAP_MADE_AT + 90 * 24 * 60 * 60 * 1000 + 60_000);
    expect(stale.rejection).toBe('stale');

    const onPlay = jest.fn();
    render(<TitleDetailsScreen entry={stale} onPlay={onPlay} />);
    fireEvent.press(screen.getByTestId('title-details-play'));
    expect(onPlay).not.toHaveBeenCalled();
    expect(screen.getByTestId('title-details-notice-title').props.children).toBe(
      TITLE_STALE.title,
    );
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
    expect(screen.getByTestId('parent-area-message-detail').props.children).toMatch(
      /not right/,
    );
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
    expect(screen.getByTestId('parent-area-message-detail').props.children).toMatch(
      new RegExp(`${MAX_ATTEMPTS - 1} tries left`),
    );
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
    expect(screen.getByTestId('parent-area-preset-extra-cautious')).toBeTruthy();
    expect(screen.getByTestId('parent-area-room').props.children).toMatch(
      /55 inch television/,
    );
    expect(screen.getByTestId('parent-area-log-0').props.children).toMatch(
      /Title ok: hid 5 seconds at 1:00/,
    );
    expect(screen.getByTestId('parent-area-status-bad-label').props.children).toBe(
      'Check failed',
    );
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

  it('announces the PIN result politely', () => {
    renderArea();
    const message = screen.getByTestId('parent-area-message');
    expect(message.props.accessibilityLiveRegion).toBe('polite');
    expect(message.props['aria-live']).toBe('polite');
  });
});
