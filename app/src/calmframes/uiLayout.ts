/**
 * Where things sit on a screen, measured off the rendered tree.
 *
 * The ten foot pass measures type, contrast and focus off the rendered tree,
 * because the virtual device cannot be photographed (uiContrast.ts says why).
 * Overlap needs positions as well, and the test renderer does no layout: it
 * hands back styles, not rectangles. So this is a small ruler for the one kind
 * of layout the player's own words use: blocks placed absolutely on the
 * screen, holding columns of text with padding, borders, margins and a
 * maximum width.
 *
 * It errs on the side of too big. Text is wrapped as if every character were
 * 0.6 of the font size wide, where English in a television's sans serif
 * averages nearer 0.5, and a Text that sets no line height is given 1.35 times
 * its size. A box this ruler places clear of another is clear on the screen
 * as long as the text keeps inside those bounds. Anything it does not
 * understand, a row, a percentage, a block placed inside another, is an error
 * rather than a guess.
 *
 * Nothing here is imported by a screen. It exists so tests can measure them.
 */

import { flattenStyle, RenderedNode } from './uiContrast';

/** A rectangle in 1080p units, from the top left of the screen. */
export interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface ScreenSize {
  width: number;
  height: number;
}

export interface TextMetrics {
  /** The width allowed for one character, as a share of the font size. */
  advanceEm: number;
  /** The line height used when a Text sets none, as a share of the font size. */
  lineHeightEm: number;
}

/** Wider and taller than real text, so overlap is overstated, never missed. */
export const CONSERVATIVE_TEXT: TextMetrics = {
  advanceEm: 0.6,
  lineHeightEm: 1.35,
};

export function boxesOverlap(one: Box, other: Box): boolean {
  return (
    one.left < other.right &&
    other.left < one.right &&
    one.top < other.bottom &&
    other.top < one.bottom
  );
}

/** A style value that has to be a plain number of units, if it is there at all. */
function units(style: Record<string, unknown>, key: string): number | undefined {
  const value = style[key];
  if (value === undefined) {
    return undefined;
  }
  if (typeof value !== 'number') {
    throw new Error(`the ruler measures plain numbers, and ${key} is ${String(value)}`);
  }
  return value;
}

/** The first of these keys that is set, as React Native resolves them. */
function first(style: Record<string, unknown>, keys: string[]): number {
  for (const key of keys) {
    const value = units(style, key);
    if (value !== undefined) {
      return value;
    }
  }
  return 0;
}

interface Edges {
  horizontal: number;
  vertical: number;
}

/** Padding and border together: what a block puts between its edge and its content. */
function insets(style: Record<string, unknown>): Edges & { left: number; top: number } {
  const padding = (side: string, axis: string) =>
    first(style, [`padding${side}`, `padding${axis}`, 'padding']);
  const border = (side: string) =>
    first(style, [`border${side}Width`, 'borderWidth']);
  const left = padding('Left', 'Horizontal') + border('Left');
  const right = padding('Right', 'Horizontal') + border('Right');
  const top = padding('Top', 'Vertical') + border('Top');
  const bottom = padding('Bottom', 'Vertical') + border('Bottom');
  return { left, top, horizontal: left + right, vertical: top + bottom };
}

function margins(style: Record<string, unknown>): Edges {
  const margin = (side: string, axis: string) =>
    first(style, [`margin${side}`, `margin${axis}`, 'margin']);
  return {
    horizontal: margin('Left', 'Horizontal') + margin('Right', 'Horizontal'),
    vertical: margin('Top', 'Vertical') + margin('Bottom', 'Vertical'),
  };
}

function textOf(node: RenderedNode | string | number | null | undefined): string {
  if (node === null || node === undefined) {
    return '';
  }
  if (typeof node === 'string' || typeof node === 'number') {
    return String(node);
  }
  return (node.children ?? [])
    .map((child) => textOf(child as RenderedNode))
    .join('');
}

/**
 * How many lines a piece of text takes at this width, and how wide the widest
 * one is, breaking at spaces and, for a word longer than a line, inside it.
 */
export function wrapText(
  text: string,
  fontSize: number,
  width: number,
  metrics: TextMetrics = CONSERVATIVE_TEXT,
): { lines: number; widest: number } {
  const advance = fontSize * metrics.advanceEm;
  const perLine = Math.max(1, Math.floor(width / advance));
  let lines = 0;
  let used = 0;
  let widest = 0;
  const endLine = () => {
    lines += 1;
    widest = Math.max(widest, used);
    used = 0;
  };
  for (const word of text.split(/\s+/).filter(Boolean)) {
    let length = word.length;
    if (used > 0 && used + 1 + length > perLine) {
      endLine();
    }
    if (used > 0) {
      used += 1;
    }
    while (used + length > perLine) {
      length -= perLine - used;
      used = perLine;
      endLine();
    }
    used += length;
  }
  if (used > 0) {
    endLine();
  }
  return { lines, widest: widest * advance };
}

interface Size {
  width: number;
  height: number;
}

