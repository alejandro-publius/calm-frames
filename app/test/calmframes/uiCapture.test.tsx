/**
 * The app's own screens, and the check that they do not flash.
 *
 * Two jobs:
 *
 * 1. Prove the frames the app reports are the colours it really paints. Every
 *    screen is rendered here for real and the colours are read off the rendered
 *    tree. If a style changes and the declared frame does not, this fails.
 * 2. Write the timeline out, so tools/ui_flashmap.mjs can turn it into a video
 *    and run flashmap over it. That file is the input to the CI step.
 *
 * Pixel capture is not available on Vega, which is why the frames are reported
 * rather than photographed. uiCapture.ts says what was tried.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import fs from 'fs';
import path from 'path';
import React from 'react';
import CalmCard from '../../src/calmframes/CalmCard';
import { CALM_COLORS } from '../../src/calmframes/calmStyles';
import { Card, cardAt, NO_CARD } from '../../src/calmframes/cards';
import CoverLayer from '../../src/calmframes/CoverLayer';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import { emptyHideLog } from '../../src/calmframes/hideLog';
import KidHomeScreen from '../../src/calmframes/KidHomeScreen';
import ParentAreaScreen from '../../src/calmframes/ParentAreaScreen';
import { emptyPinGate, setPin } from '../../src/calmframes/parentGate';
import TitleDetailsScreen from '../../src/calmframes/TitleDetailsScreen';
import { CheckedTitle } from '../../src/calmframes/titleStatus';
import {
  frameFromTree,
  getUiCaptureTimeline,
  recordUiFrame,
  RenderedNode,
  startUiCapture,
  stopUiCapture,
  UiFrame,
} from '../../src/calmframes/uiCapture';
import {
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_FRAME,
  PARENT_LOCKED_FRAME,
  PARENT_OPEN_FRAME,
  playerFrame,
  TITLE_DETAILS_FRAME,
} from '../../src/calmframes/uiFrames';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';

const OUT_DIR = path.join(__dirname, '..', '..', 'build', 'ui-capture');

function makeTitle(id: string, status: CheckedTitle['status']): CheckedTitle {
  return {
    title: {
      id,
      title: `Title ${id}`,
      uri: `https://example.invalid/${id}.m3u8`,
      sha256: 'a'.repeat(64),
      durationMs: 600_000,
    },
    status,
    segments: [
      { startMs: 60_000, endMs: 64_000 },
      { startMs: 300_000, endMs: 301_000, reason: 'red' },
    ],
    hiddenMs: 5_000,
    verifiedProfiles: ['wcag'],
  };
}

/** What the player paints over the video, for one card state. */
const PlayerLayer = ({ covered, card }: { covered: boolean; card: Card }) => (
  <>
    <CoverLayer visible={covered} />
    <CalmCard card={card} />
  </>
);

const intervals = buildCoverIntervals([{ startMs: 20_000, endMs: 24_000 }], {
  guardBandMs: 500,
});

/** Colours read off a rendered tree, as the app would paint them. */
function renderedFrame(name: string, element: React.ReactElement): UiFrame {
  const { toJSON, unmount } = render(element);
  const tree = toJSON();
  const frame = frameFromTree(name, tree as unknown as RenderedNode);
  unmount();
  return frame;
}

describe('what the app paints', () => {
  it('reads the colours off a rendered tree, background first', () => {
    const frame = renderedFrame('kid-home', (
      <KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />
    ));
    expect(frame.background).toBe(CALM_COLORS.BACKGROUND);
    expect(frame.surfaces).toContain(CALM_COLORS.SURFACE);
  });

  it('matches what the kid home reports, unfocused and focused', () => {
    expect(
      renderedFrame('kid-home', (
        <KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />
      )),
    ).toEqual(KID_HOME_FRAME);

    render(<KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />);
    fireEvent(screen.getByTestId('kid-home-poster-ok'), 'focus');
    const focused = frameFromTree(
      'kid-home-focused',
      screen.toJSON() as unknown as RenderedNode,
    );
    expect(focused).toEqual(KID_HOME_FOCUSED_FRAME);
  });

  it('matches what the details page reports', () => {
    expect(
      renderedFrame('title-details', (
        <TitleDetailsScreen entry={makeTitle('ok', 'verified')} onPlay={jest.fn()} />
      )),
    ).toEqual(TITLE_DETAILS_FRAME);
  });

  it('matches what the parent area reports, locked and open', () => {
    const gate = setPin(emptyPinGate(), '1357', 'seed', 4);
    const area = (
      <ParentAreaScreen
        gate={gate}
        onGateChange={jest.fn()}
        settings={DEFAULT_SETTINGS}
        onSettingsChange={jest.fn()}
        log={emptyHideLog()}
        titles={[makeTitle('ok', 'verified')]}
        nowMs={() => 0}
      />
    );
    expect(renderedFrame('parent-area-locked', area)).toEqual(PARENT_LOCKED_FRAME);

    render(area);
    for (const digit of '1357') {
      fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
    }
    expect(
      frameFromTree('parent-area-open', screen.toJSON() as unknown as RenderedNode),
    ).toEqual(PARENT_OPEN_FRAME);
  });

  it('matches what the player layer reports, covered and clear', () => {
    const cases: Array<[boolean, Card]> = [
      [false, NO_CARD],
      [false, cardAt(intervals, 16_000)],
      [true, cardAt(intervals, 22_000)],
      [false, cardAt(intervals, 24_600)],
      [true, cardAt([], 0, { rejection: 'missing' })],
    ];
    for (const [covered, card] of cases) {
      const expected = playerFrame(covered, card.kind);
      const actual = renderedFrame(expected.screen, (
        <PlayerLayer covered={covered} card={card} />
      ));
      // Every colour the app's own layer paints, in paint order. With the
      // cover off there is no background of ours, so the first colour found is
      // already one of the surfaces.
      const painted =
        actual.background === '#000000' && actual.surfaces.length === 0 && !covered
          ? []
          : [actual.background, ...actual.surfaces];
      if (covered) {
        expect(painted[0]).toBe(CALM_COLORS.COVER);
        expect(painted.slice(1)).toEqual(expected.surfaces);
      } else {
        expect(painted).toEqual(expected.surfaces);
      }
    }
  });
});

