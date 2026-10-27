import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { once } from 'node:events';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const file = fileURLToPath(import.meta.url);
import { legacyConsumer } from './legacy_consumer.mjs';

if (legacyConsumer('node_modules/fbjs-scripts')) {
const app = dirname(dirname(file));
const fbEntry = join(app, 'node_modules/fbjs-scripts/gulp/check-dependencies.js');
const fbRequire = createRequire(fbEntry);
const localeRequire = createRequire(join(app, 'node_modules/os-locale/index.js'));
const execaRequire = createRequire(localeRequire.resolve('execa'));

if (process.argv.includes('--escape-child')) {
  const require = process.argv.at(-1) === 'locale' ? execaRequire : fbRequire;
  const directory = dirname(require.resolve('cross-spawn'));
  let escape;
  try {
    escape = require(join(directory, 'lib/util/escape.js')).argument;
  } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
    const old = require(join(directory, 'lib/util/escapeArgument.js'));
    escape = argument => old(argument, true);
  }
  const input = '\\'.repeat(200000) + 'X';
  const output = escape(input, false);
  assert.ok(output.length >= input.length);
} else {
  test('only legacy spawn consumers use the existing fixed 6.x version', () => {
    assert.equal(fbRequire('../package.json').version, '1.2.0');
    assert.equal(localeRequire('./package.json').version, '2.1.0');
    assert.equal(execaRequire('./package.json').version, '0.7.0');
    for (const require of [fbRequire, execaRequire]) {
      assert.equal(require('cross-spawn/package.json').version, '6.0.6');
    }
    const modern = createRequire(join(app, 'package.json'));
    assert.equal(modern('cross-spawn/package.json').version, '7.0.6');
  });

  test('the Windows argument escaper handles long literal backslashes in bounded child processes', () => {
    for (const consumer of ['fbjs', 'locale']) {
      const result = spawnSync(process.execPath, [file, '--escape-child', consumer], {
        encoding: 'utf8', timeout: 2500, maxBuffer: 16 * 1024,
      });
      assert.equal(result.error, undefined, `${consumer}: ${result.error?.message}`);
      assert.equal(result.status, 0, result.stderr);
    }
  });

  test('the old locale dependency keeps async/sync arguments, environment and failure results', async () => {
    const execa = localeRequire('execa');
    const args = ['space value', 'semi;literal', 'quote " value', '\\tail'];
    const source = 'process.stdout.write(JSON.stringify({args:process.argv.slice(1),value:process.env.CALM_SPAWN_FIXTURE}))';
    const options = { env: { CALM_SPAWN_FIXTURE: 'retained' }, timeout: 2000 };
    const sync = execa.sync(process.execPath, ['-e', source, ...args], options);
    assert.deepEqual(JSON.parse(sync.stdout), { args, value: 'retained' });
    const async = await execa(process.execPath, ['-e', source, ...args], options);
    assert.deepEqual(JSON.parse(async.stdout), { args, value: 'retained' });
    const failed = await execa(process.execPath, ['-e', 'process.stderr.write("fixture failure");process.exit(7)'], { reject: false, timeout: 2000 });
    assert.equal(failed.code, 7);
    assert.equal(failed.failed, true);
    assert.equal(failed.stderr, 'fixture failure');
    await assert.rejects(execa('calm-fixture-command-does-not-exist', [], { timeout: 2000 }), { code: 'ENOENT' });
    assert.throws(() => execa.sync('calm-fixture-command-does-not-exist'), { code: 'ENOENT' });
  });

  test('the actual FBJS dependency checker retains child streams and the requested directory', async t => {
    const root = mkdtempSync(join(tmpdir(), 'calm-spawn-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    const spawn = fbRequire('cross-spawn');
    const requested = [];
    const module = { exports: {} };
    vm.runInNewContext(readFileSync(fbEntry, 'utf8'), {
      module, console,
      require(name) {
        if (name !== 'cross-spawn') return fbRequire(name);
        return (command, args, options) => {
          requested.push({ command, args: Array.from(args), cwd: options.cwd });
          const data = { type: 'table', data: { head: ['Package', 'Current', 'Package Type'], body: [['fixture', '1.2.3', 'dependencies']] } };
          return spawn(process.execPath, ['-e', `process.stdout.write(${JSON.stringify(JSON.stringify(data) + '\n')})`], options);
        };
      },
    }, { filename: fbEntry, timeout: 1000 });
    const checker = module.exports();
    const finished = once(checker, 'finish');
    checker.end({ path: join(root, 'package.json'), contents: Buffer.from('{"dependencies":{"fixture":"^1.0.0"}}') });
    await finished;
    assert.deepEqual(requested, [{ command: 'yarn', args: ['outdated', '--json'], cwd: root }]);
  });
}

}
