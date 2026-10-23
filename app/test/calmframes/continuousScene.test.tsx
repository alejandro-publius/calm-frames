/** Exact approved route and presentation contracts; no native playback is performed. */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { createHash } from 'crypto';
import fs from 'fs';
import path from 'path';
import { continuousEndingForRoute, MCWAY_DURATION_MS, MCWAY_RENDITION_SHA256, MCWAY_SOURCE_SHA256 } from '../../src/calmframes/continuousScene';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { ambientArtworkFor } from '../../src/calmframes/AmbientScene';
import { checkedShelf } from './shelfFixtures';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
import { guardedParamsFor, titleDataFor } from '../../src/screens/KidModeScreen';
import { checkTitle } from '../../src/calmframes/titleStatus';
import type { CheckedTitle } from '../../src/calmframes/titleStatus';

const mcway: CheckedTitle = { status: 'verified', segments: [], hiddenMs: 0, verifiedProfiles: ['wcag', 'broadcast'], title: {
  id: `prepared-${MCWAY_SOURCE_SHA256}`, title: 'McWay test fixture', uri: 'assets/raw/prepared-library/test/wcag.mp4',
  sha256: MCWAY_SOURCE_SHA256, renditionSha256: MCWAY_RENDITION_SHA256, durationMs: MCWAY_DURATION_MS,
} };
const guarded = { sha256: MCWAY_SOURCE_SHA256, renditionSha256: MCWAY_RENDITION_SHA256,
  durationMs: MCWAY_DURATION_MS, settings: DEFAULT_SETTINGS };

afterEach(() => jest.restoreAllMocks());

test('ending requires exact compiled route acceptance, edition and duration', () => {
  const accept = jest.spyOn(packagedLibrary, 'acceptsRoute').mockReturnValue(false);
  expect(continuousEndingForRoute(mcway.title, guarded)).toBeUndefined();
  accept.mockReturnValue(true);
  expect(continuousEndingForRoute(mcway.title, guarded)).toBeDefined();
  for (const change of [{ sha256: '0'.repeat(64) }, { renditionSha256: '0'.repeat(64) }, { durationMs: 12000 }]) {
    expect(continuousEndingForRoute(mcway.title, { ...guarded, ...change })).toBeUndefined();
  }
  expect(continuousEndingForRoute(mcway.title, undefined)).toBeUndefined();
});

test('ending image remains the extracted exact-rendition final frame', () => {
  const image = fs.readFileSync(path.resolve(__dirname, '../../assets/image/tv/mcway-final-frame.png'));
  expect(createHash('sha256').update(image).digest('hex')).toBe('feaef416d06e4b8d92359f6ef60d60694e341d921935480b42628113f840f1e4');
});

test('five-minute scene is explicit playback while old still choices remain available', () => {
  const others = checkedShelf().filter(entry => entry.title.sha256 !== MCWAY_SOURCE_SHA256 && ['coastal', 'forest', 'sea-otters'].includes(
    titlePresentation(entry.title).menuArt ?? titlePresentation(entry.title).art ?? ''));
  const play = jest.fn(); const still = jest.fn();
  const view = render(<KidHomeScreen titles={[mcway, ...others]} selectedTitleId={mcway.title.id}
    onOpen={jest.fn()} onPlay={play} onAmbient={still} />);
  expect(view.getByTestId('kid-home-islands')).toBeTruthy();
  expect(view.getByTestId('kid-home-environment-ocean-name')).toBeTruthy();
  expect(view.getByTestId('kid-home-environment-forest-name')).toBeTruthy();
  expect(ambientArtworkFor(mcway)).toBeUndefined();
  const coast = others.find(entry => titlePresentation(entry.title).art === 'coastal')!;
  const one = StyleSheet.flatten(view.getByTestId(`kid-home-poster-${mcway.title.id}`).props.style);
  const two = StyleSheet.flatten(view.getByTestId(`kid-home-poster-${coast.title.id}`).props.style);
  expect(one.top + one.height).toBeLessThan(two.top);
  expect(play).not.toHaveBeenCalled();
  fireEvent.press(view.getByTestId('kid-home-watch'));
  expect(play).toHaveBeenCalledWith(mcway);
  expect(still).not.toHaveBeenCalled();
  for (const entry of others) expect(view.getByTestId(`kid-home-poster-${entry.title.id}`)).toBeTruthy();
});

test.each(PRESET_NAMES)('real approved %s route retains the final frame at its authenticated duration', preset => {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const title = packagedLibrary.consumerTitles(settings).find(item => item.sha256 === MCWAY_SOURCE_SHA256)!;
  expect(title).toBeDefined();
  expect(title.durationMs).toBe(MCWAY_DURATION_MS);
  const checked = checkTitle(title, { settings,
    publicKeyBase64: packagedLibrary.publicKeyFor(title, settings)!,
    nowMs: Date.parse(JSON.parse(title.maps!.wcag!).created_utc) + 60000 });
  expect(checked.status).toBe('verified');
  expect(checked.segments).toEqual([]);
  const data = titleDataFor(checked), guard = guardedParamsFor(checked, settings);
  expect(continuousEndingForRoute(data, guard)).toBeDefined();
  expect(continuousEndingForRoute({ ...data, uri: data.uri + '.substituted' }, guard)).toBeUndefined();
});
