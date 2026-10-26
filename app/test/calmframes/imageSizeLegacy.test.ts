import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const appRoot = resolve(__dirname, '../..');
const metroEntry = join(appRoot, 'node_modules/react-native-tscodegen-types/node_modules/metro/src/Assets.js');
const legacyRequire = createRequire(metroEntry);
const runtimeFs = legacyRequire('node:fs') as typeof fs;
const imageSize = legacyRequire('image-size') as ((input: Buffer | string,
  callback?: (error: Error | null, dimensions?: { width: number; height: number }) => void)
  => { width: number; height: number }) & { types: string[] };
const svg = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="7" height="9"></svg>');

// The malformed header is bytes only. Never display or play generated fixtures.
const rejectedChild = String.raw`
  const fs = require('node:fs');
  const { join } = require('node:path');
  const imageSize = require(process.argv[1]);
  const input = Buffer.alloc(16);
  input.write('icns', 0); input.writeUInt32BE(16, 4); input.write('ic07', 8);
  const scratch = process.argv[3];
  const path = join(scratch, 'renamed.png');
  fs.writeFileSync(path, input);
  function finish(error) {
    if (!error || !/Invalid ICNS/.test(error.message)) process.exit(2);
    process.stdout.write('rejected');
  }
  if (process.argv[2] === 'callback') {
    imageSize(path, (error) => finish(error));
  } else {
    try { imageSize(process.argv[2] === 'buffer' ? input : path); finish(null); }
    catch (error) { finish(error); }
  }
`;

