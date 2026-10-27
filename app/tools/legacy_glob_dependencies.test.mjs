/** Existing legacy file filters and a real watcher; no native device or server. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { once } from 'node:events';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { legacyConsumer } from './legacy_consumer.mjs';

if (legacyConsumer('node_modules/sane')) {
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'package.json'));
const sane = createRequire(require.resolve('sane/src/common'));
const legacy = createRequire(join(app, 'node_modules/react-native-tscodegen-types/package.json'));

for (const [name, consumer] of [['sane', sane], ['legacy types', legacy]]) {
  test(`${name} malformed-glob processing is bounded and reaches the fixed packages`, () => {
    const module = consumer.resolve('micromatch');
    const probe = `const match=require(${JSON.stringify(module)});
      for (const input of ['{'.repeat(60000), '{x,'.repeat(12000)]) {
        try { match.braces(input); } catch (e) {
          if (!/length|max|limit/i.test(e.message)) throw e;
        }
      }`;
    const child = spawnSync(process.execPath, ['--max-old-space-size=64', '-e', probe], { timeout: 1500, maxBuffer: 4096 });
    assert.equal(child.error, undefined, 'glob child exceeded its resource bound');
    assert.equal(child.status, 0);
    assert.equal(consumer('micromatch/package.json').version, '4.0.8');
    const braceConsumer = createRequire(module);
    assert.equal(braceConsumer('braces/package.json').version, '3.0.3');
  });
}

test('legacy anymatch keeps string, regex, callback, negation and returned-index contracts', () => {
  for (const consumer of [sane, legacy]) {
    const anymatch = consumer('anymatch');
    const patterns = ['**/*.tsx', /(^|\/)notes\.txt$/, value => value === 'README', '!**/ignored/**'];
    assert.equal(anymatch(patterns, 'src/Home.tsx'), true);
    assert.equal(anymatch(patterns, 'src/notes.txt'), true);
    assert.equal(anymatch(patterns, 'README'), true);
    assert.equal(anymatch(patterns, 'src/ignored/Home.tsx'), false);
    assert.equal(anymatch(patterns, 'image.png'), false);
    assert.equal(anymatch(patterns, 'src/notes.txt', true), 1);
    const match = anymatch(patterns);
    assert.equal(match('src/Home.tsx'), true);
    assert.equal(match('src/ignored/Home.tsx'), false);
  }
});

test('the actual sane inclusion filter keeps dotfile, ignore and brace-alternative behavior', () => {
  const { isFileIncluded } = sane('./common');
  const ignored = value => value.startsWith('ignored/');
  for (const [file, expected] of [['src/Home.tsx', true], ['src/Home.ts', true],
    ['src/Home.js', false], ['ignored/Home.tsx', false], ['.hidden/Home.tsx', false]]) {
    assert.equal(isFileIncluded(['**/*.{ts,tsx}'], false, ignored, file), expected);
  }
  assert.equal(isFileIncluded(['**/*.{ts,tsx}'], true, ignored, '.hidden/Home.tsx'), true);
  assert.equal(isFileIncluded([], false, ignored, 'src/Home.tsx'), true);
  assert.equal(isFileIncluded([], false, ignored, '.hidden'), false);
});

test('the legacy watcher observes a matching file while preserving its ignored-file filter', { timeout: 7000 }, async t => {
  const root = mkdtempSync(join(tmpdir(), 'calm-glob-watch-'));
  mkdirSync(join(root, 'src'));
  const NodeWatcher = sane('./node_watcher');
  const watcher = new NodeWatcher(root, { glob: ['**/*.txt'], ignored: '**/ignored/**', dot: false });
  t.after(async () => { await new Promise(resolve => watcher.close(resolve)); rmSync(root, { recursive: true, force: true }); });
  await once(watcher, 'ready', { signal: AbortSignal.timeout(2000) });
  const added = once(watcher, 'add', { signal: AbortSignal.timeout(3000) });
  writeFileSync(join(root, 'src/watched.txt'), 'fictional fixture');
  const [relative, directory] = await added;
  assert.equal(relative, join('src', 'watched.txt'));
  assert.equal(directory, root);
  assert.equal(watcher.register(join(root, 'ignored/untracked.txt')), false);
  assert.equal(watcher.register(join(root, '.hidden.txt')), false);
});

}
