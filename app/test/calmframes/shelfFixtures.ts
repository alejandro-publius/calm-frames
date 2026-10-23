/**
 * The retained regression shelf, checked the way KidModeScreen checks it.
 *
 * Every bundled title, including internal demos, verified by the real reader against the
 * key KidModeScreen would choose for it, at a moment when none of the three
 * maps is stale. Consumer selection is tested separately; these fixtures keep
 * Harbor and the playback check available for reproducibility.
 */

import {
  benignStorySettings,
  benignStoryTitle,
  bundledTitlePublicKey,
} from '../../src/calmframes/benignStory';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { OFFLINE_PUBLIC_KEY_BASE64, OFFLINE_VIDEO_URI, offlineTitle } from '../../src/calmframes/offlineTitle';
import {
  concernsPackagedLibrary,
  packagedLibrary,
} from '../../src/calmframes/packagedLibrary';
import { CheckedTitle, checkTitle } from '../../src/calmframes/titleStatus';

export function regressionCatalog() {
  return [benignStoryTitle(), ...packagedLibrary.titles(DEFAULT_SETTINGS), offlineTitle(OFFLINE_VIDEO_URI)];
}

const created = (text: string | null | undefined): number =>
  Date.parse(JSON.parse(text ?? '{}').created_utc);

/** A minute after the newest bundled map was made. */
export const SHELF_NOW =
  Math.max(...regressionCatalog().map((title) => created(title.maps?.wcag))) +
  60_000;

export function checkedShelf(nowMs = SHELF_NOW): CheckedTitle[] {
  return regressionCatalog().map((title) =>
    checkTitle(title, {
      settings: benignStorySettings(title, DEFAULT_SETTINGS),
      publicKeyBase64: concernsPackagedLibrary(title)
        ? packagedLibrary.publicKeyFor(title, DEFAULT_SETTINGS) ?? ''
        : bundledTitlePublicKey(title, OFFLINE_PUBLIC_KEY_BASE64),
      nowMs,
    }),
  );
}
