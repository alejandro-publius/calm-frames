/**
 * Tests for the measurement run config.
 *
 * Every assertion here was seen to fail: each rule was broken on purpose in
 * harnessConfig.ts and the suite went red before the file was restored.
 */
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
