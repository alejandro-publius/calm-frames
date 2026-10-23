import React from 'react';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { fireEvent, render } from '@testing-library/react-native';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { titlePresentation, SEA_OTTER_SOURCE_SHA256 } from '../../src/calmframes/TitleArtwork';
import { createPackagedLibrary, createApprovedLibrary, packagedLibrary, ACADIA_SOURCE_SHA256 } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { bakedAmbientForRendition } from '../../src/calmframes/approvedBakedAmbient';
import { guardedParamsFor, titleDataFor, defaultCatalog } from '../../src/screens/KidModeScreen';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
const raw = readFileSync(resolve(__dirname, '../../../results/sea-otters-2026-10-18/candidate-catalog.json'), 'utf8');
// Compare the retained exact candidate against the now-approved production catalog.
const candidate = createPackagedLibrary(raw);
const title = candidate.titles(DEFAULT_SETTINGS)[0];
const nowMs = Date.parse(JSON.parse(title.maps!.wcag!).created_utc) + 60000;
const otter = checkTitle(title, { settings: DEFAULT_SETTINGS, publicKeyBase64: candidate.publicKeyBase64, nowMs });
const acadia = checkedShelf().find(entry => entry.title.sha256 === ACADIA_SOURCE_SHA256)!;
afterEach(() => jest.restoreAllMocks());

it.each(PRESET_NAMES)('the real signed %s preview retains duration, identity and empty findings', preset => {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const item = candidate.titles(settings)[0];
  const checked = checkTitle(item, { settings, publicKeyBase64: candidate.publicKeyBase64, nowMs });
  expect(candidate.problem).toBeNull(); expect(checked.status).toBe('verified');
  expect(checked.segments).toEqual([]); expect(item.durationMs).toBe(19986.633);
  expect(item.sha256).toBe(SEA_OTTER_SOURCE_SHA256); expect(item.title).toBe('Sea otters in Alaska');
  expect(item.textTrack).toBeUndefined();
  expect(candidate.acceptsRoute(titleDataFor(checked), guardedParamsFor(checked, settings))).toBe(true);
  expect(bakedAmbientForRendition(item.renditionSha256, preset)).toBeNull();
});
it('approves only the exact otter catalog and rejects other content under the same signer', () => {
  expect(defaultCatalog().some(item => item.sha256 === SEA_OTTER_SOURCE_SHA256)).toBe(true);
  expect(packagedLibrary.publicKeyFor(title, DEFAULT_SETTINGS)).toBe(candidate.publicKeyBase64);
  expect(packagedLibrary.acceptsRoute(titleDataFor(otter), guardedParamsFor(otter, DEFAULT_SETTINGS))).toBe(true);
  expect(checkTitle(title, { settings: DEFAULT_SETTINGS, publicKeyBase64: packagedLibrary.publicKeyFor(acadia.title, DEFAULT_SETTINGS)!, nowMs }).status).toBe('failed');
  expect(createApprovedLibrary(raw).problem).toBeNull();
  expect(createApprovedLibrary(raw + ' ').titles(DEFAULT_SETTINGS)).toEqual([]);
  const other = JSON.parse(raw); other.titles[0].id = 'prepared-unapproved';
  expect(createApprovedLibrary(JSON.stringify(other)).titles(DEFAULT_SETTINGS)).toEqual([]);
  expect(packagedLibrary.acceptsRoute({ ...titleDataFor(otter), id: 'prepared-unapproved' }, guardedParamsFor(otter, DEFAULT_SETTINGS))).toBe(false);
  expect(packagedLibrary.publicKeyFor({ ...title, renditionSha256: 'a'.repeat(64) }, DEFAULT_SETTINGS)).toBeNull();
});
it('uses the existing content rail without playing on focus or changing ambient registration', () => {
  const play = jest.fn(), open = jest.fn();
  const ambient = bakedAmbientForRendition(acadia.title.renditionSha256, DEFAULT_SETTINGS.preset);
  const screen = render(<KidHomeScreen titles={[acadia, otter]} onOpen={open} onPlay={play} />);
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Acadia');
  fireEvent(screen.getByTestId(`kid-home-poster-${title.id}`), 'focus');
  expect(open).not.toHaveBeenCalled(); expect(play).not.toHaveBeenCalled();
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Sea otters in Alaska');
  expect(screen.getByTestId(`kid-home-poster-qualifier-${title.id}`).props.children).toBe('Silent · 20 sec');
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Sea otters in Alaska');
  expect(screen.getByTestId('coastal-world')).toBeTruthy();
  expect(screen.queryAllByTestId(/^kid-home-poster-(?!image-|title-|qualifier-)/)).toHaveLength(2);
  fireEvent.press(screen.getByTestId('kid-home-watch')); expect(play).toHaveBeenCalledWith(otter);
  fireEvent.press(screen.getByTestId('kid-home-more-info')); expect(open).toHaveBeenCalledWith(otter);
  fireEvent(screen.getByTestId(`kid-home-poster-${acadia.title.id}`), 'focus');
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Acadia');
  expect(bakedAmbientForRendition(acadia.title.renditionSha256, DEFAULT_SETTINGS.preset)).toBe(ambient);
});
it.each(['watch', 'details', 'poster'] as const)('retains the preview and a single %s return focus', control => {
  const screen = render(<KidHomeScreen titles={[acadia, otter]} onOpen={jest.fn()} returnFocusId={title.id} returnFocusControl={control} />);
  const id = control === 'watch' ? 'kid-home-watch' : control === 'details' ? 'kid-home-more-info' : `kid-home-poster-${title.id}`;
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Sea otters in Alaska');
  expect(screen.getByTestId(id).props.hasTVPreferredFocus).toBe(true);
  expect(screen.getAllByRole('button').filter(button => button.props.hasTVPreferredFocus)).toHaveLength(1);
});
it('shows duration, silent/once wording and source attribution in the approved Details flow', () => {
  const play = jest.fn(), back = jest.fn();
  const screen = render(<TitleDetailsScreen entry={otter} onPlay={play} onBack={back} />);
  expect(screen.getByTestId('title-details-meta').props.children).toBe('20 seconds · Silent · Plays once');
  expect(screen.getByTestId('title-details-play').props.accessibilityLabel).toBe('Watch: Sea otters in Alaska');
  fireEvent.press(screen.getByTestId('title-details-play')); expect(play).toHaveBeenCalledWith(otter);
  fireEvent.press(screen.getByTestId('title-details-show-info'));
  expect(screen.getByTestId('title-details-attribution').props.children).toContain('NOAA Fisheries');
  expect(screen.getByTestId('title-details-attribution').props.children).toContain('Public-domain B-roll');
  fireEvent.press(screen.getByTestId('title-details-info-back'));
  fireEvent.press(screen.getByTestId('title-details-back')); expect(back).toHaveBeenCalledTimes(1);
});
it('does not apply excerpt claims to another source/duration or list an unverified preview', () => {
  expect(titlePresentation({ ...title, durationMs: 10000 }).runtime).toBeUndefined();
  expect(titlePresentation({ ...title, sha256: 'a'.repeat(64) }).attribution).toBeUndefined();
  const screen = render(<KidHomeScreen titles={[acadia, { ...otter, status: 'failed' }]} onOpen={jest.fn()} />);
  expect(screen.queryByTestId(`kid-home-poster-${title.id}`)).toBeNull();
});
