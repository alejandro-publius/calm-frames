/**
 * The cards: what they say, when they say it, and that VoiceView hears them.
 */

import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { AccessibilityInfo } from 'react-native';
import {
  announceForAccessibility,
  resetAnnouncements,
} from '../../src/calmframes/announce';
import CalmCard from '../../src/calmframes/CalmCard';
import {
  AFTER_CARD_MS,
  Card,
  cardAt,
  cardChanged,
  COUNTDOWN_LEAD_MS,
  NO_CARD,
  SKIP_MARGIN_MS,
} from '../../src/calmframes/cards';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import { MINIMUM_TEXT_SIZE } from '../../src/calmframes/calmStyles';

const intervals = buildCoverIntervals(
  [
    { startMs: 20_000, endMs: 24_000 },
    { startMs: 60_000, endMs: 60_800, reason: 'red' },
  ],
  { guardBandMs: 500, durationMs: 120_000 },
);
// Guard bands make these 19500 to 24500 and 59500 to 61300.

describe('cardAt', () => {
  it('shows nothing when nothing is near', () => {
    expect(cardAt(intervals, 5_000)).toEqual(NO_CARD);
  });

  it('shows the countdown five seconds before the cover', () => {
    const early = cardAt(intervals, 19_500 - COUNTDOWN_LEAD_MS - 1);
    expect(early.kind).toBe('none');

    const card = cardAt(intervals, 19_500 - COUNTDOWN_LEAD_MS);
    expect(card.kind).toBe('countdown');
    expect(card.title).toBe('Flashing part coming up');
    expect(card.secondsLeft).toBe(5);
    expect(card.skipToMs).toBe(24_500 + SKIP_MARGIN_MS);
  });

  it('counts down in whole seconds and says one second in the singular', () => {
    expect(cardAt(intervals, 19_500 - 3_000).secondsLeft).toBe(3);
    const oneLeft = cardAt(intervals, 19_500 - 900);
    expect(oneLeft.secondsLeft).toBe(1);
    expect(oneLeft.detail).toMatch(/In 1 second\./);
    expect(oneLeft.detail).not.toMatch(/1 seconds/);
  });

  it('shows the covering card while the picture is hidden', () => {
    const card = cardAt(intervals, 22_000);
    expect(card.kind).toBe('covering');
    expect(card.announcement).toBe(
      'Hiding a flashing part. Sound and captions keep playing.',
    );
  });

  it('says what was hidden once the part is over', () => {
    const card = cardAt(intervals, 24_600);
    expect(card.kind).toBe('after');
    // The interval is 19500 to 24500, which is five seconds of cover.
    expect(card.title).toBe('Hid 5 seconds of flashing');
    expect(card.detail).toBe('Sound and captions kept playing.');
  });

  it('stops saying it after the card has had its time', () => {
    expect(cardAt(intervals, 24_500 + AFTER_CARD_MS - 1).kind).toBe('after');
    expect(cardAt(intervals, 24_500 + AFTER_CARD_MS).kind).toBe('none');
  });

  it('rounds a short hide to one second rather than zero', () => {
    const short = buildCoverIntervals([{ startMs: 1_000, endMs: 1_200 }], {
      guardBandMs: 0,
      minCoverMs: 400,
    });
    expect(cardAt(short, 1_500).title).toBe('Hid 1 second of flashing');
  });

  it('prefers the next part over the one that just ended', () => {
    const close = buildCoverIntervals(
      [
        { startMs: 10_000, endMs: 11_000 },
        { startMs: 13_000, endMs: 14_000 },
      ],
      { guardBandMs: 0 },
    );
    // 11200 is inside the after window of the first and inside the countdown
    // window of the second.
    const card = cardAt(close, 11_200);
    expect(card.kind).toBe('countdown');
  });

  it('says the title is not checked yet when the map did not verify', () => {
    for (const rejection of ['missing', 'stale', 'unsigned', 'unparseable', 'wrong-file'] as const) {
      const card = cardAt(intervals, 22_000, { rejection });
      expect(card.kind).toBe('unverified');
      expect(card.title).toBe('Not checked yet');
      expect(card.detail).toMatch(/picture stays hidden/);
    }
  });

  it('has no dashes and none of the banned words anywhere', () => {
    const cards: Card[] = [
      cardAt(intervals, 15_000),
      cardAt(intervals, 22_000),
      cardAt(intervals, 24_600),
      cardAt(intervals, 0, { rejection: 'missing' }),
    ];
    for (const card of cards) {
      const text = `${card.title} ${card.detail ?? ''} ${card.announcement}`;
      expect(text).not.toMatch(/[–—]/);
      expect(text.toLowerCase()).not.toMatch(/genuinely|honestly|straightforward/);
    }
  });
});

