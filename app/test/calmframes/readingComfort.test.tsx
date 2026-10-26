/** Fictional profiles only. Reading preferences never change protection or identity. */
import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { ScrollView, StyleSheet } from 'react-native';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import CalmTouchable from '../../src/calmframes/CalmTouchable';
import { CALM_SPACE, scale } from '../../src/calmframes/calmStyles';
import { wrapText } from '../../src/calmframes/uiLayout';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { loadHousehold, saveHousehold, SavedHousehold, validateHousehold } from '../../src/calmframes/householdStorage';
import {
  addProfile, clampFamily, effectiveSettings, Family, newFamily, renameProfile,
  setProfileReadingComfort, setProfileSettings,
} from '../../src/calmframes/profiles';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({}));

const family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');
const gate = setPin(emptyPinGate(), '1357', 'comfort-fixture');
const record: SavedHousehold = { version: 1, family, gate };
const press = (id: string) => fireEvent.press(screen.getByTestId(id));
const flush = () => act(async () => { await Promise.resolve(); });
const style = (id: string) => StyleSheet.flatten(screen.getByTestId(id).props.style);
const control = (id: string) => screen.UNSAFE_getAllByType(CalmTouchable).find(node => node.props.testID === id)!;
type Props = React.ComponentProps<typeof ParentAreaScreen>;

function openParents(overrides: Partial<Props> = {}) {
  const props: Props = {
    gate: setPin(emptyPinGate(), '1357', 'comfort-fixture', 4),
    onGateChange: jest.fn(), settings: DEFAULT_SETTINGS, onSettingsChange: jest.fn(),
    log: emptyHideLog(), family, onFamilyChange: jest.fn(),
    onProfilePreferencesChange: jest.fn(async () => true),
    titles: [], nowMs: () => 0, onBack: jest.fn(), ...overrides,
  };
  const view = render(<ParentAreaScreen {...props} />);
  for (const digit of '1357') press(`parent-area-key-${digit}`);
  return { view, props };
}

describe('Reading comfort persistence and isolation', () => {
  it('defaults new and legacy profiles off without changing the household record', () => {
    expect(family.profiles.every(profile => profile.readingComfortEnabled === false)).toBe(true);
    const legacy = JSON.parse(JSON.stringify(record));
    for (const profile of legacy.family.profiles) delete profile.readingComfortEnabled;
    expect(validateHousehold(legacy)).toEqual(record);
  });

  it('changes only the named kid and preserves protection through later edits', () => {
    const next = setProfileReadingComfort(family, 'profile-2', true);
    expect(next).toEqual({ ...family, profiles: [family.profiles[0], { ...family.profiles[1], readingComfortEnabled: true }] });
    expect(effectiveSettings(next, next.profiles[1])).toEqual(effectiveSettings(family, family.profiles[1]));
    expect(setProfileReadingComfort(family, 'missing', true)).toBe(family);
    expect(clampFamily(next)).toEqual(next);
    expect(renameProfile(next, 'profile-2', 'Ash').profiles[1].readingComfortEnabled).toBe(true);
    expect(setProfileSettings(next, 'profile-2', { preset: 'extra-cautious' }).profiles[1].readingComfortEnabled).toBe(true);
    expect(addProfile(next, 'Lee').profiles[2].readingComfortEnabled).toBe(false);
    expect(setProfileReadingComfort(next, 'profile-2', false)).toEqual(family);
  });

  it('roundtrips a single enabled preference without changing PIN, floor or active profile', async () => {
    let disk: string | null = null;
    const storage = { getItem: async () => disk, setItem: async (_key: string, text: string) => { disk = text; } };
    const enabled = { ...record, family: { ...family, profiles: [family.profiles[0], { ...family.profiles[1], readingComfortEnabled: true }] } };
    await saveHousehold(storage, enabled);
    expect(await loadHousehold(storage)).toEqual(enabled);
    await saveHousehold(storage, record);
    expect(await loadHousehold(storage)).toEqual(record);
  });

  it.each(['true', 1, null, {}])('rejects a malformed stored preference: %p', value => {
    const bad = JSON.parse(JSON.stringify(record));
    bad.family.profiles[1].readingComfortEnabled = value;
    expect(() => validateHousehold(bad)).toThrow('Invalid household profile');
    expect(clampFamily(bad.family).profiles[1].readingComfortEnabled).toBe(false);
  });
});

