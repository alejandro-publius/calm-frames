import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { readFileSync } from 'node:fs';
import http from 'node:http';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { deflateSync, gzipSync } from 'node:zlib';

const file = fileURLToPath(import.meta.url);
const app = dirname(dirname(file));
const consumer = join(app, 'node_modules/@react-native-community/cli-server-api/build/openStackFrameMiddleware.js');
const cliRequire = createRequire(consumer);
const bodyParser = cliRequire('body-parser');

function stackFrameMiddleware() {
  const exports = {};
  const opened = [];
  vm.runInNewContext(readFileSync(consumer, 'utf8'), {
    exports,
    require(name) {
      if (name === '@react-native-community/cli-tools') {
        // Exercise the actual middleware without opening an editor or process.
        return { launchEditor: (...args) => opened.push(args) };
      }
      return cliRequire(name);
    },
  }, { filename: consumer, timeout: 1000 });
  return { middleware: exports.default({}), opened };
}

async function listen(handler) {
  const server = http.createServer(handler);
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  return server;
}

function close(server) {
  server.closeAllConnections();
  return new Promise(resolve => server.close(resolve));
}

function request(server, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request({
      host: '127.0.0.1', port: server.address().port, method: 'POST', agent: false,
      headers: { 'Content-Type': 'application/json', 'Content-Length': body.length, ...headers },
    }, res => {
      let text = '';
      res.setEncoding('utf8');
      res.on('data', chunk => { text += chunk; });
      res.on('error', reject);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, text }));
    });
    req.on('error', reject);
    req.setTimeout(1500, () => req.destroy(new Error('fixture request timed out')));
    req.end(body);
  });
}

async function compressedChild() {
  const { middleware, opened } = stackFrameMiddleware();
  const server = await listen(middleware);
  try {
    const frame = Buffer.from(JSON.stringify({ file: 'fixture.ts', lineNumber: 7 }));
    const encoded = Buffer.concat([gzipSync(frame), Buffer.from([0]), Buffer.alloc(100 * 1024, 0x58)]);
    const response = await request(server, encoded, { 'Content-Encoding': 'gzip' });
    assert.equal(response.status, 200);
    // The old decoder throws after the successful response. Give the bounded
    // local stream time to deliver its trailing data, then prove service health.
    await new Promise(resolve => setTimeout(resolve, 200));
    const next = await request(server, frame);
    assert.equal(next.status, 200);
    assert.deepEqual(opened, [['fixture.ts', 7], ['fixture.ts', 7]]);
  } finally {
    await close(server);
  }
}

if (process.argv.includes('--compressed-child')) {
  await compressedChild();
} else {
  test('the CLI keeps its version and resolves a body parser within its declared major', () => {
    assert.equal(cliRequire('../package.json').version, '20.2.0');
    assert.equal(cliRequire('../package.json').dependencies['body-parser'], '^2.2.2');
    assert.equal(cliRequire('body-parser/package.json').version, '2.4.0');
  });

  test('the actual CLI middleware survives trailing compressed bytes and serves the next request', () => {
    const result = spawnSync(process.execPath, [file, '--compressed-child'], {
      encoding: 'utf8', timeout: 5000, maxBuffer: 64 * 1024,
    });
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(result.status, 0, result.stderr || 'bounded decoder child did not finish');
  });

  test('the actual CLI retains plain/compressed JSON and rejects malformed JSON without opening an editor', async () => {
    const { middleware, opened } = stackFrameMiddleware();
    const server = await listen((req, res) => middleware(req, res, error => {
      res.statusCode = error?.status || 404;
      res.end(error?.type || 'not found');
    }));
    try {
      const frame = Buffer.from(JSON.stringify({ file: 'fixture.ts', lineNumber: 9 }));
      assert.equal((await request(server, frame)).status, 200);
      assert.equal((await request(server, gzipSync(frame), { 'Content-Encoding': 'gzip' })).status, 200);
      const invalid = await request(server, Buffer.from('{invalid'));
      assert.equal(invalid.status, 400);
      assert.equal(invalid.text, 'entity.parse.failed');
      assert.deepEqual(opened, [['fixture.ts', 9], ['fixture.ts', 9]]);
    } finally {
      await close(server);
    }
  });

  test('decompression completion preserves a second raw-body consumer and drains the whole request', async () => {
    const first = Buffer.concat([deflateSync(Buffer.from('{"fixture":true}')), Buffer.from([0])]);
    const trailing = Buffer.alloc(1024);
    const expectedHash = createHash('sha256').update(first).update(trailing).digest('hex');
    const parser = bodyParser.json();
    let client;
    const server = await listen((req, res) => {
      const hash = createHash('sha256');
      req.pipe(hash);
      parser(req, res, error => {
        if (error) { res.statusCode = error.status; res.end(error.type); return; }
        hash.once('finish', () => {
          res.setHeader('X-Body-SHA256', hash.digest('hex'));
          res.end(JSON.stringify(req.body));
        });
        client.end(trailing);
      });
    });
    try {
      const response = await new Promise((resolve, reject) => {
        client = http.request({
          host: '127.0.0.1', port: server.address().port, method: 'POST', agent: false,
          headers: { 'Content-Type': 'application/json', 'Content-Encoding': 'deflate', 'Content-Length': first.length + trailing.length },
        }, res => {
          let text = '';
          res.setEncoding('utf8');
          res.on('data', chunk => { text += chunk; });
          res.on('error', reject);
          res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, text }));
        });
        client.on('error', reject);
        client.setTimeout(1500, () => client.destroy(new Error('raw-body consumer did not finish')));
        client.write(first);
      });
      assert.equal(response.status, 200);
      assert.equal(response.text, '{"fixture":true}');
      assert.equal(response.headers['x-body-sha256'], expectedHash);
    } finally {
      client?.destroy();
      await close(server);
    }
  });
}
