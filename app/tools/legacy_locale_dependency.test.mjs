import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

import { legacyConsumer } from './legacy_consumer.mjs';

if (legacyConsumer('node_modules/os-locale')) {
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const entry = join(app, 'node_modules/os-locale/index.js');
const require = createRequire(entry);
const mem = require('mem');

function locale({ env = {}, output = 'LANG="sv_SE.UTF-8"', fail = false } = {}) {
  const module = { exports: {} };
  const calls = [];
  const process = { env: { ...env }, platform: 'linux' };
  vm.runInNewContext(readFileSync(entry, 'utf8'), {
    module, process,
    require(name) {
      if (name !== 'execa') return require(name);
      // Execute the installed locale consumer with controlled process results.
      // Neither the host locale command nor an external service is launched.
      return {
        stdout(command) {
          calls.push(['async', command]);
          return fail ? Promise.reject(new Error('fixture locale failure')) : Promise.resolve(output);
        },
        sync(command) {
          calls.push(['sync', command]);
          if (fail) throw new Error('fixture locale failure');
          return { stdout: output };
        },
      };
    },
  }, { filename: entry, timeout: 1000 });
  return { value: module.exports, calls, env: process.env };
}

test('the unchanged old locale consumer receives only the reviewed CommonJS cache line', () => {
  assert.equal(require('./package.json').version, '2.1.0');
  assert.equal(require('mem/package.json').version, '4.3.0');
  assert.equal(typeof mem, 'function');
  assert.equal(typeof mem.clear, 'function');
});

test('expired entries are removed from the supplied cache without rereading each key', { timeout: 2000 }, async () => {
  const cache = new Map();
  const memoized = mem(value => `fixture-${value}`, { cache, maxAge: 20 });
  for (let n = 0; n < 16; n++) assert.equal(memoized(n), `fixture-${n}`);
  assert.equal(cache.size, 16);
  await delay(100);
  assert.equal(cache.size, 0);
});

test('the actual locale module retains environment priority, normalization and explicit cache clearing', async () => {
  const { value, calls, env } = locale({ env: { LC_ALL: 'fr_CA.UTF-8', LANG: 'de_DE.UTF-8' } });
  assert.equal(value.sync({ spawn: false }), 'fr_CA');
  assert.equal(await value({ spawn: false }), 'fr_CA');
  env.LC_ALL = 'en_GB.UTF-8';
  assert.equal(value.sync({ spawn: false }), 'fr_CA');
  assert.equal(await value({ spawn: false }), 'fr_CA');
  mem.clear(value.sync);
  mem.clear(value);
  assert.equal(value.sync({ spawn: false }), 'en_GB');
  assert.equal(await value({ spawn: false }), 'en_GB');
  assert.deepEqual(calls, []);
});

test('the actual locale module keeps command parsing and memoization for sync and async callers', async () => {
  const { value, calls } = locale();
  assert.equal(value.sync(), 'sv_SE');
  assert.equal(value.sync(), 'sv_SE');
  const first = value();
  assert.equal(value(), first);
  assert.equal(await first, 'sv_SE');
  assert.deepEqual(calls, [['sync', 'locale'], ['async', 'locale']]);
});

test('the actual locale module retains its default for disabled spawning and failed commands', async () => {
  const disabled = locale();
  assert.equal(disabled.value.sync({ spawn: false }), 'en_US');
  assert.equal(await disabled.value({ spawn: false }), 'en_US');
  assert.deepEqual(disabled.calls, []);
  const failed = locale({ fail: true });
  assert.equal(failed.value.sync(), 'en_US');
  assert.equal(await failed.value(), 'en_US');
  assert.deepEqual(failed.calls, [['sync', 'locale'], ['async', 'locale']]);
});

}
