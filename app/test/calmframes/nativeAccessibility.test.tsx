/**
 * What VoiceView says, held to what the screen shows.
 *
 * On the Vega Virtual Device VoiceView speaks the control that has focus and
 * the headings of a page as it appears, and nothing else: text that cannot
 * take focus is never spoken. Recorded on the installed build of 6a87937,
 * it said:
 *
 * - "Choose who is watching, button" for the Home button that shows Kid;
 * - "McWay Falls, Ocean middle dot 5 minutes" for a card showing 5 min, and
 *   "Sea Otters, Ocean wildlife middle dot 20 seconds" for one showing Still
 *   scene;
 * - "not selected, selected" for every card focus landed on;
 * - nothing of the Details title or what the strip says will be covered;
 * - nothing of How it works or More info but their headings and buttons, so
 *   never the approved safety sentence;
 * - "Extra picture covers, button" for every title in Parents alike, and
 *   nothing of the hidden scenes record.
 *
 * Each test below holds one of those to what the screen draws.
 *
 * Seen to fail, each by putting one change back on purpose: the profile
 * button saying only "Choose who is watching"; the card label built from the
 * title's kind with its separator; the card state carrying selected false;
 * the Details title without its heading role; Watch without its hint, and
 * CalmButton not passing a hint on; More info, How it works and the hidden
 * scenes record each back in a plain view; Extra picture covers without the
 * title; a flush stop keeping its inset; `spoken` leaving the separator in;
 * and the strip summary speaking its raw line. Every one turned its test red
 * at an assertion, and nothing else.
 *
 * On the TV the first build of this cut the left side off the How it works
 * ring, drawn outside the text and clipped by the scroller. The room tests
 * were seen to fail by taking the scroller's room away, which measured zero
 * room around the stop, and by keeping the room but not reaching out, which
 * moved the text.
 */
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';
import { ScrollView, StyleSheet, Text } from 'react-native';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import PictureHoldIntroduction from '../../src/calmframes/PictureHoldIntroduction';
import ReadingStop from '../../src/calmframes/ReadingStop';
import { ambientArtworkFor } from '../../src/calmframes/AmbientScene';
import { coveredSectionsSummary } from '../../src/calmframes/CoveredSectionsStrip';
import { DETECTION_LIMITS_LINE, ONLY_IN_CALM_FRAMES_LINE, SAFETY_NOTE, SAVING_CHANGES, spoken } from '../../src/calmframes/copy';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import { addProfile, newFamily } from '../../src/calmframes/profiles';
import { titlePresentation } from '../../src/calmframes/TitleArtwork';
import { checkedShelf } from './shelfFixtures';

jest.mock('@react-native-async-storage/async-storage', () => ({ getItem: jest.fn(async () => null), setItem: jest.fn(async () => undefined) }));

const shelf = checkedShelf();
// The four titles the installed catalog shows on the island map. The
// regression shelf also holds a prepared Harbor, which keeps Home on the
// older flowing shelf.
const SHIPPED = ['Acadia', 'McWay Falls', 'Sea otters in Alaska', 'Forest creek at Redwood'];
const shipped = shelf.filter((entry) => SHIPPED.includes(titlePresentation(entry.title).name));
const family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');
const [robin, sam] = family.profiles;

/** Every string a host element draws, in tree order. */
const textsIn = (node: { findAllByType: (type: typeof Text) => { props: { children?: unknown } }[] }) =>
  node.findAllByType(Text).map((one) => [one.props.children].flat().join('')).filter(Boolean);

const renderHome = (props: Partial<React.ComponentProps<typeof KidHomeScreen>> = {}) =>
  render(<KidHomeScreen titles={shipped} onOpen={jest.fn()} onAmbient={jest.fn()} profiles={family.profiles}
    activeProfileId={sam.id} onChooseProfile={jest.fn()} {...props} />);

