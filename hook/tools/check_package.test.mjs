/** Packaging guards must reject an incomplete or unsafe external install. */
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import {
  assertDependencyClosure, assertInstalledEntry, assertPackageManifest,
  assertPackedFiles, assertPeerCompatibility, EXPECTED_FILES, PEERS, publicExports,
} from './check_package.mjs';

const hookRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const appRequire = createRequire(join(hookRoot, '..', 'app', 'package.json'));
const ts = appRequire('typescript');
const manifest = JSON.parse(readFileSync(join(hookRoot, 'package.json'), 'utf8'));
const index = readFileSync(join(hookRoot, 'src/index.ts'), 'utf8');

test('the actual package declares installable source entry points and peers', () => {
  assertPackageManifest(manifest);
});

test('the included Apache licence matches the repository licence', () => {
  assert.equal(readFileSync(join(hookRoot, 'LICENSE'), 'utf8'),
    readFileSync(join(hookRoot, '..', 'LICENSE'), 'utf8'));
});

test('every essential public value and type is exported', () => {
  assert(publicExports(ts, index).length > 12);
  assert.throws(() => publicExports(ts,
    index.replace("export { useFlashGuard } from './engine/useFlashGuard';", '')),
  /missing public export: useFlashGuard/);
});

test('a packed entry and every engine dependency are mandatory', () => {
  assertPackedFiles(EXPECTED_FILES);
  for (const missing of ['src/index.ts', 'src/pixelUtils.ts', 'src/engine/sceneHolds.ts', 'LICENSE']) {
    assert.throws(() => assertPackedFiles(EXPECTED_FILES.filter((one) => one !== missing)),
      /packed file inventory/);
  }
  assert.throws(() => assertPackedFiles([...EXPECTED_FILES, EXPECTED_FILES[0]]), /duplicate packed path/);
});

test('keys, media, fixtures, app files and development tools cannot enter the tarball', () => {
  for (const extra of ['team_key.pem', 'clip.mp4', 'test/fixtures/key.pem',
    'tools/sync.mjs', '../app/src/calmframes/offlineTitle.ts', 'src/private.ts']) {
    assert.throws(() => assertPackedFiles([...EXPECTED_FILES, extra]), /packed file inventory/);
  }
});

test('source entries cannot silently resolve somewhere outside the packed package', () => {
  for (const field of ['main', 'types', 'react-native']) {
    assert.throws(() => assertPackageManifest({ ...manifest, [field]: '../app/src/index.ts' }),
      /must resolve to packed source/);
  }
});

test('a missing runtime peer cannot be hidden by the monorepo', () => {
  const { react, ...others } = manifest.peerDependencies;
  assert(react);
  assert.throws(() => assertPackageManifest({ ...manifest, peerDependencies: others }),
    /declare all required Vega peers/);
});

test('the reused real peers satisfy every declared package range', () => {
  const versions = Object.fromEntries(PEERS.map((peer) => [peer,
    JSON.parse(readFileSync(join(hookRoot, '..', 'app/node_modules', peer, 'package.json'), 'utf8')).version]));
  const semver = appRequire('semver');
  assertPeerCompatibility(manifest, versions, semver);
  assert.throws(() => assertPeerCompatibility({ ...manifest,
    peerDependencies: { ...manifest.peerDependencies, react: '>=999.0.0' } }, versions, semver),
  /current peer does not satisfy declared range: react/);
});

test('relative dependency checks reject missing and escaping source paths', () => {
  const scratch = mkdtempSync(join(tmpdir(), 'calm-hook-closure-'));
  try {
    mkdirSync(join(scratch, 'src/engine'), { recursive: true });
    const entry = join(scratch, 'src/index.ts');
    writeFileSync(join(scratch, 'src/engine/public.ts'), 'export const value = 1;');
    writeFileSync(entry, "export { value } from './engine/public';");
    const files = ['src/index.ts', 'src/engine/public.ts'];
    assertDependencyClosure(scratch, ts, files);
    writeFileSync(entry, "export { value } from './engine/missing';");
    assert.throws(() => assertDependencyClosure(scratch, ts, files), /missing packed dependency/);
    mkdirSync(join(scratch, 'app'));
    writeFileSync(join(scratch, 'app/private.ts'), 'export const value = 2;');
    writeFileSync(entry, "export { value } from '../app/private';");
    assert.throws(() => assertDependencyClosure(scratch, ts, [...files, 'app/private.ts']),
      /relative import escaped package/);
    writeFileSync(entry, "import value from 'undeclared-peer';");
    assert.throws(() => assertDependencyClosure(scratch, ts, files), /undeclared external import/);
    writeFileSync(entry, '-----BEGIN PRIVATE KEY-----');
    assert.throws(() => assertDependencyClosure(scratch, ts, files), /private key in packed source/);
    writeFileSync(entry, 'binary\0source');
    assert.throws(() => assertDependencyClosure(scratch, ts, files), /binary source in package/);
    writeFileSync(entry, "export { value } from './engine/public';");
    const extra = join(scratch, 'src/linked.ts');
    symlinkSync(entry, extra);
    assert.throws(() => assertDependencyClosure(scratch, ts, [...files, 'src/linked.ts']),
      /packed source must be a regular file/);
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
});

test('consumer entry must be installed source rather than the repository copy', () => {
  assertInstalledEntry(join(hookRoot, 'src/index.ts'), hookRoot);
  assert.throws(() => assertInstalledEntry(join(hookRoot, 'src/pixelUtils.ts'), hookRoot),
    /consumer must resolve the installed tarball/);
});
