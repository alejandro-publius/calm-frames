/**
 * The package in hook/ is a mirror of the engine in app/src/calmframes.
 *
 * A mirror that is allowed to drift is worse than no mirror: someone installs
 * the package, gets an older guard than the one this repository tests, and has
 * no way of knowing. So the copy is checked here, on every run, against what
 * hook/tools/sync.mjs would produce today.
 *
 * When this fails, the fix is one command from the repository root:
 *
 *     node hook/tools/sync.mjs
 */

import fs from 'fs';
import path from 'path';

const REPO_ROOT = path.join(__dirname, '..', '..', '..');
const APP_ENGINE = path.join(REPO_ROOT, 'app', 'src', 'calmframes');
const HOOK_ENGINE = path.join(REPO_ROOT, 'hook', 'src', 'engine');
const SYNC_SCRIPT = path.join(REPO_ROOT, 'hook', 'tools', 'sync.mjs');

/**
 * The file list and the rewrites, read out of the sync script itself.
 *
 * Importing an ESM script from a CommonJS jest run is more trouble than it is
 * worth for two arrays, and reading them means the test cannot drift from the
 * script either.
 */
function readSyncScript() {
  const text = fs.readFileSync(SYNC_SCRIPT, 'utf8');
  const listMatch = /export const MIRRORED = \[([\s\S]*?)\];/.exec(text);
  const rewriteMatch = /export const REWRITES = \[([\s\S]*?)\];/.exec(text);
  if (!listMatch || !rewriteMatch) {
    throw new Error('hook/tools/sync.mjs no longer declares MIRRORED and REWRITES');
  }
  const mirrored = [...listMatch[1].matchAll(/'([^']+)'/g)].map((one) => one[1]);
  const rewrites = [...rewriteMatch[1].matchAll(/\["([^"]+)", "([^"]+)"\]/g)].map(
    (one) => [one[1], one[2]] as [string, string],
  );
  return { mirrored, rewrites };
}

const { mirrored, rewrites } = readSyncScript();

describe('the hook package mirror', () => {
  it('mirrors the engine, and nothing else', () => {
    expect(mirrored.length).toBeGreaterThan(10);
    expect(fs.readdirSync(HOOK_ENGINE).sort()).toEqual([...mirrored].sort());
  });

  it('is byte for byte what the sync script would write today', () => {
    for (const name of mirrored) {
      const appText = fs.readFileSync(path.join(APP_ENGINE, name), 'utf8');
      let expected = appText;
      for (const [from, to] of rewrites) {
        expected = expected.split(from).join(to);
      }
      const hookText = fs.readFileSync(path.join(HOOK_ENGINE, name), 'utf8');
      // The mirror carries a header saying where it came from, then the file.
      expect(hookText).toContain('Mirrored from app/src/calmframes');
      expect(hookText.slice(hookText.indexOf('\n */\n') + 5)).toBe(expected);
    }
  });

  it('leaves no import pointing outside the package', () => {
    for (const name of mirrored) {
      const text = fs.readFileSync(path.join(HOOK_ENGINE, name), 'utf8');
      for (const line of text.split('\n')) {
        const match = /^import .*from '(\.[^']*)'/.exec(line.trim());
        if (!match) {
          continue;
        }
        const target = match[1];
        expect(target.startsWith('../../')).toBe(false);
        if (target.startsWith('./')) {
          const base = target.replace('./', '');
          const candidates = [`${base}.ts`, `${base}.tsx`];
          expect(
            candidates.some((one) => fs.existsSync(path.join(HOOK_ENGINE, one))),
          ).toBe(true);
        }
      }
    }
  });

  it('exports the hook and the pieces an app has to draw', () => {
    const index = fs.readFileSync(
      path.join(REPO_ROOT, 'hook', 'src', 'index.ts'),
      'utf8',
    );
    for (const name of [
      'useFlashGuard',
      'CoverLayer',
      'CalmCard',
      'SafeMediaControlHandler',
      'verifyFlashMap',
      'kidModeTitles',
    ]) {
      expect(index).toContain(name);
    }
  });

  it('declares the runtime it needs as peers, not as dependencies', () => {
    const manifest = JSON.parse(
      fs.readFileSync(path.join(REPO_ROOT, 'hook', 'package.json'), 'utf8'),
    );
    expect(manifest.peerDependencies['@amazon-devices/react-native-w3cmedia']).toBeDefined();
    expect(manifest.dependencies).toBeUndefined();
    expect(manifest.license).toBe('Apache-2.0');
  });
});
