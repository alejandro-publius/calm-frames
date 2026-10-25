import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'package.json'));
const queryRequire = createRequire(require.resolve('query-string'));
const mapRequire = createRequire(require.resolve('source-map-resolve'));
const query = require('query-string');
const decoder = queryRequire('decode-uri-component');

test('both existing consumers use the callable adapter and only the pinned fixed parser', () => {
  assert.equal(require('query-string/package.json').version, '7.1.3');
  assert.equal(require('source-map-resolve/package.json').version, '0.5.3');
  assert.equal(typeof decoder, 'function');
  assert.equal(decoder, mapRequire('decode-uri-component'));
  const lock = JSON.parse(readFileSync(join(app, 'package-lock.json')));
  const parsers = Object.entries(lock.packages).filter(([path, entry]) =>
    path.includes('node_modules/decode-uri-component') && !entry.link);
  assert.equal(parsers.length, 1);
  assert.equal(parsers[0][1].name, 'decode-uri-component');
  assert.equal(parsers[0][1].version, '0.5.1');
});

test('legacy callable keeps ordinary text, plus signs and invalid input behavior', () => {
  for (const [input, expected] of [
    ['', ''], ['Sea+Otters', 'Sea Otters'], ['Sea%2BOtters', 'Sea+Otters'],
    ['%C3%A5%20%F0%9F%8C%8A', 'å 🌊'], ['raw%ZZ%', 'raw%ZZ%'],
    ['%FE%FF', '\uFFFD\uFFFD'], ['%C2', '\uFFFD'], ['%E0%A4%A', '%E0%A4%A'],
    ['%FF%41', '%FFA'], ['%25C3%25A5', '%C3%A5'],
  ]) assert.equal(decoder(input), expected, input);
  for (const input of [null, undefined, 7, {}, []]) assert.throws(() => decoder(input), TypeError);
});

test('actual query parser retains arrays, empty values, Unicode and literal plus', () => {
  assert.deepEqual({ ...query.parse('scene=Sea+Otters&scene=Forest&empty=&flag&symbol=%2B&name=%C3%85sa') }, {
    empty: '', flag: null, name: 'Åsa', scene: ['Sea Otters', 'Forest'], symbol: '+',
  });
  const value = { scene: 'Sequoia Trail', symbol: '+', items: ['Acadia', 'Sea Otters'] };
  assert.deepEqual({ ...query.parse(query.stringify(value)) }, value);
  assert.deepEqual(query.parseUrl('/watch?scene=Sea%20Otters#more', { parseFragmentIdentifier: true }), {
    url: '/watch', query: query.parse('scene=Sea%20Otters'), fragmentIdentifier: 'more',
  });
});

test('malformed percent input completes inside a bounded child process', () => {
  const result = spawnSync(process.execPath, ['-e', `
    const assert = require('node:assert/strict');
    const query = require(${JSON.stringify(require.resolve('query-string'))});
    const input = '%FF'.repeat(1000);
    assert.equal(query.parse('scene=' + input).scene, input);
    console.log('completed');
  `], { timeout: 1000, encoding: 'utf8' });
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout.trim(), 'completed');
});

test('actual source-map consumer preserves a plus in a source URL and reads inline maps', () => {
  const decodeSource = require('source-map-resolve/lib/decode-uri-component');
  assert.equal(decodeSource('file:///a+b%20c.js'), 'file:///a+b c.js');
  const map = { version: 3, sources: ['a+b.ts'], names: [], mappings: '' };
  const result = require('source-map-resolve').resolveSourceMapSync(
    '//# sourceMappingURL=data:application/json,' + encodeURIComponent(JSON.stringify(map)),
    '/fixture/app.js', () => { throw new Error('No filesystem read expected'); },
  );
  assert.deepEqual(result.map, map);
});

test('the installed navigation path reader and writer retain query parameters', async () => {
  const core = dirname(require.resolve('@amazon-devices/react-navigation__core/package.json'));
  const { getStateFromPath } = await import(pathToFileURL(join(core, 'lib/module/getStateFromPath.js')));
  const { getPathFromState } = await import(pathToFileURL(join(core, 'lib/module/getPathFromState.js')));
  const options = { screens: { Watch: 'watch/:title' } };
  const state = getStateFromPath('/watch/forest?scene=Sea%20Otters&symbol=%2B', options);
  assert.deepEqual(state.routes[0].params, { title: 'forest', scene: 'Sea Otters', symbol: '+' });
  const roundtrip = getStateFromPath(getPathFromState(state, options), options);
  assert.deepEqual(roundtrip.routes[0].params, state.routes[0].params);
});
