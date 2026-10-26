/** The cover draws the bundled copy when it has one, and the data URI otherwise. */
import React from 'react';
import { render, screen } from '@testing-library/react-native';
import type { ImageSourcePropType } from 'react-native';
import CoverLayer from '../../src/calmframes/CoverLayer';

const uri = 'data:image/jpeg;base64,/9j/4AAQ';

test('a bundled source replaces the data URI for the same still', () => {
  const bundled: ImageSourcePropType = 7;
  render(<CoverLayer visible imageUri={uri} imageSource={bundled} />);
  expect(screen.getByTestId('calm-frames-cover-still').props.source).toBe(bundled);
});

test('without a bundled copy the still keeps the authenticated data URI', () => {
  render(<CoverLayer visible imageUri={uri} />);
  expect(screen.getByTestId('calm-frames-cover-still').props.source).toEqual({ uri });
});

test('a bundled source alone never paints: the authenticated data URI decides whether there is a still', () => {
  render(<CoverLayer visible imageSource={7} />);
  expect(screen.queryByTestId('calm-frames-cover-still')).toBeNull();
});
