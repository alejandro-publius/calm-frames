/**
 * Home, Details and the opening shell put the title at the same height.
 *
 * Watch takes a person from the Details hero to the opening shell and then to
 * the picture. If the title moved between the first two, the eye would follow
 * it instead of the picture. The hero offset is one token, CALM_FLOW.HERO_TOP;
 * the opening shell draws an eyebrow above its title, so it starts that
 * eyebrow's line height and margin higher. The line height is written as a
 * number of 1080p units in PlayerOpening; this test holds it to the text style.
 */
import { render } from '@testing-library/react-native';
import React from 'react';
import { StyleSheet } from 'react-native';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CheckedTitle } from '../../src/calmframes/titleStatus';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { CALM_FLOW, CALM_TEXT, scale } from '../../src/calmframes/calmStyles';
import PlayerOpening, { EYEBROW_LINE_HEIGHT, OPENING_COPY_TOP } from '../../src/calmframes/PlayerOpening';

test('the eyebrow line height written in the opening shell is the supporting text style', () => {
  expect(scale(EYEBROW_LINE_HEIGHT)).toBe(CALM_TEXT.supporting.lineHeight);
});

test('the opening title starts where the hero title starts', () => {
  expect(OPENING_COPY_TOP).toBe(CALM_FLOW.HERO_TOP - (EYEBROW_LINE_HEIGHT + 12));
  expect(OPENING_COPY_TOP).toBeGreaterThan(0);
  const view = render(<PlayerOpening title="Acadia" onBack={jest.fn()} />);
  expect(view.getByText('Acadia')).toBeTruthy();
  expect(view.getByText('Opening your video…')).toBeTruthy();
});


test.each(['Acadia', 'A long coastal journey together'])('Details and opening retain the rendered typography for %s', (title) => {
  const entry = { title: { id: 'test', title, uri: 'test.mp4', sha256: 'a'.repeat(64), durationMs: 20_000 },
    status: 'verified', segments: [], hiddenMs: 0, verifiedProfiles: ['wcag'] } as CheckedTitle;
  const details = render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} />);
  const detailStyle = StyleSheet.flatten(details.getByTestId('title-details-title').props.style);
  details.unmount();
  const opening = render(<PlayerOpening title={title} onBack={jest.fn()} />);
  const openingStyle = StyleSheet.flatten(opening.getByText(title).props.style);
  const expected = title.length > 20 ? CALM_TEXT.screen : CALM_TEXT.feature;
  for (const key of ['fontFamily', 'fontSize', 'lineHeight', 'fontWeight'] as const) {
    expect(detailStyle[key]).toBe(expected[key]);
    expect(openingStyle[key]).toBe(detailStyle[key]);
  }
});
