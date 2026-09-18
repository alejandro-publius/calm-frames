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

/** Nothing has been checked yet, so the shelf is one notice. */
export const KID_HOME_EMPTY_FRAME: UiFrame = {
  screen: 'kid-home-empty',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

/** The service is unreachable, so a notice sits above what still verifies. */
export const KID_HOME_OFFLINE_FRAME: UiFrame = {
  screen: 'kid-home-offline',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE, CALM_COLORS.BORDER],
};

export const TITLE_DETAILS_FRAME: UiFrame = {
  screen: 'title-details',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE, CALM_COLORS.PENDING, CALM_COLORS.FAILED],
};

/**
 * A title that is not ready to play.
 *
 * No strip, because a title that did not verify has no schedule to show, so
 * neither of the strip's colours is painted. What is left is the notice.
 */
export const TITLE_DETAILS_BLOCKED_FRAME: UiFrame = {
  screen: 'title-details-blocked',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

export const PARENT_LOCKED_FRAME: UiFrame = {
  screen: 'parent-area-locked',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

/**
 * The keypad after a wrong PIN.
 *
 * The same colours as the locked screen, which is the point: a wrong PIN
 * changes the words, not the picture. It is recorded separately so the
 * timeline shows the state was visited.
 */
export const PARENT_WRONG_PIN_FRAME: UiFrame = {
  screen: 'parent-area-wrong-pin',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

export const PARENT_OPEN_FRAME: UiFrame = {
  screen: 'parent-area-open',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE_FOCUSED, CALM_COLORS.SURFACE],
};

/** The four steps of the first run, in order. */
export const FIRST_RUN_PIN_FRAME: UiFrame = {
  screen: 'first-run-pin',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

export const FIRST_RUN_PRESET_FRAME: UiFrame = {
  screen: 'first-run-preset',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE_FOCUSED, CALM_COLORS.SURFACE],
};

export const FIRST_RUN_ROOM_FRAME: UiFrame = {
  screen: 'first-run-room',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE, CALM_COLORS.SURFACE_FOCUSED],
};

export const FIRST_RUN_EXPLAINER_FRAME: UiFrame = {
  screen: 'first-run-explainer',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
};

/**
 * The credits.
 *
 * One card colour behind every entry and nothing else, so arriving here from
 * any other screen is the same small step in brightness as any other move.
 */
export const CREDITS_FRAME: UiFrame = {
  screen: 'credits',
  background: CALM_COLORS.BACKGROUND,
  surfaces: [CALM_COLORS.SURFACE],
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
  FIRST_RUN_PIN_FRAME,
  FIRST_RUN_PRESET_FRAME,
  FIRST_RUN_ROOM_FRAME,
  FIRST_RUN_EXPLAINER_FRAME,
  KID_HOME_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_EMPTY_FRAME,
  KID_HOME_OFFLINE_FRAME,
  TITLE_DETAILS_FRAME,
  TITLE_DETAILS_BLOCKED_FRAME,
  PARENT_LOCKED_FRAME,
  PARENT_WRONG_PIN_FRAME,
  PARENT_OPEN_FRAME,
  CREDITS_FRAME,
  playerFrame(false, 'none'),
  playerFrame(false, 'countdown'),
  playerFrame(true, 'covering'),
  playerFrame(false, 'after'),
  playerFrame(true, 'unverified'),
];
