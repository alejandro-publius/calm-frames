/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
import { scaleUxToDp } from '../pixelUtils';

/** Approved ivory coast menu palette. Playback keeps CALM_COLORS below. */
export const COASTAL_COLORS = {
  BACKGROUND: '#F5EBDD', SURFACE: '#E9DFD0', SURFACE_FOCUSED: '#DED0BD',
  BORDER: '#8B8173', FOCUS_RING: '#193B3C', PRIMARY: '#193B3C',
  TEXT_DISABLED: '#60645F', ACCENT_DARK: '#98492D', TEXT: '#193234',
  TEXT_DIM: '#40514D', INK: '#193234', VERIFIED: '#24584D',
  PENDING: '#4E5B68', FAILED: '#873F2C', COVER: '#000000',
} as const;

/** Terracotta boundary against both the ivory page and focused deep-teal primary. */
export const COASTAL_PRIMARY_FOCUS = '#C16C45';

/** Approved dusk coast palette; shared across application screens. Contrast is checked against rendered text and focus. */
export const CALM_COLORS = {
  /** Every Calm Frames screen sits on this. */
  BACKGROUND: '#151C26',
  /** A card on the ground, and the same card with focus on it. */
  SURFACE: '#303B48',
  SURFACE_FOCUSED: '#3B4856',
  BORDER: '#697585',
  /** Lighthouse gold is reserved for focus. */
  FOCUS_RING: '#E6B963',
  PRIMARY: '#D88B72',
  TEXT_DISABLED: '#9DA4AE',
  /** The secondary accent. Edges and fills only, it carries no text at all. */
  ACCENT_DARK: '#8E5648',
  TEXT: '#F4ECDD',
  TEXT_DIM: '#BDC2C9',
  /** Text on a light surface, where cream would disappear. */
  INK: '#151C26',
  /** The shield on a checked title. */
  VERIFIED: '#E7D9BF',
  /** A title still being checked. */
  PENDING: '#B9C9DA',
  /** A title whose check failed. Not a warning red, this is not an alarm. */
  FAILED: '#F2BDB1',
  /** The cover itself. */
  COVER: '#000000',
} as const;

/** Legacy size tokens in 1080p units. Named CALM_TEXT styles below add real faces and line heights. */
export const CALM_TYPE = {
  CARD_TITLE: 38,
  CARD_DETAIL: 38,
  SCREEN_TITLE: 64,
  SECTION: 42,
  BODY: 36,
  SMALL: 32,
  BUTTON: 36,
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

/**
 * Where the player puts its own words, in 1080p units from the top left.
 *
 * Captions own the bottom of the picture. PlayerScreen's KeplerCaptionsView
 * ends 240 scaled units above the bottom edge and its cues stack upward from there.
 * The card used to stand 160 units up from the bottom, inside that band, so
 * it covered the captions at the very moment a hidden picture made them the
 * only way to follow the story. It now hangs from the upper part of the safe
 * area instead.
 *
 * A labelled demo's practice label sits on a plate in the top left corner of
 * the safe area, on a row of its own: one line of small text on the plate
 * ends about 125 units down, and the card starts at 160.
 *
 * test/calmframes/tenFoot.test.tsx renders the player in each card state and
 * fails if the card, the plate and the caption band overlap.
 */
export const PLAYER_LAYOUT = {
  PLATE_TOP: CALM_SPACE.SAFE_Y,
  PLATE_LEFT: CALM_SPACE.SAFE_X,
  CARD_TOP: 160,
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

/** Fixed geometry for all interactive surfaces; selection and focus never resize them. */
export const CALM_CONTROL = { RADIUS: 18, MIN_HEIGHT: 88 } as const;

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

/** Licensed static display/UI faces packaged in assets/fonts. No synthetic weight. */
export const CALM_FONT = { regular: 'CalmSansRegular', medium: 'CalmSansSemibold', semibold: 'CalmSansSemibold', display: 'CalmDisplaySemibold' } as const;
const typography = (size: number, height: number, face: string) => ({
  fontFamily: face, fontSize: scale(size), lineHeight: scale(height), fontWeight: '400' as const,
});
export const CALM_TEXT = {
  feature: typography(80, 92, CALM_FONT.display),
  screen: typography(64, 76, CALM_FONT.display),
  section: typography(42, 54, CALM_FONT.display),
  numeral: typography(64, 76, CALM_FONT.semibold),
  card: typography(38, 48, CALM_FONT.medium),
  body: typography(36, 48, CALM_FONT.regular),
  control: typography(36, 46, CALM_FONT.semibold),
  supporting: typography(32, 42, CALM_FONT.regular),
} as const;

/** Shared reading geometry for choosing a video and reviewing its analysis. */
export const CALM_FLOW = { READING_WIDTH: 1040, HERO_TOP: 96, HERO_HEIGHT: 700 } as const;