describe('patched image-size behind the legacy Metro API', () => {
  let scratch: string;
  beforeEach(() => { scratch = fs.mkdtempSync(join(tmpdir(), 'calm-image-size-test-')); });
  afterEach(() => { fs.rmSync(scratch, { recursive: true, force: true }); jest.restoreAllMocks(); });

  test('the installed parser is the exact official fixed version, not a renamed vulnerable copy', () => {
    const modern = JSON.parse(fs.readFileSync(join(appRoot, 'node_modules/image-size-modern/package.json'), 'utf8'));
    const adapter = JSON.parse(fs.readFileSync(join(appRoot, 'vendor/image-size-legacy/package.json'), 'utf8'));
    const manifest = JSON.parse(fs.readFileSync(join(appRoot, 'package.json'), 'utf8'));
    const lock = JSON.parse(fs.readFileSync(join(appRoot, 'package-lock.json'), 'utf8'));
    expect(modern).toMatchObject({ name: 'image-size', version: '2.0.4' });
    expect(adapter).toMatchObject({ name: '@calm-frames/image-size-legacy',
      peerDependencies: { 'image-size-modern': '2.0.4' } });
    expect(manifest.dependencies['image-size-modern']).toBe('npm:image-size@2.0.4');
    expect(manifest.overrides['metro@0.54.1']).toEqual({ 'image-size': '$image-size' });
    expect(legacyRequire.resolve('image-size')).toBe(join(appRoot, 'vendor/image-size-legacy/index.cjs'));
    for (const [path, component] of Object.entries(lock.packages) as [string,
      { name?: string; version?: string; link?: boolean }][]) {
      if (component.name === 'image-size' || /(?:^|\/)node_modules\/image-size$/.test(path)) {
        if (!component.link) expect(component.version).toBe('2.0.4');
      }
    }
  });

  test.each(['buffer', 'filename', 'callback'])('malformed ICNS terminates with an error through %s', (mode) => {
    const result = spawnSync(process.execPath, ['-e', rejectedChild, legacyRequire.resolve('image-size'), mode, scratch], {
      encoding: 'utf8', timeout: 1500, killSignal: 'SIGKILL',
    });
    // A timed-out child is a failed regression, never a successful rejection.
    expect(result.error).toBeUndefined();
    expect(result.signal).toBeNull();
    expect(result.status).toBe(0);
    expect(result.stdout).toBe('rejected');
  });

  test('legacy callers retain the callable Buffer and filename API', () => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, svg);
    expect(typeof imageSize).toBe('function');
    expect(imageSize(svg)).toMatchObject({ width: 7, height: 9 });
    expect(imageSize(path)).toMatchObject({ width: 7, height: 9 });
    expect(imageSize.types).toEqual(expect.arrayContaining(['png', 'jpg', 'svg', 'icns']));
  });

  test('callback success and parse errors are delivered once', async () => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, svg);
    const callback = jest.fn();
    await new Promise<void>((done) => imageSize(path, (error, dimensions) => {
      callback(error, dimensions); done();
    }));
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith(null, expect.objectContaining({ width: 7, height: 9 }));
    fs.writeFileSync(path, 'not an image');
    const failure = jest.fn();
    await new Promise<void>((done) => imageSize(path, (error) => { failure(error); done(); }));
    expect(failure).toHaveBeenCalledTimes(1);
    expect(failure.mock.calls[0][0]).toBeInstanceOf(Error);
  });

  test('synchronous file reads close descriptors after success and parser errors', () => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, svg);
    const close = jest.spyOn(runtimeFs, 'closeSync');
    expect(imageSize(path)).toMatchObject({ width: 7, height: 9 });
    expect(close).toHaveBeenCalledTimes(1);
    fs.writeFileSync(path, 'not an image');
    expect(() => imageSize(path)).toThrow();
    expect(close).toHaveBeenCalledTimes(2);
  });

  test.each(['stat', 'read'])('synchronous %s errors still close the descriptor', (failure) => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, svg);
    const close = jest.spyOn(runtimeFs, 'closeSync');
    const operation = failure === 'stat' ? 'fstatSync' : 'readSync';
    jest.spyOn(runtimeFs, operation).mockImplementationOnce(() => { throw new Error('forced I/O error'); });
    expect(() => imageSize(path)).toThrow('forced I/O error');
    expect(close).toHaveBeenCalledTimes(1);
  });

  test('synchronous reads are bounded and partial reads do not lose bytes', () => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, svg);
    const realRead = runtimeFs.readSync as unknown as (...args: unknown[]) => number;
    const read = jest.spyOn(runtimeFs, 'readSync').mockImplementation((...args: unknown[]) => {
      args[3] = Math.min(args[3] as number, 7);
      return realRead(...args);
    });
    expect(imageSize(path)).toMatchObject({ width: 7, height: 9 });
    expect(read.mock.calls.length).toBeGreaterThan(1);
    read.mockRestore();
    fs.appendFileSync(path, Buffer.alloc(1024 * 1024));
    const bounded = jest.spyOn(runtimeFs, 'readSync');
    expect(imageSize(path)).toMatchObject({ width: 7, height: 9 });
    for (const call of bounded.mock.calls) {
      expect((call[1] as Buffer).length).toBeLessThanOrEqual(512 * 1024);
    }
    expect(bounded).toHaveBeenCalledTimes(1);
  });

  test.each(['missing', 'empty', 'directory'])('callback %s failures are delivered once', async (kind) => {
    const path = join(scratch, 'input.svg');
    if (kind === 'empty') fs.writeFileSync(path, '');
    if (kind === 'directory') fs.mkdirSync(path);
    const callback = jest.fn();
    await new Promise<void>((done) => imageSize(path, (error) => { callback(error); done(); }));
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback.mock.calls[0][0]).toBeDefined();
  });

  test.each(['success', 'parse', 'stat', 'read'])('the upstream callback %s path closes its handle', async (kind) => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, kind === 'parse' ? 'not an image' : svg);
    const realOpen = runtimeFs.promises.open.bind(runtimeFs.promises);
    const close = jest.fn();
    jest.spyOn(runtimeFs.promises, 'open').mockImplementation(async (...args) => {
      const handle = await realOpen(...args);
      const realClose = handle.close.bind(handle);
      jest.spyOn(handle, 'close').mockImplementation(async () => { close(); await realClose(); });
      if (kind === 'stat') jest.spyOn(handle, 'stat').mockImplementationOnce(async () => { throw new Error('forced stat error'); });
      if (kind === 'read') jest.spyOn(handle, 'read').mockImplementationOnce(async () => { throw new Error('forced read error'); });
      return handle;
    });
    const callback = jest.fn();
    await new Promise<void>((done) => imageSize(path, (error, dimensions) => {
      callback(error, dimensions); done();
    }));
    expect(callback).toHaveBeenCalledTimes(1);
    if (kind === 'success') expect(callback.mock.calls[0][0]).toBeNull();
    else expect(callback.mock.calls[0][0]).toBeDefined();
    expect(close).toHaveBeenCalledTimes(1);
  });

  test.each([
    ['png', 'assets/raw/SplashScreenImages/_loop/loop000.png', 1920, 1080],
    ['jpg', 'src/assets/movie-content/tile01.jpg', 704, 408],
  ])('actual Metro retains %s asset dimensions', async (extension, asset, width, height) => {
    const path = join(scratch, `plain.${extension}`);
    fs.copyFileSync(join(appRoot, asset as string), path);
    expect(imageSize(path)).toMatchObject({ width, height });
    expect(imageSize(fs.readFileSync(path))).toMatchObject({ width, height });
    const assets = legacyRequire(metroEntry) as { getAssetData: (path: string, local: string,
      plugins: string[], platform: string | null, publicPath: string) => Promise<unknown> };
    await expect(assets.getAssetData(path, `plain.${extension}`, [], null, '/assets')).resolves.toMatchObject({
      width, height, type: extension, __packager_asset: true,
    });
  });

  test('the actual legacy Metro asset builder retains image dimensions', async () => {
    const path = join(scratch, 'plain.svg');
    fs.writeFileSync(path, svg);
    const assets = legacyRequire(metroEntry) as { getAssetData: (path: string, local: string,
      plugins: string[], platform: string | null, publicPath: string) => Promise<unknown> };
    await expect(assets.getAssetData(path, 'plain.svg', [], null, '/assets')).resolves.toMatchObject({
      width: 7, height: 9, type: 'svg', __packager_asset: true,
    });
  });
});
