/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * Where everything on the island Home sits, in 1080p units from the screen's top left.
 *
 * The map is painted by an SVG with a 1920 by 1080 view box and the controls
 * are laid out by Yoga, and on Oct 18 nothing tied the two together: the hero
 * was pinned to the bottom of a scroll view, the cards were pushed down by a
 * margin, and the islands, boat, waves and shorelines sat at their own
 * numbers. Rendered from the component tree, the heading sat across a shoreline, a wave ran
 * through the featured title, the cards hid half of each island and cut the
 * lighthouse in two, and the boat touched the bottom of the selected card.
 *
 * So the map and the controls read their positions from here, and the bands
 * are stacked so that every word and every control sits on one flat colour:
 *
 *   54 to 142    header, on the cream sky
 *   166 to 220   Ocean and Forest, each heading over its own cards
 *   240 to 260   the sky's shoreline, nothing on it
 *   292 to 602   the cards, each standing on its own island in the sea
 *   660 to 722   the boat, in open water in front of the chosen island
 *   742 to 784   the sand's two shorelines, nothing on them
 *   868 to 956   Watch and Details, on the cream sand; with no cards to
 *                name the video, its title and runtime stand above them,
 *                from 798 to 1026
 *
 * Each card covers the middle of its island, and the landmarks that say which
 * island it is (lighthouse, pines, kelp) stand on the strips either side of
 * the card. test/calmframes/homeIslands.test.tsx renders Home and fails if any
 * of these touch.
 */
import { CALM_FLOW, CALM_SPACE } from './calmStyles';

export type IslandSlotKind = 'coastal' | 'forest' | 'sea-otters';

/** Left to right, the order the islands sit in on the map: the two Ocean islands together, then Forest. */
export const ISLAND_ORDER: IslandSlotKind[] = ['coastal', 'sea-otters', 'forest'];

/** The environments Home names, and the islands in each. One name per environment everywhere. */
export const ENVIRONMENTS: Array<{ name: 'Ocean' | 'Forest'; kinds: IslandSlotKind[] }> = [
  { name: 'Ocean', kinds: ['coastal', 'sea-otters'] },
  { name: 'Forest', kinds: ['forest'] },
];

const SCREEN_HEIGHT = 1080;
const HEADER_HEIGHT = 88;

export const HOME_ISLANDS = {
  /** The bottom of CalmPageHeader's row. */
  HEADER_BOTTOM: CALM_SPACE.SAFE_Y + HEADER_HEIGHT,
  HEADING: { top: 166, height: 54 },
  /** The cream sky meets the sea along a wave this far down, give or take AMPLITUDE. */
  SKY_EDGE: 250,
  /** The sand's darker edge; its cream edge runs SAND_STEP below it. */
  SAND_EDGE: 752,
  SAND_STEP: 22,
  WAVE_AMPLITUDE: 10,
  /** Island centres across the screen, wide enough apart that neighbouring islands never meet. */
  CENTERS: { coastal: 400, 'sea-otters': 960, forest: 1520 } as Record<IslandSlotKind, number>,
  ISLAND_Y: 536,
  ISLAND_SCALE: 0.8,
  CARD: { top: 292, width: 400, height: 310 },
  BOAT: { top: 660, width: 72, height: 62 },
  HERO: { left: CALM_SPACE.SAFE_X, top: 798, width: CALM_FLOW.HERO_TITLE_WIDTH, height: 228 },
  /** Watch and Details alone, centred in the sand, when the cards already name every video. */
  ACTIONS: { left: CALM_SPACE.SAFE_X, top: 868, width: CALM_FLOW.HERO_TITLE_WIDTH, height: 88 },
  /** Who is watching takes the row of cards while it is open, from the first card's left to the last card's right. */
  PICKER: { left: 400 - 200, top: 292, width: 1520 - 400 + 400, height: 310 },
  /** The service notice takes the empty right half of the sand, so it never moves the map. */
  NOTICE: { left: 1000, top: 798, width: 1920 - CALM_SPACE.SAFE_X - 1000, height: 228 },
} as const;

/**
 * Details and its opening screen: the reading panel on the left, one island on the right.
 *
 * The same rule as Home. Back sits on the cream sky above the shoreline; on
 * Details the photograph stands on the island the way a card does on Home, so
 * the landmarks stand either side of it and below it; the island stays in the
 * sea, above the sand. The opening screen has no photograph and shows the
 * whole island.
 */
export const DETAIL = {
  PANEL: { left: 90, top: 200, width: 900, height: 700 },
  ISLAND: { x: 1450, y: 700, scale: 1.12 },
  PHOTO: { left: 1450 - 280, top: 475, width: 560, height: 315 },
  SAND_EDGE: 930,
  RIPPLES: [[1120, 320], [1700, 330]] as Array<[number, number]>,
} as const;

/** The bottom of the safe area. The hero ends here. */
export const SAFE_BOTTOM = SCREEN_HEIGHT - CALM_SPACE.SAFE_Y;

export interface ScreenBox { left: number; top: number; width: number; height: number }

export function islandCenter(kind: IslandSlotKind): { x: number; y: number } {
  return { x: HOME_ISLANDS.CENTERS[kind], y: HOME_ISLANDS.ISLAND_Y };
}

/** The card for a destination, centred over its island. */
export function islandCardBox(kind: IslandSlotKind): ScreenBox {
  const { top, width, height } = HOME_ISLANDS.CARD;
  return { left: HOME_ISLANDS.CENTERS[kind] - width / 2, top, width, height };
}

/** Two coast choices share their island without covering each other. */
export function islandChoiceBox(kind: IslandSlotKind, index: number, count: number): ScreenBox {
  const box = islandCardBox(kind);
  if (count !== 2) return box;
  const height = (box.height - 16) / 2;
  return { ...box, top: box.top + index * (height + 16), height };
}

/** An environment's heading, centred over the cards it names, in the heading band. */
export function environmentHeadingBox(kinds: IslandSlotKind[]): ScreenBox {
  const boxes = kinds.map(islandCardBox);
  const left = Math.min(...boxes.map((box) => box.left));
  const right = Math.max(...boxes.map((box) => box.left + box.width));
  return { left, top: HOME_ISLANDS.HEADING.top, width: right - left, height: HOME_ISLANDS.HEADING.height };
}

/** Where the boat waits when this island is chosen: centred on it, in the water in front. */
export function boatBox(kind: IslandSlotKind): ScreenBox {
  const { top, width, height } = HOME_ISLANDS.BOAT;
  return { left: HOME_ISLANDS.CENTERS[kind] - width / 2, top, width, height };
}

/**
 * A gentle wave across the whole width, centred on `y`.
 *
 * Quadratic segments 320 units long whose control points alternate above and
 * below the line, so the curve itself stays within half the amplitude of the
 * control points and inside `y` plus or minus WAVE_AMPLITUDE.
 */
export function shoreline(y: number, fillToBottom: boolean): string {
  const lift = HOME_ISLANDS.WAVE_AMPLITUDE * 2;
  const span = 1920 / 6;
  // The sky is drawn right to left along its lower edge, the sand left to right along its upper one.
  let path = fillToBottom ? `M0 1080V${y}` : `M0 0H1920V${y}`;
  for (let i = 0; i < 6; i += 1) {
    const from = fillToBottom ? span * i : 1920 - span * i;
    const to = fillToBottom ? from + span : from - span;
    path += `Q${(from + to) / 2} ${y + (i % 2 === 0 ? -lift : lift)} ${to} ${y}`;
  }
  return fillToBottom ? `${path}V1080Z` : `${path}Z`;
}
