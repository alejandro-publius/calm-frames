import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const sdkEntry = join(app, 'node_modules/@amazon-devices/kepler-cli-platform',
  'dist/common/packageJsonUtils.js');
const extractorEntry = join(app, 'node_modules/@microsoft/api-extractor',
  'lib/api/ExtractorConfig.js');
const sdkRequire = createRequire(sdkEntry);
const extractorRequire = createRequire(extractorEntry);
const consumers = [sdkRequire, extractorRequire];

function fixture(t) {
  const dir = mkdtempSync(join(tmpdir(), 'calm-build-deps-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

test('both build tools resolve the fixed Lodash without upgrading either tool', () => {
  assert.equal(sdkRequire('../../package.json').version, '0.22.14');
  assert.equal(extractorRequire('../../package.json').version, '7.47.0');
  for (const require of consumers) {
    assert.equal(require('lodash/package.json').version, '4.18.1');
  }
  const lock = JSON.parse(readFileSync(join(app, 'package-lock.json'), 'utf8'));
  for (const [path, item] of Object.entries(lock.packages)) {
    if (path.endsWith('node_modules/lodash')) assert.equal(item.version, '4.18.1', path);
  }
});

test('Lodash rejects template imports that are not parameter names', () => {
  for (const require of consumers) {
    const lodash = require('lodash');
    for (const key of ['injected = 1', 'bad,key']) {
      // Compile only a harmless literal; never invoke an injected expression.
      assert.throws(() => lodash.template('plain', { imports: { [key]: 1 } }),
        /Invalid `imports`/);
    }
    assert.equal(lodash.template('<%= label %>', { imports: { label: 'Acadia' } })(),
      'Acadia');
  }
});

test('Lodash blocks prototype deletion through string and coerced path segments', () => {
  for (const require of consumers) {
    const lodash = require('lodash');
    for (const segment of ['prototype', ['prototype']]) {
      // An isolated prototype sentinel, never a built-in or application object.
      function Target() {}
      Target.prototype.keep = 'retained';
      assert.equal(lodash.unset({ Target }, ['Target', segment, 'keep']), false);
      assert.equal(Target.prototype.keep, 'retained');
    }
    const ordinary = { settings: { removable: true, keep: true } };
    assert.equal(lodash.unset(ordinary, ['settings', 'removable']), true);
    assert.deepEqual(ordinary, { settings: { keep: true } });
  }
});

test('the installed SDK config loader retains defaults and explicit bundle settings', t => {
  const exports = {};
  const warnings = [];
  vm.runInNewContext(readFileSync(sdkEntry, 'utf8'), {
    exports,
    require(name) {
      if (name === '../common') return { logger: { warn(text) { warnings.push(text); } } };
      return sdkRequire(name);
    },
  }, { filename: sdkEntry, timeout: 1000 });
  const ConfigLoader = exports.default;
  const cases = [
    [{}, true, true, undefined],
    [{ kepler: { useSystemJsBundles: false } }, false, true, false],
    [{ kepler: { useSystemJsBundlesForHeadlessJs: false } }, true, false, undefined],
    [{ kepler: { disableSplitBundle: true } }, false, true, undefined],
    [{ kepler: { disableSplitBundle: true, useSystemJsBundles: true } }, true, true, true],
  ];
  for (const [config, bundles, headless, explicit] of cases) {
    const root = fixture(t);
    writeFileSync(join(root, 'package.json'), JSON.stringify(config));
    const loader = new ConfigLoader({ root });
    assert.equal(loader.getUseSystemJsBundlesConfig(), bundles);
    assert.equal(loader.getUseSystemJsBundlesForHeadlessJsConfig(), headless);
    assert.equal(loader.getExplicitUseSystemJsBundlesConfig(), explicit);
  }
  assert.equal(warnings.length, 2);
  assert.deepEqual(JSON.parse(JSON.stringify(ConfigLoader.DEFAULT_CONFIG)), {
    kepler: { useSystemJsBundles: true, useSystemJsBundlesForHeadlessJs: true },
  });
});

test('the installed API Extractor merges inherited config without changing defaults', t => {
  const { ExtractorConfig } = extractorRequire(extractorEntry);
  const root = fixture(t);
  const base = join(root, 'base.json');
  const child = join(root, 'child.json');
  const original = JSON.stringify({
    mainEntryPointFilePath: './index.d.ts',
    apiReport: { enabled: false, reportFileName: 'base.api.md' },
    docModel: { enabled: false },
    dtsRollup: { enabled: false },
  });
  writeFileSync(base, original);
  writeFileSync(child, JSON.stringify({
    extends: './base.json', apiReport: { enabled: true },
  }));
  const defaults = JSON.stringify(ExtractorConfig._defaultConfig);
  const loaded = ExtractorConfig.loadFile(child);
  assert.equal(loaded.mainEntryPointFilePath, join(root, 'index.d.ts'));
  assert.equal(loaded.apiReport.enabled, true);
  assert.equal(loaded.apiReport.reportFileName, 'base.api.md');
  assert.equal(loaded.docModel.enabled, false);
  assert.equal(readFileSync(base, 'utf8'), original);
  assert.equal(JSON.stringify(ExtractorConfig._defaultConfig), defaults);
  writeFileSync(child, JSON.stringify({ extends: './child.json' }));
  assert.throws(() => ExtractorConfig.loadFile(child), /contains a cycle/);
});

test('the installed API Extractor retains exact names and matches bundled package globs', () => {
  const { Collector } = extractorRequire('../collector/Collector.js');
  const resolved = Collector._resolveBundledPackagePatterns(
    ['@calm/*', 'tool-*', 'literal-package', 'not-found-*'], {
      dependencies: { '@calm/core': '1', unrelated: '1' },
      devDependencies: { 'tool-dev': '1' },
      peerDependencies: { '@calm/peer': '1' },
      optionalDependencies: { 'tool-optional': '1' },
    });
  assert.deepEqual([...resolved].sort(),
    ['@calm/core', '@calm/peer', 'literal-package', 'tool-dev', 'tool-optional']);
  assert.equal(Collector._resolveBundledPackagePatterns([], undefined).size, 0);
});

test('the Minimatch 3 backport leaves the TypeScript consumer on its modern major', () => {
  assert.equal(extractorRequire('minimatch/package.json').version, '3.1.5');
  const typescriptRequire = createRequire(join(app,
    'node_modules/@typescript-eslint/typescript-estree/package.json'));
  assert.equal(typescriptRequire('minimatch/package.json').version, '10.2.6');
  const lock = JSON.parse(readFileSync(join(app, 'package-lock.json'), 'utf8'));
  for (const [path, item] of Object.entries(lock.packages)) {
    if (path.endsWith('node_modules/minimatch') && item.version.startsWith('3.')) {
      assert.equal(item.version, '3.1.5', path);
    }
  }
});
