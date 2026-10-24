/**
 * The first run.
 *
 * What it has to get right is not the happy path, which is four presses and a
 * button. It is these:
 *
 * - a PIN typed differently the second time does not get set. On a device with
 *   no account and no recovery, a mistyped PIN locks a parent out of the
 *   settings that protect their child, for good;
 * - what the parent chose is what comes out the other end, not the defaults;
 * - the explainer carries the approved sentence and nothing stronger;
 * - the PIN never appears anywhere in what is handed back. What is stored is a
 *   salted hash of it.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import React from 'react';
import { ScrollView } from 'react-native';
import { EXPLAINER_LINES, SAFETY_NOTE } from '../../src/calmframes/copy';
import FirstRunScreen, {
  FirstRunResult,
} from '../../src/calmframes/FirstRunScreen';
import {
  DEFAULT_SETTINGS,
  TV_DIAGONAL_CHOICES_IN,
} from '../../src/calmframes/household';
import { attemptPin, hashPin } from '../../src/calmframes/parentGate';

const ROUNDS = 4;

function renderFirstRun() {
  const onDone = jest.fn<void, [FirstRunResult]>();
  render(
    <FirstRunScreen onDone={onDone} newSalt={() => 'a-fresh-salt'} rounds={ROUNDS} />,
  );
  return onDone;
}

const type = (digits: string) => {
  for (const digit of digits) {
    fireEvent.press(screen.getByTestId(`first-run-key-${digit}`));
  }
};

describe('the first run', () => {
  it('corrects a digit in both PIN entries before saving the intended PIN', () => {
    const onDone = renderFirstRun();
    // Empty correction is harmless and does not leave the PIN step.
    fireEvent.press(screen.getByTestId('first-run-key-delete'));
    type('139');
    fireEvent.press(screen.getByTestId('first-run-key-delete'));
    expect(screen.getByTestId('first-run-entered').props.children).toBe('**');
    type('57');
    type('139');
    fireEvent.press(screen.getByTestId('first-run-key-delete'));
    type('57');
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-done'));
    expect(attemptPin(onDone.mock.calls[0][0].gate, '1357', 0).ok).toBe(true);
  });

  it('asks for the PIN, the preset, the room and then explains itself', () => {
    const onDone = renderFirstRun();

    expect(screen.getByTestId('first-run-step').props.children).toEqual(
      expect.arrayContaining(['Step ', 1, ' of ', 4]),
    );
    type('2468');
    expect(screen.getByTestId('first-run-title').props.children).toBe(
      'Confirm your PIN',
    );
    type('2468');

    expect(screen.getByTestId('first-run-preset-wcag')).toBeTruthy();
    fireEvent.press(screen.getByTestId('first-run-preset-broadcast'));
    fireEvent.press(screen.getByTestId('first-run-next'));

    fireEvent.press(screen.getByTestId('first-run-tv-65'));
    fireEvent.press(screen.getByTestId('first-run-seat-72'));
    fireEvent.press(screen.getByTestId('first-run-next'));

    expect(screen.getByTestId('first-run-explainer')).toBeTruthy();
    fireEvent.press(screen.getByTestId('first-run-done'));

    expect(onDone).toHaveBeenCalledTimes(1);
    const result = onDone.mock.calls[0][0];
    expect(result.settings).toEqual({
      preset: 'broadcast',
      tvDiagonalIn: 65,
      seatDistanceIn: 72,
    });
  });

  it('sets a PIN that the gate then accepts, and stores only its hash', () => {
    const onDone = renderFirstRun();
    type('1379');
    type('1379');
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-done'));

    const { gate } = onDone.mock.calls[0][0];
    expect(gate.record?.salt).toBe('a-fresh-salt');
    expect(gate.record?.hash).toBe(hashPin('1379', 'a-fresh-salt', ROUNDS));
    expect(JSON.stringify(gate)).not.toContain('1379');
    expect(attemptPin(gate, '1379', 0).ok).toBe(true);
    expect(attemptPin(gate, '1378', 0).ok).toBe(false);
  });

  it('will not set a PIN that was typed differently the second time', () => {
    const onDone = renderFirstRun();
    type('1111');
    type('2222');

    // Back to the first step, saying why, with nothing carried over.
    expect(screen.getByTestId('first-run-title').props.children).toBe(
      'Choose a PIN',
    );
    expect(screen.getByTestId('first-run-notice-title').props.children).toBe(
      'Those two did not match',
    );
    expect(onDone).not.toHaveBeenCalled();

    // And the second attempt still works.
    type('3333');
    type('3333');
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-done'));
    expect(onDone.mock.calls[0][0].gate.record?.hash).toBe(
      hashPin('3333', 'a-fresh-salt', ROUNDS),
    );
  });

  it('keeps the defaults when nothing is chosen', () => {
    const onDone = renderFirstRun();
    type('5555');
    type('5555');
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-done'));
    expect(onDone.mock.calls[0][0].settings).toEqual(DEFAULT_SETTINGS);
  });

  it('reviews the chosen household before opening the checked library', () => {
    const onDone = renderFirstRun();
    type('5555');
    type('5555');
    fireEvent.press(screen.getByTestId('first-run-preset-broadcast'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-tv-65'));
    fireEvent.press(screen.getByTestId('first-run-seat-72'));
    fireEvent.press(screen.getByTestId('first-run-next'));

    expect(screen.getByTestId('first-run-review-preset').props.children).toBe(
      'Broadcast',
    );
    expect(screen.getByTestId('first-run-review-room').props.children).toBe(
      '65 inch television, seats about 6 feet away',
    );
    expect(screen.getByTestId('first-run-done-label').props.children).toBe(
      'Open library',
    );
    expect(onDone).not.toHaveBeenCalled();
  });

  it('revises room and preset choices without repeating the PIN or saving early', () => {
    const onDone = jest.fn<void, [FirstRunResult]>();
    const newSalt = jest.fn(() => 'a-fresh-salt');
    render(<FirstRunScreen onDone={onDone} newSalt={newSalt} rounds={ROUNDS} />);
    type('2468');
    type('2468');
    fireEvent.press(screen.getByTestId('first-run-preset-broadcast'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-tv-65'));
    fireEvent.press(screen.getByTestId('first-run-seat-72'));
    fireEvent.press(screen.getByTestId('first-run-next'));

    fireEvent.press(screen.getByLabelText('Back to TV and seating'));
    expect(screen.getByTestId('first-run-tv-65').props.accessibilityState.checked).toBe(true);
    expect(screen.getByTestId('first-run-seat-72').props.accessibilityState.checked).toBe(true);
    expect(screen.getByTestId('first-run-tv-65').props.hasTVPreferredFocus).toBe(true);
    fireEvent.press(screen.getByTestId('first-run-tv-85'));
    fireEvent.press(screen.getByTestId('first-run-seat-48'));

    fireEvent.press(screen.getByLabelText('Back to viewing preset'));
    expect(screen.getByTestId('first-run-preset-broadcast').props.accessibilityState.checked).toBe(true);
    expect(screen.getByTestId('first-run-preset-broadcast').props.hasTVPreferredFocus).toBe(true);
    expect(screen.queryByTestId('first-run-back')).toBeNull();
    fireEvent.press(screen.getByTestId('first-run-preset-extra-cautious'));
    fireEvent.press(screen.getByTestId('first-run-next'));
    expect(screen.getByTestId('first-run-tv-85').props.accessibilityState.checked).toBe(true);
    expect(screen.getByTestId('first-run-seat-48').props.accessibilityState.checked).toBe(true);
    fireEvent.press(screen.getByTestId('first-run-next'));
    expect(screen.getByTestId('first-run-review-preset').props.children).toBe('Extra cautious');
    expect(screen.getByTestId('first-run-review-room').props.children).toBe(
      '85 inch television, seats about 4 feet away',
    );
    expect(onDone).not.toHaveBeenCalled();
    expect(newSalt).not.toHaveBeenCalled();

    fireEvent.press(screen.getByTestId('first-run-done'));
    expect(onDone).toHaveBeenCalledTimes(1);
    expect(newSalt).toHaveBeenCalledTimes(1);
    const result = onDone.mock.calls[0][0];
    expect(result.settings).toEqual({
      preset: 'extra-cautious',
      tvDiagonalIn: 85,
      seatDistanceIn: 48,
    });
    expect(attemptPin(result.gate, '2468', 0).ok).toBe(true);
  });

  it('says what the room setting can and cannot do before asking for it', () => {
    renderFirstRun();
    type('5555');
    type('5555');
    fireEvent.press(screen.getByTestId('first-run-next'));
    expect(screen.getByTestId('first-run-title').props.children).toBe(
      'Your TV and seating',
    );
    expect(JSON.stringify(screen.toJSON())).toContain(
      'can hide more of the video, never less',
    );
  });

  it('carries the approved sentence in the explainer, and nothing stronger', () => {
    renderFirstRun();
    type('5555');
    type('5555');
    fireEvent.press(screen.getByTestId('first-run-next'));
    fireEvent.press(screen.getByTestId('first-run-next'));

    const shown = EXPLAINER_LINES.map(
      (_line, index) =>
        screen.getByTestId(`first-run-explainer-line-${index}`).props.children,
    );
    expect(shown).toEqual(EXPLAINER_LINES);
    expect(shown).toContain(SAFETY_NOTE);
    expect(shown.join(' ')).not.toMatch(/prevent|proof|safe from/i);
  });

  /**
   * Every list of choices is one question, and says so.
   *
   * The three lists here carried `accessibilityState.selected` alone and no
   * role on the list itself, so a screen reader read three questions as
   * thirteen unrelated buttons and said nothing about which answer was
   * standing. The profile picker was moved to a labelled radiogroup with
   * `checked` and these follow it rather than inventing a second way.
   *
   * Seen to fail twice. With the radiogroup role taken back off the
   * television row:
   *
   *     ● the first run › reads each list of choices as one question
   *
   *       Unable to find an element with accessibilityLabel: Television size
   *
   *       at Object.getByLabelText (test/calmframes/firstRun.test.tsx:207:19)
   *
   * And with `checked` dropped back to `selected` alone in all three lists:
   *
   *       expect(received).toEqual(expected) // deep equality
   *
   *       - Expected  - 1
   *       + Received  + 4
   *
   *         Object {
   *       -   "checked": true,
   *       +   "busy": undefined,
   *       +   "checked": undefined,
   *       +   "disabled": undefined,
   *       +   "expanded": undefined,
   *           "selected": true,
   *         }
   *
   *       at Object.toEqual (test/calmframes/firstRun.test.tsx:200:7)
   */
  it('reads each list of choices as one question', () => {
    renderFirstRun();
    type('5555');
    type('5555');

    expect(
      screen.getByLabelText('Choose a viewing preset').props.accessibilityRole,
    ).toBe('radiogroup');
    expect(
      screen.getByTestId('first-run-preset-wcag').props.accessibilityState,
    ).toEqual({ checked: true, selected: true });
    expect(
      screen.getByTestId('first-run-preset-broadcast').props.accessibilityState,
    ).toEqual({ checked: false, selected: false });

    fireEvent.press(screen.getByTestId('first-run-next'));

    expect(
      screen.getByLabelText('Television size').props.accessibilityRole,
    ).toBe('radiogroup');
    expect(
      screen.getByLabelText('Viewing distance').props.accessibilityRole,
    ).toBe('radiogroup');
    expect(
      screen.getByTestId('first-run-tv-55').props.accessibilityState,
    ).toEqual({ checked: true, selected: true });
    expect(
      screen.getByTestId('first-run-seat-96').props.accessibilityState,
    ).toEqual({ checked: true, selected: true });
    expect(
      screen.getByTestId('first-run-seat-48').props.accessibilityState,
    ).toEqual({ checked: false, selected: false });
  });

  it('retains checked choices without redundant captions and keeps navigation outside the scroller', () => {
    const onDone = renderFirstRun();
    type('5555'); type('5555');
    const assertFooter = (button: string) => {
      const footer = screen.getByTestId('first-run-footer');
      const scroll = screen.getByTestId('first-run-scroll');
      expect(footer.findAllByProps({testID: button}).length).toBeGreaterThan(0);
      expect(scroll.findAllByProps({testID: button})).toHaveLength(0);
    };
    assertFooter('first-run-next');
    fireEvent.press(screen.getByTestId('first-run-next'));
    assertFooter('first-run-next'); assertFooter('first-run-back');
    expect(screen.queryByTestId('first-run-brand-line')).toBeNull();
    expect(screen.queryByTestId('first-run-tv-chosen')).toBeNull();
    expect(screen.queryByTestId('first-run-seat-chosen')).toBeNull();
    const chipText = () => TV_DIAGONAL_CHOICES_IN.map(inches =>
      String(screen.getByTestId(`first-run-tv-${inches}-label`).props.children));
    const before = chipText();
    fireEvent.press(screen.getByTestId('first-run-tv-85'));
    fireEvent.press(screen.getByTestId('first-run-seat-48'));
    expect(screen.getByTestId('first-run-tv-85').props.accessibilityState.checked).toBe(true);
    expect(screen.getByTestId('first-run-seat-48').props.accessibilityState.checked).toBe(true);
    expect(chipText()).toEqual(before);
    fireEvent.press(screen.getByTestId('first-run-next'));
    assertFooter('first-run-done'); assertFooter('first-run-back');
    fireEvent.press(screen.getByTestId('first-run-done'));
    expect(onDone.mock.calls[0][0].settings).toEqual({...DEFAULT_SETTINGS, tvDiagonalIn: 85, seatDistanceIn: 48});
  });

  it('opens every step at the top of a scroller of its own, not where the last step left it', () => {
    // On the device, choosing Extra cautious scrolls the preset list, and the
    // room step then opened at that same offset with its first line, the
    // statement that the room can only hide more, scrolled out of sight.
    // Back from the end of the explainer hid the whole first row of TV sizes.
    // The offset lives in the native scroll view, so this asks the thing that
    // carries it: is the next step's scroller a new one or the last one?
    // Seen to fail: before each step had its own key, the room step's
    // scroller was the preset step's own object. Giving the room the
    // preset's key, or the explainer the room's, turned it red again.
    renderFirstRun();
    type('5555'); type('5555');
    const scroller = () => screen.UNSAFE_getByType(ScrollView).instance;
    const preset = scroller();
    expect(preset).toBeTruthy();
    fireEvent.press(screen.getByTestId('first-run-next'));
    const room = scroller();
    expect(room).not.toBe(preset);
    fireEvent.press(screen.getByTestId('first-run-next'));
    const explainer = scroller();
    expect(explainer).not.toBe(room);
    fireEvent.press(screen.getByLabelText('Back to TV and seating'));
    const roomAgain = scroller();
    expect(roomAgain).not.toBe(explainer);
    fireEvent.press(screen.getByLabelText('Back to viewing preset'));
    expect(scroller()).not.toBe(roomAgain);
  });

  it('has no motion: nothing on any step animates', () => {
    renderFirstRun();
    const tree = JSON.stringify(screen.toJSON());
    expect(tree).not.toMatch(/Animated|useNativeDriver|transition/i);
  });
});
