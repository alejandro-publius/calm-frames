/**
 * Copy the flash guard engine out of the app and into the package.
 *
 * The app is where the engine lives and where it is used every day, so that is
 * where it is edited. The package is a mirror of those files, so anyone can
 * `npm install` it without taking the whole app with it.
 *
 * A mirror rots. app/test/calmframes/hookMirror.test.ts reads both sides and
 * fails when they differ, so a change to the engine that was not synced turns
 * the suite red rather than shipping a stale package.
 *
 * Run it from the repository root:
 *
 *     node hook/tools/sync.mjs
 */

import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const hookRoot = join(here, '..');
const repoRoot = join(hookRoot, '..');
const source = join(repoRoot, 'app', 'src', 'calmframes');
const target = join(hookRoot, 'src', 'engine');

/** Every file the hook needs. Screens and app wiring stay in the app. */
export const MIRRORED = [
  'announce.ts',
  'CalmCard.tsx',
  'CalmControlSurface.tsx',
  'CalmTouchable.tsx',
  'CoastalAppearance.ts',
  'calmStyles.ts',
  'canonicalJson.ts',
  'cards.ts',
  'CoverLayer.tsx',
  'coverSchedule.ts',
  'ed25519.ts',
  'flashMap.ts',
  'hideLog.ts',
  'household.ts',
  'mapRegistry.ts',
  'mediaClock.ts',
  'SafeMediaControlHandler.ts',
  'seekSafety.ts',
  'sceneHolds.ts',
  'sha512.ts',
  'timingLog.ts',
  'titleStatus.ts',
  'useCoverHarness.ts',
  'useFlashGuard.ts',
];

/**
 * Imports that point outside app/src/calmframes, and what they become here.
 *
 * There is one. Keeping the list explicit means a new outside import shows up
 * as a broken build in the package rather than as a silent difference.
 */
export const REWRITES = [["from '../utils/pixelUtils'", "from '../pixelUtils'"]];

const HEADER = `/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run \`node hook/tools/sync.mjs\`.
 */
`;

/** The text this file should have in the package, given the app's copy. */
export function mirrorText(sourceText) {
  let text = sourceText;
  for (const [from, to] of REWRITES) {
    text = text.split(from).join(to);
  }
  return HEADER + text;
}

export function fingerprint(text) {
  return createHash('sha256').update(text, 'utf8').digest('hex').slice(0, 16);
}

function main() {
  rmSync(target, { recursive: true, force: true });
  mkdirSync(target, { recursive: true });

  const known = new Set(readdirSync(source));
  const manifest = {};
  for (const name of MIRRORED) {
    if (!known.has(name)) {
      throw new Error(`hook sync: ${name} is not in app/src/calmframes any more`);
    }
    const text = mirrorText(readFileSync(join(source, name), 'utf8'));
    writeFileSync(join(target, name), text);
    manifest[name] = fingerprint(text);
  }

  writeFileSync(
    join(hookRoot, 'src', 'mirror.json'),
    `${JSON.stringify({ source: 'app/src/calmframes', files: manifest }, null, 2)}\n`,
  );
  console.log(`hook sync: ${MIRRORED.length} files copied`);
}

if (process.argv[1] && process.argv[1].endsWith('sync.mjs')) {
  main();
}
