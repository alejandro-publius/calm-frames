/**
 * Scaling for a ten foot screen.
 *
 * Sizes in the guard's own views are written in the units they would have on a
 * 1080p television, and scaled from there to whatever the device reports. A
 * 4K panel reports 1080p logical pixels on Vega, so on most devices this is
 * the identity, and on the ones where it is not the type stays the same
 * physical size across the room.
 */

import { Dimensions, PixelRatio } from 'react-native';

const REFERENCE_HEIGHT = 1080;

export function scaleUxToDp(uxUnit: number): number {
  const { height } = Dimensions.get('window');
  const ratio = height > 0 ? height / REFERENCE_HEIGHT : 1;
  return PixelRatio.roundToNearestPixel(uxUnit * ratio);
}
