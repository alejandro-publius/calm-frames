import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { checkNativeInputs, PLAYER_INPUTS } from './check_native_inputs.mjs';
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'calm-native-inputs-'));
  t.after(() => fs.rmSync(root, { recursive: true }));
  return root;
}
function write(root, name, text) {
  const file = path.join(root, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, text);
}
test('a headless-only checkout gets actionable missing-runtime instructions', t => {
  const root = fixture(t);
  write(root, 'node_modules/@amazon-devices/kepler-cli-platform/package.json', '{}');
  const result = checkNativeInputs(root, '22.23.2');
  assert.equal(result.nativeInputs, 'blocked'); assert.deepEqual(result.missing, PLAYER_INPUTS);
  assert.match(result.problems.join(' '), /npm run setup:player/);
  assert.deepEqual(fs.readdirSync(root), ['node_modules']);
});
test('incomplete dependencies and unsupported Node are reported together', t => {
  const result = checkNativeInputs(fixture(t), '20.0.0');
  assert.match(result.problems.join(' '), /Node 22/); assert.match(result.problems.join(' '), /npm ci/);
});
test('runtime syntax is checked without executing it and a partial repair still fails', t => {
  const root = fixture(t);
  write(root, 'node_modules/@amazon-devices/kepler-cli-platform/package.json', '{}');
  for (const name of PLAYER_INPUTS) write(root, name, 'throw new Error("must not execute");');
  assert.equal(checkNativeInputs(root, '22.23.2').nativeInputs, 'ready');
  write(root, PLAYER_INPUTS[0], 'not valid JavaScript {');
  assert.match(checkNativeInputs(root, '22.23.2').problems.join(' '), /syntax check/);
  fs.unlinkSync(path.join(root, PLAYER_INPUTS[1]));
  assert.deepEqual(checkNativeInputs(root, '22.23.2').missing, [PLAYER_INPUTS[1]]);
});
