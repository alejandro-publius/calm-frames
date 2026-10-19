import React from 'react';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { fireEvent, render } from '@testing-library/react-native';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { titlePresentation, FOREST_SOURCE_SHA256 } from '../../src/calmframes/TitleArtwork';
import { createPackagedLibrary, createApprovedLibrary, packagedLibrary, ACADIA_SOURCE_SHA256 } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { bakedAmbientForRendition } from '../../src/calmframes/approvedBakedAmbient';
import { guardedParamsFor, titleDataFor, defaultCatalog } from '../../src/screens/KidModeScreen';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
const raw = readFileSync(resolve(__dirname, '../../../results/forest-candidate-2026-10-18/candidate-catalog.json'), 'utf8');
// Compare the retained exact candidate against the now-approved production catalog.
const candidate = createPackagedLibrary(raw);
const title = candidate.titles(DEFAULT_SETTINGS)[0];
const nowMs = Date.parse(JSON.parse(title.maps!.wcag!).created_utc) + 60000;
const forest = checkTitle(title, { settings: DEFAULT_SETTINGS, publicKeyBase64: candidate.publicKeyBase64, nowMs });
const acadia = checkedShelf().find(entry => entry.title.sha256 === ACADIA_SOURCE_SHA256)!;
afterEach(() => jest.restoreAllMocks());

it.each(PRESET_NAMES)('the real signed %s preview retains duration, identity and empty findings', preset => {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const item = candidate.titles(settings)[0];
  const checked = checkTitle(item, { settings, publicKeyBase64: candidate.publicKeyBase64, nowMs });
  expect(candidate.problem).toBeNull(); expect(checked.status).toBe('verified');
  expect(checked.segments).toEqual([]); expect(item.durationMs).toBe(12000);
  expect(item.sha256).toBe(FOREST_SOURCE_SHA256); expect(item.title).toBe('Forest creek at Redwood');
  expect(item.textTrack).toBeUndefined();
  expect(candidate.acceptsRoute(titleDataFor(checked), guardedParamsFor(checked, settings))).toBe(true);
  expect(bakedAmbientForRendition(item.renditionSha256, preset)).toBeNull();
});
it('approves only the exact forest catalog and rejects other content under the same signer', () => {
  expect(defaultCatalog().some(item => item.sha256 === FOREST_SOURCE_SHA256)).toBe(true);
  expect(packagedLibrary.publicKeyFor(title, DEFAULT_SETTINGS)).toBe(candidate.publicKeyBase64);
  expect(packagedLibrary.acceptsRoute(titleDataFor(forest), guardedParamsFor(forest, DEFAULT_SETTINGS))).toBe(true);
  expect(checkTitle(title, { settings: DEFAULT_SETTINGS, publicKeyBase64: packagedLibrary.publicKeyFor(acadia.title, DEFAULT_SETTINGS)!, nowMs }).status).toBe('failed');
  expect(createApprovedLibrary(raw).problem).toBeNull();
  expect(createApprovedLibrary(raw + ' ').titles(DEFAULT_SETTINGS)).toEqual([]);
  const other = JSON.parse(raw); other.titles[0].id = 'prepared-unapproved';
  expect(createApprovedLibrary(JSON.stringify(other)).titles(DEFAULT_SETTINGS)).toEqual([]);
  expect(packagedLibrary.acceptsRoute({ ...titleDataFor(forest), id: 'prepared-unapproved' }, guardedParamsFor(forest, DEFAULT_SETTINGS))).toBe(false);
  expect(packagedLibrary.publicKeyFor({ ...title, renditionSha256: 'a'.repeat(64) }, DEFAULT_SETTINGS)).toBeNull();
});
it('uses the existing content rail without playing on focus or changing ambient registration', () => {
  const play = jest.fn(), open = jest.fn();
  const ambient = bakedAmbientForRendition(acadia.title.renditionSha256, DEFAULT_SETTINGS.preset);
  const screen = render(<KidHomeScreen titles={[acadia, forest]} onOpen={open} onPlay={play} />);
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Acadia');
  fireEvent(screen.getByTestId(`kid-home-poster-${title.id}`), 'focus');
  expect(open).not.toHaveBeenCalled(); expect(play).not.toHaveBeenCalled();
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Forest creek at Redwood');
  expect(screen.getByTestId(`kid-home-poster-qualifier-${title.id}`).props.children).toBe('Nature audio · 12 sec');
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Forest creek at Redwood');
  expect(screen.getByTestId('coastal-world')).toBeTruthy();
  expect(screen.queryAllByTestId(/^kid-home-poster-(?!image-|title-|qualifier-)/)).toHaveLength(2);
  fireEvent.press(screen.getByTestId('kid-home-watch')); expect(play).toHaveBeenCalledWith(forest);
  fireEvent.press(screen.getByTestId('kid-home-more-info')); expect(open).toHaveBeenCalledWith(forest);
  fireEvent(screen.getByTestId(`kid-home-poster-${acadia.title.id}`), 'focus');
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Acadia');
  expect(bakedAmbientForRendition(acadia.title.renditionSha256, DEFAULT_SETTINGS.preset)).toBe(ambient);
});
it.each(['watch', 'details', 'poster'] as const)('retains the preview and a single %s return focus', control => {
  const screen = render(<KidHomeScreen titles={[acadia, forest]} onOpen={jest.fn()} returnFocusId={title.id} returnFocusControl={control} />);
  const id = control === 'watch' ? 'kid-home-watch' : control === 'details' ? 'kid-home-more-info' : `kid-home-poster-${title.id}`;
  // The cards name the videos; what Watch will play is what it announces.
  expect(screen.getByTestId('kid-home-watch').props.accessibilityLabel).toBe('Watch: Forest creek at Redwood');
  expect(screen.getByTestId(id).props.hasTVPreferredFocus).toBe(true);
  expect(screen.getAllByRole('button').filter(button => button.props.hasTVPreferredFocus)).toHaveLength(1);
});
it('shows duration, nature-audio/once wording and source attribution in the approved Details flow', () => {
  const play = jest.fn(), back = jest.fn();
  const screen = render(<TitleDetailsScreen entry={forest} onPlay={play} onBack={back} />);
  expect(screen.getByTestId('title-details-meta').props.children).toBe('12 seconds · Nature sounds · Plays once');
  expect(screen.getByTestId('title-details-play').props.accessibilityLabel).toBe('Watch: Forest creek at Redwood');
  fireEvent.press(screen.getByTestId('title-details-play')); expect(play).toHaveBeenCalledWith(forest);
  fireEvent.press(screen.getByTestId('title-details-show-info'));
  expect(screen.getByTestId('title-details-attribution').props.children).toContain('NPS: G Litten');
  expect(screen.getByTestId('title-details-attribution').props.children).toContain('Public-domain footage');
  fireEvent.press(screen.getByTestId('title-details-info-back'));
  fireEvent.press(screen.getByTestId('title-details-back')); expect(back).toHaveBeenCalledTimes(1);
});
it('does not apply excerpt claims to another source/duration or list an unverified preview', () => {
  expect(titlePresentation({ ...title, durationMs: 10000 }).runtime).toBeUndefined();
  expect(titlePresentation({ ...title, sha256: 'a'.repeat(64) }).attribution).toBeUndefined();
  const screen = render(<KidHomeScreen titles={[acadia, { ...forest, status: 'failed' }]} onOpen={jest.fn()} />);
  expect(screen.queryByTestId(`kid-home-poster-${title.id}`)).toBeNull();
});
