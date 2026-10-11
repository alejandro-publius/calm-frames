import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join } from 'node:path';
import { test } from 'node:test';
import { negativeControl } from './ui_flashmap.mjs';

// These fixtures contain marker bytes, never encoded or playable hazard media.
function fixture(t, change = () => {}) {
  const root = mkdtempSync(join(tmpdir(), 'ui-control-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const outputDir = join(root, 'build');
  const mediaRoot = join(root, 'media');
  mkdirSync(mediaRoot);
  writeFileSync(join(mediaRoot, 'unrelated.txt'), 'keep');
  const encoded = [];
  const options = {
    outputDir, mediaRoot,
    encodeFrames: async (_frames, path) => {
      encoded.push(path);
      writeFileSync(path, 'NOT A VIDEO');
      return 0;
    },
    checkVideo: (path, profile, reportPath) => {
      const passes = path.includes('pattern') && profile === 'wcag';
      const reason = profile === 'broadcast' ? 'pattern' : 'general';
      const report = { version: 1,
        source: { sha256: createHash('sha256').update(readFileSync(path)).digest('hex') },
        profile: { name: profile },
        segments: passes ? [] : [{ start_ms: 0, end_ms: 500, reason }],
        summary: { pass: passes, segment_count: passes ? 0 : 1,
          flash_pass: passes || reason === 'pattern', pattern_pass: passes || reason !== 'pattern' },
      };
      const result = { status: passes ? 0 : 1,
        output: passes ? `PASS ${path}: below the ${profile} thresholds\n` :
          `FAIL ${path}: 1 segment(s) over the thresholds\n` };
      change({ result, report, path, profile });
      if (reportPath && !result.noReport) writeFileSync(reportPath, result.malformed ? '{' : JSON.stringify(report));
      return result;
    },
  };
  return { options, encoded, root, outputDir, mediaRoot };
}

test('measured controls pass and remove only their HAZARD_ scratch files', async (t) => {
  const f = fixture(t);
  assert.equal(await negativeControl(f.options), 0);
  assert.equal(f.encoded.length, 2);
  for (const path of f.encoded) {
    assert.match(basename(path), /^HAZARD_/);
    assert.equal(dirname(dirname(path)), f.mediaRoot);
    assert.equal(existsSync(path), false);
  }
  assert.deepEqual(readdirSync(f.mediaRoot), ['unrelated.txt']);
  const saved = JSON.parse(readFileSync(join(f.outputDir, 'ui-flashmap-negative-control.json')));
  assert.equal(Object.values(saved.verdicts).every(Boolean), true);
});

for (const failure of ['error exit', 'spawn error', 'signal', 'missing report', 'malformed report',
  'wrong source', 'wrong profile', 'wrong reason', 'no finding', 'passing report', 'missing refusal']) {
  test(`analyzer ${failure} cannot count as a measured hazard and is cleaned up`, async (t) => {
    const f = fixture(t, ({ result, report, path }) => {
      if (!basename(path).includes('flash')) return;
      if (failure === 'error exit') result.status = 2;
      if (failure === 'spawn error') { result.status = null; result.error = new Error('spawn failed'); }
      if (failure === 'signal') { result.status = null; result.signal = 'SIGTERM'; }
      if (failure === 'missing report') result.noReport = true;
      if (failure === 'malformed report') result.malformed = true;
      if (failure === 'wrong source') report.source.sha256 = '0'.repeat(64);
      if (failure === 'wrong profile') report.profile.name = 'broadcast';
      if (failure === 'wrong reason') report.segments[0].reason = 'pattern';
      if (failure === 'no finding') report.segments = [];
      if (failure === 'passing report') report.summary.pass = true;
      if (failure === 'missing refusal') result.output = 'Traceback: analyzer crashed';
    });
    assert.notEqual(await negativeControl(f.options), 0);
    assert.equal(f.encoded.every((path) => !existsSync(path)), true);
    assert.deepEqual(readdirSync(f.mediaRoot), ['unrelated.txt']);
  });
}

for (const failure of ['encoder exit', 'encoder throw', 'analyzer throw', 'report write']) {
  test(`partial fixtures are deleted after ${failure}`, async (t) => {
    const f = fixture(t);
    const encodeFrames = f.options.encodeFrames;
    let count = 0;
    f.options.encodeFrames = async (...args) => {
      await encodeFrames(...args);
      count += 1;
      if (count === 2 && failure === 'encoder exit') return 2;
      if (count === 2 && failure === 'encoder throw') throw new Error('encoder failed');
      return 0;
    };
    if (failure === 'analyzer throw') f.options.checkVideo = () => { throw new Error('check failed'); };
    if (failure === 'report write') {
      mkdirSync(join(f.outputDir, 'ui-flashmap-negative-control.json'), { recursive: true });
    }
    if (failure === 'encoder exit') assert.equal(await negativeControl(f.options), 2);
    else await assert.rejects(negativeControl(f.options));
    assert.equal(f.encoded.every((path) => !existsSync(path)), true);
    assert.deepEqual(readdirSync(f.mediaRoot), ['unrelated.txt']);
  });
}
