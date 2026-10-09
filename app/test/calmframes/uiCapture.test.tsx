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
import { BENIGN_STORY_LABEL } from '../../src/calmframes/benignStory';
import CalmCard from '../../src/calmframes/CalmCard';
import { CALM_COLORS } from '../../src/calmframes/calmStyles';
import CornerPlate from '../../src/calmframes/CornerPlate';
import {
  Card,
  cardAt,
  CHECKING_CARD,
  NO_CARD,
} from '../../src/calmframes/cards';
import CoverLayer from '../../src/calmframes/CoverLayer';
import CreditsScreen from '../../src/calmframes/CreditsScreen';
import { buildCoverIntervals } from '../../src/calmframes/coverSchedule';
import FirstRunScreen from '../../src/calmframes/FirstRunScreen';
import HouseholdStorageScreen from '../../src/calmframes/HouseholdStorageScreen';
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
  ALL_UI_FRAMES,
  HOUSEHOLD_LOADING_FRAME,
  HOUSEHOLD_ERROR_FRAME,
  FIRST_RUN_EXPLAINER_FRAME,
  FIRST_RUN_PIN_FRAME,
  FIRST_RUN_PRESET_FRAME,
  FIRST_RUN_ROOM_FRAME,
  KID_HOME_EMPTY_FRAME,
  KID_HOME_FOCUSED_FRAME,
  KID_HOME_FRAME,
  KID_HOME_OFFLINE_FRAME,
  KID_HOME_PROFILES_FRAME,
  PARENT_LOCKED_FRAME,
  PARENT_OPEN_FRAME,
  PARENT_PROFILE_FRAME,
  PARENT_REMOVE_KID_FRAME,
  PARENT_WRONG_PIN_FRAME,
  playerFrame,
  TITLE_DETAILS_BLOCKED_FRAME,
  TITLE_DETAILS_FRAME,
} from '../../src/calmframes/uiFrames';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
import {
  addProfile,
  Family,
  newFamily,
} from '../../src/calmframes/profiles';

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

/**
 * What the player paints over the video, for one card state. `plate` adds the
 * practice plate the labelled Harbor demo carries, as PlayerScreen draws it.
 */
const PlayerLayer = ({
  covered,
  card,
  plate = false,
}: {
  covered: boolean;
  card: Card;
  plate?: boolean;
}) => (
  <>
    <CoverLayer visible={covered} />
    <CalmCard card={card} />
    {plate ? <CornerPlate label={BENIGN_STORY_LABEL} testID="benign-demo" /> : null}
  </>
);

const intervals = buildCoverIntervals([{ startMs: 20_000, endMs: 24_000 }], {
  guardBandMs: 500,
});

/**
 * Colours read off a rendered tree, as the app would paint them.
 *
 * `act` is where a state that needs pressing or focusing gets there: a wrong
 * PIN, a focused poster, the step after the one the screen opens on. Whatever
 * it does, the frame is read after it, so what is recorded is the state a
 * person would be looking at.
 */
function renderedFrame(
  name: string,
  element: React.ReactElement,
  act?: () => void,
): UiFrame {
  const { unmount } = render(element);
  act?.();
  const frame = frameFromTree(name, screen.toJSON() as unknown as RenderedNode);
  unmount();
  return frame;
}

const press = (testID: string) => fireEvent.press(screen.getByTestId(testID));
const pressAll = (...testIDs: string[]) => testIDs.forEach(press);

/** The four presses that set a PIN, typed twice. */
const FIRST_RUN_PIN = ['1', '3', '5', '7'].map((digit) => `first-run-key-${digit}`);

const firstRun = () => (
  <FirstRunScreen onDone={jest.fn()} newSalt={() => 'seed'} rounds={4} />
);

const parentArea = (titles: CheckedTitle[]) => (
  <ParentAreaScreen
    gate={setPin(emptyPinGate(), '1357', 'seed', 4)}
    onGateChange={jest.fn()}
    settings={DEFAULT_SETTINGS}
    onSettingsChange={jest.fn()}
    log={emptyHideLog()}
    titles={titles}
    nowMs={() => 0}
  />
);

