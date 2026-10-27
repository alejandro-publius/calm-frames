/** Prove removal of the unused RN 0.60 host graph at its real SDK consumer. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'package.json'));
const manifest = require('./package.json');
const lock = require('./package-lock.json');
const securityPath = dirname(require.resolve('@amazon-devices/security-manager-lib/package.json'));
const files = JSON.parse(readFileSync(join(app, '../results/checklist12-dependencies-2026-10-27/security-manager-files.json')));

test('codegen shares the exact app RN while the obsolete host toolchain is absent', () => {
  assert.equal(manifest.dependencies['react-native'], '0.83.0');
  assert.deepEqual(manifest.overrides['react-native-tscodegen-types@0.66.0'], { 'react-native': '$react-native' });
  const codegen = createRequire(require.resolve('react-native-tscodegen-types/package.json'));
  assert.equal(codegen('./package.json').version, '0.66.0');
  assert.equal(codegen.resolve('react-native'), require.resolve('react-native'));
  assert.ok(require.resolve('react-native').startsWith(app + '/node_modules/'));
  const versions = name => Object.entries(lock.packages)
    .filter(([path]) => path.endsWith('node_modules/' + name)).map(([, entry]) => entry.version);
  assert.deepEqual(versions('react-native'), ['0.83.0']);
  assert.deepEqual(versions('react-devtools-core'), ['6.1.5']);
  assert.deepEqual(versions('ws').sort(), ['6.2.6', '7.5.13']);
  const obsolete = ['metro-inspector-proxy', 'sane', 'fbjs', 'fbjs-scripts', 'isomorphic-fetch',
    'os-locale', 'external-editor', 'xcode'];
  for (const name of obsolete) {
    assert.deepEqual(versions(name), [], name);
    assert.equal(existsSync(join(app, 'node_modules', name)), false, name);
  }
  const oldTree = 'node_modules/react-native-tscodegen-types/node_modules';
  assert.ok(Object.keys(lock.packages).every(path => !path.startsWith(oldTree + '/')));
  assert.equal(existsSync(join(app, oldTree, 'react-native')), false);
});

test('the published SDK consumer, native metadata and system bundles remain byte-identical', () => {
  function walk(root, prefix = '') {
    return readdirSync(root, { withFileTypes: true }).flatMap(entry => {
      const path = prefix + entry.name;
      return entry.isDirectory() ? walk(join(root, entry.name), path + '/') : [path];
    });
  }
  assert.deepEqual(walk(securityPath).sort(), Object.keys(files).sort());
  for (const [path, hash] of Object.entries(files)) {
    const bytes = readFileSync(join(securityPath, path));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), hash, path);
    // Includes declarations, JS, both Hermes system bundles and their maps.
    if (path !== 'package.json') assert.equal(bytes.includes('react-native-tscodegen-types'), false, path);
  }
  const consumers = Object.entries(lock.packages).filter(([, entry]) =>
    entry.dependencies?.['react-native-tscodegen-types']);
  assert.deepEqual(consumers.map(([path]) => path), ['node_modules/@amazon-devices/security-manager-lib']);
  assert.equal(consumers[0][1].dependencies['react-native-tscodegen-types'], '0.66.0');
});

test('actual SecurityManager and Amazon registry retain permission results, errors and native registration', () => {
  const result = spawnSync(process.execPath, ['--input-type=commonjs', '-e', `
    const assert = require('node:assert/strict');
    const Module = require('node:module');
    const load = Module._load;
    Module._load = function (name, ...args) {
      assert.ok(!name.includes('react-native-tscodegen-types'), 'unused codegen became a runtime consumer');
      return load.call(this, name, ...args);
    };
    const calls = [];
    let state = 'ALLOW';
    let failure;
    const native = {
      registerICredentialCtor(value) { calls.push(['register', typeof value]); },
      getSelfPrivilegeState(value) { calls.push(['self', value]); return failure ? Promise.reject(failure) : Promise.resolve(state); },
      getPrivilegeState(value, id) { calls.push(['package', value, id]); return Promise.resolve(state); },
      requestPrivilege(value) { calls.push(['request', value]); return failure ? Promise.reject(failure) : Promise.resolve(state); },
    };
    global.__turboModuleProxy = name => { assert.equal(name, 'SecurityManager'); return native; };
    const { SecurityManager, PrivilegeState } = require('@amazon-devices/security-manager-lib');
    (async () => {
      assert.equal(await SecurityManager.getPrivilegeState('fixture.network'), PrivilegeState.ALLOW);
      state = 'DENY';
      assert.equal(await SecurityManager.getPrivilegeState('fixture.network', 'io.fixture'), PrivilegeState.DENY);
      assert.equal(await SecurityManager.requestPrivilege('fixture.network'), PrivilegeState.DENY);
      state = 'ALLOW';
      assert.equal(await SecurityManager.requestPrivilege('fixture.network'), PrivilegeState.ALLOW);
      state = 'unexpected';
      assert.equal(await SecurityManager.getPrivilegeState('fixture.network'), PrivilegeState.DENY);
      failure = new Error('fixture refusal');
      await assert.rejects(SecurityManager.getPrivilegeState('fixture.network'), error => error === failure);
      await assert.rejects(SecurityManager.requestPrivilege('fixture.network'), error => error === failure);
      assert.deepEqual(calls.slice(0, 4), [['register', 'function'], ['self', 'fixture.network'],
        ['package', 'fixture.network', 'io.fixture'], ['request', 'fixture.network']]);
    })().catch(error => { console.error(error); process.exitCode = 1; });
  `], { cwd: app, encoding: 'utf8', timeout: 3000 });
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, result.stderr);
});

test('actual Amazon registry refuses a missing native security module', () => {
  const result = spawnSync(process.execPath, ['-e', `
    const assert = require('node:assert/strict');
    global.__turboModuleProxy = () => null;
    assert.throws(() => require('@amazon-devices/security-manager-lib'), /SecurityManager.*could not be found/);
  `], { cwd: app, encoding: 'utf8', timeout: 3000 });
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, result.stderr);
});

test('the actual Amazon code generator retains the baseline C++ output', t => {
  const root = mkdtempSync(join(tmpdir(), 'calm-codegen-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const source = join(root, 'NativeCalmFixture.ts');
  writeFileSync(source, `
import { KeplerTurboModule, TurboModuleRegistry } from '@amazon-devices/keplerscript-turbomodule-api';
export interface Spec extends KeplerTurboModule {
  echo(value: string): Promise<string>;
}
export default TurboModuleRegistry.getEnforcing<Spec>('CalmFixture');
`);
  const cli = require.resolve('@amazon-devices/keplerscript-turbomodule-api/cli.js');
  const result = spawnSync(process.execPath, [cli, 'codegen', source,
    '--outputPath', root, '--namespace', 'calm::fixture', '--new'],
  { cwd: app, encoding: 'utf8', timeout: 5000 });
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, result.stderr);
  const expected = JSON.parse(readFileSync(join(app, '../results/checklist12-dependencies-2026-10-27/codegen-files.json')));
  for (const [path, hash] of Object.entries(expected)) {
    assert.equal(createHash('sha256').update(readFileSync(join(root, path))).digest('hex'), hash, path);
  }
});
