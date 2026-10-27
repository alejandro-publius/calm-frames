import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const consumer = join(app, 'node_modules',
  '@react-native-community/cli-platform-android/build/commands/logAndroid/index.js');
const legacyRequire = createRequire(consumer);
const adbFile = legacyRequire.resolve('logkitty/build/android/adb.js');
const adbRequire = createRequire(adbFile);

function loadAdb({ output = Buffer.from('1234\n'), fail } = {}) {
  const calls = [];
  const child = { fixture: 'logging process' };
  const childProcess = {};
  for (const name of ['execSync', 'execFileSync', 'spawn']) {
    childProcess[name] = (...args) => {
      calls.push({ name, args: JSON.parse(JSON.stringify(args)) });
      if (fail === name) throw new Error('fixture process failure');
      return name === 'spawn' ? child : output;
    };
  }
  const exports = {};
  vm.runInNewContext(readFileSync(adbFile, 'utf8'), {
    exports,
    process: { env: {} },
    require: name => name === 'child_process' ? childProcess : adbRequire(name),
  }, { filename: adbFile, timeout: 1000 });
  return { api: exports, calls, child };
}

test('the current CLI resolves the fixed logger without upgrading the CLI', () => {
  assert.equal(legacyRequire('../../../package.json').version, '20.2.0');
  assert.equal(legacyRequire('logkitty/package.json').version, '0.7.1');
  const lock = JSON.parse(readFileSync(join(app, 'package-lock.json'), 'utf8'));
  for (const [path, item] of Object.entries(lock.packages)) {
    if (path.endsWith('node_modules/logkitty')) assert.equal(item.version, '0.7.1', path);
  }
});

test('buffer cleanup keeps an executable path literal and never starts a host shell', () => {
  const { api, calls, child } = loadAdb();
  const executable = '/tmp/fixture SDK; literal/platform-tools/adb';
  assert.equal(api.spawnLogcatProcess(executable), child);
  assert.deepEqual(calls, [
    { name: 'execFileSync', args: [executable, ['logcat', '-c']] },
    { name: 'spawn', args: [executable, ['logcat', '-v', 'time', 'process', 'tag'], { stdio: 'pipe' }] },
  ]);
});

test('PID lookup passes the application identifier as one argument without host-shell interpolation', () => {
  const { api, calls } = loadAdb();
  const executable = '/tmp/fixture SDK/platform-tools/adb';
  const identifier = 'io.example.fixture; literal';
  assert.equal(api.getApplicationPid(identifier, executable), 1234);
  assert.deepEqual(calls, [{ name: 'execFileSync', args: [resolve(executable), ['shell', 'pidof', '-s', identifier]] }]);
});

test('the logger preserves specific process and unparsable-PID errors', () => {
  const errors = adbRequire('../errors');
  let loaded = loadAdb({ fail: 'execFileSync' });
  assert.throws(() => loaded.api.spawnLogcatProcess('/tmp/fixture-adb'),
    error => error.code === errors.ERR_ANDROID_CANNOT_CLEAN_LOGCAT_BUFFER);
  assert.throws(() => loaded.api.getApplicationPid('io.example.fixture', '/tmp/fixture-adb'),
    error => error.code === errors.ERR_ANDROID_CANNOT_GET_APP_PID);
  loaded = loadAdb({ fail: 'spawn' });
  assert.throws(() => loaded.api.spawnLogcatProcess('/tmp/fixture-adb'),
    error => error.code === errors.ERR_ANDROID_CANNOT_START_LOGCAT);
  for (const output of [Buffer.from('not a pid'), Buffer.alloc(0)]) {
    const { api } = loadAdb({ output });
    assert.throws(() => api.getApplicationPid('io.example.fixture', '/tmp/fixture-adb'),
      error => error.code === errors.ERR_ANDROID_UNPROCESSABLE_PID);
  }
});

test('the actual current CLI retains React Native tag filtering and formatted events', async () => {
  const api = legacyRequire('logkitty');
  const emitter = new EventEmitter();
  const started = [];
  const printed = [];
  const exports = {};
  vm.runInNewContext(readFileSync(consumer, 'utf8'), {
    exports,
    require(name) {
      if (name === 'logkitty') return { ...api, logkitty(options) { started.push(options); return emitter; } };
      if (name === '@react-native-community/cli-tools') {
        return { logger: { info: text => printed.push(text), log: text => printed.push(text) } };
      }
      return legacyRequire(name);
    },
  }, { filename: consumer, timeout: 1000 });
  await exports.default.func();
  assert.equal(exports.default.name, 'log-android');
  assert.equal(started.length, 1);
  const options = started[0];
  assert.equal(options.platform, 'android');
  assert.equal(options.priority, api.AndroidPriority.VERBOSE);
  const filter = options.filter(options.platform, options.priority);
  const entry = {
    platform: 'android', pid: 1234, priority: api.AndroidPriority.INFO,
    tag: 'ReactNativeJS', messages: ['fixture message'],
    date: { format: () => '12:34:56' },
  };
  assert.equal(filter.shouldInclude(entry), true);
  assert.equal(filter.shouldInclude({ ...entry, tag: 'ReactNative' }), true);
  assert.equal(filter.shouldInclude({ ...entry, tag: 'Other' }), false);
  assert.equal(filter.shouldInclude({ ...entry, priority: 0 }), false);
  emitter.emit('entry', entry);
  emitter.emit('error', new Error('fixture failure'));
  assert.ok(printed.some(text => text.includes('ReactNativeJS') && text.includes('fixture message')));
  assert.ok(printed.some(text => text.includes('fixture failure')));
});
