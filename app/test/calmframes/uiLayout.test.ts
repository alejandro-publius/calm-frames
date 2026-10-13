/**
 * The ruler the ten foot pass uses for overlap, checked against boxes worked
 * out by hand.
 *
 * The numbers use the conservative text metrics: 0.6 of the font size per
 * character and 1.35 of it per line, so a 20 unit font is 12 units a
 * character and 27 units a line.
 */

import { RenderedNode } from '../../src/calmframes/uiContrast';
import {
  boxesOverlap,
  findByTestID,
  placedBox,
  wrapText,
} from '../../src/calmframes/uiLayout';

const SCREEN = { width: 1920, height: 1080 };

function text(words: string, style: Record<string, unknown> = { fontSize: 20 }): RenderedNode {
  return { type: 'Text', props: { style }, children: [words] };
}

function view(style: Record<string, unknown>, ...children: RenderedNode[]): RenderedNode {
  return { type: 'View', props: { style }, children };
}

describe('wrapText', () => {
  it('keeps words together and breaks between them', () => {
    // 100 units at 12 a character is 8 characters a line.
    expect(wrapText('aaaa bbbb', 20, 100)).toEqual({ lines: 2, widest: 48 });
    expect(wrapText('aaa bbbb', 20, 100)).toEqual({ lines: 1, widest: 96 });
  });

  it('breaks a word longer than a line inside the word', () => {
    expect(wrapText('abcdefghijkl', 20, 100)).toEqual({ lines: 2, widest: 96 });
  });

  it('counts nothing for no words', () => {
    expect(wrapText('   ', 20, 100)).toEqual({ lines: 0, widest: 0 });
  });
});

describe('placedBox', () => {
  it('places a block hung from the top by its own size', () => {
    const tree = view(
      { position: 'absolute', top: 100, left: 50, padding: 10, borderWidth: 2 },
      text('aaaa bbbb'),
    );
    const plate = { ...tree, props: { ...tree.props, testID: 'plate' } };
    // 9 characters is 108 wide and one 27 unit line; padding and border add
    // 24 each way.
    expect(placedBox(plate, 'plate', SCREEN)).toEqual({
      left: 50,
      top: 100,
      right: 50 + 108 + 24,
      bottom: 100 + 27 + 24,
    });
  });

  it('places a block stood on the bottom edge by its height', () => {
    const tree = {
      ...view({ position: 'absolute', bottom: 160, left: 0, right: 0 }, text('aaaa')),
    };
    tree.props = { ...tree.props, testID: 'card' };
    const box = placedBox(tree, 'card', SCREEN);
    expect(box?.bottom).toBe(1080 - 160);
    expect(box?.top).toBe(1080 - 160 - 27);
  });

  it('measures a centring strip across the screen by what it holds', () => {
    const tree = view(
      { position: 'absolute', top: 160, left: 0, right: 0, alignItems: 'center' },
      view(
        { maxWidth: 400, paddingHorizontal: 20, paddingVertical: 10, alignItems: 'center' },
        // 41 characters is 492 wide, over the 360 left inside the padding,
        // which holds 30, so it wraps to two lines of 21 and 19.
        text('aaaaaaaaaa bbbbbbbbbb cccccccccc dddddddd'),
      ),
    );
    tree.props = { ...tree.props, testID: 'card' };
    const box = placedBox(tree, 'card', SCREEN);
    const width = 21 * 12 + 40;
    expect(box).toEqual({
      left: (1920 - width) / 2,
      top: 160,
      right: (1920 + width) / 2,
      bottom: 160 + 2 * 27 + 20,
    });
  });

  it('adds margins between stacked blocks and honours a set line height', () => {
    const tree = view(
      { position: 'absolute', top: 0, left: 0 },
      text('aa', { fontSize: 20, lineHeight: 30 }),
      text('bb', { fontSize: 20, lineHeight: 30, marginTop: 12 }),
    );
    tree.props = { ...tree.props, testID: 'stack' };
    expect(placedBox(tree, 'stack', SCREEN)?.bottom).toBe(30 + 12 + 30);
  });

  it('refuses what it cannot measure rather than guessing', () => {
    const row = view({ position: 'absolute', top: 0, left: 0, flexDirection: 'row' }, text('a'));
    row.props = { ...row.props, testID: 'row' };
    expect(() => placedBox(row, 'row', SCREEN)).toThrow(/columns only/);

    const percent = view({ position: 'absolute', top: '10%', left: 0 }, text('a'));
    percent.props = { ...percent.props, testID: 'percent' };
    expect(() => placedBox(percent, 'percent', SCREEN)).toThrow(/plain numbers/);

    const flowing = view({ top: 0 }, text('a'));
    flowing.props = { ...flowing.props, testID: 'flowing' };
    expect(() => placedBox(flowing, 'flowing', SCREEN)).toThrow(/not placed absolutely/);
  });

  it('finds nothing for a testID that is not there', () => {
    expect(findByTestID(view({}, text('a')), 'missing')).toBeNull();
    expect(placedBox(view({}), 'missing', SCREEN)).toBeNull();
  });
});

describe('boxesOverlap', () => {
  const box = { left: 0, top: 0, right: 100, bottom: 100 };

  it('is true when two boxes share area', () => {
    expect(boxesOverlap(box, { left: 50, top: 50, right: 150, bottom: 150 })).toBe(true);
  });

  it('is false for boxes that only touch, or sit apart', () => {
    expect(boxesOverlap(box, { left: 100, top: 0, right: 200, bottom: 100 })).toBe(false);
    expect(boxesOverlap(box, { left: 0, top: 101, right: 100, bottom: 200 })).toBe(false);
  });
});
