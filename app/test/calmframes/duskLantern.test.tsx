/**
 * The coastal Home and Details. Home is the app's name over the scenery with
 * Play and Details and nothing else in the hero: the title's facts live on
 * Details, which is also where the practice demo is reached.
 */
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { BENIGN_STORY_ID } from '../../src/calmframes/benignStory';
import { COASTAL_COLORS as CALM_COLORS, MINIMUM_TEXT_SIZE } from '../../src/calmframes/calmStyles';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { checkedShelf } from './shelfFixtures';

const titles = checkedShelf();
const demo = titles.find((entry) => entry.title.id === BENIGN_STORY_ID)!;
const harbor = titles.find((entry) => entry.title.title === 'Harbor story (prepared locally)')!;
const BANNED = [/settle into/i, /watch with fewer flashes/i, /original Calm Frames short/i, /small boat rests/i, /original story/i, /a calm frames original/i, /prevents? seizures/i, /seizure.proof/i, /other streaming apps/i];

function preferred(): string[] {
  const ids = screen.UNSAFE_root
    .findAll((node) => node.props.hasTVPreferredFocus === true && typeof node.props.testID === 'string')
    .map((node) => node.props.testID as string);
  return [...new Set(ids)];
}

test('Home is the app name, the scenery, Play and Details: no title facts, no explanation, no demo card, no notice', () => {
  const onOpen = jest.fn();
  const launch = jest.fn();
  render(<KidHomeScreen titles={titles} onOpen={onOpen} onPlay={jest.fn()} onLaunchControl={launch} onOpenParentArea={jest.fn()} />);
  expect(screen.getByTestId('kid-home-title').props.children).toBe('Calm Frames');
  expect(screen.getAllByText('Calm Frames')).toHaveLength(1);
  expect(screen.queryByTestId('kid-home-meta')).toBeNull();
  expect(screen.queryByText(/No picture holds/)).toBeNull();
  expect(screen.queryByText('Picture holds on supported videos. Audio continues.')).toBeNull();
  expect(screen.queryByTestId('kid-home-demo')).toBeNull();
  expect(screen.queryByText('Try picture holds')).toBeNull();
  expect(screen.queryByText(/practice hold/)).toBeNull();
  expect(screen.queryByTestId('kid-home-hidden-count')).toBeNull();
  expect(screen.queryByText(/unavailable/)).toBeNull();
  expect(screen.getByRole('button', { name: 'Play: Harbor' })).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Details: Harbor' })).toBeTruthy();
  expect(screen.getByTestId('kid-home-parent-area')).toBeTruthy();
  expect(preferred()).toEqual(['kid-home-watch']);
  fireEvent.press(screen.getByTestId('kid-home-more-info'));
  expect(launch).toHaveBeenCalledWith('details');
  expect(onOpen).toHaveBeenCalledWith(harbor);
  for (const pattern of BANNED) {
    expect(screen.queryByText(pattern)).toBeNull();
  }
});

test('one teal action on Home: Play is primary, Details and Help are quiet', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} />);
  const watch = StyleSheet.flatten(screen.getByTestId('kid-home-watch').props.style);
  expect(watch.backgroundColor).toBe(CALM_COLORS.PRIMARY);
  for (const id of ['kid-home-more-info', 'kid-home-learn', 'kid-home-parent-area']) {
    expect(StyleSheet.flatten(screen.getByTestId(id).props.style).backgroundColor).not.toBe(CALM_COLORS.PRIMARY);
  }
});

test('How it works lives in the header, hides while the explanation is open, and regains focus after it', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} />);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  expect(screen.getByTestId('picture-hold-introduction')).toBeTruthy();
  expect(screen.queryByTestId('kid-home-learn')).toBeNull();
  fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
  expect(preferred()).toEqual(['kid-home-learn']);
});

test('returning from Details focuses Details; returning from the demo page reached through Help focuses Help', () => {
  const first = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} returnFocusId={harbor.title.id} returnFocusControl="details" />);
  expect(preferred()).toEqual(['kid-home-more-info']);
  first.unmount();
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} returnFocusId={BENIGN_STORY_ID} />);
  expect(preferred()).toEqual(['kid-home-learn']);
});

