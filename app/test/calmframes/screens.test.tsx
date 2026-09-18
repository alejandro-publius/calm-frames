/**
 * Kid mode's shelf, the details page and the parent area.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { MINIMUM_TEXT_SIZE } from '../../src/calmframes/calmStyles';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import FlashMapStrip, {
  describeStrip,
  MINIMUM_MARK_FRACTION,
  stripMarks,
} from '../../src/calmframes/FlashMapStrip';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { addHideEntry, emptyHideLog } from '../../src/calmframes/hideLog';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import ShieldBadge from '../../src/calmframes/ShieldBadge';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CheckedTitle } from '../../src/calmframes/titleStatus';

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

  it('says so plainly when nothing is ready', () => {
    render(<KidHomeScreen titles={[titles[1]]} onOpen={jest.fn()} />);
    expect(screen.getByTestId('kid-home-subtitle').props.children).toMatch(
      /Nothing is ready yet/,
    );
  });

  it('has no video and nothing that plays by itself', () => {
    const { toJSON } = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} />);
    const tree = JSON.stringify(toJSON());
    expect(tree).not.toMatch(/autoPlay|shouldPlay|Video|KeplerVideoSurfaceView/i);
    // An Image is a still. That is the only picture on this screen.
    expect(screen.getByTestId('kid-home-poster-image-ok')).toBeTruthy();
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

  it('will not play a title that is not checked', () => {
    const onPlay = jest.fn();
    render(
      <TitleDetailsScreen
        entry={makeTitle('waiting', 'pending', {
          reason: 'This title is not checked yet, so the picture stays hidden.',
        })}
        onPlay={onPlay}
      />,
    );
    const play = screen.getByTestId('title-details-play');
    expect(play.props.accessibilityState).toEqual({ disabled: true });
    fireEvent.press(play);
    expect(onPlay).not.toHaveBeenCalled();
    expect(screen.getByTestId('title-details-reason')).toBeTruthy();
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
    render(
      <ParentAreaScreen
        gate={gate}
        onGateChange={jest.fn()}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={onSettingsChange}
        log={log}
        titles={titles}
        nowMs={() => 0}
        {...overrides}
      />,
    );
    return { onSettingsChange };
  }

  const enter = (pin: string) => {
    for (const digit of pin) {
      fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
    }
  };

  it('shows only the keypad until the PIN is right', () => {
    renderArea();
    expect(screen.getByTestId('parent-area')).toBeTruthy();
    expect(screen.queryByTestId('parent-area-open')).toBeNull();
    expect(screen.queryByTestId('parent-area-preset-wcag')).toBeNull();

    enter('0000');
    expect(screen.queryByTestId('parent-area-open')).toBeNull();
    expect(screen.getByTestId('parent-area-message').props.children).toMatch(
      /not right/,
    );
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