describe('Reading comfort in Parents', () => {
  it('is offered only behind the PIN, for a kid and with a result-aware save adapter', () => {
    const { view, props } = openParents();
    expect(screen.queryByTestId('parent-area-reading-comfort')).toBeNull();
    press('parent-area-profiles-profile-2');
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityRole).toBe('switch');
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityState.checked).toBe(false);
    view.rerender(<ParentAreaScreen {...props} onProfilePreferencesChange={undefined} />);
    expect(screen.queryByTestId('parent-area-reading-comfort')).toBeNull();
    view.unmount();
    render(<ParentAreaScreen {...props} />);
    expect(screen.queryByTestId('parent-area-reading-comfort')).toBeNull();
  });

  it('waits for the saved family, blocks duplicate presses and retains a single focus target', async () => {
    let complete!: (accepted: boolean) => void;
    const save = jest.fn((_next: Family) => new Promise<boolean>(resolve => { complete = resolve; }));
    const { view, props } = openParents({ onProfilePreferencesChange: save });
    press('parent-area-profiles-profile-2');
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'focus');
    const toggle = control('parent-area-reading-comfort').props.onPress;
    act(() => { toggle(); toggle(); });
    expect(save).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityState).toMatchObject({ checked: false, disabled: true });
    expect(screen.getByTestId('parent-area-reading-comfort').props.focusable).toBe(true);
    expect(screen.getByTestId('parent-area-profiles-profile-1').props.accessibilityState.disabled).toBe(true);
    await act(async () => complete(true));
    // A returned true is not an optimistic toggle. The persisted family owns On.
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityState.checked).toBe(false);
    const next = save.mock.calls[0][0] as Family;
    view.rerender(<ParentAreaScreen {...props} family={next} />);
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityState.checked).toBe(true);
    expect(screen.getByTestId('parent-area-reading-comfort').props.hasTVPreferredFocus).toBe(true);
    expect(screen.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);
    expect(style('parent-area-room').fontSize).toBe(scale(40));
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'blur');
    press('parent-area-profiles-profile-1');
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityState.checked).toBe(false);
    expect(screen.getByTestId('parent-area-reading-comfort').props.hasTVPreferredFocus).toBe(false);
    expect(style('parent-area-room').fontSize).toBe(scale(36));
  });

  it('does not rearm the page-top Back when the saved switch blurs', async () => {
    openParents();
    press('parent-area-profiles-profile-2');
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'focus');
    press('parent-area-reading-comfort');
    await flush();
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'blur');
    expect(screen.getByTestId('parent-area-back-top').props.hasTVPreferredFocus).toBe(false);
  });

  it.each([720, 1080])('keeps the enlarged switch and state in view after layout at %s', height => {
    const scroll = jest.spyOn(ScrollView.prototype, 'scrollTo').mockImplementation(() => {});
    const { view, props } = openParents();
    press('parent-area-profiles-profile-2');
    const layout = (id: string, y: number, h: number) => fireEvent(screen.getByTestId(id), 'layout', {
      nativeEvent: { layout: { x: 0, y, width: 1000, height: h } },
    });
    layout('parent-area-open', 0, height);
    layout('parent-area-reading-group', 1500, 250);
    layout('parent-area-reading-comfort', 50, 180);
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'focus');
    scroll.mockClear();
    view.rerender(<ParentAreaScreen {...props} family={setProfileReadingComfort(family, 'profile-2', true)} />);
    layout('parent-area-reading-group', 1800, 330);
    layout('parent-area-reading-comfort', 60, 250);
    expect(scroll).toHaveBeenCalled();
    const last = scroll.mock.calls[scroll.mock.calls.length - 1][0] as { y: number; animated: boolean };
    expect(last.animated).toBe(false);
    expect(1860 - last.y).toBeGreaterThanOrEqual(0);
    expect(2110 - last.y).toBeLessThanOrEqual(height);
    scroll.mockClear();
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'blur');
    layout('parent-area-reading-group', 1900, 330);
    expect(scroll).not.toHaveBeenCalled();
    scroll.mockRestore();
  });

  it.each([720, 1080])('reconciles an actual native scroll clamped before enlarged layout at %s', height => {
    const scroll = jest.spyOn(ScrollView.prototype, 'scrollTo').mockImplementation(() => {});
    const { view, props } = openParents();
    press('parent-area-profiles-profile-2');
    const layout = (id: string, y: number, h: number) => fireEvent(screen.getByTestId(id), 'layout', {
      nativeEvent: { layout: { x: 0, y, width: 1000, height: h } },
    });
    layout('parent-area-open', 0, height);
    layout('parent-area-reading-group', 1500, 250);
    layout('parent-area-reading-comfort', 50, 180);
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'focus');
    view.rerender(<ParentAreaScreen {...props} family={setProfileReadingComfort(family, 'profile-2', true)} />);
    layout('parent-area-reading-group', 1800, 330);
    layout('parent-area-reading-comfort', 60, 250);
    // The native focus/scroll pass reports its actual position after the
    // requested correction. A requested offset is not an observed offset.
    scroll.mockClear();
    fireEvent.scroll(screen.getByTestId('parent-area-open'), { nativeEvent: { contentOffset: { x: 0, y: 1700 - height } } });
    expect(scroll).toHaveBeenCalled();
    const last = scroll.mock.calls[scroll.mock.calls.length - 1][0] as { y: number; animated: boolean };
    expect(2110 - last.y).toBeLessThanOrEqual(height);
    scroll.mockClear();
    fireEvent.scroll(screen.getByTestId('parent-area-open'), { nativeEvent: { contentOffset: { x: 0, y: last.y } } });
    expect(scroll).not.toHaveBeenCalled();
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'blur');
    fireEvent.scroll(screen.getByTestId('parent-area-open'), { nativeEvent: { contentOffset: { x: 0, y: 0 } } });
    expect(scroll).not.toHaveBeenCalled();
    scroll.mockRestore();
  });

  it('does not steal focus if the remote moved away during the save', async () => {
    let complete!: (accepted: boolean) => void;
    const save = jest.fn((_next: Family) => new Promise<boolean>(resolve => { complete = resolve; }));
    openParents({ onProfilePreferencesChange: save });
    press('parent-area-profiles-profile-2');
    fireEvent(screen.getByTestId('parent-area-reading-comfort'), 'focus');
    press('parent-area-reading-comfort');
    // The test library suppresses all events on accessibility-disabled nodes,
    // but native D-pad focus can still leave a focusable pending switch.
    act(() => control('parent-area-reading-comfort').props.onBlur());
    await act(async () => complete(true));
    expect(screen.getByTestId('parent-area-reading-comfort').props.hasTVPreferredFocus).toBe(false);
  });

  it.each(['false', 'rejection'] as const)('keeps the old preference after %s and allows retry', async outcome => {
    const save = jest.fn(async (_next: Family) => {
      if (outcome === 'rejection') throw new Error('fictional write failure');
      return false;
    });
    openParents({ onProfilePreferencesChange: save });
    press('parent-area-profiles-profile-2');
    press('parent-area-reading-comfort');
    await flush();
    expect(screen.getByTestId('parent-area-reading-comfort').props.accessibilityState.checked).toBe(false);
    expect(screen.getByTestId('parent-area-reading-comfort-failure').props.children).toBe('Reading comfort was not saved. Choose it again to retry.');
    expect(screen.getByTestId('parent-area-reading-comfort').props.hasTVPreferredFocus).toBe(true);
    press('parent-area-reading-comfort');
    await flush();
    expect(save).toHaveBeenCalledTimes(2);
    expect(save.mock.calls[1][0]).toEqual(save.mock.calls[0][0]);
  });
});

