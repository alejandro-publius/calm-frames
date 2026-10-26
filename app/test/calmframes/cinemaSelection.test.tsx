import { MCWAY_SOURCE_SHA256 } from '../../src/calmframes/continuousScene';
import React from 'react';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { fireEvent, render } from '@testing-library/react-native';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { checkedShelf } from './shelfFixtures';
import { ACADIA_SOURCE_SHA256 } from '../../src/calmframes/packagedLibrary';

// Retain this two-title regression fixture; the real consumer pair is tested in otterPreview.
const titles = checkedShelf().filter(entry => entry.title.sha256 !== MCWAY_SOURCE_SHA256).filter(entry => !['Sea otters in Alaska', 'Forest creek at Redwood'].includes(entry.title.title));
const acadia = titles.find(entry => entry.title.sha256 === ACADIA_SOURCE_SHA256)!;

test('the actual-video rail selects artwork and both actions without starting playback on focus', () => {
  const play = jest.fn(); const open = jest.fn(); const launch = jest.fn();
  const view = render(<KidHomeScreen titles={titles} onOpen={open} onPlay={play} onLaunchControl={launch} />);
  expect(view.queryAllByTestId(/^kid-home-poster-(?!image-|title-|qualifier-)/)).toHaveLength(2);
  fireEvent(view.getByTestId(`kid-home-poster-${acadia.title.id}`), 'focus');
  expect(play).not.toHaveBeenCalled();
  expect(open).not.toHaveBeenCalled();
  expect(view.getByTestId('kid-home-video-title').props.children).toBe('Acadia');
  expect(view.getByTestId('coastal-world')).toBeTruthy();
  fireEvent.press(view.getByTestId('kid-home-watch'));
  expect(play).toHaveBeenCalledWith(acadia);
  expect(launch).toHaveBeenLastCalledWith('watch');
  fireEvent.press(view.getByTestId('kid-home-more-info'));
  expect(open).toHaveBeenCalledWith(acadia);
  expect(launch).toHaveBeenLastCalledWith('details');
});

test.each(['watch', 'details', 'poster'] as const)('return from Acadia restores the selected title and the %s control', control => {
  const view = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} returnFocusId={acadia.title.id} returnFocusControl={control} />);
  expect(view.getByTestId('kid-home-video-title').props.children).toBe('Acadia');
  const id = control === 'watch' ? 'kid-home-watch' : control === 'details' ? 'kid-home-more-info' : `kid-home-poster-${acadia.title.id}`;
  expect(view.getByTestId(id).props.hasTVPreferredFocus).toBe(true);
  expect(view.getAllByRole('button').filter(button => button.props.hasTVPreferredFocus)).toHaveLength(1);
});

test.each(['Acadia coastal scenery (National Park Service, public domain)', 'Sea otters in Alaska', 'Forest creek at Redwood'])(
  'activating %s without focus updates selection, Watch, Details and restored focus', name => {
    const shelf = checkedShelf();
    const entry = shelf.find(item => item.title.title === name)!;
    expect(entry).toBeDefined();
    const other = shelf.find(item => item.title.id !== entry.title.id)!;
    const open = jest.fn(); const play = jest.fn(); const select = jest.fn(); const launch = jest.fn();
    const view = render(<KidHomeScreen titles={shelf} onOpen={open} onPlay={play}
      onSelectTitle={select} onLaunchControl={launch} returnFocusId={other.title.id} />);
    fireEvent.press(view.getByTestId(`kid-home-poster-${entry.title.id}`));
    expect(select).toHaveBeenLastCalledWith(entry.title.id);
    expect(open).toHaveBeenLastCalledWith(entry);
    expect(launch).toHaveBeenLastCalledWith('poster');
    expect(play).not.toHaveBeenCalled();
    expect(view.getByTestId(`kid-home-poster-${entry.title.id}`).props.accessibilityState.selected).toBe(true);
    fireEvent.press(view.getByTestId('kid-home-watch'));
    expect(play).toHaveBeenLastCalledWith(entry);
    fireEvent.press(view.getByTestId('kid-home-more-info'));
    expect(open).toHaveBeenLastCalledWith(entry);
    view.rerender(<KidHomeScreen titles={shelf} onOpen={open} returnFocusId={entry.title.id} returnFocusControl="poster" />);
    expect(view.getByTestId(`kid-home-poster-${entry.title.id}`).props.hasTVPreferredFocus).toBe(true);
  },
);

test('activation while a household update is saving cannot change selection or open a title', () => {
  const open = jest.fn(); const select = jest.fn(); const launch = jest.fn();
  const view = render(<KidHomeScreen titles={titles} onOpen={open} onSelectTitle={select}
    onLaunchControl={launch} saving />);
  fireEvent.press(view.getByTestId(`kid-home-poster-${acadia.title.id}`));
  expect(select).not.toHaveBeenCalled();
  expect(launch).not.toHaveBeenCalled();
  expect(open).not.toHaveBeenCalled();
});
