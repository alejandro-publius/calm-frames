/** Legacy build-tool consumers, with bounded hostile fixtures and no device/server. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const appRequire = createRequire(join(app, 'package.json'));
const inspectorPath = appRequire.resolve('metro-inspector-proxy/src/cli.js');
const inspectorRequire = createRequire(inspectorPath);
const metroRequire = createRequire(join(app, 'node_modules/react-native-tscodegen-types/node_modules/metro/src/cli.js'));
const builderPath = appRequire.resolve('@amazon-devices/kepler-module-manifest-builder');
const builderRequire = createRequire(builderPath);
const toml = builderRequire('toml');

for (const [name, require] of [['inspector', inspectorRequire], ['legacy Metro', metroRequire]]) {
  test(`${name} parser refuses prototype mutation in a separate process`, () => {
    const code = `const parse=require(${JSON.stringify(require.resolve('yargs-parser'))});
      try { parse(['--__proto__.calm_parser_probe=yes']); } catch {}
      if (({}).calm_parser_probe !== undefined) process.exit(7);`;
    const child = spawnSync(process.execPath, ['-e', code], { timeout: 1500 });
    assert.equal(child.status, 0, 'prototype must remain unchanged');
    assert.equal(require('yargs/package.json').version, '9.0.1');
    assert.equal(require('yargs-parser/package.json').version, '13.1.2');
  });
}

test('the actual inspector CLI retains default and explicit numeric ports without opening a server', () => {
  for (const [args, expected] of [[[], 8081], [['--port', '9123'], 9123], [['-p', '9124'], 9124]]) {
    const yargs = inspectorRequire('yargs/yargs')(args).exitProcess(false);
    let port;
    vm.runInNewContext(readFileSync(inspectorPath, 'utf8'), {
      require: name => name === 'yargs' ? yargs : name === './index'
        ? { runInspectorProxy: value => { port = value; } } : inspectorRequire(name),
    }, { timeout: 1000 });
    assert.equal(port, expected);
  }
});

test('actual Metro build options retain aliases, arrays, boolean negation and numeric coercion', () => {
  const command = metroRequire('./commands/build')();
  let parsed;
  const yargs = metroRequire('yargs/yargs')([]).exitProcess(false);
  yargs.command({ ...command, handler: argv => { parsed = argv; } });
  yargs.parse(['build', 'index.js', '-O', 'out.js', '-P', 'one', 'two', '-p', 'kepler',
    '--no-minify', '--dev', '-j', '2', '--source-map', '--source-map-url', 'out.map']);
  assert.equal(parsed.entry, 'index.js');
  assert.equal(parsed.out, 'out.js');
  assert.deepEqual(parsed.projectRoots, ['one', 'two']);
  assert.equal(parsed.platform, 'kepler');
  assert.equal(parsed.minify, false);
  assert.equal(parsed.dev, true);
  assert.equal(parsed.maxWorkers, 2);
  assert.equal(parsed.sourceMap, true);
  assert.equal(parsed.sourceMapUrl, 'out.map');
});

test('old yargs still validates required options and keeps arguments after the delimiter', () => {
  const yargs = metroRequire('yargs/yargs')([]).exitProcess(false);
  const command = metroRequire('./commands/build')();
  yargs.command({ ...command, handler: () => {} });
  let failure;
  yargs.parse(['build', 'index.js'], (err) => { failure = err; });
  assert.match(failure.message, /out/);
  const parsed = inspectorRequire('yargs/yargs')(['--port=9123', '--', '--literal']).exitProcess(false).argv;
  assert.equal(parsed.port, 9123);
  assert.deepEqual(parsed._, ['--literal']);
});

test('the actual SDK manifest reader preserves all declared privileges', () => {
  const require = createRequire(join(dirname(builderPath), 'src/utils/compatibility-utils.js'));
  const { getPrivilegesFromManifest } = require('./compatibility-utils');
  const text = readFileSync(join(app, 'manifest.toml'), 'utf8');
  const values = [...text.matchAll(/\[\[needs\.privilege\]\]\s*id\s*=\s*"([^"]+)"/g)].map(match => match[1]);
  assert.ok(values.length > 0);
  assert.deepEqual(getPrivilegesFromManifest(join(app, 'manifest.toml')), values);
  assert.equal(builderRequire('toml/package.json').version, '5.0.1');
});

for (const payload of [
  '[a.b]\ny=1\n[a.b.y.__proto__.__proto__]\ncalm_parser_probe="yes"\n',
  'aa=1\n[[a]]\n[aa.__proto__.__proto__]\ncalm_parser_probe="yes"\n',
]) {
  test('TOML rejects scalar-path prototype pollution without changing the process prototype', () => {
    const code = `const toml=require(${JSON.stringify(builderRequire.resolve('toml'))});
      let refused=false; try { toml.parse(${JSON.stringify(payload)}); } catch { refused=true; }
      if (!refused || ({}).calm_parser_probe !== undefined) process.exit(7);`;
    const child = spawnSync(process.execPath, ['-e', code], { timeout: 1500 });
    assert.equal(child.status, 0);
  });
}

test('TOML enforces nesting and integer limits with ordinary parse errors', () => {
  assert.throws(() => toml.parse('v=' + '['.repeat(600) + '1' + ']'.repeat(600)),
    err => !(err instanceof RangeError) && /depth|nesting/i.test(err.message));
  assert.throws(() => toml.parse('v=0x' + 'f'.repeat(200000)), /range|integer|long/i);
  assert.throws(() => toml.parse('v=9007199254740993'), /lossless|safe|BigInt/);
  assert.throws(() => toml.parse('v=1\nv=2'), /redefin|duplicate/i);
});

for (const shape of ['tables', 'path']) {
  test(`TOML ${shape} hostile fixture completes within a bounded child process`, () => {
    const code = `const toml=require(${JSON.stringify(builderRequire.resolve('toml'))});
      const doc=${JSON.stringify(shape)}==='tables'
        ? Array.from({length:20000},(_,i)=>'[[t'+i+']]\\nv=1').join('\\n')
        : '['+Array.from({length:20000},(_,i)=>'t'+i).join('.')+']\\nv=1';
      toml.parse(doc);`;
    const child = spawnSync(process.execPath, ['-e', code], { timeout: 1500 });
    assert.equal(child.error, undefined, 'bounded parser process timed out');
    assert.equal(child.status, 0);
  });
}
