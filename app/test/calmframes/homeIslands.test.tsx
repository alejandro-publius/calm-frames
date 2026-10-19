/**
 * The island Home, measured: no word, control, card, island or boat touches another.
 *
 * On Oct 18 the heading sat across the sky's shoreline, a wave ran through the
 * featured title, Watch sat on the sand line, the cards cut the lighthouse in
 * two and the boat touched the selected card. Every unit test passed, because
 * none of them knew where anything was. This one renders Home, reads the boxes
 * the screen actually places (the cards, the heading, the hero, the notice) and
 * the shapes the map actually draws (every path, ellipse and rect in the SVG,
 * through its transforms, with its stroke), and checks them against each other.
 *
 * Shapes are measured generously: a curve's box includes its control points,
 * which the curve never reaches, and half its stroke. So a shape this test
 * places clear of a card is clear of it on the screen too.
 *
 * Seen to fail, Oct 19 2026, one break at a time and restored after each:
 * islands at the old 0.86 scale (neighbouring islands meet); the boat at the
 * old y of 600 (it lands on the cards); the lighthouse moved back to x 200
 * (the card covers it); the hero at the old top of 760 (it sits on the sand
 * line); the sky's shoreline at 200 (it runs through the heading). Then, for
 * Ocean and Forest: the chosen title shown again under the cards; Forest back
 * between the Ocean islands; a card's second line back to "20 seconds"; an
 * environment given another name. And for Details: the old 660 by 380
 * photograph (it covers the landmarks), and the old sky curve (it runs up
 * into Back). Each turned its test red.
 */
import { act, fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { StyleSheet } from 'react-native';
jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));
import { CALM_SPACE } from '../../src/calmframes/calmStyles';
import { DETAIL, ENVIRONMENTS, HOME_ISLANDS, ISLAND_ORDER, IslandSlotKind, boatBox, environmentHeadingBox, islandCardBox, ScreenBox } from '../../src/calmframes/homeIslands';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import PlayerOpening from '../../src/calmframes/PlayerOpening';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
import { CheckedTitle } from '../../src/calmframes/titleStatus';
import { CONSERVATIVE_TEXT, wrapText } from '../../src/calmframes/uiLayout';
import { checkedShelf } from './shelfFixtures';

interface Box { left: number; top: number; right: number; bottom: number }
interface Node { type: string; props: Record<string, any>; children: Array<Node | string> | null }

/** Units kept between a decoration and anything a person reads or presses. */
const CLEARANCE = 4;

const islandOf = (entry: CheckedTitle): IslandSlotKind | undefined => {
  const art = titlePresentation(entry.title);
  return art.menuArt ?? (art.art === 'coastal' ? 'coastal' : undefined);
};
const consumer = checkedShelf().filter((entry) => islandOf(entry));
const profiles = [{ id: 'everyone', name: 'Everyone' }] as never;

const toBox = ({ left, top, width, height }: ScreenBox): Box => ({ left, top, right: left + width, bottom: top + height });
const grow = (box: Box, by: number): Box => ({ left: box.left - by, top: box.top - by, right: box.right + by, bottom: box.bottom + by });
const touches = (one: Box, other: Box) => one.left < other.right && other.left < one.right && one.top < other.bottom && other.top < one.bottom;
const union = (boxes: Box[]): Box => ({
  left: Math.min(...boxes.map((b) => b.left)), top: Math.min(...boxes.map((b) => b.top)),
  right: Math.max(...boxes.map((b) => b.right)), bottom: Math.max(...boxes.map((b) => b.bottom)),
});
const show = (box: Box) => `[${box.left.toFixed(1)}, ${box.top.toFixed(1)}, ${box.right.toFixed(1)}, ${box.bottom.toFixed(1)}]`;