/** The cards on the island map, with what each one draws under its name. */
function cards() {
  return shipped.flatMap((entry) => {
    const card = screen.queryByTestId(`kid-home-poster-${entry.title.id}`);
    if (!card) return [];
    return [{
      entry,
      card,
      name: screen.getByTestId(`kid-home-poster-title-${entry.title.id}`).props.children as string,
      line: screen.queryByTestId(`kid-home-poster-qualifier-${entry.title.id}`)?.props.children as string | undefined,
    }];
  });
}

describe('Home', () => {
  it('says who is watching on the button that shows it', () => {
    const view = renderHome();
    expect(screen.getByTestId('kid-home-choose-profile-label').props.children).toBe('Sam');
    expect(screen.getByTestId('kid-home-choose-profile').props.accessibilityLabel).toBe('Sam is watching. Choose who is watching');
    view.rerender(<KidHomeScreen titles={shipped} onOpen={jest.fn()} onAmbient={jest.fn()} profiles={family.profiles}
      activeProfileId={robin.id} onChooseProfile={jest.fn()} />);
    expect(screen.getByTestId('kid-home-choose-profile').props.accessibilityLabel).toBe('Robin is watching. Choose who is watching');
    view.rerender(<KidHomeScreen titles={shipped} onOpen={jest.fn()} onAmbient={jest.fn()} profiles={family.profiles}
      activeProfileId={robin.id} onChooseProfile={jest.fn()} saving />);
    expect(screen.getByTestId('kid-home-choose-profile').props.accessibilityLabel).toBe(SAVING_CHANGES);
  });

  it('announces each card by the words drawn on it, with no separator read aloud', () => {
    renderHome();
    const shown = cards();
    expect(Object.fromEntries(shown.map(({ name, card }) => [name, card.props.accessibilityLabel]))).toEqual({
      'Acadia': 'Acadia, Still scene',
      'McWay Falls': 'McWay Falls, 5 minutes',
      'Sea Otters': 'Sea Otters, Still scene',
      'Forest': 'Forest, Still scene',
    });
    for (const { entry, card, name, line } of shown) {
      expect(card.props.accessibilityLabel).not.toMatch(/·|\bmin\b|\bsec\b/);
      expect(card.props.accessibilityLabel.startsWith(`${name}, `)).toBe(true);
      // A still scene is what Watch opens, so that is what the card says.
      expect(line === 'Still scene').toBe(Boolean(ambientArtworkFor(entry)));
    }
  });

  it('never reports a card as not selected, since focus selects it a render later', () => {
    renderHome();
    // React Native fills in every key of the state; a key left out is
    // undefined, and undefined never reaches the native view. False does.
    const chosen = () => cards().filter(({ card }) => card.props.accessibilityState.selected === true).map(({ name }) => name);
    const saidFalse = () => cards().filter(({ card }) => card.props.accessibilityState.selected === false).map(({ name }) => name);
    expect(chosen()).toHaveLength(1);
    expect(saidFalse()).toEqual([]);
    const other = cards().find(({ card }) => card.props.accessibilityState.selected !== true)!;
    fireEvent(other.card, 'focus');
    expect(chosen()).toEqual([other.name]);
    expect(saidFalse()).toEqual([]);
  });
});

