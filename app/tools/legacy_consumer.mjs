/** Keep historical consumer probes, but require proof when their tool is removed. */
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
const app = dirname(dirname(fileURLToPath(import.meta.url)));
const lock = JSON.parse(readFileSync(join(app, 'package-lock.json')));

export function legacyConsumer(path) {
  if (lock.packages[path]) return true;
  test(`retired consumer stays absent from the lock and installed tree: ${path}`, () => {
    assert.equal(lock.packages[path], undefined);
    assert.equal(existsSync(join(app, path)), false);
  });
  return false;
}
