/**
 * The title that ships inside the package.
 *
 * docs/BUILD_PROMPT.md 4.11: bundle one short non-hazardous title and its
 * signed map inside the .vpkg, so the app still works with the backend down.
 * A judge with no network, or with our backend switched off, still gets a
 * working kid mode with one checked title on the shelf.
 *
 * What is bundled:
 *
 *   assets/raw/offline/calm_gradient.mp4            12 seconds, made with
 *                                                   ffmpeg, a slow colour
 *                                                   gradient, nothing that
 *                                                   flashes
 *   assets/raw/offline/calm_gradient.flashmap.json  its signed map, which says
 *                                                   no segment broke the
 *                                                   thresholds
 *
 * The map text is compiled in as well, in offlineMapText.ts, because a
 * signature covers bytes and reading the file back at runtime is one more way
 * to end up checking something other than what was signed.
 *
 * The clip is not hazardous. It was analysed by flashmap before being
 * committed and the map that ships with it is the result: zero segments. The
 * app still runs the whole guard over it, which is the point. A title that
 * hides nothing still has to be checked before it plays.
 */

import { CatalogTitle } from './titleStatus';
import { OFFLINE_MAP_JSON } from './offlineMapText';

/**
 * The public key this build trusts, base64 of the 32 raw Ed25519 bytes.
 *
 * The private half never enters the repository. This is the demo key the
 * bundled title was signed with. A real deployment ships the studio key here
 * and rotates it with a new release.
 */
export const OFFLINE_PUBLIC_KEY_BASE64 =
  '533gF/bCDXyQppRnqiiT41+JwyyUYRN8P4YVZnCbKLQ=';

/** Where the packaged clip lives once the app is installed. */
export const OFFLINE_VIDEO_PATH = 'assets/raw/offline/calm_gradient.mp4';

/**
 * The same clip, as the player addresses it on a device.
 *
 * `/pkg/assets` is the read only root of the package's assets in a Vega app's
 * sandbox, which is where `app/assets` ends up once installed. The Kepler file
 * system README lists the sandbox paths.
 *
 * This has not been played from a device yet. If the scheme turns out to be
 * wrong, the guard treats it the way it treats any file it cannot open: the
 * picture stays hidden and the shelf says so, which is the right failure but
 * an unhelpful one to debug, so the path is here on its own rather than
 * written into a screen.
 */
export const OFFLINE_VIDEO_URI = `file:///pkg/${OFFLINE_VIDEO_PATH}`;

export const OFFLINE_TITLE_ID = 'calm-frames-offline';

/**
 * The bundled title as a catalog entry.
 *
 * `uri` is filled in by the caller, because how a packaged asset is addressed
 * at runtime depends on where the package was installed, and guessing a path
 * that turns out to be wrong would look like a missing file rather than a
 * wrong assumption.
 */
export function offlineTitle(uri: string): CatalogTitle {
  return {
    id: OFFLINE_TITLE_ID,
    title: 'Calm gradient (bundled)',
    uri,
    sha256:
      'af2934dc45c9519bcace8db253d0a9e0c10f9db6682a04ad2cf3f906e1755224',
    maps: { wcag: OFFLINE_MAP_JSON },
    durationMs: 12_000,
    bifFromSafeRendition: true,
  };
}
