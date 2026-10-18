import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { approvedCatalogModule, checkApprovedCatalogs, readApprovalRegistry } from './approved_prepared_libraries.mjs';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
function fixture(t) {
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'calm-exact-approval-')));
  t.after(() => fs.rmSync(root, { recursive: true }));
  fs.mkdirSync(path.join(root, 'config'));
  fs.mkdirSync(path.join(root, 'src/calmframes'), { recursive: true });
  const config = path.join(root, 'config/approved-prepared-libraries.json');
  fs.copyFileSync(path.join(APP, 'config/approved-prepared-libraries.json'), config);
  const entry = readApprovalRegistry(root)[0];
  const manifest = path.join(root, 'assets/raw/prepared-library', entry.bundleId, 'manifest.json');
  fs.mkdirSync(path.dirname(manifest), { recursive: true });
  fs.copyFileSync(path.join(APP, 'assets/raw/prepared-library', entry.bundleId, 'manifest.json'), manifest);
  const generated = path.join(root, 'src/calmframes/approvedPreparedCatalogs.ts');
  fs.writeFileSync(generated, approvedCatalogModule(root).module);
  return { root, config, manifest, generated };
}

test('existing exact Acadia fixture matches generated input; generation repeats byte-for-byte', t => {
  const { root } = fixture(t);
  assert.equal(checkApprovedCatalogs(root).length, 1);
  assert.equal(approvedCatalogModule(root).module, approvedCatalogModule(root).module);
  assert.match(checkApprovedCatalogs(root)[0].label, /fixture/);
});
for (const change of ['catalog', 'key', 'bundle', 'duplicate', 'generated', 'missing-generated', 'symlink']) {
  test(`rejects ${change} substitution without changing approval`, t => {
    const { root, config, manifest, generated } = fixture(t);
    const registry = JSON.parse(fs.readFileSync(config));
    if (change === 'catalog') fs.appendFileSync(manifest, ' ');
    if (change === 'key') registry.catalogs[0].publicKeyFingerprint = 'f'.repeat(64);
    if (change === 'bundle') registry.catalogs[0].bundleId = 'f'.repeat(64);
    if (change === 'duplicate') registry.catalogs.push(registry.catalogs[0]);
    if (change === 'generated') fs.appendFileSync(generated, '\n');
    if (change === 'missing-generated') fs.unlinkSync(generated);
    if (change === 'symlink') { fs.renameSync(manifest, manifest + '.old'); fs.symlinkSync(manifest + '.old', manifest); }
    fs.writeFileSync(config, JSON.stringify(registry));
    assert.throws(() => checkApprovedCatalogs(root));
  });
}

test('consumer membership is generated from reviewed data rather than title-specific code', t => {
  const { root, config } = fixture(t);
  const registry = JSON.parse(fs.readFileSync(config));
  registry.catalogs[0].consumer = false;
  fs.writeFileSync(config, JSON.stringify(registry));
  assert.match(approvedCatalogModule(root).module, /"consumer": false/);
  assert.throws(() => checkApprovedCatalogs(root), /Compiled approved/);
});
