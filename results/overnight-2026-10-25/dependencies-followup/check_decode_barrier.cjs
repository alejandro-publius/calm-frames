const assert = require('node:assert/strict');
const fs = require('node:fs');
const {createRequire} = require('node:module');
const {resolve} = require('node:path');
const vm = require('node:vm');
assert.ok(process.argv[2] && process.argv[3], 'Usage: node check_decode_barrier.cjs <checkout> <extracted-decode-0.5.1/index.js>');
const entry = resolve(process.argv[2], 'app/node_modules/query-string/index.js');
const localRequire = createRequire(entry);
const fixed = localRequire(resolve(process.argv[3]));
const source = fs.readFileSync(entry, 'utf8');
function load(replace) {
  const module = {exports: {}};
  vm.runInNewContext(source, {
    module, exports: module.exports, Buffer,
    require: name => name === 'decode-uri-component' && replace ? fixed : localRequire(name),
  }, {filename: entry, timeout: 1000});
  return module.exports;
}
assert.equal(load(false).parse('scene=Sequoia%20Trail').scene, 'Sequoia Trail');
assert.equal(typeof fixed.default, 'function');
let message;
try {
  load(true).parse('scene=Sequoia%20Trail');
  assert.fail('Expected the actual CommonJS consumer to reject the module namespace');
} catch (error) {
  assert.equal(error.name, 'TypeError');
  assert.match(error.message, /decodeComponent is not a function/);
  message = error.message;
}
console.log(JSON.stringify({
  consumer: 'query-string 7.1.3', installed_decode: '0.2.2', proposed_decode: '0.5.1',
  ordinary_parse_before: 'passed', proposed_override: 'rejected', error: message,
  scope: 'Actual consumer in an isolated VM; no installed dependency changed or external request made.',
}, null, 2));