describe('cardChanged', () => {
  it('is true for a new kind and for a new interval, false for a tick', () => {
    const first = cardAt(intervals, 19_500 - 5_000);
    const laterSameCard = cardAt(intervals, 19_500 - 3_000);
    expect(cardChanged(first, laterSameCard)).toBe(false);
    expect(cardChanged(first, cardAt(intervals, 22_000))).toBe(true);
    expect(
      cardChanged(cardAt(intervals, 22_000), cardAt(intervals, 60_000)),
    ).toBe(true);
  });
});

describe('announceForAccessibility', () => {
  beforeEach(() => {
    resetAnnouncements();
    jest.restoreAllMocks();
  });

  it('queues the announcement rather than interrupting one', () => {
    const withOptions = jest.fn();
    (AccessibilityInfo as unknown as Record<string, unknown>).announceForAccessibilityWithOptions =
      withOptions;

    expect(announceForAccessibility('Flashing part coming up')).toBe(true);
    expect(withOptions).toHaveBeenCalledWith('Flashing part coming up', {
      queue: true,
    });
  });

  it('does not repeat the same words twice in a row', () => {
    const withOptions = jest.fn();
    (AccessibilityInfo as unknown as Record<string, unknown>).announceForAccessibilityWithOptions =
      withOptions;

    announceForAccessibility('Hiding a flashing part');
    announceForAccessibility('Hiding a flashing part');
    expect(withOptions).toHaveBeenCalledTimes(1);
    announceForAccessibility('Hiding a flashing part', { force: true });
    expect(withOptions).toHaveBeenCalledTimes(2);
  });

  it('falls back to the interrupting call when the queued one is missing', () => {
    const plain = jest.fn();
    (AccessibilityInfo as unknown as Record<string, unknown>).announceForAccessibilityWithOptions =
      undefined;
    (AccessibilityInfo as unknown as Record<string, unknown>).announceForAccessibility =
      plain;

    expect(announceForAccessibility('Not checked yet')).toBe(true);
    expect(plain).toHaveBeenCalledWith('Not checked yet');
  });

  it('never throws when the runtime has no announcement api at all', () => {
    (AccessibilityInfo as unknown as Record<string, unknown>).announceForAccessibilityWithOptions =
      undefined;
    (AccessibilityInfo as unknown as Record<string, unknown>).announceForAccessibility =
      undefined;
    expect(announceForAccessibility('anything')).toBe(false);
    expect(announceForAccessibility('   ')).toBe(false);
  });
});

describe('CalmCard', () => {
  it('draws nothing when there is no card', () => {
    const { queryByTestId } = render(<CalmCard card={NO_CARD} />);
    expect(queryByTestId('calm-card')).toBeNull();
  });

  it('marks the card as a polite live region and labels it with what is said', () => {
    const card = cardAt(intervals, 22_000);
    const { getByTestId } = render(<CalmCard card={card} />);
    const root = getByTestId('calm-card');
    expect(root.props.accessibilityLiveRegion).toBe('polite');
    expect(root.props['aria-live']).toBe('polite');
    expect(root.props.accessibilityLabel).toBe(card.announcement);
  });

  it('gives the Skip button D-pad focus on a countdown and reports the target', () => {
    const card = cardAt(intervals, 19_500 - 5_000);
    const onSkip = jest.fn();
    const { getByTestId } = render(<CalmCard card={card} onSkip={onSkip} />);
    const skip = getByTestId('calm-card-skip');
    expect(skip.props.hasTVPreferredFocus).toBe(true);
    fireEvent.press(skip);
    expect(onSkip).toHaveBeenCalledWith(24_500 + SKIP_MARGIN_MS);
  });

  it('shows a visible focus ring only while focused', () => {
    const card = cardAt(intervals, 19_500 - 5_000);
    const { getByTestId } = render(<CalmCard card={card} />);
    const skip = getByTestId('calm-card-skip');
    const flatten = (style: unknown) =>
      Array.isArray(style)
        ? Object.assign({}, ...style.filter(Boolean))
        : (style as Record<string, unknown>);

    const unfocused = flatten(skip.props.style);
    fireEvent(skip, 'focus');
    const focused = flatten(getByTestId('calm-card-skip').props.style);
    expect(focused.borderColor).not.toBe(unfocused.borderColor);
    expect(focused.backgroundColor).not.toBe(unfocused.backgroundColor);
  });

  it('has no Skip button on a card that is not a countdown', () => {
    const { queryByTestId } = render(<CalmCard card={cardAt(intervals, 22_000)} />);
    expect(queryByTestId('calm-card-skip')).toBeNull();
  });

  it('draws every line at a ten foot size', () => {
    const { getByTestId } = render(
      <CalmCard card={cardAt(intervals, 19_500 - 5_000)} />,
    );
    for (const id of ['calm-card-title', 'calm-card-detail']) {
      const style = getByTestId(id).props.style;
      const flat = Array.isArray(style)
        ? Object.assign({}, ...style.filter(Boolean))
        : style;
      expect(flat.fontSize).toBeGreaterThanOrEqual(MINIMUM_TEXT_SIZE);
    }
  });
});
