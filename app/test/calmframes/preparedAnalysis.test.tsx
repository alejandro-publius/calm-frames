jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import React from 'react';
import { render } from '@testing-library/react-native';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import PreparedVideoAnalysis from '../../src/calmframes/PreparedVideoAnalysis';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { checkedShelf } from './shelfFixtures';
import { BENIGN_STORY_ID } from '../../src/calmframes/benignStory';
import { ACADIA_SOURCE_SHA256, packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { checkTitle } from '../../src/calmframes/titleStatus';

const entries = checkedShelf();
const prepared = entries.find(entry => entry.title.id.startsWith('prepared-'))!;
const demo = entries.find(entry => entry.title.id === BENIGN_STORY_ID)!;
test('shows two distinct detected Acadia periods and the selected rendition settings', () => {
  const settings = { ...DEFAULT_SETTINGS, preset: 'extra-cautious' as const };
  const title = packagedLibrary.titles(settings).find(one => one.sha256 === ACADIA_SOURCE_SHA256)!;
  const entry = checkTitle(title, { settings, nowMs: Date.parse('2026-10-16T00:00:00Z'), publicKeyBase64: packagedLibrary.publicKeyFor(title, settings)! });
  const view = render(<PreparedVideoAnalysis entry={entry} settings={settings} compact />);
  expect(view.getByText('2 flagged periods')).toBeTruthy();
  view.rerender(<PreparedVideoAnalysis entry={entry} settings={settings} />);
  expect(view.getByText('8.3 to 11.7 sec')).toBeTruthy();
  expect(view.getByText('29.1 to 30.6 sec')).toBeTruthy();
  expect(view.getByText('7.3 to 12.7 sec')).toBeTruthy();
  expect(view.getByText(/20 nits change, dark image below 160 nits, assumed peak 200 nits/)).toBeTruthy();
  expect(view.getByText(/relative luminance change 0.1, dark image below 0.8/)).toBeTruthy();
  expect(view.getAllByText('Preparation room: 85-inch screen at 4 feet.')).toHaveLength(2);
});
test('shows zero findings and the pre-analysis boundary for a genuine prepared selection', () => {
  const view = render(<PreparedVideoAnalysis entry={prepared} settings={DEFAULT_SETTINGS} compact />);
  expect(view.getByText('No scenes flagged')).toBeTruthy();
  expect(view.getByText('This prepared video has no scheduled hidden scenes.')).toBeTruthy();
  expect(view.getByText(/Analyzed before playback/)).toBeTruthy();
});
test('does not promote unverified or substituted metadata into evidence', () => {
  const view = render(<PreparedVideoAnalysis entry={{ ...prepared, status: 'pending' }} settings={DEFAULT_SETTINGS} compact />);
  expect(view.toJSON()).toBeNull();
  view.rerender(<PreparedVideoAnalysis entry={{ ...prepared, title: { ...prepared.title, renditionSha256: '0'.repeat(64) } }} settings={DEFAULT_SETTINGS} compact />);
  expect(view.toJSON()).toBeNull();
});
test('labels simulated pauses rather than treating the demo as detector findings', () => {
  const view = render(<PreparedVideoAnalysis entry={demo} settings={DEFAULT_SETTINGS} compact />);
  expect(view.getByText('Simulated picture pauses')).toBeTruthy();
  expect(view.getByText('These events were added for the demo. They are not detected flashing.')).toBeTruthy();
  expect(view.queryByText('No scenes flagged')).toBeNull();
});
test('file record separates source and rendition and states the same-analyzer limitation', () => {
  const view = render(<PreparedVideoAnalysis entry={prepared} settings={DEFAULT_SETTINGS} />);
  expect(view.getByTestId('prepared-analysis-source').props.children).toContain(prepared.title.sha256.slice(0, 12));
  expect(view.getByTestId('prepared-analysis-rendition').props.children).toContain(prepared.title.renditionSha256!.slice(0, 12));
  expect(view.getByText(/not an independent safety assessment/)).toBeTruthy();
});

test('a prepared entry without a matching file record has Back but no Play action', () => {
  const view = render(<TitleDetailsScreen entry={{ ...prepared, title: { ...prepared.title, renditionSha256: '0'.repeat(64) } }} onBack={jest.fn()} onPlay={jest.fn()} />);
  expect(view.getByText('This video is unavailable')).toBeTruthy();
  expect(view.queryByTestId('title-details-play')).toBeNull();
  expect(view.getByTestId('title-details-back').props.hasTVPreferredFocus).toBe(true);
});
