/** Actual notification callers and argument boundaries; never opens a desktop notification. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(app, 'package.json'));
const cli = createRequire(join(app, 'node_modules/react-native-tscodegen-types/node_modules/@react-native-community/cli/package.json'));
const notifier = cli('node-notifier');
const notifierRequire = createRequire(cli.resolve('node-notifier'));
const utils = notifierRequire('./lib/utils');

function parseArguments(args) {
  // Exercise actual POSIX quoting with harmless literal probes, a clean env,
  // and builtins only. No notifier or other desktop executable is launched.
  const child = spawnSync('/bin/sh', ['-c', 'set -- ' + args.join(' ') + '; printf "%s\\0" "$@"'],
    { encoding: 'utf8', env: { PATH: '/usr/bin:/bin' }, timeout: 1500, maxBuffer: 65536 });
  assert.equal(child.error, undefined);
  assert.equal(child.status, 0, child.stderr);
  return child.stdout.split('\0').slice(0, -1);
}

function captureLinux(t) {
  const calls = [];
  const options = notifier.options;
  notifier.options = { ...options, suppressOsdCheck: true };
  t.after(() => { notifier.options = options; });
  t.mock.method(utils, 'command', (binary, args, callback) => {
    assert.equal(binary, 'notify-send');
    calls.push(parseArguments(args));
    callback(null, '');
  });
  return calls;
}

test('the actual legacy CLI broadcasts a no-client notice without changing its protocol', t => {
  const calls = captureLinux(t);
  // The real server is never listened on: this exercises only the no-client path.
  const server = createServer();
  const messageSocket = cli('./build/commands/server/messageSocket').default;
  const channel = messageSocket.attachToServer(server, '/message');
  t.after(() => server.removeAllListeners());
  channel.broadcast('reload', {});
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], 'React Native: No apps connected');
  assert.match(calls[0][1], /^Sending 'reload' to all React Native apps failed\./);
  assert.deepEqual(messageSocket.parseMessage('{"version":2,"method":"reload"}', false),
    { version: 2, method: 'reload' });
});

test('actual Jest notification reporter retains success and failure text without running a watch loop', t => {
  const calls = captureLinux(t);
  const reporterRequire = createRequire(require.resolve('@jest/reporters'));
  assert.equal(reporterRequire('node-notifier'), notifier);
  const NotifyReporter = reporterRequire('./NotifyReporter').default;
  const reporter = new NotifyReporter({ rootDir: 'Fictional review', notifyMode: 'always' }, { firstRun: true });
  reporter.onRunComplete(new Set(), { numFailedTests: 0, numRuntimeErrorTestSuites: 0, numTotalTests: 2, numPassedTests: 2 });
  reporter.onRunComplete(new Set(), { numFailedTests: 1, numRuntimeErrorTestSuites: 0, numTotalTests: 2, numPassedTests: 1 });
  assert.match(calls[0][0], /100% Passed$/);
  assert.equal(calls[0][1], '2 tests passed');
  assert.match(calls[1][0], /50% Failed$/);
  assert.equal(calls[1][1], '1 of 2 tests failed');
});

test('Linux string and array options remain literal arguments, including shell metacharacters', t => {
  const calls = captureLinux(t);
  const payloads = ['Sea Otters', '$(printf CALM_PROBE)', '`printf CALM_PROBE`', '"; printf CALM_PROBE; #', 'name\\tail'];
  for (const message of [...payloads, payloads]) {
    notifier.notify({ title: 'Fictional review', message });
    const args = calls.at(-1);
    assert.equal(args[0], 'Fictional review');
    assert.equal(args[1], Array.isArray(message) ? message.join(',') : message);
    assert.ok(args.every(arg => typeof arg === 'string'), 'no shell operators or substitutions');
  }
});

test('the macOS backend keeps content and callbacks with its bounded default and unchanged binary', t => {
  const binary = notifierRequire.resolve('./vendor/mac.noindex/terminal-notifier.app/Contents/MacOS/terminal-notifier');
  assert.equal(createHash('sha256').update(readFileSync(binary)).digest('hex'),
    '2588f4ae2118396419767c388cf2b0a9a5e0cb53ce5d05a07c00f68a97a50215');
  t.mock.method(utils, 'isMountainLion', () => true);
  let seen;
  t.mock.method(utils, 'fileCommandJson', (file, args, callback) => {
    assert.equal(file, binary);
    seen = args;
    callback(null, { activationType: 'timeout' });
  });
  const mac = new notifier.NotificationCenter({ withFallback: true });
  let observed;
  const result = mac.notify({ title: 'Fictional review', message: 'Sea Otters', sound: false },
    (error, response) => { assert.equal(error, null); observed = response; });
  assert.equal(result, mac);
  assert.equal(observed, 'timeout');
  assert.deepEqual(seen, ['-title', '"Fictional review"', '-message', '"Sea Otters"',
    '-timeout', '"10"', '-json', '"true"']);
  // This is an argument/callback check, not macOS notification delivery acceptance.
});

test('the fixed notifier UUID consumer keeps unique v4 pipe names without creating an OS pipe', async t => {
  assert.equal(notifierRequire('./package.json').version, '8.0.2');
  assert.equal(notifierRequire('uuid/package.json').version, '11.1.1');
  const names = [];
  t.mock.method(utils, 'isWin8', () => true);
  t.mock.method(utils, 'createNamedPipe', async server => { names.push(server.namedPipe); return Buffer.alloc(0); });
  t.mock.method(utils, 'fileCommand', (_file, _args, callback) => callback(null));
  for (let i = 0; i < 2; i++) {
    await new Promise((resolve, reject) => {
      new notifier.WindowsToaster({ withFallback: false }).notify({ title: 'Fictional', message: 'Fixture' },
        error => error ? reject(error) : resolve());
    });
  }
  assert.equal(names.length, 2);
  assert.notEqual(names[0], names[1]);
  for (const name of names) assert.match(name, /^\\\\\.\\pipe\\notifierPipe-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
});
