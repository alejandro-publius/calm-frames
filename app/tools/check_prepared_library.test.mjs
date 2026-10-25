import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { checkPreparedDirectory, checkPreparedNamespace, checkPreparedPackage,
  checkRuntimeAssetDirectory, checkRuntimeAssetNames } from './check_prepared_library.mjs';

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

test('runtime assets contain no Python, shell or C/C++ build sources', () => {
  const result = checkRuntimeAssetDirectory();
  assert.equal(result.build_sources, 'excluded');
  assert.ok(result.files > 0);
});

test('asset source exclusions retain generated catalogs and reject aliased build paths', () => {
  assert.doesNotThrow(() => checkRuntimeAssetNames([
    'assets/raw/prepared-library/catalog.ts', 'assets/image/CalmFrames.png',
    'assets/raw/sound/menu-select.mp3', 'lib/aarch64/runtime.so',
  ]));
  for (const name of ['assets/brand/../tools/build.PY', '/assets/brand/render.sh',
    'assets/brand/render_qt.cpp', './assets/raw/sound/generate_menu_select.py']) {
    assert.throws(() => checkRuntimeAssetNames([name]), /Build-only source/);
  }
});

test('runtime asset source check cannot be bypassed through a linked directory', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'calm-linked-assets-'));
  try {
    fs.mkdirSync(path.join(directory, 'assets'));
    fs.mkdirSync(path.join(directory, 'tools'));
    fs.writeFileSync(path.join(directory, 'tools/build.py'), '# build source');
    fs.symlinkSync('../tools', path.join(directory, 'assets/linked'));
    assert.throws(() => checkRuntimeAssetDirectory(path.join(directory, 'assets')), /symlinks/);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

test('checks the actual generated library and exact byte total', () => {
  assert.equal(check(fixture).titles, 1);
  assert.equal(check(fixture).bytes, [...fixture.values()].reduce((total, data) => total + data.length, 0));
  assert.deepEqual(checkPreparedDirectory(root), check(fixture));
  const required = new Set([...fixture.entries()].filter(([name]) => name.endsWith('/manifest.json'))
    .flatMap(([, bytes]) => JSON.parse(bytes).titles.map((title) => title.verification.reportSha256)));
  const present = new Set([...fixture.keys()].filter((name) => name.startsWith('reports/'))
    .map((name) => name.slice('reports/'.length, -'.json'.length)));
  assert.deepEqual(check(fixture).verification_reports, { required: required.size, present: present.size,
    missing: [...required].filter((digest) => !present.has(digest)).sort() });
  // Attaching the real originals must keep this checkout's tests green. The
  // legacy omission case is explicit, independent of the current evidence state.
  const legacy = new Map([...fixture.entries()].filter(([name]) => !name.startsWith('reports/')));
  assert.throws(() => checkPreparedNamespace([...legacy.keys()], (name) => legacy.get(name), undefined,
    { requireReports: true }), /Original verification reports are missing/);
});

// Fabricated reports exercise the delivery contract; they are never evidence
// for the bundled film. Each fixture changes its own catalog to its own digest.
function reportFixture(change = () => {}, rawChange = (raw) => raw) {
  const hash = (raw) => createHash('sha256').update(raw).digest('hex');
  const manifest = JSON.parse(fixture.get('catalog.json'));
  const oldBundle = manifest.bundleId;
  const title = manifest.titles[0];
  const presets = ['wcag', 'broadcast', 'extra-cautious'];
  const core = ['map_hash', 'map_signature', 'plan_matches_map', 'safe_rendition_clean',
    'rendition_matches_source', 'cover_proof', 'cover_model_clean', 'hls_rendition_clean', 'hls_timing_matches_master'];
  const report = { sha256: title.sourceSha256, source_path: 'FABRICATED CONTRACT SOURCE', presets,
    passed: true, outcome: 'no flagged segments', started_at: 0, finished_at: 0,
    checks: ['source_hash', ...presets.flatMap((preset) => core.map((name) => `${name}:${preset}`))]
      .map((name) => ({ name, passed: true, detail: 'FABRICATED CONTRACT CHECK', data: {} })) };
  change(report, title);
  const raw = Buffer.from(rawChange(JSON.stringify(report)));
  const digest = hash(raw);
  title.verification.reportSha256 = digest;
  delete manifest.bundleId;
  const sorted = (value) => Array.isArray(value) ? value.map(sorted) :
    value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, sorted(value[key])])) : value;
  manifest.bundleId = hash(JSON.stringify(sorted(manifest)));
  const text = JSON.stringify(sorted(manifest), null, 2) + '\n';
  const files = new Map([...fixture.entries()].filter(([name]) => name.startsWith(oldBundle + '/titles/'))
    .map(([name, bytes]) => [name.replace(oldBundle, manifest.bundleId), bytes]));
  files.set('catalog.json', Buffer.from(text));
  files.set('catalog.ts', Buffer.from('/** Generated by pipeline.packaged_library. Verify before building the app. */\n' +
    `export const PACKAGED_LIBRARY_JSON = ${JSON.stringify(text)};\n` +
    `export const PACKAGED_LIBRARY_SHA256 = ${JSON.stringify(hash(text))};\n`));
  files.set(`${manifest.bundleId}/manifest.json`, Buffer.from(text));
  files.set(`reports/${digest}.json`, raw);
  return files;
}

