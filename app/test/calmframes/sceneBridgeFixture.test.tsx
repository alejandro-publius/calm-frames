import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { BackHandler, StyleSheet } from 'react-native';
import SceneBridgeFixture from '../../src/calmframes/SceneBridgeFixture';
import PictureHoldIntroduction from '../../src/calmframes/PictureHoldIntroduction';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import * as traces from '../../src/calmframes/trace';
import { checkedShelf } from './shelfFixtures';

const originalDev = (global as any).__DEV__;
beforeEach(() => { (global as any).__DEV__ = true; });
afterEach(() => { (global as any).__DEV__ = originalDev; jest.restoreAllMocks(); });
it('renders verified fixture text and an opaque ordinary fallback for stale identity', () => {
  const trace = jest.spyOn(traces, 'trace');
  render(<SceneBridgeFixture onBack={jest.fn()} />);
  expect(screen.getByText('Test fixture: a card displays one.')).toBeTruthy();
  expect(StyleSheet.flatten(screen.getByTestId('scene-bridge-fixture-cover').props.style).opacity).toBe(1);
  fireEvent.press(screen.getByTestId('scene-bridge-fixture-fallback'));
  expect(screen.queryByText('Test fixture: a card displays one.')).toBeNull();
  expect(screen.queryByText('This scene is covered')).toBeNull();
  expect(StyleSheet.flatten(screen.getByTestId('scene-bridge-fixture-cover').props.style).opacity).toBe(1);
  expect(trace).toHaveBeenCalledWith('playback', 'scene-bridge-fixture state=fallback opaque_requested=true media=none');
  fireEvent.press(screen.getByTestId('scene-bridge-fixture-valid'));
  expect(screen.getByText('Scene bridge test')).toBeTruthy();
});
it('dismisses with remote Back and removes its listener', () => {
  const remove = jest.fn();
  const subscribe = jest.spyOn(BackHandler, 'addEventListener').mockReturnValue({ remove });
  const back = jest.fn(); const view = render(<SceneBridgeFixture onBack={back} />);
  act(() => { expect(subscribe.mock.calls[0][1]()).toBe(true); });
  expect(back).toHaveBeenCalledTimes(1);
  view.unmount(); expect(remove).toHaveBeenCalled();
});
it('has no release entry or release-renderable fixture', () => {
  (global as any).__DEV__ = false;
  const view = render(<PictureHoldIntroduction onBridgeTest={jest.fn()} />);
  expect(screen.queryByTestId('picture-hold-bridge-test')).toBeNull();
  view.unmount(); render(<SceneBridgeFixture onBack={jest.fn()} />);
  expect(screen.queryByTestId('scene-bridge-fixture')).toBeNull();
});
it('keeps development diagnostics out of the consumer explanation', () => {
  const open = jest.fn();
  render(<KidHomeScreen titles={checkedShelf()} onOpen={open} />);
  fireEvent.press(screen.getByTestId('kid-home-learn'));
  expect(screen.queryByTestId('picture-hold-bridge-test')).toBeNull();
  expect(screen.queryByTestId('scene-bridge-fixture')).toBeNull();
  expect(open).not.toHaveBeenCalled();
});