test('when the demo itself leads the shelf there is no second demo control and no no-holds line', () => {
  render(<KidHomeScreen titles={[demo]} onOpen={jest.fn()} onPlay={jest.fn()} />);
  expect(screen.queryByTestId('kid-home-demo')).toBeNull();
  expect(screen.queryByTestId('kid-home-no-holds')).toBeNull();
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toMatch(/Play demo/);
});

test('the Home heading is one large line sized to clear the artwork, and Details uses the same reading scale', () => {
  const home = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} />);
  const homeTitle = StyleSheet.flatten(home.getByTestId('kid-home-title').props.style);
  // "Calm Frames" measures 755 units at 120 in the display face and would
  // reach the lighthouse island at 184; see KidHomeScreen's style note.
  expect(homeTitle.fontSize).toBe(120);
  expect(homeTitle.fontSize).toBeGreaterThanOrEqual(MINIMUM_TEXT_SIZE * 3);
  home.unmount();
  const details = render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} />);
  const detailsTitle = StyleSheet.flatten(details.getByTestId('title-details-title').props.style);
  expect(detailsTitle.fontSize).toBe(homeTitle.fontSize);
  expect(StyleSheet.flatten(details.getByTestId('title-details-meta').props.style).fontSize).toBeGreaterThanOrEqual(MINIMUM_TEXT_SIZE);
});

test('Details lists runtime and holds in one factual line under the title', () => {
  const prepared = render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} />);
  expect(prepared.getByTestId('title-details-meta').props.children).toBe('20 sec · No flashing found');
  expect(prepared.getByText('Checked frame by frame. No flashing found, so the picture never holds.')).toBeTruthy();
  for (const pattern of BANNED) {
    expect(prepared.queryByText(pattern)).toBeNull();
  }
  prepared.unmount();
  const practice = render(<TitleDetailsScreen entry={demo} onPlay={jest.fn()} />);
  expect(practice.getByTestId('title-details-meta').props.children).toBe('Practice version · 20 sec · 2 practice holds');
  expect(practice.getByTestId('title-details-play').props.accessibilityLabel).toMatch(/Play demo/);
});

test('Details offers the practice demo beside Play, quiet, and the demo page itself does not', () => {
  const openPractice = jest.fn();
  const prepared = render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} practice={demo} onOpenPractice={openPractice} />);
  const entry = prepared.getByTestId('title-details-practice');
  expect(entry.props.accessibilityLabel).toBe('Try picture holds. 20 sec · 2 practice holds');
  expect(StyleSheet.flatten(entry.props.style).backgroundColor).not.toBe(CALM_COLORS.PRIMARY);
  expect(prepared.getByTestId('title-details-play').props.hasTVPreferredFocus).toBe(true);
  expect(entry.props.hasTVPreferredFocus).toBe(false);
  fireEvent.press(entry);
  expect(openPractice).toHaveBeenCalledWith(demo);
  prepared.unmount();
  const returned = render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} practice={demo} onOpenPractice={openPractice} preferPracticeFocus />);
  expect(returned.getByTestId('title-details-practice').props.hasTVPreferredFocus).toBe(true);
  expect(returned.getByTestId('title-details-play').props.hasTVPreferredFocus).toBe(false);
  returned.unmount();
  const practice = render(<TitleDetailsScreen entry={demo} onPlay={jest.fn()} practice={demo} onOpenPractice={openPractice} />);
  expect(practice.queryByTestId('title-details-practice')).toBeNull();
  expect(practice.getByTestId('title-details-play').props.hasTVPreferredFocus).toBe(true);
});

test('the practice entry follows the demo duration and schedule rather than fixed copy', () => {
  const shorterDemo = { ...demo, title: { ...demo.title, durationMs: 30000 }, segments: demo.segments.slice(0, 1) };
  render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} practice={shorterDemo} onOpenPractice={jest.fn()} />);
  expect(screen.getByTestId('title-details-practice').props.accessibilityLabel).toBe('Try picture holds. 30 sec · 1 practice hold');
});
