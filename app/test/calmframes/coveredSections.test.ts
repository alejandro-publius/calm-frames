/**
 * The covered sections helper: the player's schedule, read for the Details page.
 *
 * Every expected number here is written out by hand from the rule in
 * coverSchedule.ts (a 500 ms guard band on each side under the WCAG preset,
 * a 1000 ms band under Extra cautious, clamp to the running time, merge what
 * overlaps or touches), never computed by the helper under test.
 *
 * Seen to fail, Oct 16 2026: with the running time left out of the schedule
 * call in coveredSections.ts, the two clamp tests went red, reporting ends of
 * 37500 and 40500 where 37000 was expected and a section at 49500 to 51500
 * that should have been dropped; the other eleven stayed green.
 */
import { BENIGN_STORY_ID, BENIGN_STORY_URI } from '../../src/calmframes/benignStory';
import { BENIGN_STORY_SHA256 } from '../../src/calmframes/benignStoryData';
import {
  COVERED_SECTIONS_NO_DURATION,
  COVERED_SECTIONS_NONE,
  COVERED_SECTIONS_UNAVAILABLE,
  coveredSections,
  coveredSectionsLine,
} from '../../src/calmframes/coveredSections';
import { buildCoverIntervals, FlashSegment } from '../../src/calmframes/coverSchedule';
import { coverOptionsFor, DEFAULT_SETTINGS, PRESET_NAMES } from '../../src/calmframes/household';
import { CheckedTitle, checkTitle } from '../../src/calmframes/titleStatus';
import { ACADIA_SOURCE_SHA256, packagedLibrary } from '../../src/calmframes/packagedLibrary';
import { SHELF_NOW } from './shelfFixtures';

function entry(
  segments: FlashSegment[],
  overrides: Partial<CheckedTitle> = {},
  title: Partial<CheckedTitle['title']> = {},
): CheckedTitle {
  return {
    title: {
      id: 'prepared-test',
      title: 'Test title',
      uri: 'file:///test.mp4',
      sha256: 'a'.repeat(64),
      durationMs: 37_000,
      ...title,
    },
    status: 'verified',
    segments,
    hiddenMs: 0,
    verifiedProfiles: ['wcag'],
    ...overrides,
  };
}

function spans(result: ReturnType<typeof coveredSections>) {
  if (result.kind !== 'ready') throw new Error(`expected ready, got ${result.kind}`);
  return result.sections.map((section) => [section.startMs, section.endMs, section.reason]);
}

describe('the covered sections of a verified title', () => {
  it('widens one segment by the guard band and says so in one sentence', () => {
    const result = coveredSections(entry([{ startMs: 10_000, endMs: 12_000 }]), DEFAULT_SETTINGS);
    expect(spans(result)).toEqual([[9_500, 12_500, 'general']]);
    expect(result.kind === 'ready' && result.coveredMs).toBe(3_000);
    expect(result.text).toBe('1 scene · 3 seconds');
  });

  it('clamps a section at the start of the video to zero', () => {
    const result = coveredSections(entry([{ startMs: 0, endMs: 2_000 }]), DEFAULT_SETTINGS);
    expect(spans(result)).toEqual([[0, 2_500, 'general']]);
    expect(result.kind === 'ready' && result.coveredMs).toBe(2_500);
  });

  it('clamps a section that ends exactly at the running time', () => {
    const result = coveredSections(entry([{ startMs: 36_000, endMs: 37_000 }]), DEFAULT_SETTINGS);
    expect(spans(result)).toEqual([[35_500, 37_000, 'general']]);
    expect(result.kind === 'ready' && result.coveredMs).toBe(1_500);
  });

  it('clamps a section that runs past the running time, and drops one beyond it', () => {
    const result = coveredSections(
      entry([
        { startMs: 36_800, endMs: 40_000 },
        { startMs: 50_000, endMs: 51_000 },
      ]),
      DEFAULT_SETTINGS,
    );
    expect(spans(result)).toEqual([[36_300, 37_000, 'general']]);
    expect(result.kind === 'ready' && result.coveredMs).toBe(700);
    // Under a second is said as one second, never as none.
    expect(result.text).toBe('1 scene · 1 second');
  });

  it('merges overlapping sections before it counts the total', () => {
    const result = coveredSections(
      entry([
        { startMs: 10_000, endMs: 12_000 },
        { startMs: 12_300, endMs: 13_000, reason: 'red' },
      ]),
      DEFAULT_SETTINGS,
    );
    // 9500 to 12500 and 11800 to 13500 overlap: one red section of 4000 ms,
    // not two sections adding up to 4700.
    expect(spans(result)).toEqual([[9_500, 13_500, 'red']]);
    expect(result.kind === 'ready' && result.coveredMs).toBe(4_000);
    expect(result.text).toBe('1 scene · 4 seconds');
  });

  it('counts separate sections separately', () => {
    const result = coveredSections(
      entry([
        { startMs: 5_000, endMs: 6_000 },
        { startMs: 20_000, endMs: 22_000 },
      ]),
      DEFAULT_SETTINGS,
    );
    expect(spans(result)).toEqual([
      [4_500, 6_500, 'general'],
      [19_500, 22_500, 'general'],
    ]);
    expect(result.kind === 'ready' && result.coveredMs).toBe(5_000);
    expect(result.text).toBe('2 scenes · 5 seconds');
  });

  it('is the schedule the player builds, band for band', () => {
    const segments: FlashSegment[] = [
      { startMs: 8_343, endMs: 9_864 },
      { startMs: 9_135, endMs: 11_699 },
      { startMs: 29_113, endMs: 30_593 },
    ];
    const result = coveredSections(entry(segments), DEFAULT_SETTINGS);
    expect(result.kind).toBe('ready');
    expect(result.kind === 'ready' && result.sections).toEqual(
      buildCoverIntervals(segments, { ...coverOptionsFor(DEFAULT_SETTINGS), durationMs: 37_000 }),
    );
  });

  it('uses the demo preset and the demo noun for the bundled demo', () => {
    const demo = entry(
      [
        { startMs: 6_000, endMs: 8_000 },
        { startMs: 13_000, endMs: 15_000 },
      ],
      {},
      { id: BENIGN_STORY_ID, uri: BENIGN_STORY_URI, sha256: BENIGN_STORY_SHA256, durationMs: 20_000 },
    );
    const result = coveredSections(demo, DEFAULT_SETTINGS);
    // Extra cautious: a 1000 ms band on each side.
    expect(spans(result)).toEqual([
      [5_000, 9_000, 'general'],
      [12_000, 16_000, 'general'],
    ]);
    expect(result.text).toBe('2 simulated pauses · 8 seconds');
  });

  it('never promises captions', () => {
    expect(coveredSectionsLine(3, 12_000, 37_000, false)).toBe(
      '3 scenes · 12 seconds',
    );
    expect(coveredSectionsLine(1, 90_000, 125_000, false)).toBe(
      '1 scene · 1 minute 30 seconds',
    );
    expect(coveredSectionsLine(1, 1_000, 37_000, false)).not.toMatch(/caption/i);
  });
});

