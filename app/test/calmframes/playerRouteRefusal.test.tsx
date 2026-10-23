/**
 * A prepared title plays only on the exact route the build compiled.
 *
 * PlayerScreen asks packagedLibrary.acceptsRoute before it builds the guard
 * or loads any media. The question these tests settle is what a person sees
 * when the answer is no: not the opening shell, not a surface with the
 * original file in it, and not a card that reads like a checked title. The
 * guard is a stand in here on purpose and always answers verified, so a refusal
 * that leaked through to it would show up as a playing picture.
 *
 * Seen to fail, Oct 16 2026: with the refusal taken out of guardedParams in
 * PlayerScreen (`const guardedParams = route.params.guarded;`), every refused
 * variant rendered the stand in guard's card instead of the unavailable card,
 * and the first assertion on the card title went red.
 */
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(async () => null),
  setItem: jest.fn(async () => undefined),
}));
import { startPlayer } from './playbackUiHarness';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { ACADIA_SOURCE_SHA256, packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { guardedParamsFor, titleDataFor } from '../../src/screens/KidModeScreen';
import PlayerScreen from '../../src/screens/PlayerScreen';
import { VideoHandler } from '../../src/utils/VideoHandler';
import { SHELF_NOW } from './shelfFixtures';
import { MCWAY_SOURCE_SHA256 } from '../../src/calmframes/continuousScene';

function acadiaRoute(source = ACADIA_SOURCE_SHA256) {
  const title = packagedLibrary.titles(DEFAULT_SETTINGS).find((one) => one.sha256 === source)!;
  const entry = checkTitle(title, {
    settings: DEFAULT_SETTINGS,
    publicKeyBase64: packagedLibrary.publicKeyFor(title, DEFAULT_SETTINGS) ?? '',
    nowMs: SHELF_NOW,
  });
  expect(entry.status).toBe('verified');
  return { data: titleDataFor(entry), guarded: guardedParamsFor(entry, DEFAULT_SETTINGS) };
}

type Route = ReturnType<typeof acadiaRoute>;
type Params = { data: Route['data']; guarded: Partial<Route['guarded']> & Record<string, unknown> };

const refused: Array<[string, (route: Params) => void]> = [
  ['a different source hash', (route) => { route.guarded.sha256 = 'a'.repeat(64); }],
  ['an altered map', (route) => { route.guarded.maps = { ...route.guarded.maps, wcag: `${route.guarded.maps!.wcag} ` }; }],
  ['a map fetched from a URL', (route) => { route.guarded.mapUrls = { wcag: 'https://example.invalid/map.json' }; }],
  ['the unprocessed original instead of the rendition', (route) => { route.data = { ...route.data, uri: 'file:///pkg/assets/raw/prepared-library/original.mp4' }; }],
  ['a different rendition hash', (route) => { route.guarded.renditionSha256 = 'b'.repeat(64); }],
  ['a different duration', (route) => { route.guarded.durationMs = (route.guarded.durationMs ?? 0) + 1; }],
  ['a streaming format', (route) => { route.data = { ...route.data, format: 'HLS' }; }],
  ['no household settings', (route) => { delete route.guarded.settings; }],
  ['another title id', (route) => { route.guarded.titleId = 'prepared-other'; }],
];

let preBuffer: jest.SpyInstance;
beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  // The harness stand in guard reports a verified, uncovered title. Nothing
  // below may depend on it answering otherwise.
  startPlayer().unmount();
  preBuffer = jest.spyOn(VideoHandler.prototype as unknown as { preBufferVideo: () => void }, 'preBufferVideo');
});
afterEach(() => { jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks(); });

function renderRoute(params: Params) {
  const goBack = jest.fn();
  render(<PlayerScreen navigation={{ goBack } as never} route={{ params: { ...params, showHomeOpening: true } } as never} />);
  return goBack;
}

it('plays the exact compiled Acadia route, which is the control for the refusals below', () => {
  renderRoute(acadiaRoute() as Params);
  expect(preBuffer).toHaveBeenCalledTimes(1);
  expect(screen.getByTestId('kepler-video-surface-view')).toBeTruthy();
  expect(screen.queryByText('This video is unavailable')).toBeNull();
});

it.each(refused)('refuses %s: no opening, no media, one unavailable card and one Back', (_name, alter) => {
  const route = acadiaRoute() as Params;
  alter(route);
  const goBack = renderRoute(route);
  expect(preBuffer).not.toHaveBeenCalled();
  expect(screen.queryByTestId('kepler-video-surface-view')).toBeNull();
  expect(screen.queryByTestId('player-home-opening')).toBeNull();
  expect(screen.queryByTestId('buffering-status')).toBeNull();
  expect(screen.getByTestId('calm-card-title').props.children).toBe('This video is unavailable');
  expect(screen.getByTestId('calm-card-detail').props.children).toBe('This video cannot be opened. Go back to the library.');
  expect(screen.queryByTestId('calm-card-skip')).toBeNull();
  // Back is the one way out. The press swaps in the returning shell, which
  // carries no second Back, and the route leaves exactly once.
  fireEvent.press(screen.getByRole('button', { name: 'Back' }));
  expect(screen.getByText('Going back…')).toBeTruthy();
  expect(screen.queryByRole('button', { name: 'Back' })).toBeNull();
  act(() => jest.advanceTimersByTime(701));
  expect(goBack).toHaveBeenCalledTimes(1);
});

it('a substituted continuous-scene edition cannot prebuffer; Back still returns once', () => {
  const route = acadiaRoute(MCWAY_SOURCE_SHA256) as Params;
  route.guarded.renditionSha256 = 'b'.repeat(64);
  const goBack = renderRoute(route);
  expect(preBuffer).not.toHaveBeenCalled();
  expect(screen.queryByTestId('kepler-video-surface-view')).toBeNull();
  expect(screen.getByText('This video is unavailable')).toBeTruthy();
  fireEvent.press(screen.getByRole('button', { name: 'Back' }));
  act(() => jest.advanceTimersByTime(701));
  expect(goBack).toHaveBeenCalledTimes(1);
});