describe('Details', () => {
  const playable = shipped;

  it.each(playable.map((entry) => [titlePresentation(entry.title).name, entry] as const))('names %s as the page heading and says what is covered after Watch', (_, entry) => {
    render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} onAmbient={ambientArtworkFor(entry) ? jest.fn() : undefined} />);
    expect(screen.getByTestId('title-details-title').props.accessibilityRole).toBe('header');
    const strip = screen.getByTestId('title-details-covered');
    const watch = screen.getByTestId('title-details-play');
    // The same sentence the strip draws, heard after the Watch button.
    expect(watch.props.accessibilityHint).toBe(strip.props.accessibilityLabel);
    const heading = screen.getByTestId('title-details-covered-heading').props.children;
    const line = screen.getByTestId('title-details-covered-line').props.children;
    expect(watch.props.accessibilityHint).toBe(`${heading}. ${spoken(line)}`);
    expect(watch.props.accessibilityHint).not.toContain('·');
  });

  it('gives no hint while a save is in flight, when the button says it is saving', () => {
    const entry = playable[0];
    render(<TitleDetailsScreen entry={entry} onPlay={jest.fn()} saving />);
    expect(screen.getByTestId('title-details-play').props.accessibilityLabel).toBe(SAVING_CHANGES);
    expect(screen.getByTestId('title-details-play').props.accessibilityHint).toBeUndefined();
  });

  it('puts the safety sentence on More info where the remote, and so VoiceView, can land', () => {
    render(<TitleDetailsScreen entry={playable[0]} onPlay={jest.fn()} />);
    fireEvent.press(screen.getByTestId('title-details-show-info'));
    const stop = screen.getByTestId('title-details-info-reading');
    expect(stop.props.focusable).toBe(true);
    expect(stop.props.accessible).toBe(true);
    expect(textsIn(stop)).toEqual(expect.arrayContaining([ONLY_IN_CALM_FRAMES_LINE, `${DETECTION_LIMITS_LINE} ${SAFETY_NOTE}`]));
  });
});

describe('How it works', () => {
  it('is one stop the remote can land on, with the approved sentence in it', () => {
    render(<PictureHoldIntroduction onPlaybackCheck={jest.fn()} />);
    const stop = screen.getByTestId('how-it-works-reading');
    expect(stop.props.focusable).toBe(true);
    expect(stop.props.accessible).toBe(true);
    const texts = textsIn(stop);
    expect(texts).toEqual(expect.arrayContaining([
      'Calm Frames hides flagged flashing scenes in prepared videos.', ONLY_IN_CALM_FRAMES_LINE, `${DETECTION_LIMITS_LINE} ${SAFETY_NOTE}`,
    ]));
  });
});

describe('Parents', () => {
  const gate = setPin(emptyPinGate(), '1357', 'seed', 4);
  function renderParents() {
    render(<ParentAreaScreen gate={gate} onGateChange={jest.fn()} settings={DEFAULT_SETTINGS} onSettingsChange={jest.fn()}
      log={emptyHideLog()} family={family} onFamilyChange={jest.fn()} titles={shelf} nowMs={() => 0} onBack={jest.fn()} />);
    for (const digit of '1357') fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
  }

  it('names the title on every Extra picture covers button', () => {
    renderParents();
    const buttons = shelf.flatMap((entry) => {
      const button = screen.queryByTestId(`parent-area-extra-${entry.title.id}`);
      return button ? [{ entry, button }] : [];
    });
    expect(buttons.length).toBeGreaterThan(1);
    const labels = buttons.map(({ button }) => button.props.accessibilityLabel);
    expect(new Set(labels).size).toBe(labels.length);
    for (const { entry, button } of buttons) {
      expect(button.props.accessibilityLabel).toBe(`Extra picture covers: ${titlePresentation(entry.title).name}`);
    }
  });

  it('puts the hidden scenes record where the remote, and so VoiceView, can land', () => {
    renderParents();
    const stop = screen.getByTestId('parent-area-hidden-reading');
    expect(stop.props.focusable).toBe(true);
    expect(textsIn(stop)).toContain(screen.getByTestId('parent-area-total').props.children);
  });
});

describe('spoken', () => {
  it.each([
    ['5 min', '5 minutes'],
    ['1 min', '1 minute'],
    ['Silent · 38 sec', 'Silent, 38 seconds'],
    ['Nature audio · 1 sec', 'Nature audio, 1 second'],
    ['2 scenes · 7 seconds', '2 scenes, 7 seconds'],
    ['Still scene', 'Still scene'],
  ])('says %j as %j', (line, said) => {
    expect(spoken(line)).toBe(said);
  });

  it('is what the covered strip and the Watch hint say', () => {
    const result = { kind: 'ready', text: '2 scenes · 7 seconds', sections: [], durationMs: 1 } as never;
    expect(coveredSectionsSummary(result)).toBe('Scenes covered. 2 scenes, 7 seconds');
    expect(coveredSectionsSummary(result, true)).toBe('Scenes replaced. 2 scenes, 7 seconds');
  });
});

