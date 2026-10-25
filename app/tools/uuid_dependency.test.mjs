import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'node_modules/xcode/lib/pbxProject.js'));
const uuid = require('uuid');

test('v3 and v5 reject short output buffers instead of silently truncating a UUID', () => {
  for (const version of [uuid.v3 ?? require('uuid/v3'), uuid.v5 ?? require('uuid/v5')]) {
    assert.throws(() => version('fictional-fixture', version.DNS, Buffer.alloc(1)), RangeError);
    assert.throws(() => version('fictional-fixture', version.DNS, Buffer.alloc(16), 1), RangeError);
    const output = Buffer.alloc(16);
    version('fictional-fixture', version.DNS, output);
    assert.equal(output.equals(Buffer.alloc(16)), false);
  }
});

test('xcode stays on its existing version and its v4 IDs remain unique 24-character uppercase hex', () => {
  assert.equal(require('../package.json').version, '2.1.0');
  assert.equal(require('uuid/package.json').version, '11.1.1');
  const project = require('../').project('fictional.pbxproj');
  project.hash = { project: { objects: {} } };
  const values = Array.from({ length: 256 }, () => project.generateUuid());
  assert.equal(new Set(values).size, 256);
  for (const value of values) assert.match(value, /^[A-F0-9]{24}$/);
});

test('the actual project parser can add a group, serialize it and parse it again', t => {
  const dir = mkdtempSync(join(tmpdir(), 'calm-uuid-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const file = join(dir, 'fictional.pbxproj');
  writeFileSync(file, `// !$*UTF8*$!
{
 archiveVersion = 1;
 classes = {};
 objectVersion = 46;
 objects = {
/* Begin PBXProject section */
  AAAAAAAAAAAAAAAAAAAAAAAA = {isa = PBXProject; mainGroup = BBBBBBBBBBBBBBBBBBBBBBBB; targets = ();};
/* End PBXProject section */
/* Begin PBXGroup section */
  BBBBBBBBBBBBBBBBBBBBBBBB = {isa = PBXGroup; children = (); sourceTree = "<group>";};
/* End PBXGroup section */
 };
 rootObject = AAAAAAAAAAAAAAAAAAAAAAAA;
}
`);
  const project = require('../').project(file);
  project.parseSync();
  const group = project.addPbxGroup([], 'Fictional fixtures', 'Fixtures');
  assert.match(group.uuid, /^[A-F0-9]{24}$/);
  writeFileSync(file, project.writeSync());
  const reread = require('../').project(file);
  reread.parseSync();
  assert.equal(reread.hash.project.objects.PBXGroup[group.uuid].name, 'Fictional fixtures');
  assert.match(readFileSync(file, 'utf8'), /BBBBBBBBBBBBBBBBBBBBBBBB/);
});
