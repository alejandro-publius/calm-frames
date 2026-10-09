import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { checkPreparedDirectory, checkPreparedNamespace, checkPreparedPackage } from './check_prepared_library.mjs';

const root = fileURLToPath(new URL('../assets/raw/prepared-library/', import.meta.url));
const fixture = new Map();
function read(directory, prefix = '') {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const relative = prefix + entry.name;
    if (entry.isDirectory()) read(path.join(directory, entry.name), relative + '/');
    else fixture.set(relative, fs.readFileSync(path.join(directory, entry.name)));
  }
}
read(root);
const check = (files) => checkPreparedNamespace([...files.keys()], (name) => files.get(name));

test('checks the actual generated library and exact byte total', () => {
  assert.equal(check(fixture).titles, 1);
  assert.equal(check(fixture).bytes, [...fixture.values()].reduce((total, data) => total + data.length, 0));
  assert.deepEqual(checkPreparedDirectory(root), check(fixture));
});

for (const extension of ['mp4', 'vtt', 'json']) {
  test(`refuses changed prepared ${extension} bytes`, () => {
    const changed = new Map(fixture);
    const name = [...changed.keys()].find((key) => key.includes('/titles/') && key.endsWith(`.${extension}`));
    changed.set(name, Buffer.concat([changed.get(name), Buffer.from('changed')]));
    assert.throws(() => check(changed), /asset changed/);
  });
}

test('refuses a compiled literal different from the reviewed manifest', () => {
  const changed = new Map(fixture);
  changed.set('catalog.ts', Buffer.from('export const PACKAGED_LIBRARY_JSON = "{}";'));
  assert.throws(() => check(changed), /Compiled prepared catalog/);
});

test('refuses an internally valid package from a different build input', () => {
  assert.throws(() => checkPreparedNamespace([...fixture.keys()], (name) => fixture.get(name), 'a'.repeat(64)),
    /differs from the current build input/);
  assert.deepEqual(checkPreparedNamespace([...fixture.keys()], (name) => fixture.get(name), check(fixture).catalogSha256),
    check(fixture));
});

test('refuses missing assets, undisclosed siblings and duplicate package members', () => {
  const missing = new Map(fixture);
  const asset = [...missing.keys()].find((key) => key.endsWith('.mp4'));
  missing.delete(asset);
  assert.throws(() => check(missing), /Missing prepared asset/);
  const extra = new Map(fixture);
  extra.set('original-source.mp4', Buffer.from('not reviewed'));
  assert.throws(() => check(extra), /unreviewed files/);
  assert.throws(() => checkPreparedNamespace([...fixture.keys(), 'catalog.json'], (name) => fixture.get(name)), /Duplicate/);
});

test('refuses a manifest changed inside its immutable directory', () => {
  const changed = new Map(fixture);
  const manifest = [...changed.keys()].find((key) => key.endsWith('/manifest.json'));
  changed.set(manifest, Buffer.from(changed.get(manifest).toString().replace('Harbor story', 'Changed story')));
  assert.throws(() => check(changed), /immutable directory/);
});

test('refuses aliases to files outside the package', () => {
  const directory = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'calm-prepared-check-')));
  try {
    fs.cpSync(root, path.join(directory, 'assets'), { recursive: true });
    const catalog = path.join(directory, 'assets/catalog.json');
    fs.unlinkSync(catalog);
    fs.symlinkSync(path.join(root, 'catalog.json'), catalog);
    assert.throws(() => checkPreparedDirectory(path.join(directory, 'assets')), /symlinks/);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

// A small ustar writer keeps this archive test independent of tar's creation
// options, which differ between the native Mac build and Linux CI.
function tar(entries) {
  const buffers = [];
  for (const { name, bytes = Buffer.alloc(0), kind = '0', link = '' } of entries) {
    const header = Buffer.alloc(512);
    const split = name.length > 100 ? name.lastIndexOf('/', 155) : -1;
    header.write(split < 0 ? name : name.slice(split + 1), 0, 100);
    if (split >= 0) header.write(name.slice(0, split), 345, 155);
    header.write('0000644\0', 100); header.write('0000000\0', 108); header.write('0000000\0', 116);
    header.write(bytes.length.toString(8).padStart(11, '0') + '\0', 124);
    header.write('00000000000\0', 136); header.fill(' ', 148, 156);
    header.write(kind, 156); header.write(link, 157, 100);
    header.write('ustar\0', 257); header.write('00', 263);
    header.write([...header].reduce((a, b) => a + b, 0).toString(8).padStart(6, '0') + '\0 ', 148);
    buffers.push(header, bytes, Buffer.alloc((512 - bytes.length % 512) % 512));
  }
  return Buffer.concat([...buffers, Buffer.alloc(1024)]);
}

test('rejects alternate archive paths and link members before reading any prepared content', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'calm-archive-check-'));
  const archive = path.join(directory, 'package.vpkg');
  const entries = [...fixture.entries()].map(([name, bytes]) => ({ name: 'assets/raw/prepared-library/' + name, bytes }));
  try {
    fs.writeFileSync(archive, tar(entries));
    assert.deepEqual(checkPreparedPackage(archive, check(fixture).catalogSha256), check(fixture));
    for (const name of ['/assets/raw/prepared-library/catalog.json', 'assets/raw/./prepared-library/catalog.json']) {
      fs.writeFileSync(archive, tar([...entries, { name, bytes: Buffer.from('{}') }]));
      assert.throws(() => checkPreparedPackage(archive), /Noncanonical/);
    }
    for (const kind of ['1', '2']) {
      fs.writeFileSync(archive, tar([...entries, { name: 'assets/raw/prepared-library/catalog.json', kind, link: '../other.json' }]));
      assert.throws(() => checkPreparedPackage(archive), /regular files/);
    }
    fs.writeFileSync(archive, tar([...entries, { name: 'assets/raw', kind: '2', link: 'elsewhere' }]));
    assert.throws(() => checkPreparedPackage(archive), /regular files/);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
