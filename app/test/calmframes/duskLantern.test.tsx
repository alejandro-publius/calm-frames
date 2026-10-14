/**
 * The dusk lantern composition: Home leads with the harbor and one coral
 * action, says plainly what Harbor does and does not do, and puts the picture
 * hold demo one press away. Details lists its facts in one line.
 */
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { BENIGN_STORY_ID } from '../../src/calmframes/benignStory';
import { CALM_COLORS, MINIMUM_TEXT_SIZE } from '../../src/calmframes/calmStyles';
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

test('Home leads with Harbor, says it has no holds, and puts the picture hold demo one press away', () => {
  const onOpen = jest.fn();
  const launch = jest.fn();
  render(<KidHomeScreen titles={titles} onOpen={onOpen} onPlay={jest.fn()} onLaunchControl={launch} onOpenParentArea={jest.fn()} />);
  expect(screen.getByTestId('kid-home-title').props.children).toBe('Harbor');
  expect(screen.queryByText('Harbor plays without picture holds.')).toBeNull();
  expect(screen.getByTestId('kid-home-meta').props.children).toBe('20 sec · No picture holds');
  expect(screen.getByText('Picture holds on supported videos. Audio continues.')).toBeTruthy();
  expect(screen.getByText('20 sec · 2 practice holds')).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Play: Harbor' })).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Try picture holds. 20 sec · 2 practice holds' })).toBeTruthy();
  expect(preferred()).toEqual(['kid-home-watch']);
  fireEvent.press(screen.getByTestId('kid-home-demo'));
  expect(launch).toHaveBeenCalledWith('demo');
  expect(onOpen).toHaveBeenCalledWith(demo);
  for (const pattern of BANNED) {
    expect(screen.queryByText(pattern)).toBeNull();
  }
});

test('one coral action on Home: Play is primary, the demo and Details are quiet', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} />);
  const watch = StyleSheet.flatten(screen.getByTestId('kid-home-watch').props.style);
  expect(watch.backgroundColor).toBe(CALM_COLORS.PRIMARY);
  for (const id of ['kid-home-more-info', 'kid-home-demo', 'kid-home-learn']) {
    expect(StyleSheet.flatten(screen.getByTestId(id).props.style).backgroundColor).not.toBe(CALM_COLORS.PRIMARY);
  }
});

test('How it works lives in the header, hides while the explanation is open, and regains focus after it', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} />);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  expect(screen.getByTestId('picture-hold-introduction')).toBeTruthy();
  expect(screen.queryByTestId('kid-home-learn')).toBeNull();
  expect(screen.queryByTestId('kid-home-demo')).toBeNull();
  fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
  expect(preferred()).toEqual(['kid-home-learn']);
});

test('returning from the demo page focuses the demo control and nothing else', () => {
  render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} returnFocusId={BENIGN_STORY_ID} returnFocusControl="demo" />);
  expect(preferred()).toEqual(['kid-home-demo']);
});

test('when the demo itself leads the shelf there is no second demo control and no no-holds line', () => {
  render(<KidHomeScreen titles={[demo]} onOpen={jest.fn()} onPlay={jest.fn()} />);
  expect(screen.queryByTestId('kid-home-demo')).toBeNull();
  expect(screen.queryByTestId('kid-home-no-holds')).toBeNull();
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toMatch(/Watch demo/);
});

test('Home and Details titles share one size, and every added line meets the ten foot floor', () => {
  const home = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} />);
  const homeTitle = StyleSheet.flatten(home.getByTestId('kid-home-title').props.style);
  const noHolds = StyleSheet.flatten(home.getByTestId('kid-home-meta').props.style);
  expect(noHolds.fontSize).toBeGreaterThanOrEqual(MINIMUM_TEXT_SIZE);
  home.unmount();
  const details = render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} />);
  const detailsTitle = StyleSheet.flatten(details.getByTestId('title-details-title').props.style);
  expect(detailsTitle.fontSize).toBe(homeTitle.fontSize);
  expect(homeTitle.fontSize).toBeLessThanOrEqual(120);
  expect(StyleSheet.flatten(details.getByTestId('title-details-meta').props.style).fontSize).toBeGreaterThanOrEqual(MINIMUM_TEXT_SIZE);
});

test('Details lists runtime and holds in one factual line under the title', () => {
  const prepared = render(<TitleDetailsScreen entry={harbor} onPlay={jest.fn()} />);
  expect(prepared.getByTestId('title-details-meta').props.children).toBe('20 sec · No picture holds');
  expect(prepared.getByText('No picture holds in this story. Some flashing may still go undetected.')).toBeTruthy();
  for (const pattern of BANNED) {
    expect(prepared.queryByText(pattern)).toBeNull();
  }
  prepared.unmount();
  const practice = render(<TitleDetailsScreen entry={demo} onPlay={jest.fn()} />);
  expect(practice.getByTestId('title-details-meta').props.children).toBe('Optional demo · 20 sec · 2 practice holds');
  expect(practice.getByTestId('title-details-play').props.accessibilityLabel).toMatch(/Watch demo/);
});


test('demo metadata follows the title duration and schedule rather than fixed copy', () => {
  const shorterDemo = { ...demo, title: { ...demo.title, durationMs: 30000 }, segments: demo.segments.slice(0, 1) };
  render(<KidHomeScreen titles={titles.map((entry) => entry === demo ? shorterDemo : entry)} onOpen={jest.fn()} />);
  expect(screen.getByTestId('kid-home-demo-meta').props.children).toBe('30 sec · 1 practice hold');
  expect(screen.getByRole('button', { name: 'Try picture holds. 30 sec · 1 practice hold' })).toBeTruthy();
});
