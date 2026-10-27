import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import { legacyConsumer } from './legacy_consumer.mjs';

if (legacyConsumer('node_modules/external-editor')) {
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'node_modules/external-editor/main/index.js'));
const tmp = require('tmp');

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'calm-tmp-'));
  const base = join(root, 'base');
  const outside = join(root, 'outside');
  mkdirSync(base);
  mkdirSync(outside);
  t.after(() => rmSync(root, { recursive: true, force: true }));
  return { base, outside };
}

test('only the unchanged legacy editor receives the fixed temporary-file dependency', () => {
  assert.equal(require('../package.json').version, '2.2.0');
  assert.equal(require('tmp/package.json').version, '0.2.7');
});

test('temporary names reject a symlink outside their configured base', t => {
  const { base, outside } = fixture(t);
  const link = join(base, 'escape');
  symlinkSync(outside, link, 'dir');
  // Request a name only: no file is created through the escaping path, even
  // when this regression runs against the old vulnerable dependency.
  assert.throws(() => tmp.tmpNameSync({ tmpdir: base, dir: link }), /relative/);
});

for (const [option, value] of [['prefix', '../escaped'], ['postfix', '/../../escaped']]) {
  test(`temporary names reject traversal in ${option}`, t => {
    const { base } = fixture(t);
    assert.throws(() => tmp.tmpNameSync({ tmpdir: base, dir: base, [option]: value }), /Relative value not allowed/);
  });
  test(`temporary names reject a non-string traversal bypass in ${option}`, t => {
    const { base } = fixture(t);
    for (const nonString of [[value], { includes: () => false, toString: () => value }]) {
      assert.throws(() => tmp.tmpNameSync({ tmpdir: base, dir: base, [option]: nonString }), /string/);
    }
  });
}

test('temporary-file mode, cleanup and the actual editor text round trip are retained', t => {
  const { base } = fixture(t);
  const file = tmp.fileSync({ tmpdir: base, dir: base, prefix: 'fixture', postfix: '.txt' });
  try {
    assert.equal(statSync(file.name).mode & 0o777, 0o600);
    writeFileSync(file.fd, 'Fictional fixture only');
    assert.equal(readFileSync(file.name, 'utf8'), 'Fictional fixture only');
  } finally {
    file.removeCallback();
  }
  assert.equal(existsSync(file.name), false);

  const ExternalEditor = require('./index.js');
  // Construction and file I/O exercise the installed consumer. Never call
  // run/runAsync: no configured editor or child process may be launched.
  const editor = new ExternalEditor('Fictional Cedar\nA quiet place');
  try {
    assert.equal(readFileSync(editor.temp_file, 'utf8'), 'Fictional Cedar\nA quiet place');
    writeFileSync(editor.temp_file, 'Fictional Willow\nA different place', 'utf8');
    editor.readTemporaryFile();
    assert.equal(editor.text, 'Fictional Willow\nA different place');
  } finally {
    editor.cleanup();
  }
  assert.equal(existsSync(editor.temp_file), false);
});

}
