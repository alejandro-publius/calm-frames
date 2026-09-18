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
 *   the smallest text on any Calm Frames screen is 32 units at 1080p and the
 *   card headings are 56.
 * - Focus you can see from the sofa. A focused control gets a thick bright
 *   border and a lighter fill, never a colour change alone, and never an
 *   animation: kid mode has no motion.
 * - The app's own screens have to pass flashmap. The palette is deliberately
 *   narrow and dark, and every screen shares one background, so moving between
 *   screens is a small luminance step rather than a flash. test/calmframes/
 *   uiCapture.test.tsx measures that on the real rendered screens.
 *
 * The numbers below are measured, not admired. The virtual device cannot be
 * photographed, so test/calmframes/tenFoot.test.tsx renders every screen and
 * every state and checks each one against these: the type floor, the safe
 * margins, the focus ring width and the contrast ratios. Change a number here
 * and that test says what it did to every screen.
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

/**
 * Type sizes in 1080p units, scaled to the device by scaleUxToDp.
 *
 * Why the smallest is 32 rather than something smaller. On a 55 inch 16:9
 * television the picture is about 27 inches tall, so one unit at 1080p is
 * about 0.025 inches. A 32 unit line has a cap height near 0.57 inches, and
 * from a sofa 8 feet away that is about 20 arcminutes. Reading stays
 * comfortable down to roughly 16 to 20 arcminutes and gets tiring below it,
 * and a tired parent at the end of the day is the person this is for. The
 * earlier floor of 28 units came out at about 18 arcminutes, which is the edge
 * of that range rather than inside it.
 */
export const CALM_TYPE = {
  CARD_TITLE: 56,
  CARD_DETAIL: 38,
  SCREEN_TITLE: 64,
  SECTION: 44,
  BODY: 36,
  SMALL: 32,
  BUTTON: 38,
} as const;

export const CALM_SPACE = {
  TIGHT: 12,
  ROW: 20,
  BLOCK: 32,
  EDGE: 64,
  /**
   * The safe margins, in 1080p units.
   *
   * Televisions still overscan, and the amount differs by set, so the edges of
   * the picture are not a place to put anything a person has to read. Five per
   * cent of each edge is the margin television interfaces have used for
   * decades: 96 units across a 1920 wide picture and 54 down a 1080 tall one.
   * Every Calm Frames screen keeps its text and its controls inside that.
   */
  SAFE_X: 96,
  SAFE_Y: 54,
} as const;

/** The smallest text Calm Frames draws, in 1080p units. */
export const MINIMUM_TEXT_SIZE = 32;

/**
 * The focus ring, in 1080p units.
 *
 * Six units is about 0.15 inches on a 55 inch screen, which stays a visible
 * line rather than a hairline from across a room.
 *
 * Every focusable control carries a border this thick whether it has focus or
 * not, and focus changes the colour of the ring and the fill inside it at the
 * same time. Two reasons. Nothing moves when focus moves, because a border
 * that grows would push the text inside it around, and that is motion. And
 * focus is never carried by colour alone, because the fill changes with it.
 */
export const FOCUS_RING_WIDTH = 6;

/**
 * Contrast floors, as WCAG 2.2 contrast ratios.
 *
 * 4.5 to 1 is WCAG AA for small text. Every line Calm Frames draws is large
 * text by WCAG's definition, where AA asks only 3 to 1, so holding all of it
 * to 4.5 is deliberately stricter than the rule. 3 to 1 for the focus ring
 * against both neighbours is WCAG 2.2's non-text contrast, applied on both
 * sides of the ring rather than one.
 */
export const MINIMUM_TEXT_CONTRAST = 4.5;
export const MINIMUM_FOCUS_CONTRAST = 3;

export const scale = scaleUxToDp;
