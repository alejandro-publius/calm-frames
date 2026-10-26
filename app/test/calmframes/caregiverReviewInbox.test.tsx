import React from 'react';
import {ScrollView} from 'react-native';
import {act, fireEvent, render} from '@testing-library/react-native';
import CaregiverReviewsScreen from '../../src/calmframes/CaregiverReviewsScreen';
import {loadReviewInbox, MAX_REVIEW_BYTES, parseCaregiverReview, readReviewFile, REVIEW_INBOX, ReviewReader} from '../../src/calmframes/caregiverReviewInbox';
const fixture = require('../../../results/overnight-2026-10-25/personal-import/caregiver-review.json');
const name = `calm-frames-review-${'a'.repeat(32)}.json`;
const report = () => JSON.parse(JSON.stringify(fixture));
function reader(data = report()): ReviewReader {
  return {exists: jest.fn(async () => true), getEntries: jest.fn(async () => [name]),
    getMetadata: jest.fn(async () => ({size: 1000, entryType: '5'})),
    readFileAsString: jest.fn(async () => JSON.stringify(data))};
}
test('the real caregiver export is selectable but never grants playback', async () => {
  const source = reader(), list = await loadReviewInbox(source);
  expect(list.files[0].review.sourceSha256).toBe(fixture.source.sha256);
  expect(list.files[0].review.plans).toHaveLength(3);
  const view = render(<CaregiverReviewsScreen reader={source} onBack={jest.fn()} />);
  await act(async () => {});
  fireEvent.press(view.getByTestId(`caregiver-review-${name}`)); await act(async () => {});
  expect(view.getByText(/Playback remains unavailable/)).toBeTruthy();
  expect(view.getByText(/This TV has not rechecked/)).toBeTruthy();
  expect(view.queryByText('Watch')).toBeNull();
  fireEvent.press(view.getByTestId('caregiver-review-close'));
  expect(view.queryByTestId('caregiver-review-summary')).toBeNull();
  expect(view.getByTestId(`caregiver-review-${name}`).props.hasTVPreferredFocus).toBe(true);
});
test.each(['processing_permission_confirmed', 'tv_playback_authorized', 'permission_verified_by_application'])(
  'refuses an unsupported %s claim', key => {
    const data = report(); data[key] = !data[key]; expect(() => parseCaregiverReview(JSON.stringify(data))).toThrow();
  });
test.each(['source', 'duration', 'plan', 'title', 'map', 'playable'])(
  'refuses malformed or misleading %s data', change => {
    const data = report();
    if (change === 'source') data.analysis.source_sha256 = 'b'.repeat(64);
    if (change === 'duration') data.analysis.duration_ms = Infinity;
    if (change === 'plan') data.analysis.presets.wcag.covered_ms = 100;
    if (change === 'title') data.title = 'Misleading\u202e title';
    if (change === 'map') delete data.analysis.review_map_hashes;
    if (change === 'playable') data.analysis.playable = true;
    expect(() => parseCaregiverReview(JSON.stringify(data))).toThrow();
  });
