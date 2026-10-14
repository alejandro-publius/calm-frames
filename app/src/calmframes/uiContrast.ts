/**
 * Measuring a screen instead of looking at it.
 *
 * The Vega Virtual Device cannot be photographed. The app draws on a GPU layer
 * that macOS screen capture and QEMU's screendump both miss, so every
 * screenshot comes back black. docs/ENVIRONMENT.md and CLAUDE.md both record
 * it. That leaves two honest ways to check a ten foot interface:
 *
 *   1. the app's own capture path (uiCapture.ts), which records the colours
 *      each screen paints, read off the rendered tree;
 *   2. measurement, which is this file: read the type sizes, the colours and
 *      the focus rings off the same rendered tree and put numbers on them.
 *
 * So the ten foot pass is a set of measurements with thresholds, not a set of
 * screenshots with opinions. test/calmframes/tenFoot.test.tsx renders every
 * screen and every state and applies them.
 *
 * What the thresholds are, and where they come from:
 *
 * - Contrast is WCAG 2.2's relative luminance and contrast ratio, the same
 *   arithmetic flashmap uses on video frames. The formula is in
 *   docs/SPEC_SOURCES.md. 4.5 to 1 is WCAG AA for text below the large text
 *   size; all our text is above it, so 4.5 is already stricter than AA asks,
 *   which is the point on a television across a room.
 * - 3 to 1 for the focus ring against both colours it sits between is WCAG
 *   2.2's non-text contrast.
 * - Type size and safe margins are not from a specification. The reasoning is
 *   written out in calmStyles.ts next to the numbers.
 *
 * Nothing here is imported by a screen. It exists so tests can measure them.
 */

/** One channel of sRGB, linearised. WCAG 2.2 relative luminance. */
function channel(value: number): number {
  const unit = value / 255;
  return unit <= 0.03928 ? unit / 12.92 : ((unit + 0.055) / 1.055) ** 2.4;
}

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

