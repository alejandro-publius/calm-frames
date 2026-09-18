/**
 * The guards the mutation gate found nothing was watching.
 *
 * `make mutate` breaks each safety guard on purpose and expects the suite to go red. Five of
 * them did not, and every test in this file exists to kill one named survivor. The ids match
 * results/mutation.json, so a reader can go from a mutant to the test that catches it.
 *
 *   background-hides-at-once        the app going to the background hid the picture only on
 *                                   the next scheduler tick, up to 50 ms later, and every
 *                                   existing test advanced the timers before looking
 *   fail-closed-bad-segment-list    no test had a validly signed map with a segment that
 *                                   makes no sense, so skipping it rather than refusing the
 *                                   map went unnoticed
 *   red-is-the-default-reason       no test had a map with a reason this build has not seen,
 *                                   so treating it as general rather than red went unnoticed
 *   room-cannot-shorten-the-guard-band   every preset already sits above the floor, so the
 *                                   floor itself was never exercised
 *   rendition-offset-is-applied     the offset was checked at the start of each interval and
 *                                   never at the end
 *
 * The two fixtures are made by eval/fuzz_maps.py --write-fixtures, which signs them with a
 * key derived from a fixed phrase. There is no private key in this repository.
 */

import fs from 'fs';
import path from 'path';
import React from 'react';
import { Text } from 'react-native';
import { act, render, screen } from '@testing-library/react-native';

import {
  buildCoverIntervals,
  DEFAULT_GUARD_BAND_MS,
  DEFAULT_MIN_COVER_MS,
} from '../../src/calmframes/coverSchedule';
import { verifyFlashMap } from '../../src/calmframes/flashMap';
import { coverOptionsFor, PRESETS } from '../../src/calmframes/household';
import {
  MediaElementLike,
  useCoverHarness,
} from '../../src/calmframes/useCoverHarness';

const FIXTURES = path.join(__dirname, 'fixtures');

const fuzzKey = JSON.parse(
  fs.readFileSync(path.join(FIXTURES, 'fuzz_key.json'), 'utf8'),
);
const MADE_AT = Date.parse(fuzzKey.created_utc);

function readFixture(name: string): string {
  return fs.readFileSync(path.join(FIXTURES, name), 'utf8');
}

function verifyFixture(name: string) {
  return verifyFlashMap(readFixture(name), {
    publicKeyBase64: fuzzKey.public_key_base64,
    expectedSha256: fuzzKey.source_sha256,
    nowMs: MADE_AT + 1_000,
  });
}

describe('a signed map that says something impossible', () => {
  it('is refused whole, rather than having the bad segment quietly dropped', () => {
    // The signature is real, so this map gets all the way to the segment list. A reader that
    // skipped the segment instead of refusing the map would leave whatever that segment
    // described uncovered, and nothing would say so.
    const verdict = verifyFixture('signed_reversed_segment.flashmap.json');
    expect(verdict.ok).toBe(false);
    if (!verdict.ok) {
      expect(verdict.reason).toBe('unparseable');
    }
  });

  it('really is signed by the key the test holds, or the test above proves nothing', () => {
    // The negative control. If the signature did not check out, the map would be refused for
    // that instead and the segment list would never be reached.
    const document = JSON.parse(readFixture('signed_reversed_segment.flashmap.json'));
    expect(document.signature.public_key).toBe(fuzzKey.public_key_base64);
    const good = verifyFixture('signed_unknown_reason.flashmap.json');
    expect(good.ok).toBe(true);
  });
});

describe('a reason this build has never seen', () => {
  it('gets the opaque cover, not the dim one', () => {
    const verdict = verifyFixture('signed_unknown_reason.flashmap.json');
    expect(verdict.ok).toBe(true);
    if (verdict.ok) {
      expect(verdict.map.segments).toHaveLength(1);
      // WCAG's red rule keys on the red to total ratio, which dimming does not change, so
      // anything that is not the word "general" has to be treated as red.
      expect(verdict.map.segments[0].reason).toBe('red');
    }
  });
});

describe('the household floor', () => {
  it('holds even for a preset that asks for less than WCAG', () => {
    // Every preset in the table is already at or above the floor, so the floor itself has
    // never been exercised. It exists for the preset somebody adds later, and this is the
    // test that will catch that preset.
    const preset = PRESETS.wcag;
    const guard = preset.guardBandMs;
    const cover = preset.minCoverMs;
    try {
      preset.guardBandMs = 10;
      preset.minCoverMs = 10;
      const options = coverOptionsFor({
        preset: 'wcag',
        tvDiagonalIn: 55,
        seatDistanceIn: 96,
      });
      expect(options.guardBandMs).toBe(DEFAULT_GUARD_BAND_MS);
      expect(options.minCoverMs).toBe(DEFAULT_MIN_COVER_MS);
    } finally {
      preset.guardBandMs = guard;
      preset.minCoverMs = cover;
    }
  });
});

describe('the rendition start offset', () => {
  it('moves both ends of the interval, not just the start', () => {
    // Both ends shift together, so the span is unchanged and the cover comes off at the
    // right moment rather than late. Checking only the start let an interval that ended
    // 150 ms late look correct, because a longer cover still hides everything.
    const offsetMs = 150;
    const segment = { startMs: 10_000, endMs: 12_000 };
    const [interval] = buildCoverIntervals([segment], {
      guardBandMs: DEFAULT_GUARD_BAND_MS,
      renditionStartOffsetMs: offsetMs,
    });
    expect(interval.startMs).toBe(segment.startMs - offsetMs - DEFAULT_GUARD_BAND_MS);
    expect(interval.endMs).toBe(segment.endMs - offsetMs + DEFAULT_GUARD_BAND_MS);
    expect(interval.endMs - interval.startMs).toBe(
      segment.endMs - segment.startMs + 2 * DEFAULT_GUARD_BAND_MS,
    );
  });
});

/** A media element a test can drive, and a harness that can be sent to the background. */
function makeMediaElement(): MediaElementLike & { fire: (type: string) => void } {
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

const Harness = ({
  media,
  intervals,
  foreground,
}: {
  media: MediaElementLike;
  intervals: ReturnType<typeof buildCoverIntervals>;
  foreground: boolean;
}) => {
  const ref = React.useRef<MediaElementLike | null>(media);
  const state = useCoverHarness(ref, {
    mode: 'timing',
    intervals,
    tickMs: 50,
    foreground,
  });
  return <Text testID="covered">{state.covered ? 'covered' : 'clear'}</Text>;
};

describe('going to the background', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  it('hides the picture at once, without waiting for the next tick', () => {
    const media = makeMediaElement();
    const intervals = buildCoverIntervals([{ startMs: 60_000, endMs: 61_000 }]);
    const { rerender } = render(
      <Harness media={media} intervals={intervals} foreground />,
    );

    media.currentTime = 1.0;
    act(() => media.fire('playing'));
    act(() => jest.advanceTimersByTime(100));
    expect(screen.getByTestId('covered').props.children).toBe('clear');

    // No timers are advanced after this point. The scheduler re-checks every 50 ms and would
    // cover on its next run anyway, which is why every other test in the suite missed this:
    // they all advanced the clock before looking. A person pressing home wants the picture
    // gone now, not within 50 ms, and the app cannot know what is on screen at that moment.
    act(() => {
      rerender(<Harness media={media} intervals={intervals} foreground={false} />);
    });
    expect(screen.getByTestId('covered').props.children).toBe('covered');
  });
});
