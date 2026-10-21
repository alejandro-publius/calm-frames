/** Presentation for one measured edition; this never grants playback access. */
import type { ImageSourcePropType } from 'react-native';
import { concernsPackagedLibrary, packagedLibrary } from './packagedLibrary';
import type { CatalogTitle } from './titleStatus';

export const MCWAY_SOURCE_SHA256 = 'c9d5d21786c1beaf075dbc05373cf74184050a5f9b52765d5ef25d2a9cc65cb2';
export const MCWAY_RENDITION_SHA256 = '795927874818f98c03cff64b6cd1b1e60db4544f7ddd0962f0d1d6340f39ebf2';
// Exact authenticated 8991-frame duration at 30000/1001 fps.
export const MCWAY_DURATION_MS = 299999.7;
// Last decoded frame of that exact rendition, PNG SHA256:
// feaef416d06e4b8d92359f6ef60d60694e341d921935480b42628113f840f1e4.
const ending = require('../../assets/image/tv/mcway-final-frame.png');

export function isContinuousScene(title: CatalogTitle): boolean {
  return concernsPackagedLibrary(title) && title.sha256 === MCWAY_SOURCE_SHA256 &&
    title.renditionSha256 === MCWAY_RENDITION_SHA256 && title.durationMs === MCWAY_DURATION_MS;
}

export function continuousScenePicture(title: CatalogTitle): ImageSourcePropType | undefined {
  return isContinuousScene(title) ? ending : undefined;
}

export function continuousEndingForRoute(
  data: Parameters<typeof packagedLibrary.acceptsRoute>[0],
  guarded: Parameters<typeof packagedLibrary.acceptsRoute>[1],
): ImageSourcePropType | undefined {
  return guarded?.sha256 === MCWAY_SOURCE_SHA256 &&
    guarded.renditionSha256 === MCWAY_RENDITION_SHA256 && guarded.durationMs === MCWAY_DURATION_MS &&
    packagedLibrary.acceptsRoute(data, guarded) ? ending : undefined;
}