test('checks hash-bound original report bytes and retains the source catalog identity', () => {
  const files = reportFixture();
  const result = checkPreparedNamespace([...files.keys()], (name) => files.get(name), undefined, { requireReports: true });
  assert.deepEqual(result.verification_reports, { required: 1, present: 1, missing: [] });
  const name = [...files.keys()].find((name) => name.startsWith('reports/'));
  files.set(name, Buffer.concat([files.get(name), Buffer.from('\n')]));
  assert.throws(() => check(files), /report bytes differ/);
});

for (const change of ['source', 'presets', 'failed', 'missing', 'duplicate', 'outcome', 'derived', 'plan', 'key']) {
  test(`a matching report digest does not override invalid ${change} evidence`, () => {
    const files = reportFixture((report, title) => {
      if (change === 'source') report.sha256 = '0'.repeat(64);
      if (change === 'presets') report.presets = ['wcag'];
      if (change === 'failed') report.checks[0].passed = false;
      if (change === 'missing') report.checks.pop();
      if (change === 'duplicate') report.checks.push(report.checks[0]);
      if (change === 'outcome') report.outcome = 'cover proven drawn';
      if (change === 'derived') report.outcome = title.verification.outcome = 'cover proven drawn';
      if (change === 'plan') report.checks.find((check) => check.name === 'plan_matches_map:wcag').data.stored = true;
      if (change === 'key') report.source_path = '-----BEGIN PRIVATE KEY-----';
    });
    assert.throws(() => check(files), /report/);
  });
}

test('derived report outcome keeps the full suffix of extra check names', () => {
  const files = reportFixture((report, title) => {
    report.checks.push({ name: 'plan_matches_map:wcag:extra', passed: true,
      detail: 'FABRICATED CONTRACT CHECK', data: { stored: 1 } });
    report.checks.push({ name: 'cover_actually_drawn:wcag', passed: true,
      detail: 'FABRICATED CONTRACT CHECK', data: {} });
    // Python VerifyReport uses the complete suffix after the first colon.
    // Evidence for wcag cannot stand in for the distinct wcag:extra check.
    report.outcome = title.verification.outcome = 'cover not proven';
  });
  assert.equal(check(files).verification_reports.present, 1);
});

test('accepts historical infinite PSNR values without changing quoted text or evidence bytes', () => {
  const files = reportFixture((report) => {
    report.checks[0].data.psnr = 'POSITIVE';
    report.checks[0].data.lower = 'NEGATIVE';
    report.checks[0].detail = 'Infinity \\" quoted -Infinity';
  }, (raw) => raw.replace('"POSITIVE"', 'Infinity').replace('"NEGATIVE"', '-Infinity'));
  assert.equal(check(files).verification_reports.present, 1);
  const bad = reportFixture((report) => { report.started_at = 'INFINITE'; },
    (raw) => raw.replace('"INFINITE"', 'Infinity'));
  assert.throws(() => check(bad), /passing report/);
  for (const invalid of ['1Infinity', 'Infinity0', '-Infinity0', 'NaN']) {
    const malformed = reportFixture((report) => { report.checks[0].data.psnr = 'INVALID'; },
      (raw) => raw.replace('"INVALID"', invalid));
    assert.throws(() => check(malformed), SyntaxError);
  }
});

test('report namespace refuses unknown attachments, nested paths and oversized input', () => {
  for (const name of ['reports/' + '0'.repeat(64) + '.json', 'reports/nested/report.json']) {
    const files = reportFixture();
    files.set(name, Buffer.from('{}'));
    assert.throws(() => check(files), /unreferenced verification report/);
  }
  const files = reportFixture();
  const name = [...files.keys()].find((name) => name.startsWith('reports/'));
  files.set(name, Buffer.alloc(4 * 1024 * 1024 + 1));
  assert.throws(() => check(files), /byte limit/);
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
  const document = JSON.parse(changed.get(manifest).toString());
  document.titles[0].title += ' (changed)';
  changed.set(manifest, Buffer.from(JSON.stringify(document)));
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

test('refuses build scripts outside the prepared namespace in a native package', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'calm-build-assets-'));
  const archive = path.join(directory, 'package.vpkg');
  const entries = [...fixture.entries()].map(([name, bytes]) => ({ name: 'assets/raw/prepared-library/' + name, bytes }));
  try {
    for (const name of [
      'assets/brand/make_logo.py',
      'assets/brand/render.sh',
      'assets/brand/render_qt.cpp',
      'assets/raw/sound/generate_menu_select.py',
      './assets/tools/build.PY',
    ]) {
      fs.writeFileSync(archive, tar([...entries, { name, bytes: Buffer.from('build tool, not runtime media') }]));
      assert.throws(() => checkPreparedPackage(archive), /Build-only source must not ship in assets/, name);
    }
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
