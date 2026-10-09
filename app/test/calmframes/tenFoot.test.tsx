/**
 * The ten foot pass, done with a ruler instead of a screenshot.
 *
 * The Vega Virtual Device cannot be photographed: the app draws on a GPU layer
 * that macOS screen capture and QEMU's screendump both miss, so every
 * screenshot of it comes back black. That rules out looking at this interface
 * and rules out anyone else looking at it either. So every claim about how it
 * reads across a room is a measurement taken off the rendered screen:
 *
 *   type size      every line of text, in 1080p units
 *   contrast       every line against the colour actually painted behind it
 *   focus          every control, resting and focused, and the ring against
 *                  both of its neighbours
 *   safe margins   how far each screen keeps its content from the picture edge
 *   motion         nothing fades: no text is drawn at less than full opacity
 *
 * Every screen and every state goes through it, including the empty and error
 * states, because those are the ones nobody looks at.
 *
 * The numbers land in build/ui-capture/ten-foot.json so they can be read
 * rather than remembered, next to the flash check's own output.
 *
 * Seen to fail: drop MINIMUM_TEXT_SIZE into a screen, paint a label in
 * TEXT_DIM on SURFACE_FOCUSED, or take the ring off one control, and the
 * failure names the screen and the line.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';
import CalmCard from '../../src/calmframes/CalmCard';
import {
  CALM_COLORS,
  CALM_SPACE,
  FOCUS_RING_WIDTH,
  MINIMUM_FOCUS_CONTRAST,
  MINIMUM_TEXT_CONTRAST,
  MINIMUM_TEXT_SIZE,
} from '../../src/calmframes/calmStyles';
import { Card, cardAt } from '../../src/calmframes/cards';
import CoverLayer from '../../src/calmframes/CoverLayer';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import FirstRunScreen from '../../src/calmframes/FirstRunScreen';
import HouseholdStorageScreen from '../../src/calmframes/HouseholdStorageScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import {
  addProfile,
  addProfileHide,
  emptyProfileLogs,
  Family,
  newFamily,
} from '../../src/calmframes/profiles';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CheckedTitle } from '../../src/calmframes/titleStatus';
import {
  contrastRatio,
  FocusMeasurement,
  measureEdges,
  measureFocusRings,
  measureText,
  RenderedNode,
  roundRatio,
  TextMeasurement,
} from '../../src/calmframes/uiContrast';

const OUT_DIR = path.join(__dirname, '..', '..', 'build', 'ui-capture');

/**
 * The floors, written out here rather than imported.
 *
 * The first version of this test compared each screen against the same
 * constants the screens are built from, so narrowing CALM_SPACE.SAFE_X from 96
 * to 64 moved the screens and the threshold together and the test stayed
 * green. A guard that cannot fail is not a guard. These numbers are the ones
 * calmStyles.ts explains, repeated on purpose, and the first test below fails
 * if the constants ever drop below them.
 */
const FLOORS = {
  textSizeUnits: 32,
  textContrast: 4.5,
  focusRingUnits: 6,
  focusContrast: 3,
  safeMarginX: 96,
  safeMarginY: 54,
};

/**
 * What is behind the app's own layer while a title plays.
 *
 * The same mid grey tools/ui_flashmap.mjs paints for the video, so the two
 * checks talk about the same picture.
 */
const VIDEO_STAND_IN = '#808080';

function makeTitle(
  id: string,
  status: CheckedTitle['status'],
  overrides: Partial<CheckedTitle> = {},
): CheckedTitle {
  return {
    title: {
      id,
      title: `Title ${id}`,
      uri: `https://example.invalid/${id}.m3u8`,
      sha256: 'a'.repeat(64),
      durationMs: 600_000,
      posterUrl: `https://example.invalid/${id}.jpg`,
    },
    status,
    segments: [
      { startMs: 60_000, endMs: 64_000 },
      { startMs: 300_000, endMs: 301_000, reason: 'red' },
    ],
    hiddenMs: 5_000,
    verifiedProfiles: ['wcag'],
    ...overrides,
  };
}

