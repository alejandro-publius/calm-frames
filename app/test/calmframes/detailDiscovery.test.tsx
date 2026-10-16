import '@testing-library/jest-native/extend-expect';
import { act, fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { BackHandler } from 'react-native';
import { COASTAL_COLORS } from '../../src/calmframes/calmStyles';
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
  it('keeps ordinary viewing brief, with reports and demo behind separate routes', () => {
    const onPlay = jest.fn();
    const view = render(<TitleDetailsScreen entry={harbor()} onPlay={onPlay} practice={demo()} onOpenPractice={jest.fn()} />);
    expect(view.getByTestId('title-details-meta')).toHaveTextContent('20 seconds');
    for (const suffix of ['analysis', 'record', 'strip', 'practice', 'plan']) expect(view.queryByTestId(`title-details-${suffix}`)).toBeNull();
    expect(view.queryByText(/No scenes flagged|No flashing found|plays normally/)).toBeNull();
    fireEvent.press(view.getByTestId('title-details-show-info'));
    expect(view.getByTestId('title-details-practice')).toBeTruthy();
    expect(view.queryByTestId('title-details-play')).toBeNull();
    expect(view.queryByTestId('title-details-record')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-technical'));
    expect(view.getByTestId('title-details-record')).toBeTruthy();
    // Zero-change titles have no empty timeline, even in technical details.
    expect(view.queryByTestId('title-details-strip')).toBeNull();
    expect(view.queryByTestId('home-harbor-scene')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-info-back'));
    expect(view.getByTestId('title-details-technical').props.hasTVPreferredFocus).toBe(true);
    fireEvent.press(view.getByTestId('title-details-info-back'));
    expect(view.getByTestId('title-details-show-info').props.hasTVPreferredFocus).toBe(true);
    expect(onPlay).not.toHaveBeenCalled();
  });

  it('identifies simulated events before watching and keeps their timeline in technical details', () => {
    const view = render(<TitleDetailsScreen entry={demo()} onPlay={jest.fn()} />);
    expect(view.getByText('Simulated demo · 20 seconds')).toBeTruthy();
    expect(view.queryByTestId('title-details-strip')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-show-info'));
    fireEvent.press(view.getByTestId('title-details-technical'));
    expect(view.getByText('Demo pause')).toBeTruthy();
    expect(view.getByTestId('title-details-strip-mark-0')).toHaveStyle({ left: 260, width: 208 });
    expect(view.getByTestId('title-details-strip-mark-1')).toHaveStyle({ left: 624, width: 208 });
  });

  it('remote Back closes technical details then More info without leaving the title', () => {
    let handlers: Array<() => boolean | null | undefined> = [];
    jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_, handler) => {
      handlers.push(handler);
      return { remove: () => { handlers = handlers.filter(value => value !== handler); } };
    });
    const leave = jest.fn();
    const view = render(<TitleDetailsScreen entry={harbor()} onPlay={jest.fn()} onBack={leave} />);
    fireEvent.press(view.getByTestId('title-details-show-info'));
    fireEvent.press(view.getByTestId('title-details-technical'));
    act(() => { expect([...handlers].reverse().some(handler => handler())).toBe(true); });
    expect(view.getByTestId('title-details-technical').props.hasTVPreferredFocus).toBe(true);
    act(() => { expect([...handlers].reverse().some(handler => handler())).toBe(true); });
    expect(view.getByTestId('title-details-show-info').props.hasTVPreferredFocus).toBe(true);
    expect(leave).not.toHaveBeenCalled();
  });

  it('gives Acadia a content description and makes changed moments optional', () => {
    const acadia = checkedShelf().find(entry => entry.title.title.includes('Acadia'))!;
    const view = render(<TitleDetailsScreen entry={acadia} onPlay={jest.fn()} />);
    expect(view.getByText('Waves along the coast of Acadia National Park.')).toBeTruthy();
    expect(view.queryByText(/flagged|Extra cautious|Analyzed before/)).toBeNull();
    expect(view.queryByTestId('title-details-strip')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-show-info'));
    // Acadia's maps carry no scene hold and its rendition ships no captions,
    // so the page promises neither a still picture nor captions.
    expect(view.getByTestId('title-details-cover-line').props.children).toBe('Brief parts of this video are covered. The sound continues.');
    expect(view.queryByText(/still picture|captions/i)).toBeNull();
    expect(view.queryByTestId('title-details-record')).toBeNull();
    fireEvent.press(view.getByTestId('title-details-technical'));
    expect(view.getByTestId('title-details-strip')).toBeTruthy();
    expect(view.getByTestId('title-details-record-source')).toBeTruthy();
  });

  it('promises captions only for a title that ships them', () => {
    // The prepared Harbor maps carry no segments, so it gets Acadia's schedule
    // here: a verified title with covers and with a caption track.
    const acadia = checkedShelf().find(entry => entry.title.title.includes('Acadia'))!;
    const entry = { ...harbor(), segments: acadia.segments };
    expect((entry.title.textTrack ?? []).length).toBeGreaterThan(0);
    expect(acadia.segments.length).toBeGreaterThan(0);
    const view = render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} />);
    fireEvent.press(view.getByTestId('title-details-show-info'));
    expect(view.getByTestId('title-details-cover-line').props.children).toMatch(/covered\. The sound continues\. Captions continue too\.$/);
  });

  it('does not offer hold information or playback for an unavailable title', () => {
    const onPlay = jest.fn();
    const view = render(<TitleDetailsScreen entry={{ ...harbor(), status: 'failed' }} onPlay={onPlay} />);
    expect(view.queryByTestId('title-details-show-info')).toBeNull();
    expect(view.queryByTestId('title-details-strip')).toBeNull();
    expect(view.queryByTestId('title-details-play')).toBeNull();
    expect(onPlay).not.toHaveBeenCalled();
  });

  it('keeps time labels tied to longer titles and identifies red-flash holds', () => {
    const view = render(<FlashMapStrip showKey durationMs={125000} intervals={[
      { startMs: 20000, endMs: 30000, reason: 'general', sources: [] },
      { startMs: 60000, endMs: 65000, reason: 'red', sources: [] },
    ]} />);
    expect(view.getByTestId('flash-map-strip-middle')).toHaveTextContent('1:02');
    expect(view.getByTestId('flash-map-strip-end')).toHaveTextContent('2:05');
    expect(view.getByText('Picture hidden')).toBeTruthy();
    expect(view.getByText('Red flashing hidden')).toBeTruthy();
    expect(view.getByTestId('flash-map-strip-mark-1')).toHaveStyle({ backgroundColor: COASTAL_COLORS.FAILED });
  });
});


test('watch and technical Details both draw the rendition timeline and update its offset', () => {
  const entry = { title: { id: 'test', title: 'Coast', uri: 'test.mp4', sha256: 'a'.repeat(64), durationMs: 20_000, renditionStartOffsetMs: 100 },
    status: 'verified' as const, segments: [{ startMs: 5_000, endMs: 6_000 }], hiddenMs: 1_000, verifiedProfiles: ['wcag'] };
  const view = render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} />);
  expect(view.getByTestId('title-details-covered-mark-0')).toHaveStyle({ left: 136.4, width: 62 });
  fireEvent.press(view.getByTestId('title-details-show-info'));
  fireEvent.press(view.getByTestId('title-details-technical'));
  expect(view.getByTestId('title-details-strip-mark-0')).toHaveStyle({ left: 228.8, width: 104 });
  view.rerender(<TitleDetailsScreen entry={{ ...entry, title: { ...entry.title, renditionStartOffsetMs: -100 } }} onPlay={jest.fn()} />);
  expect(view.getByTestId('title-details-strip-mark-0')).toHaveStyle({ left: 239.20000000000002, width: 104 });
});
