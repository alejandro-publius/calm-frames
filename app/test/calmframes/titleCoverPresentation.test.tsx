import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { hasBakedOceanPresentation } from '../../src/calmframes/titleCoverPresentation';
import { DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { packagedLibrary, ACADIA_SOURCE_SHA256, createApprovedAcadiaLibrary } from '../../src/calmframes/packagedLibrary';
import { PACKAGED_LIBRARY_JSON } from '../../src/calmframes/acadiaCatalog';
import { checkTitle } from '../../src/calmframes/titleStatus';
import { coveredSections, coveredSectionsLine } from '../../src/calmframes/coveredSections';
import { coverLine } from '../../src/calmframes/copy';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
function fixture(preset = DEFAULT_SETTINGS.preset) {
  const settings = { ...DEFAULT_SETTINGS, preset };
  const title = packagedLibrary.consumerTitles(settings).find(t => t.sha256 === ACADIA_SOURCE_SHA256)!;
  const entry = checkTitle(title, { settings, publicKeyBase64: packagedLibrary.publicKeyFor(title, settings)!, nowMs: Date.parse('2026-10-18T05:00:00Z') });
  const schedule = coveredSections(entry, settings);
  if (schedule.kind !== 'ready') throw new Error('Missing fixture schedule');
  return { settings, entry, schedule };
}
it.each(PRESET_NAMES)('labels only exact verified %s ocean schedules as replaced', preset => {
  const { settings, entry, schedule } = fixture(preset);
  expect(hasBakedOceanPresentation(entry, settings, schedule.sections)).toBe(true);
  expect(hasBakedOceanPresentation({ ...entry, status: 'failed' }, settings, schedule.sections)).toBe(false);
  expect(hasBakedOceanPresentation({ ...entry, title: { ...entry.title, renditionSha256: 'a'.repeat(64) } }, settings, schedule.sections)).toBe(false);
  expect(hasBakedOceanPresentation(entry, settings, schedule.sections.slice(1))).toBe(false);
  const legacy = createApprovedAcadiaLibrary(PACKAGED_LIBRARY_JSON).titles(settings)[0];
  expect(hasBakedOceanPresentation({ ...entry, title: legacy }, settings, schedule.sections)).toBe(false);
});
it('shows the concise actual Extra cautious count, with ocean audio explanation only in More info', () => {
  const { settings, entry } = fixture('extra-cautious');
  const screen = render(<TitleDetailsScreen entry={entry} settings={settings} onPlay={jest.fn()} />);
  expect(screen.getByTestId('title-details-covered-heading').props.children).toBe('Scenes replaced');
  expect(screen.getByTestId('title-details-covered-line').props.children).toBe('2 scenes · 9 seconds');
  expect(screen.getByTestId('title-details-covered').props.accessibilityLabel).toBe('Scenes replaced. 2 scenes · 9 seconds');
  expect(screen.getByTestId('title-details-meta').props.children).toBe('38 seconds');
  expect(screen.getByText('Waves along the coast of Acadia National Park.')).toBeTruthy();
  expect(screen.queryByText(/The sound continues|original audio/)).toBeNull();
  fireEvent.press(screen.getByTestId('title-details-show-info'));
  expect(screen.getByTestId('title-details-cover-line').props.children).toBe('Flagged scenes are replaced with a dark frame from the start of this video. Original audio is kept when the video has sound.');
});
it('uses singular/plural without repeating runtime or promising audio in the summary', () => {
  expect(coveredSectionsLine(1, 1000, 38000, false)).toBe('1 scene · 1 second');
  expect(coveredSectionsLine(2, 9000, 38000, false)).toBe('2 scenes · 9 seconds');
  expect(coveredSectionsLine(2, 8000, 20000, true)).toBe('2 simulated pauses · 8 seconds');
  expect(coverLine(1, false)).toBe('The flagged scene is covered. Original audio is kept when the video has sound.');
  expect(coverLine(2, true)).not.toContain('Ocean');
});