describe('when there is nothing to draw', () => {
  it('says so for a verified title with no sections', () => {
    const result = coveredSections(entry([]), DEFAULT_SETTINGS);
    expect(result).toEqual({ kind: 'none', durationMs: 37_000, text: COVERED_SECTIONS_NONE });
  });

  it('says the running time is unknown rather than drawing unclamped sections', () => {
    for (const durationMs of [undefined, 0, -1, Number.NaN]) {
      const result = coveredSections(
        entry([{ startMs: 10_000, endMs: 12_000 }], {}, { durationMs }),
        DEFAULT_SETTINGS,
      );
      expect(result).toEqual({ kind: 'no-duration', text: COVERED_SECTIONS_NO_DURATION });
    }
  });

  it('says sections are unavailable for a title that has not verified', () => {
    for (const status of ['pending', 'failed'] as const) {
      const result = coveredSections(
        entry([{ startMs: 10_000, endMs: 12_000 }], { status }),
        DEFAULT_SETTINGS,
      );
      expect(result).toEqual({ kind: 'unavailable', text: COVERED_SECTIONS_UNAVAILABLE });
    }
  });

  it('says sections are unavailable when the segment list is missing', () => {
    const broken = { ...entry([]), segments: undefined } as unknown as CheckedTitle;
    expect(coveredSections(broken, DEFAULT_SETTINGS)).toEqual({
      kind: 'unavailable',
      text: COVERED_SECTIONS_UNAVAILABLE,
    });
  });
});


describe('rendition timeline parity with playback', () => {
  it.each([100, -100])('applies the verified %i ms offset before widening and clamping', (offset) => {
    const segments = [{ startMs: 0, endMs: 1_000 }, { startMs: 36_000, endMs: 37_000 }];
    const result = coveredSections(entry(segments, {}, { renditionStartOffsetMs: offset }), DEFAULT_SETTINGS);
    expect(spans(result)).toEqual([[0, 1_500 - offset, 'general'], [35_500 - offset, 37_000, 'general']]);
    expect(result.kind === 'ready' && result.sections).toEqual(buildCoverIntervals(segments, {
      ...coverOptionsFor(DEFAULT_SETTINGS), durationMs: 37_000, renditionStartOffsetMs: offset,
    }));
  });

  it.each(PRESET_NAMES)('matches the compiled Acadia player schedule under %s', (preset) => {
    const settings = { ...DEFAULT_SETTINGS, preset };
    const title = packagedLibrary.titles(settings).find(value => value.sha256 === ACADIA_SOURCE_SHA256)!;
    const checked = checkTitle(title, { settings, publicKeyBase64: packagedLibrary.publicKeyFor(title, settings)!, nowMs: SHELF_NOW });
    expect(checked.status).toBe('verified');
    const result = coveredSections(checked, settings);
    expect(result.kind === 'ready' && result.sections).toEqual(buildCoverIntervals(checked.segments, {
      ...coverOptionsFor(settings), durationMs: title.durationMs, renditionStartOffsetMs: title.renditionStartOffsetMs,
    }));
    expect(result.text).toBe(`2 scenes · ${preset === 'extra-cautious' ? 9 : 7} seconds`);
  });
});