/** A household with two kids, for the screens that carry the picker. */
const FAMILY: Family = addProfile(newFamily(DEFAULT_SETTINGS, 'Robin'), 'Sam');

const familyShelf = (offline = false) => (
  <KidHomeScreen
    titles={[makeTitle('ok', 'verified')]}
    onOpen={jest.fn()}
    offline={offline}
    profiles={FAMILY.profiles}
    activeProfileId={FAMILY.activeProfileId}
    onChooseProfile={jest.fn()}
  />
);

const familyParentArea = (titles: CheckedTitle[]) => (
  <ParentAreaScreen
    gate={setPin(emptyPinGate(), '1357', 'seed', 4)}
    onGateChange={jest.fn()}
    settings={DEFAULT_SETTINGS}
    onSettingsChange={jest.fn()}
    log={emptyHideLog()}
    family={FAMILY}
    onFamilyChange={jest.fn()}
    titles={titles}
    nowMs={() => 0}
  />
);

/** A title whose check did not pass, so its page shows a notice and no strip. */
function blockedTitle(): CheckedTitle {
  return {
    ...makeTitle('bad', 'failed'),
    rejection: 'bad-signature',
    segments: [],
  };
}

describe('what the app paints', () => {
  it('measures household storage loading and errors from the rendered screen', () => {
    expect(renderedFrame('household-loading', <HouseholdStorageScreen failed={false} onRetry={jest.fn()} />))
      .toEqual(HOUSEHOLD_LOADING_FRAME);
    expect(renderedFrame('household-error', <HouseholdStorageScreen failed onRetry={jest.fn()} />))
      .toEqual(HOUSEHOLD_ERROR_FRAME);
  });
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

  it('matches what the shelf with a family on it reports, in each of its states', () => {
    // One frame covers all three, and that is the claim being checked rather
    // than assumed: the chips carry the chosen fill, so a focused poster and
    // the offline banner add nothing new to what is painted.
    expect(renderedFrame('kid-home-profiles', familyShelf())).toEqual(
      KID_HOME_PROFILES_FRAME,
    );
    expect(renderedFrame('kid-home-profiles', familyShelf(true))).toEqual(
      KID_HOME_PROFILES_FRAME,
    );
    render(familyShelf());
    fireEvent(screen.getByTestId('kid-home-poster-ok'), 'focus');
    expect(
      frameFromTree('kid-home-profiles', screen.toJSON() as unknown as RenderedNode),
    ).toEqual(KID_HOME_PROFILES_FRAME);
  });

  it('matches what the parent area reports with a family in it', () => {
    const area = familyParentArea([makeTitle('ok', 'verified')]);
    render(area);
    for (const digit of '1357') {
      fireEvent.press(screen.getByTestId(`parent-area-key-${digit}`));
    }
    expect(
      frameFromTree('parent-area-open', screen.toJSON() as unknown as RenderedNode),
    ).toEqual(PARENT_OPEN_FRAME);

    // Choosing a kid puts the plain card colour before the chosen fill,
    // because the household chip is first in the row and is no longer chosen.
    fireEvent.press(screen.getByTestId('parent-area-profiles-profile-1'));
    expect(
      frameFromTree('parent-area-profile', screen.toJSON() as unknown as RenderedNode),
    ).toEqual(PARENT_PROFILE_FRAME);

    // Asking before removing that kid paints no new colour: the question is a
    // notice block on the card colour and the picker above it has not moved.
    // It is a frame of its own so the flash run walks through the state.
    fireEvent.press(screen.getByTestId('parent-area-remove-profile'));
    expect(
      frameFromTree('parent-area-remove-kid', screen.toJSON() as unknown as RenderedNode),
    ).toEqual(PARENT_REMOVE_KID_FRAME);
  });

  it('lists every frame the app can show, so the flash run covers them all', () => {
    // ALL_UI_FRAMES is what docs/SHOT_MANIFEST.md points at and what the
    // capture below walks. A frame declared and left out of that list is a
    // screen the flash check never sees.
    const named = new Set(ALL_UI_FRAMES.map((frame) => frame.screen));
    for (const frame of [
      KID_HOME_PROFILES_FRAME,
      PARENT_PROFILE_FRAME,
      // The player while the map is still being checked.
      playerFrame(true, 'checking'),
      // The Harbor demo between its holds, when only its plate is painted.
      playerFrame(false, 'none', true),
      // Seen to fail by taking this one back out of ALL_UI_FRAMES:
      //     expect(received).toBe(expected) // Object.is equality
      //     Expected: true
      //     Received: false
      PARENT_REMOVE_KID_FRAME,
    ]) {
      expect(named.has(frame.screen)).toBe(true);
    }
  });

  it('matches what the empty and unreachable shelves report', () => {
    expect(
      renderedFrame('kid-home-empty', (
        <KidHomeScreen titles={[]} onOpen={jest.fn()} />
      )),
    ).toEqual(KID_HOME_EMPTY_FRAME);

    expect(
      renderedFrame('kid-home-offline', (
        <KidHomeScreen
          titles={[makeTitle('ok', 'verified')]}
          onOpen={jest.fn()}
          offline
        />
      )),
    ).toEqual(KID_HOME_OFFLINE_FRAME);
  });

  it('matches what the details page reports, ready and not ready', () => {
    expect(
      renderedFrame('title-details', (
        <TitleDetailsScreen entry={makeTitle('ok', 'verified')} onPlay={jest.fn()} />
      )),
    ).toEqual(TITLE_DETAILS_FRAME);

    // A title that did not verify has no schedule, so the strip and both of
    // its colours are gone and what is left is the notice.
    expect(
      renderedFrame('title-details-blocked', (
        <TitleDetailsScreen entry={blockedTitle()} onPlay={jest.fn()} />
      )),
    ).toEqual(TITLE_DETAILS_BLOCKED_FRAME);
  });

  it('matches what each step of the first run reports', () => {
    expect(renderedFrame('first-run-pin', firstRun())).toEqual(FIRST_RUN_PIN_FRAME);

    expect(
      renderedFrame('first-run-preset', firstRun(), () => {
        pressAll(...FIRST_RUN_PIN, ...FIRST_RUN_PIN);
      }),
    ).toEqual(FIRST_RUN_PRESET_FRAME);

    expect(
      renderedFrame('first-run-room', firstRun(), () => {
        pressAll(...FIRST_RUN_PIN, ...FIRST_RUN_PIN, 'first-run-next');
      }),
    ).toEqual(FIRST_RUN_ROOM_FRAME);

    expect(
      renderedFrame('first-run-explainer', firstRun(), () => {
        pressAll(
          ...FIRST_RUN_PIN,
          ...FIRST_RUN_PIN,
          'first-run-next',
          'first-run-next',
        );
      }),
    ).toEqual(FIRST_RUN_EXPLAINER_FRAME);
  });

  it('paints the same picture for a wrong PIN as for the keypad itself', () => {
    // The words change, the colours do not. Somebody mistyping a PIN four
    // times in a row should not be making the screen flash.
    expect(
      renderedFrame('parent-area-wrong-pin', parentArea([]), () => {
        pressAll(
          'parent-area-key-2',
          'parent-area-key-2',
          'parent-area-key-2',
          'parent-area-key-2',
        );
      }),
    ).toEqual(PARENT_WRONG_PIN_FRAME);
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
      [true, CHECKING_CARD],
      [false, NO_CARD],
      [false, cardAt(intervals, 16_000)],
      [true, cardAt(intervals, 22_000)],
      [false, cardAt(intervals, 24_600)],
      [true, cardAt([], 0, { rejection: 'missing' })],
    ];
    // Each state twice: as any title shows it, and as the Harbor demo shows
    // it with its practice plate on screen as well.
    for (const plate of [false, true]) {
      for (const [covered, card] of cases) {
        const expected = playerFrame(covered, card.kind, plate);
        const actual = renderedFrame(expected.screen, (
          <PlayerLayer covered={covered} card={card} plate={plate} />
        ));
        // Every colour the app's own layer paints, in paint order. With the
        // cover off there is no background of ours, so the first colour found
        // is already one of the surfaces.
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
    // A path through the whole app, in the order a household meets it: the
    // first run one step at a time, a shelf with nothing on it, a shelf with
    // the service down, a title, the player through a flagged part, and the
    // parent area with a wrong PIN on the way in. The empty and error states
    // are in here with everything else, because a screen nobody demonstrates
    // is still a screen the app can show, and it still has to not flash on the
    // way in or out.
    //
    // A scene is one mounted screen and the states it moves through, so the
    // first run is walked the way a parent walks it rather than remounted at
    // step one for each step, which would record a path nobody takes.
    interface Stop {
      name: string;
      reason: string;
      act?: () => void;
    }
    const scenes: Array<{ element: React.ReactElement; stops: Stop[] }> = [
      { element: <HouseholdStorageScreen failed={false} onRetry={jest.fn()} />,
        stops: [{ name: 'household-loading', reason: 'restoring household' }] },
      { element: <HouseholdStorageScreen failed onRetry={jest.fn()} />,
        stops: [{ name: 'household-error', reason: 'storage unavailable' }] },
      {
        element: firstRun(),
        stops: [
          { name: 'first-run-pin', reason: 'first run, the PIN' },
          {
            name: 'first-run-preset',
            reason: 'first run, how strict',
            act: () => pressAll(...FIRST_RUN_PIN, ...FIRST_RUN_PIN),
          },
          {
            name: 'first-run-room',
            reason: 'first run, the room',
            act: () => press('first-run-next'),
          },
          {
            name: 'first-run-explainer',
            reason: 'first run, what gets hidden',
            act: () => press('first-run-next'),
          },
        ],
      },
      {
        element: <KidHomeScreen titles={[]} onOpen={jest.fn()} />,
        stops: [{ name: 'kid-home-empty', reason: 'nothing checked yet' }],
      },
      {
        element: (
          <KidHomeScreen
            titles={[makeTitle('ok', 'verified')]}
            onOpen={jest.fn()}
            offline
          />
        ),
        stops: [
          { name: 'kid-home-offline', reason: 'the check service is unreachable' },
        ],
      },
      {
        element: (
          <KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />
        ),
        stops: [
          { name: 'kid-home', reason: 'open the shelf' },
          {
            name: 'kid-home-focused',
            reason: 'poster focused',
            act: () => fireEvent(screen.getByTestId('kid-home-poster-ok'), 'focus'),
          },
        ],
      },
      {
        // One stop, not two. A shelf with a picker on it paints the same
        // colours whichever kid is chosen, so a second stop would be dropped
        // as a repeat and would only make the timeline look longer.
        element: familyShelf(),
        stops: [
          { name: 'kid-home-profiles', reason: 'the shelf asks who is watching' },
        ],
      },
      {
        element: (
          <TitleDetailsScreen entry={makeTitle('ok', 'verified')} onPlay={jest.fn()} />
        ),
        stops: [{ name: 'title-details', reason: 'open a title' }],
      },
      {
        element: <PlayerLayer covered={true} card={CHECKING_CARD} />,
        stops: [{ name: 'player-covered-checking', reason: 'checking the map' }],
      },
      {
        element: <PlayerLayer covered={false} card={NO_CARD} />,
        stops: [{ name: 'player-clear-none', reason: 'play' }],
      },
      {
        element: <PlayerLayer covered={false} card={cardAt(intervals, 16_000)} />,
        stops: [{ name: 'player-clear-countdown', reason: 'countdown' }],
      },
      {
        element: <PlayerLayer covered={true} card={cardAt(intervals, 22_000)} />,
        stops: [{ name: 'player-covered-covering', reason: 'cover on' }],
      },
      {
        element: <PlayerLayer covered={false} card={cardAt(intervals, 24_600)} />,
        stops: [{ name: 'player-clear-after', reason: 'cover off' }],
      },
      {
        element: (
          <PlayerLayer covered={true} card={cardAt([], 0, { rejection: 'missing' })} />
        ),
        stops: [{ name: 'player-covered-unverified', reason: 'title not checked' }],
      },
      // The Harbor demo, which carries its practice plate the whole time.
      {
        element: <PlayerLayer covered={true} card={CHECKING_CARD} plate />,
        stops: [{ name: 'player-covered-checking-plate', reason: 'demo, checking the map' }],
      },
      {
        element: <PlayerLayer covered={false} card={NO_CARD} plate />,
        stops: [{ name: 'player-clear-none-plate', reason: 'demo plays' }],
      },
      {
        element: <PlayerLayer covered={false} card={cardAt(intervals, 16_000)} plate />,
        stops: [{ name: 'player-clear-countdown-plate', reason: 'demo countdown' }],
      },
      {
        element: <PlayerLayer covered={true} card={cardAt(intervals, 22_000)} plate />,
        stops: [{ name: 'player-covered-covering-plate', reason: 'demo practice hold' }],
      },
      {
        element: <PlayerLayer covered={false} card={cardAt(intervals, 24_600)} plate />,
        stops: [{ name: 'player-clear-after-plate', reason: 'demo hold over' }],
      },
      {
        element: (
          <KidHomeScreen titles={[makeTitle('ok', 'verified')]} onOpen={jest.fn()} />
        ),
        stops: [{ name: 'kid-home', reason: 'back to the shelf' }],
      },
      {
        element: parentArea([makeTitle('ok', 'verified'), blockedTitle()]),
        stops: [
          { name: 'parent-area-locked', reason: 'open the parent area' },
          {
            name: 'parent-area-wrong-pin',
            reason: 'wrong PIN',
            act: () =>
              pressAll(
                'parent-area-key-2',
                'parent-area-key-2',
                'parent-area-key-2',
                'parent-area-key-2',
              ),
          },
          {
            name: 'parent-area-open',
            reason: 'the right PIN',
            act: () =>
              pressAll(
                'parent-area-key-1',
                'parent-area-key-3',
                'parent-area-key-5',
                'parent-area-key-7',
              ),
          },
        ],
      },
      {
        element: familyParentArea([makeTitle('ok', 'verified')]),
        stops: [
          {
            name: 'parent-area-open',
            reason: 'the parent area of a household with kids in it',
            act: () =>
              pressAll(
                'parent-area-key-1',
                'parent-area-key-3',
                'parent-area-key-5',
                'parent-area-key-7',
              ),
          },
          {
            name: 'parent-area-profile',
            reason: 'one kid',
            act: () => press('parent-area-profiles-profile-1'),
          },
          {
            name: 'parent-area-remove-kid',
            reason: 'the question before a kid is removed',
            act: () => press('parent-area-remove-profile'),
          },
        ],
      },
      {
        element: <TitleDetailsScreen entry={blockedTitle()} onPlay={jest.fn()} />,
        stops: [
          { name: 'title-details-blocked', reason: 'a title that is not ready' },
        ],
      },
      {
        element: <CreditsScreen />,
        stops: [{ name: 'credits', reason: 'open the credits' }],
      },
    ];

    // A quarter of a second between states is faster than anyone can press a
    // button, so it is the worst case for a flash rate. The screens record
    // themselves as well, through useUiCapture, and those entries carry the
    // wall clock. tools/ui_flashmap.mjs ignores both and holds every frame for
    // 100 ms, which is faster again than either.
    let atMs = 0;
    let stops = 0;
    for (const scene of scenes) {
      const { unmount } = render(scene.element);
      for (const stop of scene.stops) {
        stop.act?.();
        const frame = frameFromTree(
          stop.name,
          screen.toJSON() as unknown as RenderedNode,
        );
        recordUiFrame(frame, stop.reason, atMs);
        atMs += 250;
        stops += 1;
      }
      unmount();
    }

    const timeline = getUiCaptureTimeline();
    expect(timeline.length).toBeGreaterThanOrEqual(stops - 1);

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