/**
 * The outer size of one block, given the width it may take.
 *
 * `stretch` is whether its parent stretches it across, which is React
 * Native's default; a parent that centres its children lets each one shrink to
 * what it holds instead.
 */
function measure(
  node: RenderedNode,
  available: number,
  stretch: boolean,
  metrics: TextMetrics,
  inheritedFontSize?: number,
): Size {
  const style = flattenStyle(node.props?.style);
  if (style.display === 'none') {
    return { width: 0, height: 0 };
  }
  const inset = insets(style);
  const fixedWidth = units(style, 'width');
  const fixedHeight = units(style, 'height');
  const maxWidth = units(style, 'maxWidth') ?? Infinity;
  const outer = Math.min(available, maxWidth, fixedWidth ?? Infinity);
  const inner = Math.max(0, outer - inset.horizontal);

  let contentWidth = 0;
  let contentHeight = 0;
  if (node.type === 'Text') {
    const fontSize = units(style, 'fontSize') ?? inheritedFontSize;
    if (fontSize === undefined) {
      throw new Error('a Text with no font size cannot be measured');
    }
    const lineHeight = units(style, 'lineHeight') ?? fontSize * metrics.lineHeightEm;
    const { lines, widest } = wrapText(textOf(node), fontSize, inner, metrics);
    contentWidth = Math.min(inner, widest);
    contentHeight = lines * lineHeight;
  } else {
    const direction = style.flexDirection ?? 'column';
    if (direction !== 'column') {
      throw new Error(`the ruler lays out columns only, and found ${String(direction)}`);
    }
    for (const child of node.children ?? []) {
      if (!child || typeof child === 'string') {
        continue;
      }
      const childStyle = flattenStyle(child.props?.style);
      if (childStyle.position === 'absolute') {
        throw new Error('a block placed inside another block is not something this ruler measures');
      }
      const margin = margins(childStyle);
      // A block's own size comes from the natural widths of what it holds.
      // Stretching a child afterwards widens it to the block, not the block
      // to the screen, and text has already been wrapped at the width it may
      // take, so its height is the same either way.
      const size = measure(
        child,
        Math.max(0, inner - margin.horizontal),
        false,
        metrics,
        units(style, 'fontSize') ?? inheritedFontSize,
      );
      contentWidth = Math.max(contentWidth, size.width + margin.horizontal);
      contentHeight += size.height + margin.vertical;
    }
  }

  const width =
    fixedWidth ?? (stretch ? outer : Math.min(outer, contentWidth + inset.horizontal));
  const height = fixedHeight ?? contentHeight + inset.vertical;
  return { width, height };
}

type TreeLike = RenderedNode | string | null | undefined;

/** The first node in a rendered tree with this testID. */
export function findByTestID(
  tree: TreeLike | TreeLike[],
  testID: string,
): RenderedNode | null {
  if (!tree || typeof tree === 'string') {
    return null;
  }
  if (Array.isArray(tree)) {
    for (const one of tree) {
      const found = findByTestID(one, testID);
      if (found) {
        return found;
      }
    }
    return null;
  }
  if (tree.props?.testID === testID) {
    return tree;
  }
  return findByTestID(tree.children ?? [], testID);
}

/**
 * Where the absolutely placed block with this testID sits on the screen.
 *
 * The block is placed against the whole screen, which is what the player's
 * own layer is laid out in. A transparent block stretched across the screen
 * that centres what it holds is measured by what it holds, because that is
 * what a person sees; the empty sides of it cover nothing.
 */
export function placedBox(
  tree: RenderedNode | RenderedNode[] | null | undefined,
  testID: string,
  screen: ScreenSize,
  metrics: TextMetrics = CONSERVATIVE_TEXT,
): Box | null {
  const node = findByTestID(tree, testID);
  if (!node) {
    return null;
  }
  const style = flattenStyle(node.props?.style);
  if (style.position !== 'absolute') {
    throw new Error(`${testID} is not placed absolutely, so the ruler cannot say where it is`);
  }
  const left = units(style, 'left');
  const right = units(style, 'right');
  const top = units(style, 'top');
  const bottom = units(style, 'bottom');
  const stretched = left !== undefined && right !== undefined;
  const available = screen.width - (left ?? 0) - (right ?? 0);
  const size = measure(node, available, stretched, metrics);

  let x =
    left !== undefined
      ? left
      : right !== undefined
        ? screen.width - right - size.width
        : 0;
  let width = size.width;
  const y =
    top !== undefined
      ? top
      : bottom !== undefined
        ? screen.height - bottom - size.height
        : 0;

  const painted =
    typeof style.backgroundColor === 'string' &&
    style.backgroundColor !== 'transparent';
  const inset = insets(style).horizontal > 0;
  if (stretched && style.alignItems === 'center' && !painted && !inset) {
    const held = measure(node, available, false, metrics);
    x += (size.width - held.width) / 2;
    width = held.width;
  }

  return { left: x, top: y, right: x + width, bottom: y + size.height };
}
