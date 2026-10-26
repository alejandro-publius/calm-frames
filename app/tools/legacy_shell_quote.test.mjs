import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import test from 'node:test';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const entry = join(app, 'node_modules/react-native-tscodegen-types/node_modules',
  '@react-native-community/cli/build/commands/server/launchEditor.js');
const legacyRequire = createRequire(entry);
const shellQuote = legacyRequire('shell-quote');

test('legacy CLI resolves the fixed shell-quote without changing its SDK CLI version', () => {
  const manifest = JSON.parse(readFileSync(join(app, 'package.json'), 'utf8'));
  const lock = JSON.parse(readFileSync(join(app, 'package-lock.json'), 'utf8'));
  assert.equal(legacyRequire('../../../package.json').version, '2.10.0');
  assert.equal(legacyRequire('shell-quote/package.json').version, '1.11.0');
  assert.equal(manifest.overrides['shell-quote'], '1.11.0');
  for (const [path, item] of Object.entries(lock.packages)) {
    if (path.endsWith('/shell-quote')) assert.equal(item.version, '1.11.0', path);
  }
});

test('line terminators cannot become commands through structured quote tokens', () => {
  for (const token of [
    { op: ';\nprintf unexpected' },
    { op: 'glob', pattern: 'file\nprintf unexpected' },
    { comment: 'note\nprintf unexpected' },
  ]) {
    assert.throws(() => shellQuote.quote([token]), TypeError);
  }
  assert.throws(() => shellQuote.quote([{ comment: 'note' }, 'line\nprintf unexpected']),
    TypeError);
});

test('literal paths and arguments survive quoting without interpretation', () => {
  const values = ['', 'two words', "kid's file", '$NOT_AN_ENV_LOOKUP',
    '`printf unexpected`', '$(printf unexpected)', 'line\nbreak', 'a;b', 'Acadia.tsx'];
  for (const value of values) {
    assert.deepEqual(shellQuote.parse(shellQuote.quote([value]), {}), [value]);
  }
});

test('the installed legacy editor launcher preserves quoted argv and uses direct spawn', () => {
  const cases = [
    ['code --wait --reuse-window', 'code', ['--wait', '--reuse-window']],
    ['"/Applications/Editor App/bin/editor" --wait',
      '/Applications/Editor App/bin/editor', ['--wait']],
    ["editor --label='two words'", 'editor', ['--label=two words']],
  ];
  for (const [setting, expectedEditor, expectedArgs] of cases) {
    const launches = [];
    const exports = {};
    const child = { on() { return this; } };
    vm.runInNewContext(readFileSync(entry, 'utf8'), {
      exports,
      process: { env: { REACT_EDITOR: setting }, platform: 'linux', cwd: () => app },
      require(name) {
        if (name === 'child_process') return {
          spawn(...args) { launches.push(args); return child; },
          execSync() { throw new Error('Editor detection must not run for an explicit setting'); },
        };
        if (name === 'fs') return { existsSync: () => true };
        if (name === '@react-native-community/cli-tools') return {
          logger: { info() {}, error() {} },
        };
        return legacyRequire(name);
      },
    }, { filename: entry, timeout: 1000 });
    exports.default(join(app, 'a file.tsx'), undefined, [app]);
    // Normalize VM-realm prototypes, preserving every recorded value.
    assert.deepEqual(JSON.parse(JSON.stringify(launches)), [[expectedEditor,
      [...expectedArgs, join(app, 'a file.tsx')], { stdio: 'inherit' }]]);
  }
});
