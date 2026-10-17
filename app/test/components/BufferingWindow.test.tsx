import LottieView from '@amazon-devices/lottie-react-native';
import { describe } from '@jest/globals';
import { act, render } from '@testing-library/react-native';
import React from 'react';
import { AccessibilityInfo, Animated, StyleSheet, Text, View } from 'react-native';
import * as announce from '../../src/calmframes/announce';
import BufferingWindow, {
  BUFFERING_Z_INDEX,
  isOpaqueColor,
  LOADING_TEXT,
  MIN_VISIBLE_MS,
  REVEAL_DELAY_MS,
  styles,
} from '../../src/components/BufferingWindow';
import ErrorView, { styles as errorStyles } from '../../src/components/ErrorView';
import { COLORS } from '../../src/styles/Colors';

type Rendered = ReturnType<typeof render>;

function status(view: Rendered) {
  return view.queryByTestId('buffering-status');
}

function backdrop(view: Rendered): string | undefined {
  const node = view.queryByTestId('buffering-view');
  return node ? StyleSheet.flatten(node.props.style).backgroundColor : undefined;
}

function words(view: Rendered): string[] {
  return view.UNSAFE_queryAllByType(Text).map((node) => String(node.props.children));
}

function advance(ms: number) {
  act(() => jest.advanceTimersByTime(ms));
}

beforeEach(() => {
  jest.useFakeTimers();
  announce.resetAnnouncements();
});
afterEach(() => {
  jest.clearAllTimers();
  jest.useRealTimers();
  jest.restoreAllMocks();
});

// The sample's snapshot, under its original name: the first frame of a
// loading screen is exactly what it was.
describe('BufferingWindow Test Cases', () => {
  it('renders correctly', () => {
    const tree = render(<BufferingWindow />);
    expect(tree).toMatchSnapshot();
  });
});

describe('initial loading, on a screen with nothing to show yet', () => {

  it('shows the black backdrop at once and a status only once the wait has lasted', () => {
    const spoken = jest.spyOn(announce, 'announceForAccessibility');
    const view = render(<BufferingWindow />);
    expect(backdrop(view)).toBe(COLORS.BLACK);
    expect(status(view)).toBeNull();
    advance(REVEAL_DELAY_MS - 1);
    expect(status(view)).toBeNull();
    expect(spoken).not.toHaveBeenCalled();
    advance(1);
    const plate = status(view)!;
    expect(words(view)).toEqual([LOADING_TEXT]);
    expect(plate.props.accessibilityLiveRegion).toBe('none');
    expect(plate.props['aria-live']).toBe('off');
    expect(plate.props.accessibilityLabel).toBe(LOADING_TEXT);
    expect(spoken).toHaveBeenCalledTimes(1);
    expect(spoken).toHaveBeenCalledWith(LOADING_TEXT, { force: true, queue: false });
    const container = StyleSheet.flatten(view.getByTestId('buffering-view').props.style);
    expect(container.alignItems).toBe('center');
    expect(container.justifyContent).toBe('center');
  });

  it('a screen that loads quickly never shows a status', () => {
    const view = render(<BufferingWindow />);
    advance(REVEAL_DELAY_MS - 100);
    expect(status(view)).toBeNull();
    view.unmount();
  });

  it('keeps its callers\' test ids', () => {
    const view = render(<BufferingWindow testID="buffering-view-settingsScreen-loading" />);
    expect(view.getByTestId('buffering-view-settingsScreen-loading')).toBeTruthy();
  });
});

describe('legacy translucent callers', () => {
  // Preserve compatibility for conditional translucent callers. The player
  // now uses the persistent overlay presentation tested below.
  const today = () => <BufferingWindow backgroundColor={COLORS.SEMI_TRANSPARENT} />;

  it('a wait shorter than the reveal delay draws nothing: no dimming, no status', () => {
    const view = render(today());
    expect(view.toJSON()).toBeNull();
    advance(REVEAL_DELAY_MS - 1);
    expect(view.toJSON()).toBeNull();
    view.unmount();
  });

  it('a long wait dims and labels the picture only after the reveal delay', () => {
    const view = render(today());
    advance(REVEAL_DELAY_MS);
    expect(backdrop(view)).toBe(COLORS.SEMI_TRANSPARENT);
    expect(words(view)).toEqual([LOADING_TEXT]);
  });

  it('holding a seek key cannot dim and undim the picture', () => {
    let dimmedFrames = 0;
    for (let seek = 0; seek < 20; seek += 1) {
      const view = render(today());
      for (let step = 0; step < 15; step += 1) {
        advance(10);
        if (backdrop(view) !== undefined) dimmedFrames += 1;
      }
      view.unmount();
      advance(50);
    }
    expect(dimmedFrames).toBe(0);
  });
});