/** #rgb, #rrggbb or #rrggbbaa. Anything else is a mistake worth throwing on. */
export function parseColour(colour: string): Rgb {
  const text = colour.trim().replace(/^#/, '');
  const expanded =
    text.length === 3
      ? text
          .split('')
          .map((one) => one + one)
          .join('')
      : text;
  if (!/^[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(expanded)) {
    throw new Error(`not a colour this can measure: ${colour}`);
  }
  return {
    r: parseInt(expanded.slice(0, 2), 16),
    g: parseInt(expanded.slice(2, 4), 16),
    b: parseInt(expanded.slice(4, 6), 16),
  };
}

export function relativeLuminance(colour: string): number {
  const { r, g, b } = parseColour(colour);
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** WCAG contrast ratio, 1 to 21, whichever way round the two colours go. */
export function contrastRatio(one: string, other: string): number {
  const first = relativeLuminance(one);
  const second = relativeLuminance(other);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

/** Round the way a report should: two decimals, never rounding up a failure. */
export function roundRatio(ratio: number): number {
  return Math.floor(ratio * 100) / 100;
}

type StyleLike = unknown;

export function flattenStyle(style: StyleLike): Record<string, unknown> {
  if (Array.isArray(style)) {
    return style.reduce<Record<string, unknown>>(
      (out, one) => ({ ...out, ...flattenStyle(one) }),
      {},
    );
  }
  if (style && typeof style === 'object') {
    return style as Record<string, unknown>;
  }
  return {};
}

/** A node of a rendered tree, as react-test-renderer's toJSON hands it over. */
export interface RenderedNode {
  type?: string;
  props?: { style?: StyleLike; [key: string]: unknown };
  children?: Array<RenderedNode | string | null> | null;
}

export interface TextMeasurement {
  /** The words on screen, as one line. */
  text: string;
  /** Font size in 1080p units, because that is what calmStyles speaks. */
  fontSize: number;
  colour: string;
  /** The nearest colour painted behind it. */
  background: string;
  contrast: number;
  /** The smallest opacity any ancestor applies. Faded text is a finding. */
  opacity: number;
}

export interface FocusMeasurement {
  testID: string;
  /** Border width in 1080p units. */
  borderWidth: number;
  ringColour: string;
  /** What the ring is drawn on top of. */
  fill: string;
  /** What is outside the ring. */
  outside: string;
  ringOnFill: number;
  ringOnOutside: number;
}

function textOf(node: RenderedNode | string | null | undefined): string {
  if (node === null || node === undefined) {
    return '';
  }
  if (typeof node === 'string') {
    return node;
  }
  if (typeof node === 'number') {
    return String(node);
  }
  return (node.children ?? []).map((child) => textOf(child as RenderedNode)).join('');
}

export interface MeasureOptions {
  /**
   * What is behind the whole screen.
   *
   * A screen paints its own background, so this is only reached by a layer
   * drawn over the video, where what is behind is the title itself.
   */
  background: string;
}

/**
 * Every piece of text a screen draws, with its size and its contrast.
 *
 * Colour and size are inherited the way React Native inherits them inside a
 * Text, and the background is the nearest painted ancestor, which is what a
 * person actually sees the letters against.
 */
export function measureText(
  tree: RenderedNode | RenderedNode[] | null | undefined,
  options: MeasureOptions,
): TextMeasurement[] {
  const found: TextMeasurement[] = [];

  const walk = (
    node: RenderedNode | RenderedNode[] | string | null | undefined,
    background: string,
    colour: string | undefined,
    fontSize: number | undefined,
    opacity: number,
    inText: boolean,
  ): void => {
    if (!node || typeof node === 'string') {
      return;
    }
    if (Array.isArray(node)) {
      for (const one of node) {
        walk(one, background, colour, fontSize, opacity, inText);
      }
      return;
    }

    const style = flattenStyle(node.props?.style);
    const painted = style.backgroundColor;
    const nextBackground =
      typeof painted === 'string' && painted !== 'transparent' ? painted : background;
    const nextColour = typeof style.color === 'string' ? style.color : colour;
    const nextSize =
      typeof style.fontSize === 'number' ? style.fontSize : fontSize;
    const ownOpacity = typeof style.opacity === 'number' ? style.opacity : 1;
    const nextOpacity = opacity * ownOpacity;

    const isText = node.type === 'Text';
    // Only the outermost Text of a run is measured. A nested Text inherits and
    // would be counted twice.
    if (isText && !inText) {
      const words = textOf(node).trim();
      if (words.length > 0 && nextColour && nextSize) {
        found.push({
          text: words,
          fontSize: nextSize,
          colour: nextColour,
          background: nextBackground,
          contrast: contrastRatio(nextColour, nextBackground),
          opacity: nextOpacity,
        });
      }
    }

    for (const child of node.children ?? []) {
      walk(
        child as RenderedNode,
        nextBackground,
        nextColour,
        nextSize,
        nextOpacity,
        inText || isText,
      );
    }
  };

  walk(tree, options.background, undefined, undefined, 1, false);
  return found;
}

/** Roles that take D-pad focus, and so have to show that they have it. */
export const FOCUSABLE_ROLES = ['button', 'radio', 'link', 'menuitem'];

/**
 * Every control on a screen, with its ring measured against both neighbours.
 *
 * A ring is only visible from the sofa if it stands out from the thing it
 * surrounds and from what is immediately outside it, so both ratios are
 * reported. Outside is the nearest colour painted behind the control, which
 * for a button inside a card is the card, not the screen.
 *
 * Controls drawn as unavailable are left out. They do not take focus, and
 * WCAG's non-text contrast rule does not ask anything of an inactive control.
 */
export function measureFocusRings(
  tree: RenderedNode | RenderedNode[] | null | undefined,
  options: MeasureOptions,
): FocusMeasurement[] {
  const found: FocusMeasurement[] = [];

  const walk = (
    node: RenderedNode | RenderedNode[] | string | null | undefined,
    background: string,
  ): void => {
    if (!node || typeof node === 'string') {
      return;
    }
    if (Array.isArray(node)) {
      for (const one of node) {
        walk(one, background);
      }
      return;
    }

    const style = flattenStyle(node.props?.style);
    const painted = style.backgroundColor;
    const nextBackground =
      typeof painted === 'string' && painted !== 'transparent' ? painted : background;

    const role = node.props?.accessibilityRole;
    const state = node.props?.accessibilityState as { disabled?: boolean } | undefined;
    if (typeof role === 'string' && FOCUSABLE_ROLES.includes(role) && !state?.disabled) {
      const ringColour = String(style.borderColor ?? '');
      const visibleRing = ringColour && ringColour !== 'transparent';
      const fill = nextBackground;
      found.push({
        testID: String(node.props?.testID ?? ''),
        borderWidth: typeof style.borderWidth === 'number' ? style.borderWidth : 0,
        ringColour,
        fill,
        outside: background,
        ringOnFill: visibleRing ? contrastRatio(ringColour, fill) : 1,
        ringOnOutside: visibleRing ? contrastRatio(ringColour, background) : 1,
      });
    }

    for (const child of node.children ?? []) {
      walk(child as RenderedNode, nextBackground);
    }
  };

  walk(tree, options.background);
  return found;
}

export interface EdgeMeasurement {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

/**
 * How far a screen keeps its content from the edges of the picture, in 1080p
 * units.
 *
 * Read off the outermost node that has any padding, following first children,
 * because a screen built on a scroll view puts its padding on the content
 * rather than on the scroller.
 */
export function measureEdges(
  tree: RenderedNode | RenderedNode[] | null | undefined,
  depth = 4,
): EdgeMeasurement {
  const empty: EdgeMeasurement = { left: 0, right: 0, top: 0, bottom: 0 };
  let node: RenderedNode | null = Array.isArray(tree) ? tree[0] ?? null : tree ?? null;

  for (let step = 0; step < depth && node; step += 1) {
    // A scroll view keeps its padding in contentContainerStyle, and that is
    // where the safe margins of half these screens live.
    const style = {
      ...flattenStyle(node.props?.style),
      ...flattenStyle(node.props?.contentContainerStyle),
    };
    const pick = (...keys: string[]): number => {
      for (const key of keys) {
        const value = style[key];
        if (typeof value === 'number') {
          return value;
        }
      }
      return 0;
    };
    const edges: EdgeMeasurement = {
      left: pick('paddingLeft', 'paddingHorizontal', 'padding'),
      right: pick('paddingRight', 'paddingHorizontal', 'padding'),
      top: pick('paddingTop', 'paddingVertical', 'padding'),
      bottom: pick('paddingBottom', 'paddingVertical', 'padding'),
    };
    if (edges.left > 0 || edges.top > 0) {
      return edges;
    }
    const first = (node.children ?? []).find(
      (child) => child && typeof child !== 'string',
    );
    node = (first as RenderedNode) ?? null;
  }

  return empty;
}
