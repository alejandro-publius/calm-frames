/**
 * Back restores the control that started what the viewer just left.
 *
 * The route stays mounted behind the player and re-keys the shelf on the
 * navigation focus event, so on return every control is created again and
 * hasTVPreferredFocus decides where the remote's focus lands. These tests use
 * the real bundled shelf and drive the same events the navigator sends.
 */
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { BackHandler, Platform } from 'react-native';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { OFFLINE_MAP_JSON } from '../../src/calmframes/offlineMapText';
import { CatalogTitle, CheckedTitle } from '../../src/calmframes/titleStatus';
import { Screens } from '../../src/components/navigation/types';
import KidModeScreen from '../../src/screens/KidModeScreen';
import { regressionCatalog } from '../calmframes/shelfFixtures';

const NOW = Date.parse(JSON.parse(OFFLINE_MAP_JSON).created_utc) + 60_000;

async function startShelf(catalog?: CatalogTitle[]) {
  const listeners: Record<string, Array<() => void>> = {};
  const navigation = {
    navigate: jest.fn(),
    isFocused: () => true,
    addListener: (event: string, listener: () => void) => {
      (listeners[event] ??= []).push(listener);
      return () => undefined;
    },
  };
  render(<KidModeScreen catalog={catalog} navigation={navigation as never} newSalt={() => 'test-salt'} nowMs={() => NOW} />);
  await screen.findByTestId('kid-mode-first-run');
  const type = (digits: string) => {
    for (const digit of digits) fireEvent.press(screen.getByTestId(`kid-mode-first-run-key-${digit}`));
  };
  type('1357');
  type('1357');
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  fireEvent.press(screen.getByTestId('kid-mode-first-run-next'));
  await act(async () => {
    fireEvent.press(screen.getByTestId('kid-mode-first-run-done'));
  });
  /** The navigator leaves for the player and comes back. */
  const returnFromPlayer = () => {
    act(() => listeners.blur?.forEach((listener) => listener()));
    act(() => listeners.focus?.forEach((listener) => listener()));
  };
  return { navigation, returnFromPlayer };
}

/** Every control asking for the remote's focus right now. */
function preferred(): string[] {
  const ids = screen.UNSAFE_root
    .findAll((node) => node.props.hasTVPreferredFocus === true && typeof node.props.testID === 'string')
    .map((node) => node.props.testID as string);
  return [...new Set(ids)];
}

