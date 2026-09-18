/**
 * The frames the app reports for its own screens.
 *
 * Each one says what that screen paints: the colour behind everything, then
 * every other colour drawn on top. They are declared here rather than measured
 * at runtime because Vega gives the app no way to read its own pixels, and
 * they are kept true by test/calmframes/uiCapture.test.tsx, which renders each
 * screen for real and fails when the colours it finds are not these.
 *
 * tools/ui_flashmap.mjs turns this list into a video and runs flashmap over
 * it. That is the check that the app's own screens and transitions do not do
 * the thing the app exists to prevent.
 */

import { CALM_COLORS } from './calmStyles';
import { CardKind } from './cards';
import { UiFrame } from './uiCapture';

export const KID_HOME_FRAME: UiFrame = {
  screen: 'kid-home',
  background: CALM_COLORS.BACKGROUND,
  // BORDER is the block a poster sits in before its picture is there.
  surfaces: [CALM_COLORS.SURFACE, CALM_COLORS.BORDER],
};

export const KID_HOME_FOCUSED_FRAME: UiFrame = {
  screen: 'kid-home-focused',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [
    CALM_COLORS.SURFACE_FOCUSED,
    CALM_COLORS.BORDER,
    CALM_COLORS.SURFACE,
  ],
};

export const TITLE_DETAILS_FRAME: UiFrame = {
  screen: 'title-details',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE, CALM_COLORS.PENDING, CALM_COLORS.FAILED],
};

export const PARENT_LOCKED_FRAME: UiFrame = {
  screen: 'parent-area-locked',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

export const PARENT_OPEN_FRAME: UiFrame = {
  screen: 'parent-area-open',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE_FOCUSED, CALM_COLORS.SURFACE],
};

/**
 * The colour standing in for the video itself.
 *
 * When the cover is off, what is behind the app's layer is the title, and the
 * title was measured by flashmap before it was allowed to play. So this check
 * is about the app's own layer, and the video behind it is a stand-in rather
 * than a claim. tools/ui_flashmap.mjs paints it mid grey.
 */
export const VIDEO_BEHIND = 'video';

/**
 * What the player paints over the video.
 *
 * With the cover on, the app paints the whole screen black. With it off, the
 * app paints only the card, and the video shows through.
 */
export function playerFrame(covered: boolean, cardKind: CardKind): UiFrame {
  const surfaces: string[] = [];
  if (cardKind !== 'none') {
    surfaces.push(CALM_COLORS.SURFACE);
  }
  return {
    screen: `player-${covered ? 'covered' : 'clear'}-${cardKind}`,
    background: covered ? CALM_COLORS.COVER : VIDEO_BEHIND,
    surfaces,
  };
}

/** Every frame the app can show, for the flashmap run. */
export const ALL_UI_FRAMES: UiFrame[] = [
  KID_HOME_FRAME,
  KID_HOME_FOCUSED_FRAME,
  TITLE_DETAILS_FRAME,
  PARENT_LOCKED_FRAME,
  PARENT_OPEN_FRAME,
  playerFrame(false, 'none'),
  playerFrame(false, 'countdown'),
  playerFrame(true, 'covering'),
  playerFrame(false, 'after'),
  playerFrame(true, 'unverified'),
];