describe('the capture path', () => {
  beforeEach(() => {
    startUiCapture();
  });

  afterEach(() => {
    stopUiCapture();
  });

  it('records a frame only when it changes', () => {
    expect(recordUiFrame(KID_HOME_FRAME, 'kid home', 1_000)).toBe(true);
    expect(recordUiFrame(KID_HOME_FRAME, 'kid home again', 1_100)).toBe(false);
    expect(recordUiFrame(KID_HOME_FOCUSED_FRAME, 'focused', 1_200)).toBe(true);
    expect(getUiCaptureTimeline()).toHaveLength(2);
  });

  it('records nothing when it is not recording', () => {
    stopUiCapture();
    expect(recordUiFrame(KID_HOME_FRAME, 'kid home', 1_000)).toBe(false);
  });

  it('records every screen and transition the app can show, and writes them out', () => {
    // Walk the app the way a person would: shelf, focus a poster, open the
    // details, play, through a flagged part, back out, then the parent area.
    const walk: Array<[React.ReactElement, string, string]> = [
      [
        <KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />,
        'kid-home',
        'open the shelf',
      ],
      [
        <TitleDetailsScreen entry={makeTitle('ok', 'verified')} onPlay={jest.fn()} />,
        'title-details',
        'open a title',
      ],
      [<PlayerLayer covered={false} card={NO_CARD} />, 'player-clear-none', 'play'],
      [
        <PlayerLayer covered={false} card={cardAt(intervals, 16_000)} />,
        'player-clear-countdown',
        'countdown',
      ],
      [
        <PlayerLayer covered={true} card={cardAt(intervals, 22_000)} />,
        'player-covered-covering',
        'cover on',
      ],
      [
        <PlayerLayer covered={false} card={cardAt(intervals, 24_600)} />,
        'player-clear-after',
        'cover off',
      ],
      [
        <PlayerLayer
          covered={true}
          card={cardAt([], 0, { rejection: 'missing' })}
        />,
        'player-covered-unverified',
        'title not checked',
      ],
      [
        <KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />,
        'kid-home',
        'back to the shelf',
      ],
      [
        <ParentAreaScreen
          gate={setPin(emptyPinGate(), '1357', 'seed', 4)}
          onGateChange={jest.fn()}
          settings={DEFAULT_SETTINGS}
          onSettingsChange={jest.fn()}
          log={emptyHideLog()}
          titles={[makeTitle('ok', 'verified')]}
          nowMs={() => 0}
        />,
        'parent-area-locked',
        'open the parent area',
      ],
    ];

    // A quarter of a second between screens is faster than anyone can press a
    // button, so it is the worst case for a flash rate.
    let atMs = 0;
    for (const [element, name, reason] of walk) {
      const frame = renderedFrame(name, element);
      recordUiFrame(frame, reason, atMs);
      atMs += 250;
    }

    const timeline = getUiCaptureTimeline();
    expect(timeline.length).toBeGreaterThanOrEqual(8);

    fs.mkdirSync(OUT_DIR, { recursive: true });
    fs.writeFileSync(
      path.join(OUT_DIR, 'ui-frames.json'),
      `${JSON.stringify(
        {
          note:
            'Frames the app reports for its own screens and transitions. Vega has no pixel capture, so these are the colours the app paints, read off the rendered tree. tools/ui_flashmap.mjs turns them into a video and runs flashmap over it.',
          capturedBy: 'app/test/calmframes/uiCapture.test.tsx',
          frames: timeline,
        },
        null,
        2,
      )}\n`,
    );
    expect(fs.existsSync(path.join(OUT_DIR, 'ui-frames.json'))).toBe(true);
  });
});
