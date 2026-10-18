import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import PlayerOpening from '../../src/calmframes/PlayerOpening';
import { WORLD } from '../../src/calmframes/CoastalWorld';
import { CalmControlAppearance } from '../../src/calmframes/CalmControlSurface';
import SceneTimeline from '../../src/calmframes/SceneTimeline';
import { checkedShelf } from './shelfFixtures';
import { titleDataFor } from '../../src/screens/KidModeScreen';
import { titlePresentation, SEA_OTTER_SOURCE_SHA256 } from '../../src/calmframes/TitleArtwork';
import { ACADIA_SOURCE_SHA256 } from '../../src/calmframes/packagedLibrary';
import { CALM_CONTROL, FOCUS_RING_WIDTH } from '../../src/calmframes/calmStyles';
import { cardAt } from '../../src/calmframes/cards';
import { playbackCard } from '../../src/calmframes/usePlaybackPresentation';
import { CoverInterval } from '../../src/calmframes/coverSchedule';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
const titles = checkedShelf().filter(entry => [ACADIA_SOURCE_SHA256, SEA_OTTER_SOURCE_SHA256].includes(entry.title.sha256!));
const otter = titles.find(entry => entry.title.sha256 === SEA_OTTER_SOURCE_SHA256)!;

it('keeps a selected film visible after focus leaves, with no autoplay or focus resizing', () => {
  const play = jest.fn(), open = jest.fn();
  const view = render(<KidHomeScreen titles={titles} onOpen={open} onPlay={play} />);
  const id = `kid-home-poster-${otter.title.id}`;
  const before = StyleSheet.flatten(view.getByTestId(id).props.style);
  fireEvent(view.getByTestId(id), 'focus');
  fireEvent(view.getByTestId(id), 'blur');
  fireEvent(view.getByTestId('kid-home-watch'), 'focus');
  const selected = view.getByTestId(id);
  expect(selected.props.accessibilityState.selected).toBe(true);
  expect(StyleSheet.flatten(selected.props.style).borderBottomColor).toBe(WORLD.FOCUS_RING);
  for (const key of ['width','minHeight','borderWidth','padding']) expect(StyleSheet.flatten(selected.props.style)[key]).toBe(before[key]);
  expect(before.borderWidth).toBe(FOCUS_RING_WIDTH);
  expect(view.getByTestId(`kid-home-poster-image-${otter.title.id}`)).toBeTruthy();
  expect(play).not.toHaveBeenCalled(); expect(open).not.toHaveBeenCalled();
  fireEvent.press(view.getByTestId('kid-home-watch')); expect(play).toHaveBeenCalledWith(otter);
});

it.each(titles)('retains scenery, title typography and Watch size through $title.title', entry => {
  const data = titleDataFor(entry);
  const home = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} returnFocusId={entry.title.id} returnFocusControl="watch" />);
  const homeStyle = StyleSheet.flatten(home.getByTestId('kid-home-video-title').props.style);
  const button = StyleSheet.flatten(home.getByTestId('kid-home-watch').props.style);
  expect(home.getByTestId('coastal-world')).toBeTruthy();
  expect(home.queryByTestId('kid-home-benefit')).toBeNull();
  expect(homeStyle.fontFamily).toBeTruthy();
  home.unmount();
  const detail = render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} />);
  expect(detail.getByTestId('coastal-world')).toBeTruthy();
  const detailStyle = StyleSheet.flatten(detail.getByTestId('title-details-title').props.style);
  const detailButton = StyleSheet.flatten(detail.getByTestId('title-details-play').props.style);
  for (const key of ['minHeight','borderRadius','paddingHorizontal']) expect(detailButton[key]).toBe(button[key]);
  expect(button.minHeight).toBeGreaterThanOrEqual(CALM_CONTROL.MIN_HEIGHT);
  detail.unmount();
  const opening = render(<PlayerOpening title={data.title} menuArt={data.calmMenuArt} onBack={jest.fn()} />);
  expect(opening.getByTestId('coastal-world')).toBeTruthy();
  expect(opening.queryByTestId('title-details-destination-image')).toBeNull();
  const openingStyle = StyleSheet.flatten(opening.getByText(titlePresentation(entry.title).name).props.style);
  for (const key of ['fontSize','lineHeight','fontFamily']) {
    expect(openingStyle[key]).toBe(detailStyle[key]);
  }
});

const intervals: CoverInterval[] = [{ startMs: 1000, endMs: 3000, reason: 'general', sources: [] }];
it('uses identical interval geometry on a fixed Details strip and a fluid player strip without any focus or seek action', () => {
  const view = render(<SceneTimeline intervals={intervals} durationMs={10000} width={600} />);
  expect(StyleSheet.flatten(view.getByTestId('scene-timeline-mark-0').props.style)).toMatchObject({left:60,width:120});
  view.rerender(<SceneTimeline intervals={intervals} durationMs={10000} currentMs={2000} />);
  expect(StyleSheet.flatten(view.getByTestId('scene-timeline-mark-0').props.style)).toMatchObject({left:'10%',width:'20%'});
  expect(StyleSheet.flatten(view.getByTestId('scene-timeline-position').props.style).left).toBe('20%');
  expect(view.UNSAFE_root.findAll(node => node.props.onPress || node.props.focusable || node.props.hasTVPreferredFocus)).toHaveLength(0);
  view.rerender(<SceneTimeline intervals={intervals} durationMs={0} />);
  expect(view.queryByTestId('scene-timeline-track')).toBeNull();
});
it('only names a replacement when the runtime actually presents verified ocean', () => {
  const card = cardAt(intervals, 2000);
  const state = {paused:false,covered:true,buffering:false,ended:false};
  expect(playbackCard(card,{...state,oceanVisible:true}).title).toBe('Scene replaced');
  expect(playbackCard(card,state).title).toBe('Scene hidden');
  expect(playbackCard(card,{...state,paused:true}).detail).toBe('Paused');
  expect(playbackCard(card,{...state,buffering:true}).detail).toBe('Loading');
  expect(playbackCard(card,{...state,oceanVisible:true}).skipToMs).toBe(playbackCard(card,state).skipToMs);
});

it('production materials paint only the selected film at rest and preserve a persistent selection edge', () => {
  const view = render(<CalmControlAppearance.Provider value><KidHomeScreen titles={titles} onOpen={jest.fn()} /></CalmControlAppearance.Provider>);
  const card = view.getByTestId(`kid-home-poster-${otter.title.id}`);
  expect(card.findAll(node => node.type === ('LinearGradient' as never))).toHaveLength(0);
  fireEvent(card, 'focus'); fireEvent(card, 'blur');
  expect(card.props.accessibilityState.selected).toBe(true);
  expect(card.findAll(node => node.type === ('LinearGradient' as never))).toHaveLength(0);
  expect(StyleSheet.flatten(card.props.style).borderBottomColor).toBe(WORLD.FOCUS_RING);
});
