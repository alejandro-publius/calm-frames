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
import {
  EXPLAINER_LINES,
  SAFETY_NOTE,
} from '../../src/calmframes/copy';
import FirstRunScreen, {
  FirstRunResult,
} from '../../src/calmframes/FirstRunScreen';
import { DEFAULT_SETTINGS } from '../../src/calmframes/household';
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
  it('asks for the PIN, the preset, the room and then explains itself', () => {
    const onDone = renderFirstRun();

    expect(screen.getByTestId('first-run-step').props.children).toEqual(
      expect.arrayContaining(['Step ', 1, ' of ', 4]),
    );
    type('2468');
    expect(screen.getByTestId('first-run-title').props.children).toBe(
      'Type the PIN again',
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
    expect(screen.getByTestId('first-run-title').props.children).toBe('Choose a PIN');
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

  it('says what the room setting can and cannot do before asking for it', () => {
    renderFirstRun();
    type('5555');
    type('5555');
    fireEvent.press(screen.getByTestId('first-run-next'));
    expect(screen.getByTestId('first-run-title').props.children).toBe(
      'Your television and your sofa',
    );
    expect(JSON.stringify(screen.toJSON())).toContain('can only add hidden parts');
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

  it('has no motion: nothing on any step animates', () => {
    renderFirstRun();
    const tree = JSON.stringify(screen.toJSON());
    expect(tree).not.toMatch(/Animated|useNativeDriver|transition/i);
  });
});
