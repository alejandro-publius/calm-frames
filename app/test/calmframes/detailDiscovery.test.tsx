import '@testing-library/jest-native/extend-expect';
import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { ScrollView } from 'react-native';
import { CALM_COLORS, CALM_SPACE, scale } from '../../src/calmframes/calmStyles';
import FlashMapStrip from '../../src/calmframes/FlashMapStrip';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));

const harbor = () => checkedShelf().find(entry =>
  entry.title.title === 'Harbor story (prepared locally)',
)!;
const demo = () => checkedShelf().find(entry =>
  entry.title.id === 'calm-frames-benign-story',
)!;

describe('details discovery', () => {
  afterEach(() => jest.restoreAllMocks());
  it.each([900, 30])('scrolls from a measured anchor at %s without losing focus or starting playback', y => {
    const scrollTo = jest.spyOn(ScrollView.prototype, 'scrollTo');
    const onPlay = jest.fn();
    const view = render(<TitleDetailsScreen entry={harbor()} onPlay={onPlay} />);
    const info = view.getByTestId('title-details-show-info');
    fireEvent(view.getByTestId('title-details-info'), 'layout', {
      nativeEvent: { layout: { x: 0, y, width: 1040, height: 82 } },
    });
    fireEvent(info, 'focus');
    fireEvent.press(info);
    expect(scrollTo).toHaveBeenLastCalledWith({
      y: Math.max(0, y - scale(CALM_SPACE.SAFE_Y)), animated: false,
    });
    expect(view.getByTestId('title-details-show-info')).toBe(info);
    expect(info).toHaveStyle({ borderColor: CALM_COLORS.FOCUS_RING });
    expect(view.getByTestId('title-details-show-info-label')).toHaveStyle({ textDecorationLine: 'underline' });
    expect(onPlay).not.toHaveBeenCalled();
    scrollTo.mockRestore();
  });

  it('labels the real Harbor timeline without implying practice holds', () => {
    const view = render(<TitleDetailsScreen entry={harbor()} onPlay={jest.fn()} />);
    expect(view.getByTestId('title-details-strip-start')).toHaveTextContent('0:00');
    expect(view.getByTestId('title-details-strip-middle')).toHaveTextContent('0:10');
    expect(view.getByTestId('title-details-strip-end')).toHaveTextContent('0:20');
    expect(view.getByText('No scheduled holds')).toBeTruthy();
    expect(view.queryByText('Practice hold')).toBeNull();
  });

  it('explains the actual demo marks and their continuity', () => {
    const view = render(<TitleDetailsScreen entry={demo()} onPlay={jest.fn()} />);
    expect(view.getByText('Practice hold')).toBeTruthy();
    expect(view.getByText('Sound and captions continue during every hold.')).toBeTruthy();
    expect(view.getByTestId('title-details-strip-mark-0')).toHaveStyle({ left: 260, width: 208 });
    expect(view.getByTestId('title-details-strip-mark-1')).toHaveStyle({ left: 624, width: 208 });
    expect(view.getByTestId('title-details-strip').props.accessibilityLabel).toContain('From 0:00 to 0:20.');
  });

  it('does not offer hold information or playback for an unavailable title', () => {
    const onPlay = jest.fn();
    const view = render(<TitleDetailsScreen entry={{ ...harbor(), status: 'failed' }} onPlay={onPlay} />);
    expect(view.queryByTestId('title-details-show-info')).toBeNull();
    expect(view.queryByTestId('title-details-strip')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-play'));
    expect(onPlay).not.toHaveBeenCalled();
  });

  it('keeps time labels tied to longer titles and identifies red-flash holds', () => {
    const view = render(<FlashMapStrip showKey durationMs={125000} intervals={[
      { startMs: 20000, endMs: 30000, reason: 'general', sources: [] },
      { startMs: 60000, endMs: 65000, reason: 'red', sources: [] },
    ]} />);
    expect(view.getByTestId('flash-map-strip-middle')).toHaveTextContent('1:02');
    expect(view.getByTestId('flash-map-strip-end')).toHaveTextContent('2:05');
    expect(view.getByText('Picture covered')).toBeTruthy();
    expect(view.getByText('Red-flash hold')).toBeTruthy();
    expect(view.getByTestId('flash-map-strip-mark-1')).toHaveStyle({ backgroundColor: CALM_COLORS.FAILED });
  });
});
