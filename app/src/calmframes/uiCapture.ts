/**
 * Recording what the app itself puts on screen.
 *
 * docs/BUILD_PROMPT.md 4.5 says the app's own screens and transitions have to
 * pass flashmap. That needs frames, and frames are the one thing Vega will not
 * give us:
 *
 * - React Native 0.83 has no takeSnapshot. It was removed from core, and
 *   nothing in node_modules/react-native exposes a pixel read.
 * - No @amazon-devices package offers a screenshot, a view capture or a frame
 *   grab. The only match anywhere in them is `readPixels` inside a Flow type
 *   stub for the DOM, which is a type declaration, not a runtime.
 * - Capturing from outside does not work either. docs/ENVIRONMENT.md and
 *   CLAUDE.md both record it: QMP screenshots of the virtual device come back
 *   black, because the app draws on a layer the capture misses.
 *
 * So the app records what it paints rather than what it displays. Every Calm
 * Frames screen reports its own frame: the colour behind the whole screen, and
 * the distinct colours it paints on top. Those are read off the rendered tree,
 * not written down by hand, so a change to a style shows up here.
 *
 * What that buys, and what it does not:
 *
 * - it is a real record of the app's own drawing, taken from inside the app,
 *   including every transition, because a transition is two frames in a row;
 * - it is not a photograph. Where the colours land on screen is not recorded,
 *   only which colours are painted. tools/ui_flashmap.mjs turns each frame
 *   into a picture by giving every painted colour a block one WCAG window
 *   wide, which is the largest area where a flash can matter, so the video
 *   flashmap then measures overstates the area rather than understating it.
 *
 * The timeline is kept in memory and can be posted to the machine running a
 * device session, the same way the timing log is. Nothing is written to the
 * device's storage.
 */

import { useEffect } from 'react';

export interface UiFrame {
  /** Which screen this is, for the report. */
  screen: string;
  /** The colour behind the whole screen. */
  background: string;
  /** Every other colour this screen paints, in the order they were found. */
  surfaces: string[];
}

export interface UiCaptureEntry extends UiFrame {
  /** Wall clock when this frame went up, milliseconds since the epoch. */
  atMs: number;
  /** What made it change: a screen it moved to, or a state it entered. */
  reason: string;
}

let timeline: UiCaptureEntry[] = [];
let recording = false;

export function startUiCapture(): void {
  recording = true;
  timeline = [];
}

export function stopUiCapture(): UiCaptureEntry[] {
  recording = false;
  return timeline;
}

export function getUiCaptureTimeline(): UiCaptureEntry[] {
  return [...timeline];
}

export function isUiCapturing(): boolean {
  return recording;
}

function sameFrame(left: UiFrame, right: UiFrame): boolean {
  return (
    left.screen === right.screen &&
    left.background === right.background &&
    left.surfaces.length === right.surfaces.length &&
    left.surfaces.every((colour, index) => colour === right.surfaces[index])
  );
}

/**
 * Record a frame.
 *
 * Repeats are dropped, so the timeline is a list of changes: every entry is a
 * transition from the one before it, which is what a flash is made of.
 */
export function recordUiFrame(
  frame: UiFrame,
  reason: string,
  atMs: number = Date.now(),
): boolean {
  if (!recording) {
    return false;
  }
  const previous = timeline[timeline.length - 1];
  if (previous && sameFrame(previous, frame)) {
    return false;
  }
  timeline.push({ ...frame, atMs, reason });
  return true;
}

/** A style object, or a list of them, as React Native hands them over. */
type StyleLike = unknown;

function flattenStyle(style: StyleLike): Record<string, unknown> {
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

/** One node of a rendered tree, as react-test-renderer's toJSON gives it. */
export interface RenderedNode {
  props?: { style?: StyleLike; [key: string]: unknown };
  children?: Array<RenderedNode | string | null> | null;
}

/**
 * Read the colours a rendered tree paints.
 *
 * Walks the tree in paint order, which is the order React renders it, and
 * collects every distinct backgroundColor. The first one found is the screen's
 * background, because the outermost view is drawn first and the screens all
 * put their background there.
 */
export function frameFromTree(
  screen: string,
  tree: RenderedNode | RenderedNode[] | null | undefined,
): UiFrame {
  const colours: string[] = [];

  const walk = (
    node: RenderedNode | RenderedNode[] | string | null | undefined,
  ): void => {
    if (!node || typeof node === 'string') {
      return;
    }
    // A screen that renders a fragment gives back a list of roots, and both
    // the cover and the card are drawn that way.
    if (Array.isArray(node)) {
      for (const one of node) {
        walk(one);
      }
      return;
    }
    const style = flattenStyle(node.props?.style);
    const colour = style.backgroundColor;
    if (typeof colour === 'string' && colour !== 'transparent') {
      if (!colours.includes(colour)) {
        colours.push(colour);
      }
    }
    for (const child of node.children ?? []) {
      walk(child as RenderedNode);
    }
  };

  walk(tree);

  return {
    screen,
    background: colours[0] ?? '#000000',
    surfaces: colours.slice(1),
  };
}

/**
 * Send the timeline to the machine running a device session.
 *
 * Debug builds only, and only when a sink was given. A release build never
 * reaches for the network to report what it drew.
 */
export async function postUiCapture(sinkUrl: string): Promise<boolean> {
  if (typeof __DEV__ === 'undefined' || !__DEV__) {
    return false;
  }
  try {
    await fetch(sinkUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ kind: 'ui-capture', frames: timeline }),
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Record this screen's frame while it is on screen.
 *
 * The frame a screen reports here is checked against what it actually renders:
 * test/calmframes/uiCapture.test.tsx renders every screen, reads the colours
 * off the rendered tree with frameFromTree, and fails if they differ from what
 * the screen reports. So this is a record of the app's own drawing rather than
 * a description of it that could drift.
 */
export function useUiCapture(frame: UiFrame, reason: string): void {
  useEffect(() => {
    recordUiFrame(frame, reason);
    // The frame is a constant per screen state, so this runs on entering that
    // state and on every change of it, which is exactly the transition list a
    // flash check needs.
  }, [frame, reason]);
}
