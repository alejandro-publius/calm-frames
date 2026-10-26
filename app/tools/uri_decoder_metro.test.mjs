/** Exercise the runtime dependency through Metro's module interop, not Node alone. */
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'package.json'));

test('Metro executes the fixed decoder through its existing CommonJS query consumer', { timeout: 30000 }, async t => {
  const Metro = require('metro');
  mkdirSync(join(app, '.logs'), { recursive: true });
  const dir = mkdtempSync(join(app, '.logs/uri-metro-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const entry = join(dir, 'entry.js');
  const output = join(dir, 'probe.js');
  writeFileSync(entry, `global.__CALM_URI_PROBE__ = require('query-string').parse('scene=Sea+Otters&symbol=%2B&malformed=' + '%FF'.repeat(1000));`);
  const config = await Metro.loadConfig({ config: join(app, 'metro.config.js'), cwd: app }, { maxWorkers: 1 });
  await Metro.runBuild(config, { entry, out: output, platform: 'kepler', dev: false, minify: false });
  const bundle = readFileSync(output, 'utf8');
  const context = { console, setTimeout, clearTimeout, performance };
  context.global = context;
  vm.runInNewContext(bundle, context, { timeout: 1000 });
  assert.deepEqual(JSON.parse(JSON.stringify(context.__CALM_URI_PROBE__)), {
    scene: 'Sea Otters', symbol: '+', malformed: '%FF'.repeat(1000),
  });
  assert.ok(!bundle.includes('function decodeComponents('), 'old recursive decoder must not be bundled');
});
