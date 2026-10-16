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
  expect(view.getByText('Opening your video...')).toBeTruthy();
});
