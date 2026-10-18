/**
 * Home with one featured video, and Home with several.
 *
 * With Acadia alone there is nothing to choose between, so the hero stands
 * alone: title, running time in words, one line saying what the app does,
 * Watch and Details. With two prepared videos the rail returns and every one
 * is a card. A lone title without hero art keeps its poster, because that is
 * the only place its own picture appears. Whatever is on screen, exactly one
 * control asks for the remote's focus.
 *
 * Seen to fail, Oct 16 2026: with the rail rule reverted to listing every
 * main video, the first test found a "Choose a video" heading and one card.
 */
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { BackHandler } from 'react-native';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { HOME_BENEFIT_LINE } from '../../src/calmframes/copy';
import { ACADIA_SOURCE_SHA256 } from '../../src/calmframes/packagedLibrary';
import { Profile } from '../../src/calmframes/profiles';
import { CheckedTitle } from '../../src/calmframes/titleStatus';
import { checkedShelf } from './shelfFixtures';

// Retain this two-title regression fixture; the real consumer pair is tested in otterPreview.
const titles = checkedShelf().filter(entry => entry.title.title !== 'Otters · short preview');
const acadia = titles.find((entry) => entry.title.sha256 === ACADIA_SOURCE_SHA256)!;
const consumer = [acadia];
const profiles = [{ id: 'everyone', name: 'Everyone' }, { id: 'robin', name: 'Robin' }] as unknown as Profile[];

function preferred(): string[] {
  const ids = screen.UNSAFE_root
    .findAll((node) => node.props.hasTVPreferredFocus === true && typeof node.props.testID === 'string')
    .map((node) => node.props.testID as string);
  return [...new Set(ids)];
}

const posters = () => screen.queryAllByTestId(/^kid-home-poster-(?!image-|title-|qualifier-)/);

let handlers: Array<() => boolean | null | undefined> = [];
beforeEach(() => {
  handlers = [];
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_, handler) => {
    handlers.push(handler);
    return { remove: () => { handlers = handlers.filter((one) => one !== handler); } };
  });
});
afterEach(() => jest.restoreAllMocks());
const back = () => act(() => { expect([...handlers].reverse().some((handler) => handler() === true)).toBe(true); });

describe('one featured video', () => {
  it('shows the hero alone, with the runtime and actions, without a persistent explanatory line', () => {
    render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} />);
    expect(screen.getByTestId('kid-home-video-title').props.children).toBe('Acadia');
    // The fixture's duration rounds the way describeHiddenTotal rounds it; the words are what matter.
    expect(screen.getByTestId('kid-home-video-meta').props.children).toBe(`${Math.round((acadia.title.durationMs ?? 0) / 1000)} seconds`);
    expect(screen.queryByText(HOME_BENEFIT_LINE)).toBeNull();
    expect(HOME_BENEFIT_LINE).toBe('Watch with flashing scenes covered.');
    expect(screen.queryByText('Choose a video')).toBeNull();
    expect(posters()).toHaveLength(0);
    expect(screen.getByTestId('kid-home-watch')).toBeTruthy();
    expect(screen.getByTestId('kid-home-more-info')).toBeTruthy();
    expect(screen.getByTestId('kid-home-learn')).toBeTruthy();
    expect(screen.getByTestId('kid-home-parent-area')).toBeTruthy();
    expect(preferred()).toEqual(['kid-home-watch']);
  });

  it('returning from a poster that is no longer on the rail puts focus on Watch', () => {
    render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} returnFocusId={acadia.title.id} returnFocusControl="poster" />);
    expect(posters()).toHaveLength(0);
    expect(preferred()).toEqual(['kid-home-watch']);
  });
});

describe('several videos', () => {
  it('brings the rail back with a card for every prepared video', () => {
    render(<KidHomeScreen titles={titles} onOpen={jest.fn()} onPlay={jest.fn()} />);
    expect(screen.getByText('Choose a video')).toBeTruthy();
    expect(posters()).toHaveLength(2);
    expect(preferred()).toEqual(['kid-home-watch']);
  });

  it('keeps the poster of a lone title that has no hero art of its own', () => {
    const plain = { title: { id: 'plain', title: 'Plain', uri: 'plain.mp4' }, status: 'verified', verifiedProfiles: ['wcag', 'broadcast'], segments: [], hiddenMs: 0 } as unknown as CheckedTitle;
    render(<KidHomeScreen titles={[plain]} onOpen={jest.fn()} />);
    expect(posters()).toHaveLength(1);
    expect(screen.getByTestId('kid-home-video-title').props.children).toBe('Plain');
  });
});

describe('exactly one control asks for focus', () => {
  const sequences: Array<[string, (view: ReturnType<typeof render>) => void, string[]]> = [
    ['at rest', () => undefined, ['kid-home-watch']],
    ['with How it works open', () => { fireEvent.press(screen.getByTestId('kid-home-learn')); }, ['picture-hold-dismiss']],
    ['after How it works is dismissed', () => { fireEvent.press(screen.getByTestId('kid-home-learn')); fireEvent.press(screen.getByTestId('picture-hold-dismiss')); }, ['kid-home-learn']],
    ['after Profiles then Back', () => { fireEvent.press(screen.getByTestId('kid-home-choose-profile')); back(); }, ['kid-home-choose-profile']],
    ['after Profiles, Back, then How it works', () => { fireEvent.press(screen.getByTestId('kid-home-choose-profile')); back(); fireEvent.press(screen.getByTestId('kid-home-learn')); }, ['picture-hold-dismiss']],
  ];
  it.each(sequences)('%s', (_name, drive, expected) => {
    const view = render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()}
      profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
    drive(view);
    expect(preferred()).toEqual(expected);
  });

  it('back from Parents, then How it works: only the explanation Back asks', () => {
    render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()}
      returnFocusControl="parent" profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
    expect(preferred()).toEqual(['kid-home-parent-area']);
    fireEvent.press(screen.getByTestId('kid-home-learn'));
    expect(preferred()).toEqual(['picture-hold-dismiss']);
    fireEvent.press(screen.getByTestId('picture-hold-dismiss'));
    expect(preferred()).toEqual(['kid-home-learn']);
  });

  it('an empty shelf asks for Parents alone, and a saving shelf asks for nothing', () => {
    render(<KidHomeScreen titles={[]} onOpen={jest.fn()} onOpenParentArea={jest.fn()} />);
    expect(preferred()).toEqual(['kid-home-parent-area']);
    screen.unmount();
    render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} onOpenParentArea={jest.fn()} saving />);
    expect(preferred()).toEqual([]);
  });
});
