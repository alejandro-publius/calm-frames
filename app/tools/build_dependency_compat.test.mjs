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

const schemaRequire = createRequire(join(app,
  'node_modules/@rushstack/node-core-library/lib/JsonSchema.js'));
const tsdocRequire = createRequire(join(app,
  'node_modules/@microsoft/tsdoc-config/lib/TSDocConfigFile.js'));

test('schema consumers resolve patched Ajv 8 while ESLint retains Ajv 6', () => {
  assert.equal(schemaRequire('../package.json').version, '5.4.1');
  assert.equal(tsdocRequire('../package.json').version, '0.17.1');
  for (const require of [schemaRequire, tsdocRequire]) {
    assert.equal(require('ajv/package.json').version, '8.18.0');
  }
  const eslintRequire = createRequire(join(app, 'node_modules/eslint/package.json'));
  assert.equal(eslintRequire('ajv/package.json').version, '6.15.0');
});

for (const [name, require] of [['Rushstack', schemaRequire], ['TSDoc', tsdocRequire]]) {
  test(`${name} Ajv uses the selected regex engine for data-supplied patterns`, () => {
    const Ajv = require('ajv');
    const seen = [];
    function controlledRegExp(pattern, flags) {
      seen.push(pattern);
      // A harmless sentinel makes an engine bypass observable without a ReDoS
      // payload, external regex engine, timing threshold or native dependency.
      if (pattern === '^blocked-by-engine$') return { test: () => false };
      return new RegExp(pattern, flags);
    }
    const ajv = new Ajv({ $data: true, code: { regExp: controlledRegExp } });
    const validate = ajv.compile({
      type: 'object',
      properties: {
        pattern: { type: 'string' },
        value: { type: 'string', pattern: { $data: '1/pattern' } },
      },
      required: ['pattern', 'value'],
    });
    assert.equal(validate({ pattern: '^calm$', value: 'calm' }), true);
    assert.equal(validate({ pattern: '^calm$', value: 'other' }), false);
    assert.equal(validate({ pattern: '^blocked-by-engine$', value: 'blocked-by-engine' }), false);
    assert.ok(seen.includes('^blocked-by-engine$'));
  });

  test(`${name} Ajv rejects invalid data-pattern syntax without throwing`, () => {
    const Ajv = require('ajv');
    const validate = new Ajv({ $data: true }).compile({
      type: 'object',
      properties: {
        pattern: { type: 'string' },
        value: { type: 'string', pattern: { $data: '1/pattern' } },
      },
    });
    assert.equal(validate({ pattern: '[', value: 'calm' }), false);
    assert.equal(validate.errors[0].keyword, 'pattern');
  });
}

test('the installed Rushstack validator retains drafts, references and format rejection', () => {
  const { JsonSchema } = schemaRequire('./JsonSchema.js');
  for (const draft of ['draft-04', 'draft-07']) {
    const schema = JsonSchema.fromLoadedObject({
      $schema: `http://json-schema.org/${draft}/schema#`,
      type: 'object',
      definitions: { label: { type: 'string', pattern: '^[A-Za-z ]+$' } },
      properties: { label: { $ref: '#/definitions/label' }, contact: { type: 'string', format: 'email' } },
      required: ['label', 'contact'],
      additionalProperties: false,
    });
    schema.validateObject({ label: 'Calm Frames', contact: 'fixture@example.com' }, 'fixture.json');
    for (const value of [
      { label: 42, contact: 'fixture@example.com' },
      { label: 'Calm', contact: 'invalid' },
      { label: 'Calm', contact: 'fixture@example.com', extra: true },
    ]) {
      assert.throws(() => schema.validateObject(value, 'fixture.json'), /JSON validation failed/);
    }
  }
});

test('the installed TSDoc loader retains valid tags and refuses malformed config', t => {
  const { TSDocConfigFile } = tsdocRequire('./TSDocConfigFile.js');
  const root = fixture(t);
  const file = join(root, 'tsdoc.json');
  const valid = {
    $schema: TSDocConfigFile.CURRENT_SCHEMA_URL,
    tagDefinitions: [{ tagName: '@calm', syntaxKind: 'block' }],
    supportForTags: { '@calm': true },
  };
  writeFileSync(file, JSON.stringify(valid));
  const loaded = TSDocConfigFile.loadFile(file);
  assert.equal(loaded.hasErrors, false, loaded.getErrorSummary());
  assert.equal(loaded.tagDefinitions[0].tagName, '@calm');
  assert.equal(loaded.supportForTags.get('@calm'), true);
  writeFileSync(file, JSON.stringify({ ...valid, tagDefinitions: 'not an array' }));
  const invalid = TSDocConfigFile.loadFile(file);
  assert.equal(invalid.hasErrors, true);
  assert.match(invalid.getErrorSummary(), /tagDefinitions.*array/);
});

const hooksRequire = createRequire(join(app,
  'node_modules/eslint-plugin-react-hooks/package.json'));

for (const kind of ['array', 'set']) {
  test(`the hooks validator rejects oversized constrained ${kind}s before parsing elements`, () => {
    const { z } = hooksRequire('zod/v4');
    let parsed = 0;
    const element = z.string().transform(value => { parsed += 1; return value.toUpperCase(); });
    const schema = (kind === 'array' ? z.array(element) : z.set(element)).max(2);
    const make = values => kind === 'array' ? values : new Set(values);
    const refused = schema.safeParse(make(['one', 'two', 'three']));
    assert.equal(refused.success, false);
    assert.equal(refused.error.issues[0].code, 'too_big');
    assert.equal(parsed, 0);
    const accepted = schema.parse(make(['one', 'two']));
    assert.deepEqual([...accepted], ['ONE', 'TWO']);
    assert.equal(parsed, 2);
  });
}

test('the unbounded schema still visits each element; the fix is not a global parse cap', () => {
  const { z } = hooksRequire('zod/v4');
  let parsed = 0;
  const schema = z.array(z.string().transform(value => { parsed += 1; return value; }));
  assert.deepEqual(schema.parse(['one', 'two', 'three']), ['one', 'two', 'three']);
  assert.equal(parsed, 3);
});

test('the installed hooks lint rule still accepts ordinary hooks and rejects conditional calls', () => {
  const { Linter } = hooksRequire('eslint');
  const hooks = hooksRequire('eslint-plugin-react-hooks');
  const linter = new Linter({ configType: 'eslintrc' });
  linter.defineRule('react-hooks/rules-of-hooks', hooks.rules['rules-of-hooks']);
  const config = {
    parserOptions: { ecmaVersion: 2022, sourceType: 'module' },
    rules: { 'react-hooks/rules-of-hooks': 'error' },
  };
  const valid = "import { useState } from 'react'; function Screen() { const [v] = useState(0); return v; }";
  assert.deepEqual(linter.verify(valid, config), []);
  const invalid = "import { useState } from 'react'; function Screen({ enabled }) { if (enabled) { useState(0); } return null; }";
  const errors = linter.verify(invalid, config);
  assert.equal(errors.length, 1);
  assert.equal(errors[0].ruleId, 'react-hooks/rules-of-hooks');
  assert.match(errors[0].message, /conditionally/);
});