const intervals = buildCoverIntervals([{ startMs: 20_000, endMs: 24_000 }], {
  guardBandMs: 500,
});

const gate = setPin(emptyPinGate(), '1357', 'seed', 4);

const parentArea = (
  <ParentAreaScreen
    gate={gate}
    onGateChange={jest.fn()}
    settings={DEFAULT_SETTINGS}
    onSettingsChange={jest.fn()}
    log={emptyHideLog()}
    titles={[makeTitle('ok', 'verified'), makeTitle('bad', 'failed')]}
    nowMs={() => 0}
    onBack={jest.fn()}
  />
);

/** A household with two kids, for the screens that carry the picker. */
const FAMILY: Family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');

const parentAreaWithFamily = (
  <ParentAreaScreen
    gate={gate}
    onGateChange={jest.fn()}
    settings={DEFAULT_SETTINGS}
    onSettingsChange={jest.fn()}
    log={emptyHideLog()}
    family={FAMILY}
    onFamilyChange={jest.fn()}
    profileLogs={addProfileHide(emptyProfileLogs(), 'profile-1', {
      atMs: Date.parse('2026-09-17T19:30:00Z'),
      titleId: 'ok',
      titleName: 'Title ok',
      positionMs: 60_000,
      durationMs: 5_000,
      cause: 'schedule',
    })}
    titles={[makeTitle('ok', 'verified'), makeTitle('bad', 'failed')]}
    nowMs={() => 0}
    onBack={jest.fn()}
  />
);

const UNLOCK = ['1', '3', '5', '7'].map((digit) => `parent-area-key-${digit}`);

const PlayerLayer = ({ covered, card }: { covered: boolean; card: Card }) => (
  <>
    <CoverLayer visible={covered} />
    <CalmCard card={card} />
  </>
);

interface Case {
  name: string;
  element: React.ReactElement;
  /** What is behind the app's layer. A screen paints its own. */
  background: string;
  /** Full screens keep the safe margins. A layer over the video does not. */
  screen: boolean;
  /** Presses to make before measuring, by testID. */
  press?: string[];
}