describe('bounded Reading comfort typography', () => {
  it.each([1080, 720])('keeps the enlarged reading stop within a %p-high viewport under the conservative text ruler', height => {
    const entry = checkedShelf().find(item => item.title.title === 'Harbor story (prepared locally)')!;
    render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} readingComfortEnabled />);
    press('title-details-show-info');
    const stop = screen.getByTestId('title-details-info-reading');
    const box = StyleSheet.flatten(stop.props.style);
    let ancestor = stop.parent;
    while (ancestor && typeof StyleSheet.flatten(ancestor.props.style)?.maxWidth !== 'number') ancestor = ancestor.parent;
    expect(ancestor).not.toBeNull();
    const width = StyleSheet.flatten(ancestor!.props.style).maxWidth - 2 * (box.padding + box.borderWidth);
    // Native host names are wider than React's DOM-oriented ElementType union.
    const paragraphs = stop.findAll(node => typeof node.type === 'string' && (node.type as string) === 'Text');
    expect(paragraphs.length).toBeGreaterThan(1);
    const textHeight = paragraphs.reduce((total, node) => {
      const textStyle = StyleSheet.flatten(node.props.style);
      const words = node.children.filter(child => typeof child === 'string').join(' ');
      return total + wrapText(words, textStyle.fontSize, width).lines * textStyle.lineHeight;
    }, 0);
    const designHeight = (textHeight + (paragraphs.length - 1) * box.gap + 2 * (box.padding + box.borderWidth)) / scale(1);
    expect(designHeight * height / 1080).toBeLessThan(height * (1 - 2 * CALM_SPACE.SAFE_Y / 1080));
  });

  it('does not change the name editor when the edited kid has Reading comfort on', () => {
    const { view, props } = openParents({ onRenameProfile: jest.fn(async () => true) });
    press('parent-area-profiles-profile-2');
    press('parent-area-rename-profile');
    const normal = view.toJSON();
    view.rerender(<ParentAreaScreen {...props} family={setProfileReadingComfort(family, 'profile-2', true)} />);
    expect(view.toJSON()).toEqual(normal);
    expect(screen.queryByTestId('parent-area-reading-comfort')).toBeNull();
  });

  it('changes help and spacing while retaining Parents disclaimer and profile panel geometry', () => {
    const { view, props } = openParents();
    press('parent-area-profiles-profile-2');
    const disclaimer = style('parent-area-explainer-line-0');
    const profileRule = style('parent-area-profile-rule');
    const normalRoom = style('parent-area-room');
    const normalRow = style('parent-area-preset-wcag');
    view.rerender(<ParentAreaScreen {...props} family={setProfileReadingComfort(family, 'profile-2', true)} />);
    expect(style('parent-area-explainer-line-0')).toEqual(disclaimer);
    expect(style('parent-area-profile-rule')).toEqual(profileRule);
    expect(style('parent-area-room').fontSize).toBeGreaterThan(normalRoom.fontSize);
    expect(style('parent-area-room').lineHeight).toBeGreaterThan(normalRoom.lineHeight);
    expect(style('parent-area-preset-wcag').paddingVertical).toBeGreaterThan(normalRow.paddingVertical);
  });

  it('enlarges More info only, preserving Watch geometry, safety wording, reading stop and Back focus', () => {
    const entry = checkedShelf().find(item => item.title.title === 'Harbor story (prepared locally)')!;
    const props = { entry, onPlay: jest.fn(), onBack: jest.fn() };
    const view = render(<TitleDetailsScreen {...props} />);
    const watch = view.toJSON();
    view.rerender(<TitleDetailsScreen {...props} readingComfortEnabled />);
    expect(view.toJSON()).toEqual(watch);
    press('title-details-show-info');
    const enabledStop = screen.getByTestId('title-details-info-reading');
    const enabledGap = StyleSheet.flatten(enabledStop.props.style).gap;
    const safety = screen.getByTestId('title-details-info-safety');
    const safetyText = safety.props.children;
    expect(StyleSheet.flatten(safety.props.style).fontSize).toBe(scale(40));
    expect(enabledStop.props.focusable).toBe(true);
    expect(screen.getByTestId('title-details-info-back').props.hasTVPreferredFocus).toBe(true);
    view.rerender(<TitleDetailsScreen {...props} readingComfortEnabled={false} />);
    expect(screen.getByTestId('title-details-info-safety').props.children).toBe(safetyText);
    expect(style('title-details-info-safety').fontSize).toBe(scale(36));
    expect(style('title-details-info-reading').gap).toBeLessThan(enabledGap);
    press('title-details-technical');
    const technical = view.toJSON();
    view.rerender(<TitleDetailsScreen {...props} readingComfortEnabled />);
    expect(view.toJSON()).toEqual(technical);
  });
});
