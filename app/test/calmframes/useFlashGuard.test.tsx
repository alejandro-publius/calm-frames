/**
 * The whole guard, driven through a fake player.
 *
 * This is the test that says the pieces work together: the map is checked, the
 * picture starts hidden and stays hidden until the check passes, the cover
 * follows the schedule, the cards appear in order, VoiceView is told, and the
 * Skip button moves the playhead through the one safe seek function.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';
import { AccessibilityInfo, Text } from 'react-native';
import CalmCard from '../../src/calmframes/CalmCard';
import CoverLayer from '../../src/calmframes/CoverLayer';
import { resetAnnouncements } from '../../src/calmframes/announce';
import { DEFAULT_SETTINGS, HouseholdSettings } from '../../src/calmframes/household';
import { HideLogEntry } from '../../src/calmframes/hideLog';
import { MediaElementLike } from '../../src/calmframes/useCoverHarness';
import { useFlashGuard } from '../../src/calmframes/useFlashGuard';

const burstsMapText = fs.readFileSync(
  path.join(__dirname, 'fixtures', 'bursts.flashmap.json'),
  'utf8',
);
const BURSTS = JSON.parse(burstsMapText);
const KEY = '533gF/bCDXyQppRnqiiT41+JwyyUYRN8P4YVZnCbKLQ=';
const MADE_AT = Date.parse(BURSTS.created_utc);
// Segments are 4367 to 7767, 14367 to 17767 and 24367 to 27767.
// With the default 500 ms guard band the first interval is 3867 to 8267.

function makeMediaElement(): MediaElementLike & {
  fire: (type: string) => void;
} {
  const listeners: Record<string, Array<() => void>> = {};
  return {
    currentTime: 0,
    playbackRate: 1,
    addEventListener(type: string, listener: () => void) {
      listeners[type] = [...(listeners[type] ?? []), listener];
    },
    removeEventListener(type: string, listener: () => void) {
      listeners[type] = (listeners[type] ?? []).filter((one) => one !== listener);
    },
    fire(type: string) {
      for (const listener of listeners[type] ?? []) {
        listener();
      }
    },
  };
}

interface GuardedProps {
  renditionStartOffsetMs?: number;
  media: MediaElementLike;
  mapText?: string | null;
  mapUrl?: string;
  fetchText?: (url: string) => Promise<string | null>;
  settings?: HouseholdSettings;
  nowMs?: number;
  onHide?: (entry: HideLogEntry) => void;
}

const Guarded = ({
  media,
  mapText = burstsMapText,
  mapUrl,
  fetchText,
  settings = DEFAULT_SETTINGS,
  nowMs = MADE_AT + 1000,
  onHide,
  renditionStartOffsetMs,
}: GuardedProps) => {
  const ref = React.useRef<MediaElementLike | null>(media);
  const guard = useFlashGuard({
    mediaRef: ref,
    mapTexts: mapUrl ? undefined : { wcag: mapText },
    mapUrls: mapUrl ? { wcag: mapUrl } : undefined,
    fetchText,
    expectedSha256: BURSTS.source.sha256,
    publicKeyBase64: KEY,
    settings,
    nowMs: () => nowMs,
    durationMs: 30_000,
    titleId: 'bursts',
    titleName: 'Test pattern',
    onHide,
    renditionStartOffsetMs,
  });
  return (
    <>
      <Text testID="status">{guard.status}</Text>
      <Text testID="covered">{guard.covered ? 'covered' : 'clear'}</Text>
      <Text testID="card-kind">{guard.card.kind}</Text>
      <Text testID="hidden">{String(guard.hiddenMs)}</Text>
      <CoverLayer visible={guard.covered} />
      <CalmCard card={guard.card} onSkip={guard.skipTo} />
    </>
  );
};

const read = (id: string) => String(screen.getByTestId(id).props.children);

/** Let the map check, which is asynchronous, finish. */
async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe('useFlashGuard', () => {
  let announce: jest.Mock;

  beforeEach(() => {
    jest.useFakeTimers();
    resetAnnouncements();
    announce = jest.fn();
    (
      AccessibilityInfo as unknown as Record<string, unknown>
    ).announceForAccessibilityWithOptions = announce;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('starts with the picture hidden, before any map has been checked', async () => {
    const media = makeMediaElement();
    // A map that is still being fetched. Nothing about the title is known yet,
    // so the picture stays hidden.
    render(
      <Guarded
        media={media}
        mapUrl="https://example.invalid/map.json"
        fetchText={() => new Promise<string | null>(() => {})}
      />,
    );
    await settle();
    expect(read('status')).toBe('loading');
    expect(read('covered')).toBe('covered');
    expect(screen.queryByTestId('calm-frames-cover')).toBeTruthy();
    // Still checking is not the same as refused, so it gets its own card
    // rather than the "Not checked yet" one a failed map gets.
    expect(read('card-kind')).toBe('checking');
    expect(screen.getByTestId('calm-card-title').props.children).toBe(
      'Getting your story ready',
    );
    expect(screen.queryByTestId('calm-card-skip')).toBeNull();
  });

  it('shows the checking card for a replacement map, not the last refusal', async () => {
    const media = makeMediaElement();
    const { rerender } = render(<Guarded media={media} mapText={null} />);
    await settle();
    expect(screen.getByTestId('calm-card-title').props.children).toBe(
      'This title is unavailable',
    );

    // A new map arrives and is still being fetched. The refusal belonged to
    // the old one, so it must not be what the card says now.
    rerender(
      <Guarded
        media={media}
        mapUrl="https://example.invalid/replacement.json"
        fetchText={() => new Promise<string | null>(() => {})}
      />,
    );
    await settle();
    expect(read('status')).toBe('loading');
    expect(read('covered')).toBe('covered');
    expect(read('card-kind')).toBe('checking');
    expect(screen.getByTestId('calm-card-title').props.children).toBe(
      'Getting your story ready',
    );
  });

  it('keeps the picture hidden when the map cannot be fetched', async () => {
    const media = makeMediaElement();
    render(
      <Guarded
        media={media}
        mapUrl="https://example.invalid/map.json"
        fetchText={async () => null}
      />,
    );
    await settle();
    expect(read('status')).toBe('blocked');
    expect(read('covered')).toBe('covered');
  });

  it('never shows an unchecked picture after playing confirms with a missing map', async () => {
    const media = makeMediaElement();
    render(
      <Guarded
        media={media}
        mapUrl="https://example.invalid/map.json"
        fetchText={async () => null}
      />,
    );
    await settle();
    await act(async () => {
      media.fire('playing');
      jest.advanceTimersByTime(100);
    });
    // Assert the picture itself, not just the rejection category. Treating a
    // missing map as an empty verified one would otherwise leave it exposed.
    expect(read('covered')).toBe('covered');
    expect(read('status')).toBe('blocked');
  });

  it('uncovers only once a signed map has verified', async () => {
    const media = makeMediaElement();
    render(<Guarded media={media} />);
    await settle();
    expect(read('status')).toBe('verified');

    media.currentTime = 0;
    await act(async () => {
      media.fire('playing');
      jest.advanceTimersByTime(100);
    });
    expect(read('covered')).toBe('clear');
  });

  it('keeps the picture hidden and says why when the map does not verify', async () => {
    const media = makeMediaElement();
    render(<Guarded media={media} mapText={null} />);
    await settle();
    expect(read('status')).toBe('blocked');
    expect(read('covered')).toBe('covered');
    expect(read('card-kind')).toBe('unverified');
    expect(screen.getByTestId('calm-card-title').props.children).toBe(
      'This title is unavailable',
    );
  });

  it('keeps the picture hidden when the map has been tampered with', async () => {
    const media = makeMediaElement();
    const tampered = burstsMapText.replace('"hidden_ms": 10200', '"hidden_ms": 0');
    expect(tampered).not.toBe(burstsMapText);
    render(<Guarded media={media} mapText={tampered} />);
    await settle();
    expect(read('status')).toBe('blocked');
    expect(read('covered')).toBe('covered');
  });

  it('shows the countdown, then the cover, then what was hidden', async () => {
    const media = makeMediaElement();
    const hidden: HideLogEntry[] = [];
    render(<Guarded media={media} onHide={(entry) => hidden.push(entry)} />);
    await settle();

    // The first interval starts at 3867, so at the top of the title the
    // countdown is already up.
    media.currentTime = 0;
    await act(async () => {
      media.fire('playing');
      jest.advanceTimersByTime(100);
    });
    expect(read('card-kind')).toBe('countdown');
    expect(read('covered')).toBe('clear');

    // Still counting down, closer in.
    media.currentTime = 1.5;
    await act(async () => {
      media.fire('timeupdate');
      jest.advanceTimersByTime(100);
    });
    expect(read('card-kind')).toBe('countdown');
    expect(read('covered')).toBe('clear');
    expect(announce).toHaveBeenCalledWith(
      expect.stringContaining('Flashing part coming up'),
      { queue: true },
    );

    // Inside the interval.
    media.currentTime = 5;
    await act(async () => {
      media.fire('timeupdate');
      jest.advanceTimersByTime(100);
    });
    expect(read('covered')).toBe('covered');
    expect(read('card-kind')).toBe('covering');
    expect(announce).toHaveBeenCalledWith(
      'Hiding a flashing part. Sound and captions keep playing.',
      { queue: true },
    );

    // Out the other side.
    media.currentTime = 8.5;
    await act(async () => {
      media.fire('timeupdate');
      jest.advanceTimersByTime(100);
    });
    expect(read('covered')).toBe('clear');
    expect(read('card-kind')).toBe('after');
    expect(screen.getByTestId('calm-card-title').props.children).toMatch(
      /^Hid \d+ seconds of flashing$/,
    );

    // And the parent area has a line for it.
    expect(hidden).toHaveLength(1);
    expect(hidden[0]).toMatchObject({
      titleId: 'bursts',
      titleName: 'Test pattern',
      positionMs: 3_867,
      cause: 'schedule',
    });
    expect(read('hidden')).toBe('4400');
  });

  it('skips past the flashing part through the one safe seek function', async () => {
    const media = makeMediaElement();
    render(<Guarded media={media} />);
    await settle();

    media.currentTime = 1.5;
    await act(async () => {
      media.fire('playing');
      jest.advanceTimersByTime(100);
    });
    expect(read('card-kind')).toBe('countdown');

    await act(async () => {
      fireEvent.press(screen.getByTestId('calm-card-skip'));
    });
    // 8267 is the end of the first interval, plus the 100 ms margin.
    expect(media.currentTime).toBeCloseTo(8.367, 3);
  });

  it('keeps the picture hidden when the room is stricter than the check', async () => {
    const media = makeMediaElement();
    // A big television very close up: the ten degree field covers a much
    // smaller share of the screen than the window the map measured.
    render(
      <Guarded
        media={media}
        settings={{ preset: 'wcag', tvDiagonalIn: 85, seatDistanceIn: 48 }}
      />,
    );
    await settle();
    expect(read('status')).toBe('blocked');
    expect(read('covered')).toBe('covered');
    expect(screen.getByTestId('calm-card-detail').props.children).toMatch(
      /current viewing settings/,
    );
  });

  it('keeps the picture hidden when the map is older than the limit', async () => {
    const media = makeMediaElement();
    render(
      <Guarded media={media} nowMs={MADE_AT + 400 * 24 * 60 * 60 * 1000} />,
    );
    await settle();
    expect(read('status')).toBe('blocked');
    expect(read('covered')).toBe('covered');
  });

  it('plays a title whose rendition sits a little off the source', async () => {
    const media = makeMediaElement();
    render(<Guarded media={media} renditionStartOffsetMs={67} />);
    await settle();
    expect(read('status')).toBe('verified');
  });

  it('keeps the picture hidden when the rendition is further off than verify allows', async () => {
    // Larger than MAX_RENDITION_START_OFFSET_MS, so the map and the file
    // disagree about where the pictures are. There is no safe schedule to
    // build from that, and a wrong one would put covers in the wrong places.
    const media = makeMediaElement();
    render(<Guarded media={media} renditionStartOffsetMs={5_000} />);
    await settle();
    expect(read('status')).toBe('blocked');
    expect(read('covered')).toBe('covered');
  });
});