describe('overlay presentation, for a player that keeps the window mounted', () => {
  const overlay = (visible: boolean, statusText?: string | null) => (
    <BufferingWindow presentation="overlay" visible={visible} statusText={statusText} />
  );

  it('never draws a backdrop, so the scene behind stays as it was', () => {
    const view = render(overlay(true));
    expect(view.toJSON()).toBeNull();
    advance(REVEAL_DELAY_MS);
    const container = view.getByTestId('buffering-view');
    const style = StyleSheet.flatten(container.props.style);
    expect(style.backgroundColor).toBeUndefined();
    expect(style.opacity).toBeUndefined();
    expect(container.props.pointerEvents).toBe('none');
    expect(words(view)).toEqual([LOADING_TEXT]);
    // The plate is the only painted surface, in a fixed place in the middle.
    const plate = StyleSheet.flatten(status(view)!.props.style);
    expect(plate.backgroundColor).toBeDefined();
    expect(plate.position).toBeUndefined();
    expect(style.alignItems).toBe('center');
    expect(style.justifyContent).toBe('center');
  });

  it('a status that appears stays long enough not to blink, and a resumed wait keeps it without a gap', () => {
    const view = render(overlay(true));
    advance(REVEAL_DELAY_MS);
    expect(status(view)).not.toBeNull();
    advance(50);
    view.rerender(overlay(false));
    advance(MIN_VISIBLE_MS - 51);
    expect(status(view)).not.toBeNull();
    view.rerender(overlay(true));
    advance(400);
    expect(status(view)).not.toBeNull();
    view.rerender(overlay(false));
    advance(0);
    expect(status(view)).toBeNull();
  });

  it('speaks once for each separate episode without a second live-region path', () => {
    const speak = jest.spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions').mockClear();
    const view = render(overlay(true));
    advance(REVEAL_DELAY_MS);
    expect(status(view)!.props.accessibilityLiveRegion).toBe('none');
    advance(2000);
    expect(speak).toHaveBeenCalledTimes(1);
    view.rerender(overlay(false)); advance(MIN_VISIBLE_MS);
    view.rerender(overlay(true)); advance(REVEAL_DELAY_MS);
    expect(speak).toHaveBeenCalledTimes(2);
    expect(speak).toHaveBeenLastCalledWith(LOADING_TEXT, { queue: false });
  });

  it('when playback recovers, it leaves no trace', () => {
    const view = render(overlay(true));
    advance(REVEAL_DELAY_MS + 2_000);
    view.rerender(overlay(false));
    advance(MIN_VISIBLE_MS);
    expect(view.toJSON()).toBeNull();
  });

  it('with nothing to say, it shows nothing at all', () => {
    const view = render(overlay(true, null));
    advance(REVEAL_DELAY_MS * 3);
    expect(view.toJSON()).toBeNull();
  });

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])(
    'seed %i: rapid waiting and playing changes the status at most twice in any second',
    (seed) => {
      // Park and Miller's minimal standard generator, so a failure names its seed.
      let value = seed;
      const random = () => {
        value = (value * 16_807) % 2_147_483_647;
        return value / 2_147_483_647;
      };
      const view = render(overlay(false));
      const shown: boolean[] = [];
      const waitStarts: number[] = [];
      let visible = false;
      let nextFlipAt = 0;
      let flips = 0;
      for (let tick = 0; tick < 1_000; tick += 1) {
        const atMs = tick * 10;
        if (atMs >= nextFlipAt) {
          visible = !visible;
          flips += 1;
          if (visible) waitStarts.push(atMs);
          view.rerender(overlay(visible));
          // The first wait is long enough to show the status; the rest are random.
          nextFlipAt = flips === 1
            ? atMs + 1_200
            : atMs + 10 + Math.floor(random() * (random() < 0.5 ? 200 : 1_600));
        }
        advance(10);
        shown.push(status(view) !== null);
      }
      const changes: number[] = shown.map((now, index) => (index > 0 && now !== shown[index - 1] ? 1 : 0));
      for (let start = 0; start < changes.length; start += 1) {
        const inWindow = changes.slice(start, start + 100).reduce((a, b) => a + b, 0);
        expect(inWindow).toBeLessThanOrEqual(2);
      }
      // Every appearance follows a wait that had already lasted the reveal delay.
      shown.forEach((now, index) => {
        if (now && (index === 0 || !shown[index - 1])) {
          const appearedAt = (index + 1) * 10;
          const began = Math.max(...waitStarts.filter((at) => at < appearedAt));
          expect(appearedAt - began).toBeGreaterThanOrEqual(REVEAL_DELAY_MS);
        }
      });
      expect(shown.some(Boolean)).toBe(true);
      expect(shown.every(Boolean)).toBe(false);
    },
  );
});