/** A uniform scale then a translation, which is all the map's transforms use. */
interface Placement { scale: number; x: number; y: number }
const IDENTITY: Placement = { scale: 1, x: 0, y: 0 };
function parseTransform(text: string | undefined): Placement {
  let result = IDENTITY;
  if (!text) return result;
  for (const [, name, args] of text.matchAll(/(translate|scale)\(([^)]*)\)/g)) {
    const values = args.trim().split(/[\s,]+/).map(Number);
    const step = name === 'translate' ? { scale: 1, x: values[0], y: values[1] ?? 0 } : { scale: values[0], x: 0, y: 0 };
    if (name === 'scale' && values.length > 1 && values[1] !== values[0]) throw new Error(`non-uniform scale ${text}`);
    result = compose(result, step);
  }
  return result;
}
/** outer applied after inner. */
const compose = (outer: Placement, inner: Placement): Placement => ({
  scale: outer.scale * inner.scale, x: outer.scale * inner.x + outer.x, y: outer.scale * inner.y + outer.y,
});
const place = (at: Placement, box: Box): Box => ({
  left: at.scale * box.left + at.x, top: at.scale * box.top + at.y, right: at.scale * box.right + at.x, bottom: at.scale * box.bottom + at.y,
});

/** Every point a path visits or bends toward, absolute and relative commands alike. */
function pathPoints(d: string): Array<[number, number]> {
  const tokens = d.match(/[MmLlHhVvQqTtCcSsZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?/g) ?? [];
  const points: Array<[number, number]> = [];
  let i = 0, command = '', x = 0, y = 0, startX = 0, startY = 0, lastControl: [number, number] | null = null;
  const next = () => Number(tokens[i++]);
  while (i < tokens.length) {
    if (/[A-Za-z]/.test(tokens[i])) command = tokens[i++];
    const relative = command === command.toLowerCase();
    const at = (dx: number, dy: number): [number, number] => relative ? [x + dx, y + dy] : [dx, dy];
    switch (command.toUpperCase()) {
      case 'M': case 'L': { [x, y] = at(next(), next()); if (command.toUpperCase() === 'M') { startX = x; startY = y; command = relative ? 'l' : 'L'; } lastControl = null; break; }
      case 'H': { x = relative ? x + next() : next(); lastControl = null; break; }
      case 'V': { y = relative ? y + next() : next(); lastControl = null; break; }
      case 'Q': { const c = at(next(), next()); points.push(c); [x, y] = at(next(), next()); lastControl = c; break; }
      case 'T': { const c: [number, number] = lastControl ? [2 * x - lastControl[0], 2 * y - lastControl[1]] : [x, y]; points.push(c); [x, y] = at(next(), next()); lastControl = c; break; }
      case 'C': { points.push(at(next(), next())); const c = at(next(), next()); points.push(c); [x, y] = at(next(), next()); lastControl = c; break; }
      case 'S': { const c = at(next(), next()); points.push(c); [x, y] = at(next(), next()); lastControl = c; break; }
      case 'Z': { x = startX; y = startY; lastControl = null; break; }
      default: throw new Error(`path command ${command} in ${d}`);
    }
    points.push([x, y]);
  }
  return points;
}

interface Shape { id: string; box: Box; node: Node; points?: Array<[number, number]>; at: Placement }
/** Every drawn shape under a node, in screen units, with the testIDs of the groups it sits in. */
function shapes(node: Node, at: Placement, groups: string[], out: Array<Shape & { groups: string[] }>) {
  const props = node.props;
  const here = compose(at, parseTransform(props.transform));
  const stroke = props.stroke && props.stroke !== 'none' ? Number(props.strokeWidth ?? 1) / 2 : 0;
  const ids = props.testID ? [...groups, props.testID] : groups;
  let local: Box | null = null, points: Array<[number, number]> | undefined;
  if (node.type === 'Path') {
    points = pathPoints(props.d);
    local = { left: Math.min(...points.map((p) => p[0])), top: Math.min(...points.map((p) => p[1])), right: Math.max(...points.map((p) => p[0])), bottom: Math.max(...points.map((p) => p[1])) };
  } else if (node.type === 'Ellipse' || node.type === 'Circle') {
    const cx = Number(props.cx ?? 0), cy = Number(props.cy ?? 0), rx = Number(props.rx ?? props.r), ry = Number(props.ry ?? props.r);
    local = { left: cx - rx, top: cy - ry, right: cx + rx, bottom: cy + ry };
  } else if (node.type === 'Rect') {
    const x = Number(props.x ?? 0), y = Number(props.y ?? 0);
    local = { left: x, top: y, right: x + Number(props.width), bottom: y + Number(props.height) };
  }
  if (local) out.push({ id: ids[ids.length - 1] ?? node.type, groups: ids, node, at: here, points, box: place(here, grow(local, stroke)) });
  for (const child of node.children ?? []) if (typeof child !== 'string') shapes(child, here, ids, out);
}

function find(node: Node | string, test: (n: Node) => boolean, out: Node[] = []): Node[] {
  if (typeof node === 'string') return out;
  if (test(node)) out.push(node);
  for (const child of node.children ?? []) find(child, test, out);
  return out;
}
const byID = (tree: Node, id: string) => {
  const found = find(tree, (n) => n.props.testID === id && typeof n.type === 'string');
  if (!found.length) throw new Error(`no ${id}`);
  return found[0];
};
/** A block the screen places at an absolute box, read back off its style. */
function placedBox(node: Node): Box {
  const style = StyleSheet.flatten(node.props.style) as Record<string, unknown>;
  expect(style.position).toBe('absolute');
  for (const key of ['left', 'top', 'width', 'height']) expect(typeof style[key]).toBe('number');
  return toBox(style as unknown as ScreenBox);
}

function measureHome(element: React.ReactElement) {
  const view = render(element);
  const tree = view.toJSON() as unknown as Node;
  const svg = find(byID(tree, 'coastal-world'), (n) => n.type === 'Svg')[0];
  expect(svg.props.viewBox).toBe('0 0 1920 1080');
  const drawn: Array<Shape & { groups: string[] }> = [];
  shapes(svg, IDENTITY, [], drawn);
  const inGroup = (id: string) => drawn.filter((shape) => shape.groups.includes(id));
  const band = (id: string) => {
    // A shoreline's own edge, without the corners it fills to.
    const ys = inGroup(id)[0].points!.map((p) => p[1]).filter((y) => y !== 0 && y !== 1080);
    return { top: Math.min(...ys), bottom: Math.max(...ys) };
  };
  const cards = find(tree, (n) => typeof n.props.testID === 'string' && /^kid-home-poster-prepared-[0-9a-f]+$/.test(n.props.testID) && n.type === 'View');
  const boat = find(tree, (n) => typeof n.props.testID === 'string' && n.props.testID.startsWith('coastal-boat-') && n.type === 'View')[0];
  return { view, tree, drawn, inGroup, band, cards, boat };
}

const islandBox = (measured: ReturnType<typeof measureHome>, kind: IslandSlotKind) =>
  union(measured.inGroup(`island-${kind}`).filter((shape) => !shape.groups.includes(`island-landmarks-${kind}`) && shape.node.type === 'Path').map((shape) => shape.box));
const ringBox = (measured: ReturnType<typeof measureHome>, kind: IslandSlotKind) =>
  measured.inGroup(`island-${kind}`).find((shape) => shape.node.type === 'Ellipse' && shape.groups[shape.groups.length - 1] === `island-${kind}`)!.box;

describe('the island Home with all three destinations', () => {
  const measured = measureHome(<KidHomeScreen titles={consumer} onOpen={jest.fn()} onPlay={jest.fn()} onOpenParentArea={jest.fn()} profiles={profiles} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  const sky = measured.band('home-sky');
  const sandEdge = measured.band('home-sand-edge');
  const sand = measured.band('home-sand');
  const headings = ENVIRONMENTS.map(({ name }) => ({ name, box: placedBox(byID(measured.tree, `kid-home-environment-${name.toLowerCase()}`)) }));
  const hero = placedBox(byID(measured.tree, 'kid-home-hero'));
  const cards = measured.cards.map((node) => ({ node, box: placedBox(node) }));
  const header: Box = { left: CALM_SPACE.SAFE_X, top: CALM_SPACE.SAFE_Y, right: 1920 - CALM_SPACE.SAFE_X, bottom: HOME_ISLANDS.HEADER_BOTTOM };
  const read = [header, ...headings.map((one) => one.box), hero, ...cards.map((card) => card.box)];

  it('places every card on its own island, at the box homeIslands.ts gives it', () => {
    expect(cards).toHaveLength(3);
    for (const { node, box } of cards) {
      const entry = consumer.find((one) => node.props.testID === `kid-home-poster-${one.title.id}`)!;
      const kind = islandOf(entry)!;
      expect(box).toEqual(toBox(islandCardBox(kind)));
      // The ring is drawn about the island's own centre; the shore is not symmetric.
      const ring = ringBox(measured, kind);
      expect((ring.left + ring.right) / 2).toBeCloseTo((box.left + box.right) / 2, 5);
    }
  });

  it('names each environment once, Ocean over Acadia and Sea Otters and Forest over Forest, on the cream sky', () => {
    expect(header.bottom + CLEARANCE).toBeLessThanOrEqual(sky.top);
    expect(headings.map((one) => String(byID(measured.tree, `kid-home-environment-${one.name.toLowerCase()}-name`).children!.join('')))).toEqual(['Ocean', 'Forest']);
    for (const { name, box } of headings) {
      expect(box.top).toBeGreaterThanOrEqual(header.bottom);
      expect(box.bottom + CLEARANCE).toBeLessThanOrEqual(sky.top);
      const kinds = ENVIRONMENTS.find((one) => one.name === name)!.kinds;
      expect(box).toEqual(toBox(environmentHeadingBox(kinds)));
      // Over exactly its own cards: spanning them, and touching no other card's column.
      const own = cards.filter((card) => kinds.includes(islandOf(consumer.find((one) => card.node.props.testID === `kid-home-poster-${one.title.id}`)!)!));
      expect(own).toHaveLength(kinds.length);
      expect(box.left).toBe(Math.min(...own.map((card) => card.box.left)));
      expect(box.right).toBe(Math.max(...own.map((card) => card.box.right)));
      for (const card of cards.filter((one) => !own.includes(one))) expect(card.box.left >= box.right || card.box.right <= box.left).toBe(true);
    }
    expect(touches(headings[0].box, headings[1].box)).toBe(false);
    // The old single heading is gone from the map.
    expect(find(measured.tree, (n) => n.props.testID === 'kid-home-heading')).toHaveLength(0);
  });

  it('lays the islands out as the environments read: Acadia, Sea Otters, then Forest', () => {
    const order = [...cards].sort((a, b) => a.box.left - b.box.left)
      .map((card) => islandOf(consumer.find((one) => card.node.props.testID === `kid-home-poster-${one.title.id}`)!));
    expect(order).toEqual(['coastal', 'sea-otters', 'forest']);
    expect(ENVIRONMENTS.flatMap((one) => one.kinds)).toEqual(ISLAND_ORDER);
  });

  it('does not repeat the chosen title under the cards: the sand holds Watch and Details, and Watch says what it plays', () => {
    expect(find(measured.tree, (n) => n.props.testID === 'kid-home-video-title')).toHaveLength(0);
    expect(find(measured.tree, (n) => n.props.testID === 'kid-home-video-meta')).toHaveLength(0);
    expect(hero).toEqual(toBox(HOME_ISLANDS.ACTIONS));
    expect(byID(measured.tree, 'kid-home-watch').props.accessibilityLabel).toBe('Watch: Acadia');
    expect(byID(measured.tree, 'kid-home-more-info').props.accessibilityLabel).toBe('Details: Acadia');
  });

  it('gives every card the same two lines: a short name, then its sound and length', () => {
    for (const card of cards) {
      const lines = find(card.node, (n) => n.type === 'Text').map((n) => String(n.children!.join('')));
      expect(lines).toHaveLength(2);
      expect(lines[0].length).toBeLessThanOrEqual(12);
      expect(lines[1]).toMatch(/^(Silent|Nature audio) · \d+ sec$/);
    }
  });

  it('keeps Watch and Details on the cream sand, below both of its shorelines', () => {
    expect(sandEdge.bottom).toBeLessThanOrEqual(sand.bottom);
    expect(hero.top).toBeGreaterThanOrEqual(sand.bottom + CLEARANCE);
    expect(hero.bottom).toBeLessThanOrEqual(1080 - CALM_SPACE.SAFE_Y);
  });

  it('keeps the cards, the islands, the route and the waves in the sea, off both shorelines', () => {
    const sea = { top: sky.bottom, bottom: sandEdge.top };
    const inSea = [
      ...cards.map((card) => ({ id: card.node.props.testID, box: card.box })),
      ...measured.drawn.filter((shape) => shape.groups.some((id) => id.startsWith('island-') || id === 'home-route' || id === 'home-ripple')),
    ];
    for (const { id, box } of inSea) {
      expect({ id, top: box.top >= sea.top + CLEARANCE }).toEqual({ id, top: true });
      expect({ id, bottom: box.bottom + CLEARANCE <= sea.bottom }).toEqual({ id, bottom: true });
    }
  });

  it('keeps every landmark beside its card, not under it or any other', () => {
    for (const kind of ISLAND_ORDER) {
      const landmarks = measured.inGroup(`island-landmarks-${kind}`);
      expect(landmarks.length).toBeGreaterThan(0);
      for (const shape of landmarks) {
        for (const card of cards) {
          expect({ kind, shape: show(shape.box), card: show(card.box), touches: touches(grow(shape.box, CLEARANCE), card.box) })
            .toEqual(expect.objectContaining({ touches: false }));
        }
      }
    }
  });

  it('keeps the islands and their rings apart', () => {
    for (let i = 0; i < ISLAND_ORDER.length; i += 1) {
      for (let j = i + 1; j < ISLAND_ORDER.length; j += 1) {
        const [a, b] = [ISLAND_ORDER[i], ISLAND_ORDER[j]];
        expect({ a, b, islands: touches(islandBox(measured, a), islandBox(measured, b)) }).toEqual({ a, b, islands: false });
        expect({ a, b, rings: touches(ringBox(measured, a), ringBox(measured, b)) }).toEqual({ a, b, rings: false });
      }
    }
  });

  it('puts the boat in open water at each destination, clear of every card, island, wave and word', () => {
    for (const kind of ISLAND_ORDER) {
      const boat = toBox(boatBox(kind));
      for (const box of read) expect({ kind, against: show(box), touches: touches(grow(boat, CLEARANCE), box) }).toEqual(expect.objectContaining({ touches: false }));
      for (const other of ISLAND_ORDER) expect({ kind, other, touches: touches(boat, islandBox(measured, other)) }).toEqual(expect.objectContaining({ touches: false }));
      for (const shape of measured.inGroup('home-ripple')) expect({ kind, ripple: show(shape.box), touches: touches(boat, shape.box) }).toEqual(expect.objectContaining({ touches: false }));
      expect(boat.top).toBeGreaterThanOrEqual(sky.bottom);
      expect(boat.bottom + CLEARANCE).toBeLessThanOrEqual(sandEdge.top);
    }
    // The boat the screen draws is the one this test measured.
    const style = StyleSheet.flatten(measured.boat.props.style) as Record<string, any>;
    const shift = Object.assign({}, ...style.transform);
    expect({ left: style.left + shift.translateX, top: style.top + shift.translateY, width: style.width, height: style.height }).toEqual(boatBox('coastal'));
  });

  it('keeps the waves and the route off every card, island and each other', () => {
    const ripples = measured.inGroup('home-ripple');
    const route = union(measured.inGroup('home-route').map((shape) => shape.box));
    for (const ripple of ripples) {
      for (const box of [...read, route]) expect(touches(grow(ripple.box, CLEARANCE), box)).toBe(false);
      for (const kind of ISLAND_ORDER) expect(touches(ripple.box, ringBox(measured, kind))).toBe(false);
    }
    for (const box of read) expect(touches(grow(route, CLEARANCE), box)).toBe(false);
    for (const kind of ISLAND_ORDER) expect(touches(route, islandBox(measured, kind))).toBe(false);
  });

  it('holds every word on one line inside the box it is given, inside the safe area', () => {
    for (const box of read) {
      expect(box.left).toBeGreaterThanOrEqual(CALM_SPACE.SAFE_X);
      expect(box.right).toBeLessThanOrEqual(1920 - CALM_SPACE.SAFE_X);
      expect(box.top).toBeGreaterThanOrEqual(CALM_SPACE.SAFE_Y);
      expect(box.bottom).toBeLessThanOrEqual(1080 - CALM_SPACE.SAFE_Y);
    }
    for (const card of cards) {
      // A card's two lines are clipped to one each rather than allowed to grow the card.
      for (const text of find(card.node, (n) => n.type === 'Text')) expect(text.props.numberOfLines).toBe(1);
    }
    for (const text of find(byID(measured.tree, 'kid-home-hero'), (n) => n.type === 'Text' && typeof n.children?.[0] === 'string')) {
      const style = StyleSheet.flatten(text.props.style) as { fontSize: number };
      expect(wrapText(String(text.children!.join('')), style.fontSize, hero.right - hero.left, CONSERVATIVE_TEXT).lines).toBe(1);
    }
  });

  it('sizes the actions and every card to exactly what they hold', () => {
    const watch = StyleSheet.flatten(byID(measured.tree, 'kid-home-watch').props.style) as Record<string, number>;
    expect(watch.minHeight).toBe(hero.bottom - hero.top);
    for (const card of cards) {
      const style = StyleSheet.flatten(card.node.props.style) as Record<string, number>;
      const image = StyleSheet.flatten(find(card.node, (n) => n.type === 'Image')[0].props.style) as Record<string, number>;
      const texts = find(card.node, (n) => n.type === 'Text').map((n) => (StyleSheet.flatten(n.props.style) as Record<string, number>).lineHeight);
      const content = style.borderWidth + 2 * style.padding + image.height + 8 + texts.reduce((a, b) => a + b, 0) + style.borderBottomWidth;
      expect(content).toBe(card.box.bottom - card.box.top);
    }
  });
});

it('every destination selected still measures clear, because the boat follows the selection', () => {
  for (const entry of consumer) {
    const kind = islandOf(entry)!;
    const measured = measureHome(<KidHomeScreen titles={consumer} selectedTitleId={entry.title.id} onOpen={jest.fn()} onPlay={jest.fn()} />);
    const style = StyleSheet.flatten(measured.boat.props.style) as Record<string, any>;
    const shift = Object.assign({}, ...style.transform);
    expect({ left: style.left + shift.translateX, top: style.top + shift.translateY }).toEqual({ left: boatBox(kind).left, top: boatBox(kind).top });
    measured.view.unmount();
  }
});

it('puts the offline notice in the empty half of the sand, where it moves nothing', () => {
  const online = measureHome(<KidHomeScreen titles={consumer} onOpen={jest.fn()} />);
  const offline = measureHome(<KidHomeScreen titles={consumer} offline onOpen={jest.fn()} />);
  const slot = placedBox(byID(offline.tree, 'kid-home-notice-slot'));
  expect(slot).toEqual(toBox(HOME_ISLANDS.NOTICE));
  const hero = placedBox(byID(offline.tree, 'kid-home-hero'));
  expect(touches(slot, hero)).toBe(false);
  expect(slot.top).toBeGreaterThanOrEqual(offline.band('home-sand').bottom + CLEARANCE);
  expect(slot.right).toBeLessThanOrEqual(1920 - CALM_SPACE.SAFE_X);
  for (const id of ['kid-home-hero', 'kid-home-environment-ocean', 'kid-home-environment-forest']) expect(placedBox(byID(offline.tree, id))).toEqual(placedBox(byID(online.tree, id)));
  expect(offline.cards.map(placedBox)).toEqual(online.cards.map(placedBox));
});

it('gives Who is watching the row of cards while it is open, clear of the header, the boat and the hero', () => {
  const several = [{ id: 'everyone', name: 'Everyone' }, { id: 'robin', name: 'Robin' }, { id: 'sam', name: 'Sam' }] as never;
  const measured = measureHome(<KidHomeScreen titles={consumer} onOpen={jest.fn()} onPlay={jest.fn()} profiles={several} activeProfileId="everyone" onChooseProfile={jest.fn()} />);
  act(() => { fireEvent.press(measured.view.getByTestId('kid-home-choose-profile')); });
  const tree = measured.view.toJSON() as unknown as Node;
  const panel = byID(tree, 'kid-home-picker-panel');
  const style = StyleSheet.flatten(panel.props.style) as Record<string, number>;
  const box = toBox({ left: style.left, top: style.top, width: style.width, height: style.minHeight });
  expect(box).toEqual(toBox(HOME_ISLANDS.PICKER));
  // The cards and the heading step aside rather than sit under the panel, and the panel is not in the flow above them.
  expect(find(tree, (n) => typeof n.props.testID === 'string' && /^kid-home-poster-prepared-[0-9a-f]+$/.test(n.props.testID))).toHaveLength(0);
  expect(find(tree, (n) => String(n.props.testID ?? '').startsWith('kid-home-environment-'))).toHaveLength(0);
  expect(find(tree, (n) => n.props.testID === 'kid-home-profiles')).toHaveLength(1);
  expect(find(panel, (n) => n.props.testID === 'kid-home-profiles')).toHaveLength(1);
  // What it holds, measured: heading, one row of chips, the chosen line, and the panel's own edges.
  const picker = byID(panel, 'kid-home-profiles');
  const heightOf = (node: Node) => { const s = StyleSheet.flatten(node.props.style) as Record<string, number>; return (s.lineHeight ?? 0) + (s.marginTop ?? 0) + (s.marginBottom ?? 0); };
  const texts = find(picker, (n) => n.type === 'Text' && n.props.accessible !== false && !String(n.props.testID ?? '').endsWith('-name'));
  const chip = StyleSheet.flatten(find(picker, (n) => n.props.accessibilityRole === 'radio' && n.type === 'View')[0].props.style) as Record<string, number>;
  const name = StyleSheet.flatten(find(picker, (n) => String(n.props.testID ?? '').endsWith('-name'))[0].props.style) as Record<string, number>;
  const chipRow = 2 * chip.borderWidth + 2 * chip.paddingVertical + name.lineHeight + chip.marginBottom;
  const blockMargin = (StyleSheet.flatten(picker.props.style) as Record<string, number>).marginBottom ?? 0;
  const content = style.borderWidth * 2 + style.padding + texts.map(heightOf).reduce((a, b) => a + b, 0) + chipRow + blockMargin;
  expect(content).toBeLessThanOrEqual(HOME_ISLANDS.PICKER.height);
  const hero = placedBox(byID(tree, 'kid-home-hero'));
  const boats = ISLAND_ORDER.map((kind) => toBox(boatBox(kind)));
  for (const other of [hero, ...boats]) expect(touches(grow(box, CLEARANCE), other)).toBe(false);
  expect(box.top).toBeGreaterThanOrEqual(measured.band('home-sky').bottom + CLEARANCE);
  expect(box.left).toBeGreaterThanOrEqual(CALM_SPACE.SAFE_X);
  expect(box.right).toBeLessThanOrEqual(1920 - CALM_SPACE.SAFE_X);
});

it('gives an island with no card its full scenery, and keeps every island clear of the hero', () => {
  const acadia = consumer.filter((entry) => islandOf(entry) === 'coastal');
  const measured = measureHome(<KidHomeScreen titles={acadia} onOpen={jest.fn()} onPlay={jest.fn()} />);
  expect(measured.cards).toHaveLength(0);
  for (const kind of ISLAND_ORDER) expect(measured.inGroup(`island-landmarks-${kind}`)).toHaveLength(0);
  const hero = placedBox(byID(measured.tree, 'kid-home-hero'));
  // With no card to name it, the title and runtime stand above Watch, filling the hero exactly.
  expect(hero).toEqual(toBox(HOME_ISLANDS.HERO));
  const lines = (id: string) => { const s = StyleSheet.flatten(byID(measured.tree, id).props.style) as Record<string, number>; return s.lineHeight + (s.marginTop ?? 0) + (s.marginBottom ?? 0); };
  expect(lines('kid-home-video-title') + lines('kid-home-video-meta') + 88).toBe(hero.bottom - hero.top);
  for (const id of ['kid-home-video-title', 'kid-home-video-meta']) {
    const node = byID(measured.tree, id);
    const style = StyleSheet.flatten(node.props.style) as { fontSize: number };
    expect(wrapText(String(node.children!.join('')), style.fontSize, hero.right - hero.left, CONSERVATIVE_TEXT).lines).toBe(1);
  }
  expect(hero.top).toBeGreaterThanOrEqual(measured.band('home-sand').bottom + CLEARANCE);
  const sky = measured.band('home-sky'), sandEdge = measured.band('home-sand-edge');
  for (const shape of measured.drawn.filter((one) => one.groups.some((id) => id.startsWith('island-')))) {
    expect(touches(grow(shape.box, CLEARANCE), hero)).toBe(false);
    expect(shape.box.top).toBeGreaterThanOrEqual(sky.bottom + CLEARANCE);
    expect(shape.box.bottom + CLEARANCE).toBeLessThanOrEqual(sandEdge.top);
  }
  for (let i = 0; i < ISLAND_ORDER.length - 1; i += 1) expect(touches(ringBox(measured, ISLAND_ORDER[i]), ringBox(measured, ISLAND_ORDER[i + 1]))).toBe(false);
});

it('keeps the flowing shelf for a shelf whose videos are not all islands', () => {
  const legacy = checkedShelf().filter((entry) => !islandOf(entry));
  const view = render(<KidHomeScreen titles={legacy} onOpen={jest.fn()} />);
  expect(view.queryByTestId('kid-home-islands')).toBeNull();
  view.unmount();
  const islands = render(<KidHomeScreen titles={consumer} onOpen={jest.fn()} />);
  expect(islands.getByTestId('kid-home-islands')).toBeTruthy();
});

describe.each(ISLAND_ORDER)('Details and its opening for the %s island', (kind) => {
  const entry = consumer.find((one) => islandOf(one) === kind)!;
  const header: Box = { left: CALM_SPACE.SAFE_X, top: CALM_SPACE.SAFE_Y, right: 1920 - CALM_SPACE.SAFE_X, bottom: HOME_ISLANDS.HEADER_BOTTOM };
  const scenery = (measured: ReturnType<typeof measureHome>) => {
    const island = union(measured.inGroup(`island-${kind}`).filter((shape) => shape.node.type === 'Path' && !shape.groups.includes(`island-landmarks-${kind}`)).map((shape) => shape.box));
    const everything = union(measured.inGroup(`island-${kind}`).map((shape) => shape.box));
    return { island, everything, sky: measured.band('home-sky'), sandEdge: measured.band('home-sand-edge'), panel: measured.drawn.find((shape) => shape.id === 'detail-panel')!.box };
  };

  it('stands the photograph on the island with every landmark beside or below it, Back on the sky', () => {
    const measured = measureHome(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} onBack={jest.fn()} />);
    const { everything, sky, sandEdge, panel } = scenery(measured);
    const photo = placedBox(byID(measured.tree, 'title-details-destination-image'));
    expect(photo).toEqual(toBox(DETAIL.PHOTO));
    const landmarks = measured.inGroup(`island-landmarks-${kind}`);
    expect(landmarks.length).toBeGreaterThan(0);
    for (const shape of landmarks) expect({ kind, shape: show(shape.box), touches: touches(grow(shape.box, CLEARANCE), photo) }).toEqual(expect.objectContaining({ touches: false }));
    expect(header.bottom + CLEARANCE).toBeLessThanOrEqual(sky.top);
    expect(everything.top).toBeGreaterThanOrEqual(sky.bottom + CLEARANCE);
    expect(everything.bottom + CLEARANCE).toBeLessThanOrEqual(sandEdge.top);
    expect(touches(everything, panel)).toBe(false);
    expect(touches(photo, panel)).toBe(false);
    for (const ripple of measured.inGroup('home-ripple')) {
      for (const box of [photo, panel, everything]) expect(touches(grow(ripple.box, CLEARANCE), box)).toBe(false);
      expect(ripple.box.top).toBeGreaterThanOrEqual(sky.bottom + CLEARANCE);
    }
  });

  it('shows the whole island on the opening, where nothing stands on it, in the same place', () => {
    const measured = measureHome(<PlayerOpening title={titlePresentation(entry.title).name} menuArt={kind} onBack={jest.fn()} />);
    const { everything, sky, sandEdge, panel } = scenery(measured);
    expect(measured.inGroup(`island-landmarks-${kind}`)).toHaveLength(0);
    expect(header.bottom + CLEARANCE).toBeLessThanOrEqual(sky.top);
    expect(everything.top).toBeGreaterThanOrEqual(sky.bottom + CLEARANCE);
    expect(everything.bottom + CLEARANCE).toBeLessThanOrEqual(sandEdge.top);
    expect(touches(everything, panel)).toBe(false);
    const ring = measured.inGroup(`island-${kind}`).find((shape) => shape.node.type === 'Ellipse')!.box;
    expect((ring.left + ring.right) / 2).toBeCloseTo(DETAIL.ISLAND.x, 5);
  });
});