test.each(['../household.json', '/data/household.json', `${name}/../../x`])('never reads a path outside its inbox: %s', async path => {
  const source = reader(); await expect(readReviewFile(path, source)).rejects.toThrow(); expect(source.readFileAsString).not.toHaveBeenCalled();
});
test.each(['file-link', 'directory', 'oversized', 'unknown-mode', 'old-posix-mode'])('refuses %s before reading any file', async state => {
  const source = reader(); source.getMetadata = jest.fn(async () => ({
    entryType: state === 'file-link' ? '4' : state === 'directory' ? '2' : state === 'unknown-mode' ? undefined : state === 'old-posix-mode' ? 0o100600 : '5',
    size: state === 'oversized' ? MAX_REVIEW_BYTES + 1 : 1000}));
  await expect(readReviewFile(name, source)).rejects.toThrow(); expect(source.readFileAsString).not.toHaveBeenCalled();
});
test('one damaged report is isolated without reading private paths', async () => {
  const source = reader(); source.getEntries = jest.fn(async () => ['household.json', name]);
  const result = await loadReviewInbox(source); expect(result.files).toHaveLength(1); expect(result.refused).toBe(1);
  expect(source.readFileAsString).toHaveBeenCalledTimes(1);
  expect(source.readFileAsString).toHaveBeenCalledWith(`${REVIEW_INBOX}/${name}`, 'UTF-8');
});
test('missing inbox is empty and excessive entries fail without reading them', async () => {
  const source = reader(); source.exists = jest.fn(async () => false);
  expect(await loadReviewInbox(source)).toEqual({files: [], refused: 0});
  source.exists = jest.fn(async () => true); source.getEntries = jest.fn(async () => Array(9).fill(name));
  await expect(loadReviewInbox(source)).rejects.toThrow('eight'); expect(source.readFileAsString).not.toHaveBeenCalled();
});
test('selection rechecks changed bytes instead of showing an old analysis', async () => {
  const source = reader(), view = render(<CaregiverReviewsScreen reader={source} onBack={jest.fn()} />);
  await act(async () => {});
  const changed = report(); changed.title = 'Changed report'; source.readFileAsString = jest.fn(async () => JSON.stringify(changed));
  fireEvent.press(view.getByTestId(`caregiver-review-${name}`)); await act(async () => {});
  expect(view.queryByTestId('caregiver-review-summary')).toBeNull(); expect(view.getByText(/changed or could not be read/)).toBeTruthy();
});

test('SDK native FileType.FILE is accepted without treating it as POSIX mode bits', async () => {
  const source = reader();
  const result = await loadReviewInbox(source);
  expect(result.files[0].review.title).toBe(fixture.title);
  expect(source.getMetadata).toHaveBeenCalledWith(`${REVIEW_INBOX}/${name}`, true);
  expect(source.getMetadata).not.toHaveBeenCalledWith(REVIEW_INBOX, expect.anything());
});
test.each([0, 1, 2, 3, 4, 6, -1, 7, '0', '1', '2', '3', '4', '6', '05', '5 ', true, null])('refuses native non-file or unknown type %s before any read', async entryType => {
  const source = reader(); source.getMetadata = jest.fn(async () => ({entryType, size: 1000}));
  await expect(readReviewFile(name, source)).rejects.toThrow();
  expect(source.readFileAsString).not.toHaveBeenCalled();
});
test('does not use the obsolete mode declaration to override a symbolic link', async () => {
  const source = reader(); source.getMetadata = jest.fn(async () => ({mode: 5, entryType: 4, size: 1000}));
  await expect(readReviewFile(name, source)).rejects.toThrow();
  expect(source.readFileAsString).not.toHaveBeenCalled();
});
test('accepts the observed string entryType without a mode property', async () => {
  const source = reader(); source.getMetadata = jest.fn(async () => ({entryType: '5', size: 1692}));
  expect((await readReviewFile(name, source)).review.title).toBe(fixture.title);
});
test('OpenMode alone cannot establish a regular file', async () => {
  const source = reader(); source.getMetadata = jest.fn(async () => ({mode: 5, size: 1692}));
  await expect(readReviewFile(name, source)).rejects.toThrow();
  expect(source.readFileAsString).not.toHaveBeenCalled();
});
test('opening a report resets the list offset so the preferred Back control stays visible', async () => {
  const scroll = jest.spyOn(ScrollView.prototype, 'scrollTo');
  try {
    const source = reader(), view = render(<CaregiverReviewsScreen reader={source} onBack={jest.fn()} />);
    await act(async () => {});
    scroll.mockClear();
    fireEvent.press(view.getByTestId(`caregiver-review-${name}`)); await act(async () => {});
    expect(view.getByTestId('caregiver-review-summary')).toBeTruthy();
    expect(scroll).toHaveBeenCalledWith({y: 0, animated: false});
  } finally {scroll.mockRestore();}
});