describe('Back from playback and details on the real shelf', () => {
  it.each(['button', 'remote'] as const)('Parents PIN gate, %s Back: focus returns only to Parents after Details', async (back) => {
    const platform = jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(true);
    let handlers: Array<() => boolean | null | undefined> = [];
    const subscription = jest.spyOn(BackHandler, 'addEventListener').mockImplementation((event, handler) => {
      if (event === 'hardwareBackPress') handlers.push(handler);
      return { remove: () => { handlers = handlers.filter((one) => one !== handler); } };
    });
    try {
      await startShelf();
      fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
      fireEvent.press(screen.getByTestId('kid-mode-details-back'));
      expect(preferred()).toEqual(['kid-mode-home-more-info']);
      fireEvent.press(screen.getByTestId('kid-mode-home-parent-area'));
      expect(screen.getByTestId('kid-mode-parent-key-1')).toBeTruthy();
      expect(screen.queryByTestId('kid-mode-parent-preset-wcag')).toBeNull();
      if (back === 'button') {
        fireEvent.press(screen.getByTestId('kid-mode-parent-back'));
      } else {
        let handled = false;
        act(() => { handled = [...handlers].reverse().some((handler) => handler() === true); });
        expect(handled).toBe(true);
      }
      expect(preferred()).toEqual(['kid-mode-home-parent-area']);
      fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
      act(() => { expect([...handlers].reverse().some((handler) => handler() === true)).toBe(true); });
      expect(preferred()).toEqual(['kid-mode-home-learn']);
      // A later title launch still replaces the remembered Parents control.
      fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
      fireEvent.press(screen.getByTestId('kid-mode-details-back'));
      expect(preferred()).toEqual(['kid-mode-home-more-info']);
    } finally {
      subscription.mockRestore();
      platform.mockRestore();
    }
  });

  it.each(['home', 'details'] as const)('removes %s controls from the focus tree during playback and restores them on return', async (origin) => {
    const { returnFromPlayer } = await startShelf();
    if (origin === 'details') fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
    const caller = origin === 'details' ? 'kid-mode-details-play' : 'kid-mode-home-watch';
    fireEvent.press(screen.getByTestId(caller));
    expect(screen.queryByTestId(caller)).toBeNull();
    expect(screen.queryByTestId('kid-mode-details-practice')).toBeNull();
    expect(preferred()).toEqual([]);
    returnFromPlayer();
    expect(screen.getByTestId(caller)).toBeTruthy();
    expect(preferred()).toEqual([caller]);
  });

  it('Watch, then Back from the player: focus returns to Watch, and only there', async () => {
    const { navigation, returnFromPlayer } = await startShelf();
    expect(preferred()).toEqual(['kid-mode-home-watch']);
    fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
    expect(navigation.navigate).toHaveBeenCalledWith(Screens.PLAYER_SCREEN, expect.objectContaining({ showHomeOpening: true }));
    returnFromPlayer();
    expect(preferred()).toEqual(['kid-mode-home-watch']);
  });

  it('Details, then Back: focus returns to Details', async () => {
    await startShelf();
    fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
    expect(screen.getByTestId('kid-mode-details-play').props.hasTVPreferredFocus).toBe(true);
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(preferred()).toEqual(['kid-mode-home-more-info']);
  });

  it('Details, Watch, then Back from the player: the details page and its Watch return', async () => {
    const { navigation, returnFromPlayer } = await startShelf();
    fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    expect(navigation.navigate).toHaveBeenCalledWith(Screens.PLAYER_SCREEN, expect.anything());
    returnFromPlayer();
    expect(preferred()).toEqual(['kid-mode-details-play']);
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(preferred()).toEqual(['kid-mode-home-more-info']);
  });

  it('Details, More info, demo, Watch, then Back four times: one level at a time, focus on what was pressed', async () => {
    const { navigation, returnFromPlayer } = await startShelf(regressionCatalog());
    fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
    expect(screen.getByTestId('kid-mode-details-meta').props.children).toBe('20 seconds');
    expect(preferred()).toEqual(['kid-mode-details-play']);
    fireEvent.press(screen.getByTestId('kid-mode-details-show-info'));
    fireEvent.press(screen.getByTestId('kid-mode-details-practice'));
    expect(screen.getByTestId('kid-mode-details-meta').props.children).toBe('Simulated demo · 20 seconds');
    expect(screen.queryByTestId('kid-mode-details-practice')).toBeNull();
    expect(preferred()).toEqual(['kid-mode-details-play']);
    fireEvent.press(screen.getByTestId('kid-mode-details-play'));
    expect(navigation.navigate).toHaveBeenCalledWith(Screens.PLAYER_SCREEN, expect.anything());
    returnFromPlayer();
    expect(preferred()).toEqual(['kid-mode-details-play']);
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(screen.getByTestId('kid-mode-details-info')).toBeTruthy();
    expect(preferred()).toEqual(['kid-mode-details-practice']);
    fireEvent.press(screen.getByTestId('kid-mode-details-info-back'));
    expect(preferred()).toEqual(['kid-mode-details-show-info']);
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(preferred()).toEqual(['kid-mode-home-more-info']);
  });

  it('remote Back restores More info after the demo, then closes it before leaving Details', async () => {
    const platform = jest.spyOn(Platform, 'isTV', 'get').mockReturnValue(true);
    let handlers: Array<() => boolean | null | undefined> = [];
    const subscription = jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_, handler) => {
      handlers.push(handler);
      return { remove: () => { handlers = handlers.filter(one => one !== handler); } };
    });
    const back = () => act(() => { expect([...handlers].reverse().some(handler => handler())).toBe(true); });
    try {
      await startShelf(regressionCatalog());
      fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
      fireEvent.press(screen.getByTestId('kid-mode-details-show-info'));
      fireEvent.press(screen.getByTestId('kid-mode-details-practice'));
      back();
      expect(preferred()).toEqual(['kid-mode-details-practice']);
      back();
      expect(preferred()).toEqual(['kid-mode-details-show-info']);
      back();
      expect(preferred()).toEqual(['kid-mode-home-more-info']);
    } finally { subscription.mockRestore(); platform.mockRestore(); }
  });

  it('Watch, then a title from How it works: Back returns to How it works, not Watch', async () => {
    const { returnFromPlayer } = await startShelf();
    fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
    returnFromPlayer();
    fireEvent.press(screen.getByTestId('kid-mode-home-learn'));
    fireEvent.press(screen.getByTestId('picture-hold-playback-check'));
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(preferred()).toEqual(['kid-mode-home-learn']);
  });

  it('Watch, Back, then Details and Back: the latest control wins each time', async () => {
    const { returnFromPlayer } = await startShelf();
    fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
    returnFromPlayer();
    fireEvent.press(screen.getByTestId('kid-mode-home-more-info'));
    fireEvent.press(screen.getByTestId('kid-mode-details-back'));
    expect(preferred()).toEqual(['kid-mode-home-more-info']);
    fireEvent.press(screen.getByTestId('kid-mode-home-watch'));
    returnFromPlayer();
    expect(preferred()).toEqual(['kid-mode-home-watch']);
  });
});

