/**
 * The covered sections block as drawn: a label, a still strip when there is
 * something to draw, one sentence, and no way to press or seek.
 */
import '@testing-library/jest-native/extend-expect';
import { render } from '@testing-library/react-native';
import React from 'react';
import { COASTAL_COLORS } from '../../src/calmframes/calmStyles';
import CoveredSectionsStrip, { COVERED_SECTIONS_HEADING } from '../../src/calmframes/CoveredSectionsStrip';
import { spoken } from '../../src/calmframes/copy';
import {
  COVERED_SECTIONS_NO_DURATION,
  COVERED_SECTIONS_NONE,
  COVERED_SECTIONS_UNAVAILABLE,
  CoveredSectionsResult,
} from '../../src/calmframes/coveredSections';

const ready: CoveredSectionsResult = {
  kind: 'ready',
  durationMs: 20_000,
  sections: [
    { startMs: 5_000, endMs: 9_000, reason: 'general', sources: [] },
    { startMs: 12_000, endMs: 16_000, reason: 'red', sources: [] },
  ],
  coveredMs: 8_000,
  text: '2 scenes · 8 seconds',
};

function touchables(view: ReturnType<typeof render>) {
  return view.UNSAFE_root.findAll(
    (node) =>
      typeof node.props.onPress === 'function' ||
      node.props.hasTVPreferredFocus === true ||
      node.props.focusable === true ||
      node.props.accessibilityRole === 'button',
  );
}

describe('the covered sections block', () => {
  it('draws the label, one mark per section in the section colour, and the sentence', () => {
    const view = render(<CoveredSectionsStrip result={ready} width={620} />);
    expect(view.getByText(COVERED_SECTIONS_HEADING)).toBeTruthy();
    expect(view.getByTestId('covered-sections-track')).toBeTruthy();
    // 5000 of 20000 across 620 units is 155 in, 124 wide; scale is identity here.
    expect(view.getByTestId('covered-sections-mark-0')).toHaveStyle({
      left: 155,
      width: 124,
      backgroundColor: COASTAL_COLORS.PENDING,
    });
    expect(view.getByTestId('covered-sections-mark-1')).toHaveStyle({
      left: 372,
      width: 124,
      backgroundColor: COASTAL_COLORS.FAILED,
    });
    expect(view.queryByTestId('covered-sections-mark-2')).toBeNull();
    expect(view.getByTestId('covered-sections-line').props.children).toBe(ready.text);
    // Said with a pause where the line draws a dot: VoiceView read the dot aloud.
    expect(view.getByTestId('covered-sections').props.accessibilityLabel).toBe(`${COVERED_SECTIONS_HEADING}. ${spoken(ready.text)}`);
    expect(view.getByTestId('covered-sections').props.accessible).toBe(true);
  });

  it('offers nothing to press, nothing to focus and nothing that seeks', () => {
    const view = render(<CoveredSectionsStrip result={ready} />);
    expect(touchables(view)).toHaveLength(0);
  });

  it.each([
    ['none', { kind: 'none', durationMs: 20_000, text: COVERED_SECTIONS_NONE }],
    ['no-duration', { kind: 'no-duration', text: COVERED_SECTIONS_NO_DURATION }],
    ['unavailable', { kind: 'unavailable', text: COVERED_SECTIONS_UNAVAILABLE }],
  ] as Array<[string, CoveredSectionsResult]>)('draws no strip for %s, only the sentence', (_, result) => {
    const view = render(<CoveredSectionsStrip result={result} />);
    expect(view.getByText(COVERED_SECTIONS_HEADING)).toBeTruthy();
    expect(view.queryByTestId('covered-sections-track')).toBeNull();
    expect(view.queryByTestId('covered-sections-mark-0')).toBeNull();
    expect(view.getByTestId('covered-sections-line').props.children).toBe(result.text);
    expect(view.getByTestId('covered-sections').props.accessibilityLabel).toBe(`${COVERED_SECTIONS_HEADING}. ${result.text}`);
    expect(touchables(view)).toHaveLength(0);
  });

  it('never names captions in any state', () => {
    for (const result of [
      ready,
      { kind: 'none', durationMs: 1, text: COVERED_SECTIONS_NONE },
      { kind: 'no-duration', text: COVERED_SECTIONS_NO_DURATION },
      { kind: 'unavailable', text: COVERED_SECTIONS_UNAVAILABLE },
    ] as CoveredSectionsResult[]) {
      const view = render(<CoveredSectionsStrip result={result} />);
      expect(view.queryByText(/caption/i)).toBeNull();
      view.unmount();
    }
  });
});
