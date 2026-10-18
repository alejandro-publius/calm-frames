import React from 'react';
import { AccessibilityInfo, Animated } from 'react-native';
import { act, fireEvent, render } from '@testing-library/react-native';
import { useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import CoastalBoat from '../../src/calmframes/CoastalBoat';
import CoastalIsland from '../../src/calmframes/CoastalIsland';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import PlayerOpening from '../../src/calmframes/PlayerOpening';
import { titlePresentation, SEA_OTTER_SOURCE_SHA256 } from '../../src/calmframes/TitleArtwork';
import { ACADIA_SOURCE_SHA256 } from '../../src/calmframes/packagedLibrary';
import { checkedShelf } from './shelfFixtures';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
const titles = checkedShelf().filter(entry => [ACADIA_SOURCE_SHA256, SEA_OTTER_SOURCE_SHA256].includes(entry.title.sha256!));
const otter = titles.find(entry => entry.title.sha256 === SEA_OTTER_SOURCE_SHA256)!;
const flush = async () => { await act(async () => { await Promise.resolve(); await Promise.resolve(); }); };
describe('boat selection and accessibility', () => {
  let events: Record<string, (state: boolean) => void>;
  let lifecycle: (state: string) => void;
  let stop: jest.Mock, timing: jest.SpyInstance, position: jest.SpyInstance;
  beforeEach(() => {
    jest.clearAllMocks();
    events = {}; stop = jest.fn();
    (useKeplerAppStateManager as jest.Mock).mockReturnValue({ getCurrentState: () => 'active', addAppStateListener: (_name: string, cb: typeof lifecycle) => { lifecycle = cb; return { remove: jest.fn() }; } });
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
    jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(false);
    jest.spyOn(AccessibilityInfo, 'addEventListener').mockImplementation(((name: string, cb: (state: boolean) => void) => { events[name] = cb; return { remove: jest.fn() }; }) as unknown as typeof AccessibilityInfo.addEventListener);
    timing = jest.spyOn(Animated, 'timing').mockReturnValue({ start: jest.fn(), stop, reset: jest.fn() });
    position = jest.spyOn(Animated.ValueXY.prototype, 'setValue');
  });
  afterEach(() => jest.restoreAllMocks());
  it('never adds focus targets or movement with the existing motion preference off', async () => {
    const view = render(<CoastalBoat destination="coastal" />);
    view.rerender(<CoastalBoat destination="sea-otters" />); await flush();
    expect(timing).not.toHaveBeenCalled();
    const boat = view.getByTestId('coastal-boat-sea-otters');
    expect(boat.props.pointerEvents).toBe('none'); expect(boat.props.accessible).toBe(false);
    expect(AccessibilityInfo.isReduceMotionEnabled).not.toHaveBeenCalled();
  });
  it.each(['reduced', 'reader', 'unknown', 'failed'])('moves instantly for %s motion information', async mode => {
    if (mode === 'reader') jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(true);
    else if (mode === 'failed') jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockRejectedValue(new Error('unavailable'));
    else jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(mode === 'reduced' ? true : undefined as unknown as boolean);
    const view = render(<CoastalBoat destination="coastal" enabled />); await flush();
    view.rerender(<CoastalBoat destination="sea-otters" enabled />);
    expect(timing).not.toHaveBeenCalled(); expect(position).toHaveBeenLastCalledWith(expect.objectContaining({x: expect.any(Number)}));
  });
  it('cancels rapid moves and instantly settles when reduction or backgrounding begins', async () => {
    const view = render(<CoastalBoat destination="coastal" enabled />); await flush();
    view.rerender(<CoastalBoat destination="sea-otters" enabled />);
    expect(timing).toHaveBeenLastCalledWith(expect.anything(), expect.objectContaining({duration:560,isInteraction:false,useNativeDriver:true}));
    view.rerender(<CoastalBoat destination="coastal" enabled />); expect(stop).toHaveBeenCalled();
    act(() => events.reduceMotionChanged(true)); const count = timing.mock.calls.length;
    view.rerender(<CoastalBoat destination="sea-otters" enabled />); expect(timing).toHaveBeenCalledTimes(count);
    act(() => lifecycle('background')); expect(stop).toHaveBeenCalled();
    view.unmount(); expect(stop).toHaveBeenCalled();
  });
  it('stays still after a partial accessibility subscription failure and later foreground event', async () => {
    jest.spyOn(AccessibilityInfo, 'addEventListener').mockImplementation(((name: string, cb: (state: boolean) => void) => {
      if (name === 'screenReaderChanged') throw new Error('not supported');
      events[name] = cb; return { remove: jest.fn() };
    }) as unknown as typeof AccessibilityInfo.addEventListener);
    const view = render(<CoastalBoat destination="coastal" enabled />); await flush();
    act(() => lifecycle('active')); await flush();
    view.rerender(<CoastalBoat destination="sea-otters" enabled />);
    expect(timing).not.toHaveBeenCalled();
  });
  it('ignores a late preference result after the screen becomes inactive', async () => {
    let resolve!: (value: boolean) => void;
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockReturnValue(new Promise(yes => { resolve = yes; }));
    const view = render(<CoastalBoat destination="coastal" enabled />);
    view.rerender(<CoastalBoat destination="sea-otters" enabled active={false} />);
    await act(async () => resolve(false));
    expect(timing).not.toHaveBeenCalled();
  });
  it('changes selection and Watch immediately while decorative movement remains unfinished', async () => {
    const play = jest.fn(), open = jest.fn();
    const view = render(<KidHomeScreen titles={titles} onOpen={open} onPlay={play} interfaceMotionEnabled />); await flush();
    fireEvent(view.getByTestId(`kid-home-poster-${otter.title.id}`), 'focus');
    expect(view.getByTestId('coastal-boat-sea-otters')).toBeTruthy();
    fireEvent.press(view.getByTestId('kid-home-watch')); expect(play).toHaveBeenCalledWith(otter); expect(open).not.toHaveBeenCalled();
  });
});
it('shows Forest only as noninteractive scenery and retains exactly the two verified film destinations', () => {
  const view = render(<KidHomeScreen titles={titles} onOpen={jest.fn()} />);
  expect(view.getByText('Not ready to watch')).toBeTruthy();
  expect(view.getAllByTestId(/^kid-home-poster-prepared-/)).toHaveLength(2);
  const preview = view.getByTestId('forest-preview-label');
  expect(preview.props.onPress).toBeUndefined(); expect(preview.props.focusable).toBeUndefined();
  expect(view.UNSAFE_getAllByType(CoastalIsland).map(node => node.props.kind)).toEqual(['forest','coastal','sea-otters']);
});
it.each(titles)('carries the selected destination motif into Details and static loading for $title.title', entry => {
  const presentation = titlePresentation(entry.title), kind = presentation.menuArt ?? presentation.art;
  const view = render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} />);
  expect(view.UNSAFE_getByType(CoastalIsland).props.kind).toBe(kind);
  view.unmount();
  const loading = render(<PlayerOpening menuArt={kind} title={presentation.name} onBack={jest.fn()} />);
  expect(loading.UNSAFE_getByType(CoastalIsland).props.kind).toBe(kind);
  expect(loading.queryByTestId('forest-preview-label')).toBeNull();
  expect(loading.UNSAFE_root.findAllByType(CoastalBoat)).toHaveLength(0);
});
