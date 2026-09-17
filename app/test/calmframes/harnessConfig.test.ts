/**
 * Tests for the measurement run config.
 *
 * Every assertion here was seen to fail: each rule was broken on purpose in
 * harnessConfig.ts and the suite went red before the file was restored.
 */
// jest.setup.ts replaces this module so no test reaches for a run. These
// tests are about the real one.
jest.unmock('../../src/calmframes/harnessConfig');

import { parseHarnessConfig } from '../../src/calmframes/harnessConfig';

describe('parseHarnessConfig', () => {
  it('accepts a layering run', () => {
    const config = parseHarnessConfig(
      JSON.stringify({ mode: 'layering', toggleEveryMs: 5000 }),
    );
    expect(config).toEqual({ mode: 'layering', toggleEveryMs: 5000 });
  });

  it('accepts a timing run with a schedule', () => {
    const config = parseHarnessConfig(
      JSON.stringify({
        mode: 'timing',
        guardBandMs: 500,
        scheduleLabel: 'calm-timing markers v1',
        segments: [{ startMs: 1000, endMs: 2000 }],
        referencePatch: { x: 1, y: 2, width: 3, height: 4 },
      }),
    );
    expect(config?.mode).toBe('timing');
    expect(config?.segments).toHaveLength(1);
    expect(config?.segments?.[0].reason).toBe('general');
    expect(config?.referencePatch).toEqual({ x: 1, y: 2, width: 3, height: 4 });
    expect(config?.scheduleLabel).toBe('calm-timing markers v1');
  });

  it('keeps a red segment red', () => {
    const config = parseHarnessConfig(
      JSON.stringify({
        mode: 'timing',
        segments: [{ startMs: 1000, endMs: 2000, reason: 'red' }],
      }),
    );
    expect(config?.segments?.[0].reason).toBe('red');
  });

  it('refuses a timing run with no schedule, which would measure nothing', () => {
    expect(parseHarnessConfig(JSON.stringify({ mode: 'timing' }))).toBeNull();
    expect(
      parseHarnessConfig(JSON.stringify({ mode: 'timing', segments: [] })),
    ).toBeNull();
  });

  it('refuses an unknown mode', () => {
    expect(parseHarnessConfig(JSON.stringify({ mode: 'everything' }))).toBeNull();
    expect(parseHarnessConfig(JSON.stringify({}))).toBeNull();
  });

  it('refuses text that is not JSON', () => {
    expect(parseHarnessConfig('not json at all')).toBeNull();
  });

  it('refuses segments that are not numbers', () => {
    expect(
      parseHarnessConfig(
        JSON.stringify({
          mode: 'timing',
          segments: [{ startMs: 'soon', endMs: 2000 }],
        }),
      ),
    ).toBeNull();
  });

  it('refuses a segment that ends before it starts', () => {
    expect(
      parseHarnessConfig(
        JSON.stringify({
          mode: 'timing',
          segments: [{ startMs: 5000, endMs: 4000 }],
        }),
      ),
    ).toBeNull();
  });

  it('refuses a negative guard band and keeps the run', () => {
    const config = parseHarnessConfig(
      JSON.stringify({
        mode: 'timing',
        guardBandMs: -10,
        segments: [{ startMs: 1000, endMs: 2000 }],
      }),
    );
    expect(config).not.toBeNull();
    expect(config?.guardBandMs).toBeUndefined();
  });

  it('ignores an incomplete reference patch', () => {
    const config = parseHarnessConfig(
      JSON.stringify({
        mode: 'layering',
        referencePatch: { x: 1, y: 2 },
      }),
    );
    expect(config?.referencePatch).toBeUndefined();
  });
});

describe('readHarnessConfig', () => {
  const RUN = { mode: 'layering', toggleEveryMs: 5000 };

  afterEach(() => {
    jest.resetModules();
    jest.restoreAllMocks();
  });

  function loadWith(entries: string[], fileBody?: string) {
    jest.resetModules();
    jest.doMock('@amazon-devices/kepler-file-system', () => ({
      KeplerFileSystem: {
        getEntries: jest.fn().mockResolvedValue(entries),
        readFileAsString: jest.fn().mockResolvedValue(fileBody ?? ''),
      },
    }));
    // require, not import: this jest setup runs without VM modules.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require('../../src/calmframes/harnessConfig');
  }

  it('asks the network when the device has no run file', async () => {
    // On OS 1.2 nothing can put a file in the app's data directory from the
    // host, so falling through to the network is the only path that works.
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify(RUN),
    });
    (global as any).fetch = fetchMock;
    (global as any).__DEV__ = true;

    const module = loadWith([]);
    const config = await module.readHarnessConfig();

    expect(fetchMock).toHaveBeenCalledWith(
      module.HARNESS_CONFIG_URL,
      expect.anything(),
    );
    expect(config?.mode).toBe('layering');
  });

  it('prefers a run file on the device over the network', async () => {
    const fetchMock = jest.fn();
    (global as any).fetch = fetchMock;
    (global as any).__DEV__ = true;

    const module = loadWith(
      ['calm-frames-harness.json'],
      JSON.stringify({ mode: 'timing', segments: [{ startMs: 1, endMs: 2 }] }),
    );
    const config = await module.readHarnessConfig();

    expect(config?.mode).toBe('timing');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('never asks the network in a release build', async () => {
    const fetchMock = jest.fn();
    (global as any).fetch = fetchMock;
    (global as any).__DEV__ = false;

    const module = loadWith([]);
    const config = await module.readHarnessConfig();

    expect(config).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
