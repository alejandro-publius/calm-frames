/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * How Calm Frames looks, in one place.
 *
 * Three things drive every choice here:
 *
 * - Ten foot reading. Everything is sized for a television across a room, so
 *   the smallest text on any Calm Frames screen is 28 units at 1080p and the
 *   card headings are 56.
 * - Focus you can see from the sofa. A focused control gets a thick bright
 *   border and a lighter fill, never a colour change alone, and never an
 *   animation: kid mode has no motion.
 * - The app's own screens have to pass flashmap. The palette is deliberately
 *   narrow and dark, and every screen shares one background, so moving between
 *   screens is a small luminance step rather than a flash. test/calmframes/
 *   uiCapture.test.tsx measures that on the real rendered screens.
 */

import { scaleUxToDp } from '../pixelUtils';

export const CALM_COLORS = {
  /** Every Calm Frames screen sits on this. */
  BACKGROUND: '#101A24',
  SURFACE: '#1B2735',
  SURFACE_FOCUSED: '#2B3B4E',
  BORDER: '#33455A',
  FOCUS_RING: '#F2C14E',
  TEXT: '#F4F7FA',
  TEXT_DIM: '#B9C4D0',
  /** The shield on a checked title. */
  VERIFIED: '#7FD1A3',
  /** A title still being checked. */
  PENDING: '#E2C275',
  /** A title whose check failed. Not a warning red, this is not an alarm. */
  FAILED: '#E08A7B',
  /** The cover itself. */
  COVER: '#000000',
} as const;

/** Type sizes in 1080p units, scaled to the device by scaleUxToDp. */
export const CALM_TYPE = {
  CARD_TITLE: 56,
  CARD_DETAIL: 34,
  SCREEN_TITLE: 64,
  SECTION: 40,
  BODY: 32,
  SMALL: 28,
  BUTTON: 34,
} as const;

export const CALM_SPACE = {
  TIGHT: 12,
  ROW: 20,
  BLOCK: 32,
  EDGE: 64,
} as const;

/** The smallest text Calm Frames draws, in 1080p units. */
export const MINIMUM_TEXT_SIZE = 28;

export const scale = scaleUxToDp;
