import React from 'react';
import { act, fireEvent, render } from '@testing-library/react-native';
import { BackHandler } from 'react-native';
import { createHash } from 'crypto';
import { PLAYBACK_PROOF_RECORDS } from '../../src/calmframes/approvedPlaybackProof';
import { loadPlaybackProof, playbackProofFor } from '../../src/calmframes/playbackProof';
import * as proofReader from '../../src/calmframes/playbackProof';
import PlaybackProofPanel from '../../src/calmframes/PlaybackProofPanel';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { ACADIA_SOURCE_SHA256, packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { MCWAY_SOURCE_SHA256 } from '../../src/calmframes/continuousScene';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { DEFAULT_SETTINGS, HouseholdSettings } from '../../src/calmframes/household';

jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
const entryFor = (source = MCWAY_SOURCE_SHA256, settings = DEFAULT_SETTINGS) => {
  const title = packagedLibrary.titles(settings).find(item => item.sha256 === source)!;
  return checkTitle(title, { settings, nowMs: Date.parse('2026-10-21T23:00:00Z'), publicKeyBase64: packagedLibrary.publicKeyFor(title, settings)! });
};
const digest = (raw: string) => createHash('sha512').update(raw).digest('hex');
afterEach(() => jest.restoreAllMocks());

test('every approved consumer title and preset resolves to the exact record', () => {
  for (const preset of ['wcag', 'broadcast', 'extra-cautious'] as const) {
    const settings = { ...DEFAULT_SETTINGS, preset };
    const sources = PLAYBACK_PROOF_RECORDS.map(record => JSON.parse(record.raw)).filter(proof => proof.preset === preset).map(proof => proof.sourceSha256);
    for (const source of sources) {
      const entry = entryFor(source, settings), proof = playbackProofFor(entry, settings);
      expect(proof?.renditionSha256).toBe(entry.title.renditionSha256);
      expect(proof?.preset).toBe(preset);
      expect(proof?.source.map(m => m.profile)).toEqual(preset === 'wcag' ? ['wcag'] : ['wcag', 'broadcast']);
    }
  }
});

test('altered compiled summary bytes fail their digest, and malformed values fail even with a matching test digest', () => {
  const registration = PLAYBACK_PROOF_RECORDS[0];
  expect(loadPlaybackProof(registration.raw + ' ', registration.sha512)).toBeNull();
  for (const mutate of [
    (v: any) => { v.output[0].findings = -1; },
    (v: any) => { v.output[0].findings = '0'; },
    (v: any) => { v.frameCount = 0; },
    (v: any) => { v.timingPreserved = 'true'; },
    (v: any) => { v.preset = 'unknown'; },
    (v: any) => { v.source[0].mapSha256 = 'invalid'; },
  ]) {
    const value = JSON.parse(registration.raw); mutate(value);
    const raw = JSON.stringify(value);
    expect(loadPlaybackProof(raw, digest(raw))).toBeNull();
  }
});

test.each(['source', 'rendition', 'preset', 'map', 'pending', 'profiles'])('no matching proof after %s substitution', field => {
  const entry = entryFor(), settings: HouseholdSettings = { ...DEFAULT_SETTINGS };
  if (field === 'source') entry.title.sha256 = 'a'.repeat(64);
  if (field === 'rendition') entry.title.renditionSha256 = 'b'.repeat(64);
  if (field === 'preset') settings.preset = 'broadcast';
  if (field === 'map') entry.title.maps = { ...entry.title.maps, wcag: entry.title.maps!.wcag + ' ' };
  if (field === 'pending') entry.status = 'pending';
  if (field === 'profiles') entry.verifiedProfiles = [];
  expect(playbackProofFor(entry, settings)).toBeNull();
  const view = render(<PlaybackProofPanel entry={entry} settings={settings} />);
  expect(view.getByText('Playback proof unavailable')).toBeTruthy();
  expect(view.queryByTestId('playback-proof-binding')).toBeNull();
});

test('report substitution cannot display a matched selection', () => {
  const original = packagedLibrary.evidenceFor;
  jest.spyOn(packagedLibrary, 'evidenceFor').mockImplementation((title, settings) => {
    const evidence = original(title, settings);
    return evidence ? { ...evidence, reportSha256: 'c'.repeat(64) } : null;
  });
  expect(playbackProofFor(entryFor(), DEFAULT_SETTINGS)).toBeNull();
});

test.each(['sourceSha256', 'renditionSha256', 'reportSha256', 'bundleId', 'preset'])('a digest-valid test summary cannot substitute %s', field => {
  const entry = entryFor();
  const registration = PLAYBACK_PROOF_RECORDS.find(record => {
    const value = JSON.parse(record.raw);
    return value.titleId === entry.title.id && value.preset === 'wcag';
  })!;
  const original = { ...registration };
  try {
    // Isolated in-memory test only; production input remains generated and build-checked.
    const value = JSON.parse(registration.raw);
    value[field] = field === 'preset' ? 'broadcast' : 'd'.repeat(64);
    registration.raw = JSON.stringify(value);
    registration.sha512 = digest(registration.raw);
    expect(playbackProofFor(entry, DEFAULT_SETTINGS)).toBeNull();
  } finally { Object.assign(registration, original); }
});

test('presentation findings cannot contradict the authenticated source maps', () => {
  const entry = entryFor(ACADIA_SOURCE_SHA256);
  entry.segments = [];
  expect(playbackProofFor(entry, DEFAULT_SETTINGS)).toBeNull();
});

test('unknown output measurements remain explicit in the prepared stage', () => {
  const entry = entryFor(), proof = playbackProofFor(entry, DEFAULT_SETTINGS)!;
  jest.spyOn(proofReader, 'playbackProofFor').mockReturnValue({ ...proof, frameCount: null, timingPreserved: false,
    output: [{ profile: 'wcag', findings: null, analyzer: null }] });
  const view = render(<PlaybackProofPanel entry={entry} settings={DEFAULT_SETTINGS} />);
  fireEvent.press(view.getByTestId('playback-proof-step-prepared'));
  expect(view.getByText('WCAG: finding count not recorded')).toBeTruthy();
  expect(view.queryByText('WCAG: 0 output findings')).toBeNull();
  expect(view.getByText(/Complete frame-timing measurements are not recorded/)).toBeTruthy();
});

test('real report differences remain visible without safety claims or invented versions', () => {
  const view = render(<PlaybackProofPanel entry={entryFor()} settings={DEFAULT_SETTINGS} />);
  expect(view.getByText('0 flagged periods')).toBeTruthy();
  fireEvent.press(view.getByTestId('playback-proof-step-prepared'));
  expect(view.getByText('WCAG: 0 output findings')).toBeTruthy();
  expect(view.getByText('WCAG output analyzer: version not recorded in this report')).toBeTruthy();
  expect(view.getByText(/Nothing was flagged, so this result does not demonstrate a cover working/)).toBeTruthy();
  expect(view.getByText(/8991 frames/)).toBeTruthy();
  view.rerender(<PlaybackProofPanel entry={entryFor(ACADIA_SOURCE_SHA256)} settings={DEFAULT_SETTINGS} />);
  fireEvent.press(view.getByTestId('playback-proof-step-source'));
  expect(view.getByText('2 flagged periods')).toBeTruthy();
  fireEvent.press(view.getByTestId('playback-proof-step-prepared'));
  expect(view.getByText('WCAG output analyzer: flashmap 1.0.0')).toBeTruthy();
  expect(view.getByText(/replacement picture was drawn/)).toBeTruthy();
});

test('proof navigation never starts playback and remote Back restores each opener', () => {
  let handlers: Array<() => boolean | null | undefined> = [];
  jest.spyOn(BackHandler, 'addEventListener').mockImplementation((_, handler) => {
    handlers.push(handler);
    return { remove: () => { handlers = handlers.filter(h => h !== handler); } };
  });
  const play = jest.fn(), leave = jest.fn();
  const view = render(<TitleDetailsScreen entry={entryFor()} onPlay={play} onBack={leave} />);
  fireEvent.press(view.getByTestId('title-details-show-info'));
  fireEvent.press(view.getByRole('button', { name: 'Playback proof & details' }));
  expect(view.getByText('Playback proof')).toBeTruthy();
  fireEvent.press(view.getByTestId('title-details-record-proof-step-prepared'));
  expect(view.getByText('WCAG: 0 output findings')).toBeTruthy();
  fireEvent.press(view.getByTestId('title-details-record-proof-step-binding'));
  expect(view.getByTestId('title-details-record-proof-binding')).toBeTruthy();
  expect(view.getByTestId('title-details-info-back').props.hasTVPreferredFocus).toBe(true);
  act(() => { handlers[handlers.length - 1](); });
  expect(view.getByTestId('title-details-technical').props.hasTVPreferredFocus).toBe(true);
  act(() => { handlers[handlers.length - 1](); });
  expect(view.getByTestId('title-details-show-info').props.hasTVPreferredFocus).toBe(true);
  expect(play).not.toHaveBeenCalled();
  expect(leave).not.toHaveBeenCalled();
});