const CASES: Case[] = [
  { name: 'household-loading', element: <HouseholdStorageScreen failed={false} onRetry={jest.fn()} />,
    background: CALM_COLORS.BACKGROUND, screen: true },
  { name: 'household-error', element: <HouseholdStorageScreen failed onRetry={jest.fn()} />,
    background: CALM_COLORS.BACKGROUND, screen: true },
  {
    name: 'first-run-pin',
    element: <FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'first-run-preset',
    element: <FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [
      'first-run-key-1',
      'first-run-key-3',
      'first-run-key-5',
      'first-run-key-7',
      'first-run-key-1',
      'first-run-key-3',
      'first-run-key-5',
      'first-run-key-7',
    ],
  },
  {
    name: 'first-run-room',
    element: <FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [
      'first-run-key-1',
      'first-run-key-3',
      'first-run-key-5',
      'first-run-key-7',
      'first-run-key-1',
      'first-run-key-3',
      'first-run-key-5',
      'first-run-key-7',
      'first-run-next',
    ],
  },
  {
    name: 'first-run-explainer',
    element: <FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [
      'first-run-key-1',
      'first-run-key-3',
      'first-run-key-5',
      'first-run-key-7',
      'first-run-key-1',
      'first-run-key-3',
      'first-run-key-5',
      'first-run-key-7',
      'first-run-next',
      'first-run-next',
    ],
  },
  {
    name: 'kid-home',
    element: (
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified'), makeTitle('waiting', 'pending')]}
        onOpen={jest.fn()}
        onOpenParentArea={jest.fn()}
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'kid-home-profiles',
    element: (
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified'), makeTitle('waiting', 'pending')]}
        onOpen={jest.fn()}
        onOpenParentArea={jest.fn()}
        profiles={FAMILY.profiles}
        activeProfileId={FAMILY.activeProfileId}
        onChooseProfile={jest.fn()}
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'kid-home-empty',
    element: <KidHomeScreen titles={[]} onOpen={jest.fn()} onOpenParentArea={jest.fn()} />,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'kid-home-offline',
    element: (
      <KidHomeScreen
        titles={[makeTitle('ok', 'verified')]}
        onOpen={jest.fn()}
        onOpenParentArea={jest.fn()}
        offline
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'title-details',
    element: (
      <TitleDetailsScreen
        entry={makeTitle('ok', 'verified')}
        onPlay={jest.fn()}
        onBack={jest.fn()}
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'title-details-pending',
    element: (
      <TitleDetailsScreen
        entry={makeTitle('waiting', 'pending', { segments: [] })}
        onPlay={jest.fn()}
        onBack={jest.fn()}
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'title-details-failed',
    element: (
      <TitleDetailsScreen
        entry={makeTitle('bad', 'failed', {
          rejection: 'bad-signature',
          segments: [],
        })}
        onPlay={jest.fn()}
        onBack={jest.fn()}
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'parent-area-locked',
    element: parentArea,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'parent-area-wrong-pin',
    element: parentArea,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [
      'parent-area-key-2',
      'parent-area-key-2',
      'parent-area-key-2',
      'parent-area-key-2',
    ],
  },
  {
    name: 'parent-area-no-pin',
    element: (
      <ParentAreaScreen
        gate={emptyPinGate()}
        onGateChange={jest.fn()}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={jest.fn()}
        log={emptyHideLog()}
        titles={[]}
        nowMs={() => 0}
        onSetPin={jest.fn()}
        onBack={jest.fn()}
      />
    ),
    background: CALM_COLORS.BACKGROUND,
    screen: true,
  },
  {
    name: 'parent-area-open',
    element: parentArea,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [
      'parent-area-key-1',
      'parent-area-key-3',
      'parent-area-key-5',
      'parent-area-key-7',
    ],
  },
  {
    name: 'parent-area-family',
    element: parentAreaWithFamily,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [...UNLOCK],
  },
  {
    name: 'parent-area-one-kid',
    element: parentAreaWithFamily,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [...UNLOCK, 'parent-area-profiles-profile-1'],
  },
  {
    // The question before a kid is removed, which is a state a parent reads
    // and answers from the sofa like any other.
    name: 'parent-area-remove-kid',
    element: parentAreaWithFamily,
    background: CALM_COLORS.BACKGROUND,
    screen: true,
    press: [
      ...UNLOCK,
      'parent-area-profiles-profile-1',
      'parent-area-remove-profile',
    ],
  },
  {
    name: 'player-countdown',
    element: <PlayerLayer covered={false} card={cardAt(intervals, 16_000)} />,
    background: VIDEO_STAND_IN,
    screen: false,
  },
  {
    name: 'player-covering',
    element: <PlayerLayer covered card={cardAt(intervals, 22_000)} />,
    background: CALM_COLORS.COVER,
    screen: false,
  },
  {
    name: 'player-after',
    element: <PlayerLayer covered={false} card={cardAt(intervals, 24_600)} />,
    background: VIDEO_STAND_IN,
    screen: false,
  },
  {
    name: 'player-unverified',
    element: (
      <PlayerLayer covered card={cardAt([], 0, { rejection: 'missing' })} />
    ),
    background: CALM_COLORS.COVER,
    screen: false,
  },
];

interface Measured {
  name: string;
  text: TextMeasurement[];
  resting: FocusMeasurement[];
  focused: FocusMeasurement[];
  edges: ReturnType<typeof measureEdges>;
  isScreen: boolean;
}

function measureCase(one: Case): Measured {
  render(one.element);
  for (const testID of one.press ?? []) {
    fireEvent.press(screen.getByTestId(testID));
  }
  const tree = () => screen.toJSON() as unknown as RenderedNode;
  const options = { background: one.background };

  const text = measureText(tree(), options);
  const resting = measureFocusRings(tree(), options);
  const edges = measureEdges(tree());

  // Focus each control in turn and measure the ring it shows.
  const focused: FocusMeasurement[] = [];
  for (const control of resting) {
    if (!control.testID) {
      continue;
    }
    fireEvent(screen.getByTestId(control.testID), 'focus');
    const after = measureFocusRings(tree(), options).find(
      (one2) => one2.testID === control.testID,
    );
    if (after) {
      focused.push(after);
    }
    fireEvent(screen.getByTestId(control.testID), 'blur');
  }

  return { name: one.name, text, resting, focused, edges, isScreen: one.screen };
}

const measured: Measured[] = [];

describe('the ten foot pass', () => {
  it('holds the style constants to the floors this test measures against', () => {
    expect(MINIMUM_TEXT_SIZE).toBeGreaterThanOrEqual(FLOORS.textSizeUnits);
    expect(MINIMUM_TEXT_CONTRAST).toBeGreaterThanOrEqual(FLOORS.textContrast);
    expect(FOCUS_RING_WIDTH).toBeGreaterThanOrEqual(FLOORS.focusRingUnits);
    expect(MINIMUM_FOCUS_CONTRAST).toBeGreaterThanOrEqual(FLOORS.focusContrast);
    expect(CALM_SPACE.SAFE_X).toBeGreaterThanOrEqual(FLOORS.safeMarginX);
    expect(CALM_SPACE.SAFE_Y).toBeGreaterThanOrEqual(FLOORS.safeMarginY);
  });

  it.each(CASES.map((one) => [one.name, one] as const))(
    '%s reads from across a room',
    (name, one) => {
      const result = measureCase(one);
      measured.push(result);

      expect(result.text.length).toBeGreaterThan(0);

      // Everything that is wrong, in one list, so one run says all of it.
      const problems: string[] = [];

      for (const line of result.text) {
        const where = `"${line.text.slice(0, 60)}"`;
        if (line.fontSize < FLOORS.textSizeUnits) {
          problems.push(
            `${where} is ${line.fontSize} units, under the ${FLOORS.textSizeUnits} unit floor`,
          );
        }
        if (line.contrast < FLOORS.textContrast) {
          problems.push(
            `${where} is ${line.colour} on ${line.background}, ${roundRatio(
              line.contrast,
            )} to 1, under ${FLOORS.textContrast}`,
          );
        }
        // Nothing is faded. Half opacity text is unreadable across a room.
        if (line.opacity !== 1) {
          problems.push(`${where} is drawn at opacity ${line.opacity}`);
        }
      }

      for (const control of result.resting) {
        if (control.borderWidth < FLOORS.focusRingUnits) {
          problems.push(
            `${control.testID} has a ${control.borderWidth} unit border, under the ${FLOORS.focusRingUnits} unit ring`,
          );
        }
      }

      for (const control of result.focused) {
        if (control.ringColour !== CALM_COLORS.FOCUS_RING) {
          problems.push(
            `${control.testID} shows ${control.ringColour} when focused, not the focus ring`,
          );
        }
        if (control.ringOnFill < FLOORS.focusContrast) {
          problems.push(
            `${control.testID} ring on its fill is ${roundRatio(control.ringOnFill)} to 1`,
          );
        }
        if (control.ringOnOutside < FLOORS.focusContrast) {
          problems.push(
            `${control.testID} ring on what is outside it is ${roundRatio(
              control.ringOnOutside,
            )} to 1`,
          );
        }
      }

      if (result.isScreen) {
        if (result.edges.left < FLOORS.safeMarginX) {
          problems.push(
            `content sits ${result.edges.left} units from the side, inside the ${FLOORS.safeMarginX} unit safe margin`,
          );
        }
        if (result.edges.top < FLOORS.safeMarginY) {
          problems.push(
            `content sits ${result.edges.top} units from the top, inside the ${FLOORS.safeMarginY} unit safe margin`,
          );
        }
      }

      expect(problems).toEqual([]);
    },
  );

  it('measured every screen and wrote the numbers down', () => {
    expect(measured).toHaveLength(CASES.length);

    const lines = measured.flatMap((one) => one.text);
    const rings = measured.flatMap((one) => one.focused);
    const summary = {
      note:
        'Measured off the rendered screens. The virtual device cannot be photographed, so these numbers are the ten foot check rather than a screenshot. Sizes are 1080p units, ratios are WCAG 2.2 contrast ratios.',
      measuredBy: 'app/test/calmframes/tenFoot.test.tsx',
      floors: {
        text_size_units: MINIMUM_TEXT_SIZE,
        text_contrast: MINIMUM_TEXT_CONTRAST,
        focus_ring_units: FOCUS_RING_WIDTH,
        focus_contrast: MINIMUM_FOCUS_CONTRAST,
        safe_margin_units: { x: CALM_SPACE.SAFE_X, y: CALM_SPACE.SAFE_Y },
      },
      totals: {
        screens: measured.length,
        lines_of_text: lines.length,
        controls: rings.length,
        smallest_text_units: Math.min(...lines.map((line) => line.fontSize)),
        worst_text_contrast: roundRatio(
          Math.min(...lines.map((line) => line.contrast)),
        ),
        worst_focus_contrast: roundRatio(
          Math.min(...rings.map((ring) => Math.min(ring.ringOnFill, ring.ringOnOutside))),
        ),
      },
      screens: measured.map((one) => ({
        screen: one.name,
        edges: one.edges,
        smallest_text_units: Math.min(...one.text.map((line) => line.fontSize)),
        worst_text_contrast: roundRatio(
          Math.min(...one.text.map((line) => line.contrast)),
        ),
        controls: one.focused.length,
        text: one.text.map((line) => ({
          text: line.text,
          units: line.fontSize,
          colour: line.colour,
          on: line.background,
          contrast: roundRatio(line.contrast),
        })),
      })),
    };

    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.writeFileSync(
      path.join(OUT_DIR, 'ten-foot.json'),
      `${JSON.stringify(summary, null, 2)}\n`,
    );
    expect(fs.existsSync(path.join(OUT_DIR, 'ten-foot.json'))).toBe(true);
  });
});

describe('the contrast arithmetic itself', () => {
  it('matches the pairs WCAG gives as examples', () => {
    // Black on white is 21 to 1, and any colour against itself is 1 to 1.
    expect(roundRatio(contrastRatio('#000000', '#ffffff'))).toBe(21);
    expect(roundRatio(contrastRatio('#7f7f7f', '#7f7f7f'))).toBe(1);
    // The pair either way round gives the same answer.
    expect(contrastRatio('#101a24', '#f4f7fa')).toBeCloseTo(
      contrastRatio('#f4f7fa', '#101a24'),
      10,
    );
  });

  it('reads the colour a person sees, not the one on the node', () => {
    const tree: RenderedNode = {
      type: 'View',
      props: { style: { backgroundColor: '#101A24' } },
      children: [
        {
          type: 'View',
          props: { style: { backgroundColor: '#1B2735' } },
          children: [
            {
              type: 'Text',
              props: { style: { color: '#F4F7FA', fontSize: 36 } },
              children: ['on the card'],
            },
          ],
        },
        {
          type: 'Text',
          props: { style: { color: '#B9C4D0', fontSize: 32 } },
          children: ['on the screen'],
        },
      ],
    };
    const lines = measureText(tree, { background: VIDEO_STAND_IN });
    expect(lines.map((line) => line.background)).toEqual(['#1B2735', '#101A24']);
    expect(lines[0].fontSize).toBe(36);
  });
});
