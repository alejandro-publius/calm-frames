/**
 * The device bring-up lines exist in Debug and are gone from Release.
 *
 * The player now writes a debug line for every Kepler app state change, every
 * Vega Media Controls call and every OK that a countdown card's Skip owns.
 * Those are for a person reading a device log during bring-up. A judged
 * Release package should print none of them, and babel.config.js already
 * arranges that for console.log: the production build runs
 * transform-remove-console and keeps only error, info and warn.
 *
 * So the rule is that these lines are console.log and nothing louder, and
 * this test holds it by compiling each file the way each build does. A line
 * written with console.info would survive Release, and this goes red.
 *
 * Seen to fail, Oct 9 2026: with the seek line in SafeMediaControlHandler's
 * goTo switched to console.info, the Release case for that file found it
 * still in the compiled output.
 */

import { transformFileSync } from '@babel/core';
import path from 'path';

const APP = path.join(__dirname, '..', '..');

function compiled(file: string, envName: 'production' | 'development'): string {
  const result = transformFileSync(path.join(APP, file), {
    cwd: APP,
    root: APP,
    envName,
    configFile: path.join(APP, 'babel.config.js'),
    babelrc: false,
    sourceMaps: false,
  });
  return result?.code ?? '';
}

/**
 * Each file, and words that appear only in its bring-up lines.
 *
 * Fragments rather than whole lines, because the seek line is one template
 * shared by six commands and a compiler may split a template into pieces.
 */
const BRING_UP_LINES: Array<[string, string[]]> = [
  [
    'src/calmframes/SafeMediaControlHandler.ts',
    ['[SafeMediaControlHandler.ts] - ', ' ms, going to ', 'passed to the player'],
  ],
  [
    'src/screens/PlayerScreen.tsx',
    [
      'KeplerAppStateChange to ',
      'a measurement run stays on the player',
      'background, leaving the player',
      'on by default, track ',
    ],
  ],
  [
    'src/w3cmedia/mediacontrols/VideoPlayerUI.tsx',
    ['OK is a press on Skip'],
  ],
];

describe('bring-up log lines', () => {
  it.each(BRING_UP_LINES)('%s writes them in a Debug build', (file, lines) => {
    const code = compiled(file, 'development');
    for (const line of lines) {
      expect(code).toContain(line);
    }
  });

  it.each(BRING_UP_LINES)('%s writes none of them in a Release build', (file, lines) => {
    const code = compiled(file, 'production');
    for (const line of lines) {
      expect(code).not.toContain(line);
    }
    expect(code).not.toMatch(/console\.log\(/);
  });

  it('keeps the louder levels in Release, which is why the bring-up lines are not one of them', () => {
    // The sample's own console.info lines survive the Release strip. That is
    // the case this rule is written against.
    const code = compiled('src/w3cmedia/mediacontrols/VideoPlayerUI.tsx', 'production');
    expect(code).toContain('k_content_per: VideoPlayerUI : select');
  });
});