describe('a flush reading stop', () => {
  type Node = { type: unknown; props: Record<string, unknown>; parent: Node | null };
  const flat = (style: unknown) => (StyleSheet.flatten(style as never) ?? {}) as Record<string, number | string | undefined>;
  const left = (style: Record<string, number | string | undefined>, side: 'padding' | 'margin') =>
    Number(style[`${side}Left`] ?? style[`${side}Horizontal`] ?? style[side] ?? 0);

  /**
   * How much room there is to the left of a stop, inside the scroller that
   * clips it: every padding and margin between the two, and the scroller's
   * own padding and content padding.
   */
  function roomInsideScroller(stop: Node): number {
    let room = 0;
    for (let node = stop.parent; node; node = node.parent) {
      if (node.type === ScrollView) {
        return room + left(flat(node.props.style), 'padding') + left(flat(node.props.contentContainerStyle), 'padding');
      }
      if (typeof node.type === 'string') {
        const style = flat(node.props.style);
        room += left(style, 'padding') + Math.max(0, left(style, 'margin'));
      }
    }
    return Infinity;
  }

  const outset = (stop: Node) => -Number(flat(stop.props.style).margin);

  it('has room for its whole ring inside the scroller around it, wherever it is used', () => {
    // On the TV the left side of the How it works ring was cut off by the
    // scroller's edge, because the stop's ring is drawn outside its text.
    const cases: Array<[string, () => void]> = [
      ['how-it-works-reading', () => { renderHome(); fireEvent.press(screen.getByTestId('kid-home-learn')); }],
      ['title-details-info-reading', () => {
        render(<TitleDetailsScreen entry={shipped[0]} onPlay={jest.fn()} />);
        fireEvent.press(screen.getByTestId('title-details-show-info'));
      }],
      ['parent-area-hidden-reading', () => {
        render(<ParentAreaScreen gate={setPin(emptyPinGate(), '1357', 'seed', 4)} onGateChange={jest.fn()} settings={DEFAULT_SETTINGS}
          onSettingsChange={jest.fn()} log={emptyHideLog()} family={family} onFamilyChange={jest.fn()} titles={shelf} nowMs={() => 0} onBack={jest.fn()} />);
        for (const digit of '1357') fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
      }],
    ];
    for (const [testID, show] of cases) {
      show();
      const stop = screen.getByTestId(testID) as unknown as Node;
      expect([testID, outset(stop)]).toEqual([testID, expect.any(Number)]);
      expect(outset(stop)).toBeGreaterThan(0);
      expect([testID, roomInsideScroller(stop) >= outset(stop)]).toEqual([testID, true]);
      screen.unmount();
    }
  });

  it('keeps How it works where it was: its scroller reaches out as far as its content comes in', () => {
    renderHome();
    fireEvent.press(screen.getByTestId('kid-home-learn'));
    const scroller = screen.UNSAFE_getAllByType(ScrollView).find((one) => one.findAll((node) => node.props.testID === 'how-it-works-reading').length > 0)!;
    const reach = left(flat(scroller.props.style), 'margin');
    expect(reach).toBeLessThan(0);
    expect(reach + left(flat(scroller.props.contentContainerStyle), 'padding')).toBe(0);
  });

  it('takes the room for its ring out of its margins, so the text does not move', () => {
    render(<ReadingStop testID="stop" flush><Text>Line</Text></ReadingStop>);
    const style = StyleSheet.flatten(screen.getByTestId('stop').props.style);
    expect(style.borderWidth).toBeGreaterThan(0);
    expect(style.margin).toBe(-((style.borderWidth as number) + (style.padding as number)));
    expect(style.width).toBe('auto');
  });
});
