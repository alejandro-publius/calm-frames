/**
 * The credits screen, and the conditions it is not allowed to drop.
 *
 * The licences behind this project are not all the same shape. Three of them
 * carry a condition that is easy to lose in a redesign: the Blender logos are
 * excluded from the Blender Studio licences, Tears of Steel is CC BY 3.0 only
 * while its credit scroll stays in the film, and DVIDS requires a
 * non-endorsement notice. A share alike clip binds anything we publish from
 * it, and NASA asks to be named as the source without its insignia being used.
 *
 * So this suite does not check that the screen renders. It checks that every
 * title is on it with its licence and its credit line, that each of those
 * conditions is on screen in words, and that the one title we keep out of what
 * we publish is nowhere in the app.
 *
 * Each assertion here has been seen to fail: drop a condition from the screen,
 * or from eval/attribution.py, and the matching test goes red.
 */
import { render, screen } from '@testing-library/react-native';
import React from 'react';
import { COASTAL_COLORS } from '../../src/calmframes/calmStyles';
import CreditsScreen from '../../src/calmframes/CreditsScreen';
import { CREDIT_ENTRIES } from '../../src/calmframes/credits';
import {
  frameFromTree,
  RenderedNode,
} from '../../src/calmframes/uiCapture';
import { CREDITS_FRAME } from '../../src/calmframes/uiFrames';

/**
 * Only the words a person can actually read.
 *
 * Not JSON.stringify of the tree, which was the first version of this and was
 * wrong: it also caught the accessibility labels, so removing the credit line
 * from the screen left every test green while the credit was gone from the
 * picture. This walks the tree and keeps the strings inside Text nodes.
 */
function visibleText(): string {
  const parts: string[] = [];
  const walk = (node: unknown): void => {
    if (typeof node === 'string') {
      parts.push(node);
      return;
    }
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    if (!node || typeof node !== 'object') {
      return;
    }
    const element = node as { type?: string; children?: unknown };
    if (element.type === 'Text' || element.type === 'View') {
      walk(element.children);
      return;
    }
    walk(element.children);
  };
  walk(screen.toJSON());
  return parts.join('\n');
}

/** The words inside one Text node, by its testID. */
function textOf(testID: string): string {
  const node = screen.getByTestId(testID);
  const children = node.props.children;
  return (Array.isArray(children) ? children : [children])
    .filter((child: unknown) => typeof child === 'string')
    .join('');
}

describe('the credits list', () => {
  it('has every title we hold, with a licence and a credit line', () => {
    expect(CREDIT_ENTRIES.length).toBeGreaterThan(0);
    for (const entry of CREDIT_ENTRIES) {
      expect(entry.title.trim()).not.toBe('');
      expect(entry.license.trim()).not.toBe('');
      expect(entry.credit.trim()).not.toBe('');
      expect(entry.source).toMatch(/^https?:\/\//);
    }
  });

  it('puts all of them on the screen, as words and not only as labels', () => {
    render(<CreditsScreen />);
    const text = visibleText();
    for (const entry of CREDIT_ENTRIES) {
      const id = `credits-entry-${entry.title}`;
      expect(textOf(`${id}-title`)).toBe(entry.title);
      expect(textOf(`${id}-license`)).toBe(entry.license);
      expect(textOf(`${id}-credit`)).toBe(entry.credit);
      expect(text).toContain(entry.credit);
    }
  });

  it('keeps the Blender logo exclusion', () => {
    const blender = CREDIT_ENTRIES.filter(entry =>
      entry.collection.startsWith('Blender'),
    );
    expect(blender.length).toBeGreaterThan(0);
    for (const entry of blender) {
      expect(entry.obligations.join(' ')).toMatch(/logos and trademarks are not covered/);
    }
  });

  it('includes every visible credit and licence condition in its spoken label', () => {
    render(<CreditsScreen />);
    for (const entry of CREDIT_ENTRIES) {
      const row = screen.getByTestId(`credits-entry-${entry.title}`);
      for (const words of [entry.title, entry.collection, entry.license, entry.credit, ...entry.obligations]) {
        expect(row.props.accessibilityLabel).toContain(words);
        expect(row.props['aria-label']).toContain(words);
      }
    }
  });

  it('keeps the Tears of Steel credit scroll condition', () => {
    const tears = CREDIT_ENTRIES.find(entry => entry.title === 'Tears of Steel');
    expect(tears).toBeDefined();
    expect(tears?.obligations.join(' ')).toMatch(/credit scroll stays in the film/);

    render(<CreditsScreen />);
    expect(visibleText()).toContain('credit scroll stays in the film');
  });

  it('keeps the DVIDS non-endorsement notice', () => {
    const dvids = CREDIT_ENTRIES.filter(entry => entry.collection === 'DVIDS');
    expect(dvids.length).toBeGreaterThan(0);
    for (const entry of dvids) {
      expect(entry.credit).toMatch(/does not imply or constitute/);
    }

    render(<CreditsScreen />);
    expect(visibleText()).toContain('does not imply or constitute');
  });

  it('names NASA as the source without using its insignia', () => {
    const nasa = CREDIT_ENTRIES.filter(entry => entry.credit.includes('NASA'));
    expect(nasa.length).toBeGreaterThan(0);
    for (const entry of nasa) {
      expect(entry.obligations.join(' ')).toMatch(/insignia, logotype and identifiers/);
    }
  });

  it('carries the share alike condition on every share alike licence', () => {
    const shareAlike = CREDIT_ENTRIES.filter(entry =>
      entry.license.toUpperCase().includes('BY-SA'),
    );
    expect(shareAlike.length).toBeGreaterThan(0);
    for (const entry of shareAlike) {
      expect(entry.obligations.join(' ')).toMatch(/Share alike/);
    }
  });

  it("never mentions the one title we keep out of what we publish", () => {
    render(<CreditsScreen />);
    expect(visibleText()).not.toMatch(/Hell's Angels/i);
    for (const entry of CREDIT_ENTRIES) {
      expect(entry.title).not.toMatch(/Hell's Angels/i);
    }
  });

  it('uses no en dash or em dash anywhere', () => {
    render(<CreditsScreen />);
    expect(visibleText()).not.toMatch(/[–—]/);
  });
});

describe('what the credits screen paints', () => {
  it('matches the frame it reports', () => {
    const { toJSON, unmount } = render(<CreditsScreen />);
    const frame = frameFromTree('credits', toJSON() as unknown as RenderedNode);
    unmount();
    expect(frame).toEqual(CREDITS_FRAME);
    expect(frame.background).toBe(COASTAL_COLORS.BACKGROUND);
  });
});