describe('a featured title that is also on the poster shelf', () => {
  // Titles without hero art are listed as posters as well; the first one leads.
  const make = (id: string): CheckedTitle => ({
    title: { id, title: id, uri: `${id}.mp4` },
    status: 'verified',
    verifiedProfiles: ['wcag', 'broadcast'],
    intervals: [],
  } as unknown as CheckedTitle);
  const shelf = (control?: 'watch' | 'details' | 'poster') => (
    <KidHomeScreen titles={[make('first'), make('second')]} onOpen={jest.fn()} onPlay={jest.fn()}
      returnFocusId="first" returnFocusControl={control} />
  );

  it.each([
    ['watch', 'kid-home-watch'],
    ['details', 'kid-home-more-info'],
    ['poster', 'kid-home-poster-first'],
  ] as const)('returning from %s focuses only that control', (control, expected) => {
    render(shelf(control));
    expect(screen.getByTestId('kid-home-poster-first')).toBeTruthy();
    expect(preferred()).toEqual([expected]);
  });

  it('reports which control was pressed before opening or starting the title', () => {
    const calls: string[] = [];
    const onOpen = jest.fn((entry: CheckedTitle) => calls.push(`open ${entry.title.id}`));
    const onPlay = jest.fn((entry: CheckedTitle) => calls.push(`play ${entry.title.id}`));
    const onLaunchControl = jest.fn((control: string) => calls.push(control));
    render(<KidHomeScreen titles={[make('first'), make('second')]} onOpen={onOpen} onPlay={onPlay}
      onLaunchControl={onLaunchControl} />);
    fireEvent.press(screen.getByTestId('kid-home-watch'));
    fireEvent.press(screen.getByTestId('kid-home-more-info'));
    fireEvent.press(screen.getByTestId('kid-home-poster-second'));
    expect(calls).toEqual(['watch', 'play first', 'details', 'open first', 'poster', 'open second']);
    // The callbacks the shelf already had keep their one argument.
    expect(onOpen.mock.calls.every((call) => call.length === 1)).toBe(true);
    expect(onPlay.mock.calls.every((call) => call.length === 1)).toBe(true);
  });
});
