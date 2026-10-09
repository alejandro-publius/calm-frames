/**
 * The real bundled shelf, checked the way KidModeScreen checks it.
 *
 * Every title in the default catalog, verified by the real reader against the
 * key KidModeScreen would choose for it, at a moment when none of the three
 * maps is stale. A test file that imports this has to mock
 * '@react-native-async-storage/async-storage', because the catalog lives in
 * KidModeScreen.tsx and that screen reads the saved household.
 */

import {
  benignStorySettings,
  bundledTitlePublicKey,
} from '../../src/calmframes/benignStory';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { OFFLINE_PUBLIC_KEY_BASE64 } from '../../src/calmframes/offlineTitle';
import {
  concernsPackagedLibrary,
  packagedLibrary,
} from '../../src/calmframes/packagedLibrary';
import { CheckedTitle, checkTitle } from '../../src/calmframes/titleStatus';
import { defaultCatalog } from '../../src/screens/KidModeScreen';

const created = (text: string | null | undefined): number =>
  Date.parse(JSON.parse(text ?? '{}').created_utc);

/** A minute after the newest bundled map was made. */
export const SHELF_NOW =
  Math.max(...defaultCatalog().map((title) => created(title.maps?.wcag))) +
  60_000;

export function checkedShelf(nowMs = SHELF_NOW): CheckedTitle[] {
  return defaultCatalog().map((title) =>
    checkTitle(title, {
      settings: benignStorySettings(title, DEFAULT_SETTINGS),
      publicKeyBase64: concernsPackagedLibrary(title)
        ? packagedLibrary.publicKeyFor(title, DEFAULT_SETTINGS) ?? ''
        : bundledTitlePublicKey(title, OFFLINE_PUBLIC_KEY_BASE64),
      nowMs,
    }),
  );
}
