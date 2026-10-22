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

import { CALM_COLORS, COASTAL_COLORS } from './calmStyles';
import { WORLD } from './CoastalWorld';

/** Non-player notices and parent pages share the coastal map palette. */
const MENU = COASTAL_COLORS;
/**
 * Home and Details are drawn on the coastal map, so they paint its colours:
 * the cream sky and sand behind everything, cream cards and the warm Watch.
 * The map's sea is artwork, not a declared surface; cream behind everything
 * is the lighter of the two, so the check measures the larger change.
 */
const MAP = { ...COASTAL_COLORS, BACKGROUND: WORLD.BACKGROUND, SURFACE: WORLD.SURFACE, SURFACE_FOCUSED: WORLD.SURFACE_FOCUSED, PRIMARY: WORLD.PRIMARY, INK: WORLD.INK };
import { CardKind } from './cards';
import { UiFrame } from './uiCapture';

/** Early bootstrap wave, before navigation and household loading are ready. */
export const HARBOR_BOOTSTRAP_FRAME: UiFrame = {
  screen: 'harbor-bootstrap', background: MAP.BACKGROUND, surfaces: [],
};

export const HOUSEHOLD_LOADING_FRAME: UiFrame = {
  screen: 'household-loading',
  background: MAP.BACKGROUND,
  // This inventory models declared solid surfaces, not artwork pixels or motion.
  surfaces: [],
};

export const HOUSEHOLD_ERROR_FRAME: UiFrame = {
  screen: 'household-error',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE, MENU.PRIMARY],
};

export const KID_HOME_STORY_FRAME: UiFrame = { screen: 'kid-home-story', background: MAP.BACKGROUND, surfaces: [MAP.PRIMARY, MAP.SURFACE] };
export const KID_HOME_STORY_FOCUSED_FRAME: UiFrame = { screen: 'kid-home-story-focused', background: MAP.BACKGROUND, surfaces: [MAP.PRIMARY, MAP.SURFACE_FOCUSED, MAP.SURFACE] };
/** Watch focused: on the map it keeps its warm fill and takes the ring, so the colours are the resting ones. */
export const KID_HOME_STORY_WATCH_FRAME: UiFrame = { screen: 'kid-home-story-watch', background: MAP.BACKGROUND, surfaces: [MAP.PRIMARY, MAP.SURFACE] };

export const KID_HOME_FRAME: UiFrame = {
  screen: 'kid-home', background: MAP.BACKGROUND,
  surfaces: [MAP.PRIMARY, MAP.SURFACE],
};
export const KID_HOME_FOCUSED_FRAME: UiFrame = {
  screen: 'kid-home-focused', background: MAP.BACKGROUND,
  surfaces: [MAP.PRIMARY, MAP.SURFACE_FOCUSED, MAP.SURFACE],
};
export const KID_HOME_PROFILES_FRAME: UiFrame = {
  screen: 'kid-home-profiles', background: MAP.BACKGROUND,
  surfaces: [MAP.PRIMARY, MAP.SURFACE],
};
export const KID_HOME_PROFILES_OFFLINE_FRAME: UiFrame = {
  screen: 'kid-home-profiles-offline', background: MAP.BACKGROUND,
  surfaces: [MENU.SURFACE, MAP.PRIMARY],
};
export const KID_HOME_PROFILES_FOCUSED_FRAME: UiFrame = {
  screen: 'kid-home-profiles-focused', background: MAP.BACKGROUND,
  surfaces: [MAP.PRIMARY, MAP.SURFACE_FOCUSED, MAP.SURFACE],
};
export const KID_HOME_PICKER_FRAME: UiFrame = {
  screen: 'kid-home-picker', background: MAP.BACKGROUND,
  surfaces: [MAP.SURFACE_FOCUSED, MAP.SURFACE, MAP.PRIMARY],
};

/** Nothing has been checked yet, so the shelf is one notice. */
export const KID_HOME_EMPTY_FRAME: UiFrame = {
  screen: 'kid-home-empty',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
};

/** The service is unreachable, so a notice sits above what still verifies. */
export const KID_HOME_OFFLINE_FRAME: UiFrame = {
  screen: 'kid-home-offline',
  background: MAP.BACKGROUND,
  surfaces: [MENU.SURFACE, MAP.PRIMARY],
};

export const TITLE_DETAILS_HARBOR_FRAME: UiFrame = { screen: 'title-details-harbor', background: MAP.BACKGROUND, surfaces: [MAP.PRIMARY, MAP.SURFACE] };
export const TITLE_DETAILS_DEMO_FRAME: UiFrame = { screen: 'title-details-demo', background: MAP.BACKGROUND, surfaces: [MAP.PRIMARY, MAP.SURFACE, MAP.PENDING] };

export const TITLE_DETAILS_FRAME: UiFrame = {
  screen: 'title-details',
  background: MAP.BACKGROUND,
  surfaces: [MAP.PRIMARY, MENU.SURFACE, MENU.PENDING, MENU.FAILED],
};

/**
 * A title that is not ready to play. It is not drawn on the map: no destination
 * to show, so it keeps the shared coastal page palette.
 *
 * No strip, because a title that did not verify has no schedule to show, so
 * neither of the strip's colours is painted. What is left is the notice.
 */
export const TITLE_DETAILS_BLOCKED_FRAME: UiFrame = {
  screen: 'title-details-blocked',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
};

