/** Synthetic route/UI contracts; these do not approve or play a new edition. */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { createHash } from 'crypto';
import fs from 'fs';
import path from 'path';
import { continuousEndingForRoute, MCWAY_RENDITION_SHA256, MCWAY_SOURCE_SHA256 } from '../../src/calmframes/continuousScene';
import { packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import { ambientArtworkFor } from '../../src/calmframes/AmbientScene';
import { checkedShelf } from './shelfFixtures';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
import type { CheckedTitle } from '../../src/calmframes/titleStatus';

const mcway: CheckedTitle = { status: 'verified', segments: [], title: {
  id: `prepared-${MCWAY_SOURCE_SHA256}`, title: 'McWay test fixture', uri: 'assets/raw/prepared-library/test/wcag.mp4',
  sha256: MCWAY_SOURCE_SHA256, renditionSha256: MCWAY_RENDITION_SHA256, durationMs: 300000,
} };
const guarded = { sha256: MCWAY_SOURCE_SHA256, renditionSha256: MCWAY_RENDITION_SHA256,
  durationMs: 300000, settings: DEFAULT_SETTINGS };

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
  const others = checkedShelf().filter(entry => ['coastal', 'forest', 'sea-otters'].includes(
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