describe('errors stay visible and usable', () => {
  it('sits below the error screen and takes no focus or presses', () => {
    const view = render(
      <View>
        <BufferingWindow presentation="overlay" />
        <ErrorView navigateBack={jest.fn()} />
      </View>,
    );
    advance(REVEAL_DELAY_MS);
    expect(status(view)).not.toBeNull();
    const errorZ = StyleSheet.flatten(errorStyles.mainContainer).zIndex as number;
    expect(BUFFERING_Z_INDEX).toBeLessThan(errorZ);
    expect(StyleSheet.flatten(styles.overlay).zIndex).toBe(BUFFERING_Z_INDEX);
    expect(StyleSheet.flatten(styles.container).zIndex).toBe(BUFFERING_Z_INDEX);
    const inside = view.getByTestId('buffering-view');
    expect(inside.props.pointerEvents).toBe('none');
    const focusable = [inside, ...inside.findAll(() => true)].filter(
      (node) =>
        node.props.focusable ||
        node.props.accessibilityRole === 'button' ||
        node.props.hasTVPreferredFocus,
    );
    expect(focusable).toHaveLength(0);
    expect(view.getByTestId('player-error-back').props.hasTVPreferredFocus).toBe(true);
    expect(view.getByText('Playback stopped')).toBeTruthy();
  });
});

describe('motion and words', () => {
  it.each([false, true])('nothing moves in any state, with reduced motion %s', (reduced) => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(reduced);
    const views = [
      render(<BufferingWindow />),
      render(<BufferingWindow backgroundColor={COLORS.SEMI_TRANSPARENT} />),
      render(<BufferingWindow presentation="overlay" />),
    ];
    for (const moment of [0, REVEAL_DELAY_MS, MIN_VISIBLE_MS]) {
      advance(moment);
      for (const view of views) {
        expect(view.UNSAFE_queryAllByType(LottieView)).toHaveLength(0);
        expect(view.UNSAFE_queryAllByType(Animated.View)).toHaveLength(0);
      }
    }
  });

  it('the only words are the short factual status', () => {
    expect(LOADING_TEXT).toBe('Loading');
    const views = [
      render(<BufferingWindow />),
      render(<BufferingWindow backgroundColor={COLORS.SEMI_TRANSPARENT} />),
      render(<BufferingWindow presentation="overlay" />),
    ];
    advance(REVEAL_DELAY_MS);
    for (const view of views) {
      expect(words(view)).toEqual(['Loading']);
    }
  });
});

describe('isOpaqueColor', () => {
  it.each([
    ['#000000', true], ['#000', true], ['black', true], ['rgb(0, 0, 0)', true],
    ['rgba(0, 0, 0, 1)', true], ['rgba(0, 0, 0)', true], ['#000f', true], ['#000000ff', true],
    [COLORS.SEMI_TRANSPARENT, false], ['rgba(0,0,0,0.4)', false], ['#00000066', false],
    ['#0008', false], ['transparent', false], ['hsla(0, 0%, 0%, 40%)', false],
  ])('%s is opaque: %s', (color, opaque) => {
    expect(isOpaqueColor(color)).toBe(opaque);
  });
});