export const PARENT_LOCKED_FRAME: UiFrame = {
  screen: 'parent-area-locked',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
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
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
};

export const PARENT_OPEN_FRAME: UiFrame = {
  screen: 'parent-area-open',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE_FOCUSED, MENU.SURFACE],
};

/**
 * The parent area with one kid's settings open.
 *
 * The same two colours as the open parent area, in the other order: the
 * household chip is first in the row and it is not the chosen one when a kid
 * is, so the plain card colour is painted before the chosen fill. It is a
 * separate frame because it is a separate state, and the timeline should show
 * it was visited.
 */
export const PARENT_PROFILE_FRAME: UiFrame = {
  screen: 'parent-area-profile',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE, MENU.SURFACE_FOCUSED],
};

/**
 * The parent area asking before it removes a kid.
 *
 * The same two colours as the parent area with one kid open, in the same
 * order, which is the point: the question is a notice block on the card
 * colour, and the picker above it has not moved, so asking paints no new
 * colour and no new transition. It is a separate frame for the reason the
 * wrong PIN one is: a state the app can be in is a state the flash run should
 * walk through, and the timeline should show it was visited.
 */
export const PARENT_REMOVE_KID_FRAME: UiFrame = {
  screen: 'parent-area-remove-kid',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE, MENU.SURFACE_FOCUSED],
};

/** The four steps of the first run, in order. */
export const FIRST_RUN_PIN_FRAME: UiFrame = {
  screen: 'first-run-pin',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
};

export const FIRST_RUN_PRESET_FRAME: UiFrame = {
  screen: 'first-run-preset',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE_FOCUSED, MENU.SURFACE],
};

export const FIRST_RUN_ROOM_FRAME: UiFrame = {
  screen: 'first-run-room',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE, MENU.SURFACE_FOCUSED],
};

export const FIRST_RUN_EXPLAINER_FRAME: UiFrame = {
  screen: 'first-run-explainer',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
};

/**
 * The credits.
 *
 * One card colour behind every entry and nothing else, so arriving here from
 * any other screen is the same small step in brightness as any other move.
 */
export const CREDITS_FRAME: UiFrame = {
  screen: 'credits',
  background: MENU.BACKGROUND,
  surfaces: [MENU.SURFACE],
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

/** Static in-play status; the scene remains visible beneath its small plate. */
export const PLAYER_BUFFERING_FRAME: UiFrame = {
  screen: 'player-buffering', background: VIDEO_BEHIND, surfaces: [CALM_COLORS.SURFACE],
};

/**
 * What the player paints over the video.
 *
 * With the cover on, the app paints the whole screen black. With it off, the
 * app paints only the card, and the video shows through. A labelled demo also
 * paints its practice plate the whole time it plays. The plate is the card's
 * colour, so it adds a surface only when there is no card on screen.
 */
export function playerFrame(
  covered: boolean,
  cardKind: CardKind,
  plate = false,
): UiFrame {
  const surfaces: string[] = [];
  if (cardKind !== 'none' || plate) {
    surfaces.push(CALM_COLORS.SURFACE);
  }
  return {
    screen: `player-${covered ? 'covered' : 'clear'}-${cardKind}${
      plate ? '-plate' : ''
    }`,
    background: covered ? CALM_COLORS.COVER : VIDEO_BEHIND,
    surfaces,
  };
}

/** Every frame the app can show, for the flashmap run. */
export const ALL_UI_FRAMES: UiFrame[] = [
  HARBOR_BOOTSTRAP_FRAME,
  PLAYER_BUFFERING_FRAME,
  HOUSEHOLD_LOADING_FRAME,
  HOUSEHOLD_ERROR_FRAME,
  FIRST_RUN_PIN_FRAME,
  FIRST_RUN_PRESET_FRAME,
  FIRST_RUN_ROOM_FRAME,
  FIRST_RUN_EXPLAINER_FRAME,
  KID_HOME_FRAME,
  KID_HOME_STORY_FRAME, KID_HOME_STORY_FOCUSED_FRAME, KID_HOME_STORY_WATCH_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_EMPTY_FRAME,
  KID_HOME_OFFLINE_FRAME,
  KID_HOME_PROFILES_FRAME,
  KID_HOME_PROFILES_OFFLINE_FRAME,
  KID_HOME_PROFILES_FOCUSED_FRAME,
  KID_HOME_PICKER_FRAME,
  TITLE_DETAILS_FRAME,
  TITLE_DETAILS_HARBOR_FRAME, TITLE_DETAILS_DEMO_FRAME,
  TITLE_DETAILS_BLOCKED_FRAME,
  PARENT_LOCKED_FRAME,
  PARENT_WRONG_PIN_FRAME,
  PARENT_OPEN_FRAME,
  PARENT_PROFILE_FRAME,
  PARENT_REMOVE_KID_FRAME,
  CREDITS_FRAME,
  // The map is still being checked, so the picture is hidden behind a card.
  playerFrame(true, 'checking'),
  playerFrame(false, 'none'),
  playerFrame(false, 'countdown'),
  playerFrame(true, 'covering'),
  playerFrame(false, 'after'),
  playerFrame(true, 'unverified'),
  // The labelled Harbor demo, which carries its practice plate throughout.
  playerFrame(true, 'checking', true),
  playerFrame(false, 'none', true),
  playerFrame(false, 'countdown', true),
  playerFrame(true, 'covering', true),
  playerFrame(false, 'after', true),
  playerFrame(true, 'unverified', true),
];
