import assert from 'node:assert/strict';
import { once } from 'node:events';
import { readFileSync } from 'node:fs';
import { Agent, createServer } from 'node:http';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const isoEntry = join(app, 'node_modules/isomorphic-fetch/fetch-npm-node.js');
const isoRequire = createRequire(isoEntry);
const fbEntry = join(app, 'node_modules/fbjs/lib/fetch.js');
const fbRequire = createRequire(fbEntry);

function runModule(file, context) {
  const module = { exports: {} };
  vm.runInNewContext(readFileSync(file, 'utf8'), { module, ...context }, { filename: file, timeout: 1000 });
  return module.exports;
}

function consumers(nativeFetch) {
  // Load the actual installed wrappers in an isolated global. The host's
  // built-in fetch must not hide the old polyfill path under test.
  const global = nativeFetch ? { fetch: nativeFetch } : {};
  const isoFetch = runModule(isoEntry, { global, require: isoRequire });
  const fetch = runModule(fbEntry, {
    global,
    require: name => name === 'isomorphic-fetch' ? isoFetch : fbRequire(name),
  });
  const withRetries = runModule(join(dirname(fbEntry), 'fetchWithRetries.js'), {
    process, setTimeout, clearTimeout,
    require: name => name === './fetch' ? fetch : fbRequire(name),
  });
  return { global, fetch, withRetries };
}

async function server(t, host) {
  const http = createServer(async (request, response) => {
    if (request.url.startsWith('/redirect?')) {
      response.writeHead(302, { Location: new URL(request.url, 'http://fixture').searchParams.get('to') });
      response.end();
      return;
    }
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    response.writeHead(request.url === '/unavailable' ? 503 : 200, {
      'Content-Type': 'application/json; charset=utf-8', 'X-Fixture': 'response',
    });
    response.end(JSON.stringify({ method: request.method, headers: request.headers, body: Buffer.concat(chunks).toString() }));
  });
  t.after(() => new Promise(resolve => {
    http.closeAllConnections();
    http.close(resolve);
  }));
  http.listen(0, host);
  await once(http, 'listening');
  return `http://${host}:${http.address().port}`;
}

const sensitive = {
  authorization: 'fixture-auth-only', cookie: 'fixture=only', cookie2: 'fixture2=only',
  'www-authenticate': 'fixture-challenge-only',
};

test('the unchanged isomorphic and FBJS consumers reuse the existing fixed CommonJS fetch', () => {
  assert.equal(isoRequire('./package.json').version, '2.2.1');
  assert.equal(fbRequire('../package.json').version, '1.0.0');
  assert.equal(isoRequire('node-fetch/package.json').version, '2.7.0');
  const modern = createRequire(join(app, 'package.json'));
  assert.equal(isoRequire.resolve('node-fetch'), modern.resolve('node-fetch'));
  assert.equal(typeof isoRequire('node-fetch'), 'function');
});

test('the actual fallback strips sensitive headers on a redirect to a different loopback host', { timeout: 4000 }, async t => {
  const loopback = await server(t, '127.0.0.1');
  const from = loopback.replace('127.0.0.1', 'calm-from.invalid');
  const to = loopback.replace('127.0.0.1', 'calm-to.invalid');
  // Two host identities, one owned loopback server. No external DNS/network or
  // platform-specific loopback alias is required on Linux or macOS.
  const agent = new Agent({
    lookup(hostname, options, callback) {
      assert.ok(['calm-from.invalid', 'calm-to.invalid'].includes(hostname));
      if (options.all) callback(null, [{ address: '127.0.0.1', family: 4 }]);
      else callback(null, '127.0.0.1', 4);
    },
  });
  t.after(() => agent.destroy());
  const { fetch } = consumers();
  const response = await fetch(`${from}/redirect?to=${encodeURIComponent(to + '/echo')}`, {
    headers: { ...sensitive, 'x-fixture': 'retained' }, timeout: 2000, agent,
  });
  const received = await response.json();
  for (const key of Object.keys(sensitive)) assert.equal(received.headers[key], undefined, key);
  assert.equal(received.headers['x-fixture'], 'retained');
  assert.equal(response.url, to + '/echo');
});

test('same-host redirects retain headers and convert POST to GET without retaining its body', { timeout: 4000 }, async t => {
  const url = await server(t, '127.0.0.1');
  const { fetch } = consumers();
  const response = await fetch(`${url}/redirect?to=${encodeURIComponent(url + '/echo')}`, {
    method: 'POST', body: 'fixture body', headers: sensitive, timeout: 2000,
  });
  const received = await response.json();
  for (const [key, value] of Object.entries(sensitive)) assert.equal(received.headers[key], value, key);
  assert.equal(received.method, 'GET');
  assert.equal(received.body, '');
  assert.equal(received.headers['content-length'], undefined);
});

test('the installed polyfill exports retain Headers, Request and cloned Response contracts', { timeout: 4000 }, async t => {
  const url = await server(t, '127.0.0.1');
  const { fetch, global: { Headers, Request, Response } } = consumers();
  const headers = new Headers({ 'Content-Type': 'application/json', 'X-Fixture': 'first' });
  assert.equal(headers.get('x-fixture'), 'first');
  headers.append('x-fixture', 'second');
  assert.equal(headers.has('X-Fixture'), true);
  const request = new Request(url + '/echo', { method: 'POST', headers, body: '{"fixture":"Cedar"}', timeout: 2000 });
  const response = await fetch(request);
  assert.ok(response instanceof Response);
  assert.equal(response.ok, true);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('X-Fixture'), 'response');
  const copy = response.clone();
  const data = await response.json();
  assert.equal(data.method, 'POST');
  assert.equal(data.headers['x-fixture'], 'first, second');
  assert.equal(data.body, '{"fixture":"Cedar"}');
  assert.equal(response.bodyUsed, true);
  assert.deepEqual(JSON.parse(await copy.text()), data);
  await assert.rejects(response.text(), /body used already/);
});

test('the actual FBJS retry wrapper preserves successful responses and its failed-response contract', { timeout: 4000 }, async t => {
  const url = await server(t, '127.0.0.1');
  const { withRetries } = consumers();
  const response = await withRetries(url + '/echo', { fetchTimeout: 2000, retryDelays: [], headers: { 'x-fixture': 'retry-wrapper' } });
  assert.equal((await response.json()).headers['x-fixture'], 'retry-wrapper');
  await assert.rejects(withRetries(url + '/unavailable', { fetchTimeout: 2000, retryDelays: [] }), error => {
    assert.match(error.message, /no successful response/);
    assert.equal(error.response.status, 503);
    return true;
  });
});

test('FBJS still prefers an existing native fetch implementation', async () => {
  const native = function (url) { return Promise.resolve({ url, bound: this.fetch === native }); };
  const { fetch, global } = consumers(native);
  assert.equal(global.fetch, native);
  assert.equal(global.Response, undefined);
  assert.deepEqual(await fetch('fixture://native'), { url: 'fixture://native', bound: true });
});
