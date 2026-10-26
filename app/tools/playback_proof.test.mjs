import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { playbackProofModule, summarizeTitle } from './playback_proof.mjs';
const app = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.join(app, 'assets/raw/prepared-library');
const approvals = JSON.parse(fs.readFileSync(path.join(app, 'config/approved-prepared-libraries.json'))).catalogs;
const manifest = index => JSON.parse(fs.readFileSync(path.join(root, approvals[index].bundleId, 'manifest.json')));
const reportFor = title => fs.readFileSync(path.join(root, 'reports', `${title.verification.reportSha256}.json`));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

test('historical summaries retain exact measurements but private reports block new proof generation', () => {
  const stored = fs.readFileSync(path.join(app, 'src/calmframes/approvedPlaybackProof.ts'), 'utf8');
  const records = JSON.parse(/= (\[[\s\S]*\]);\n$/.exec(stored)[1]);
  const historical = approvals.flatMap((approval, index) => approval.consumer ?
    manifest(index).titles.flatMap(title => ['wcag', 'broadcast', 'extra-cautious'].map(preset => {
      const raw = JSON.stringify(summarizeTitle(manifest(index), title, preset, reportFor(title)));
      return { raw, sha512: createHash('sha512').update(raw).digest('hex') };
    })) : []);
  assert.deepEqual(historical, records);
  assert.equal(records.length, 12);
  assert.ok(!stored.includes('/Users/') && !stored.includes('PRIVATE KEY'));
  assert.throws(() => playbackProofModule(app), /local filesystem path/);
});

test('Acadia uses exact output-analysis measurements; McWay does not invent output versions or cover proof', () => {
  const acadia = manifest(0), mcway = manifest(3);
  const a = summarizeTitle(acadia, acadia.titles[0], 'wcag', reportFor(acadia.titles[0]));
  assert.deepEqual(a.output, [
    { profile: 'wcag', findings: 0, analyzer: 'flashmap 1.0.0' },
    { profile: 'broadcast', findings: 0, analyzer: 'flashmap 1.0.0' },
  ]);
  const m = summarizeTitle(mcway, mcway.titles[0], 'extra-cautious', reportFor(mcway.titles[0]));
  assert.equal(m.outcome, 'no flagged segments');
  assert.deepEqual(m.output, [{ profile: 'extra-cautious', findings: 0, analyzer: null }]);
  assert.equal(m.frameCount, 8991);
  assert.equal(m.timingPreserved, true);
});

test('absent measurements stay unknown, never zero or timing success', () => {
  const m = manifest(3), title = m.titles[0], report = JSON.parse(reportFor(title));
  delete report.checks.find(c => c.name === 'safe_rendition_clean:wcag').data.violations;
  delete report.checks.find(c => c.name === 'rendition_matches_source:wcag').data.rendition;
  const bytes = Buffer.from(JSON.stringify(report));
  // Synthetic report reference only in memory; no production approval is changed.
  title.verification.reportSha256 = sha(bytes);
  const proof = summarizeTitle(m, title, 'wcag', bytes);
  assert.equal(proof.output[0].findings, null);
  assert.equal(proof.frameCount, null);
  assert.equal(proof.timingPreserved, false);
});

for (const field of ['sourceSha256', 'renditionSha256', 'reportSha256', 'preset']) {
  test(`refuses a substituted ${field} before summarizing`, () => {
    const m = manifest(0), title = m.titles[0], bytes = reportFor(title);
    if (field === 'sourceSha256') title.sourceSha256 = 'f'.repeat(64);
    if (field === 'renditionSha256') title.renditions.wcag.sha256 = 'f'.repeat(64);
    if (field === 'reportSha256') title.verification.reportSha256 = 'f'.repeat(64);
    assert.throws(() => summarizeTitle(m, title, field === 'preset' ? 'unknown' : 'wcag', bytes));
  });
}

test('normal report and rendition substitution cannot bypass exact catalog approval', t => {
  const temp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'calm-proof-')));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  fs.mkdirSync(path.join(temp, 'config'), { recursive: true });
  fs.mkdirSync(path.join(temp, 'src/calmframes'), { recursive: true });
  fs.copyFileSync(path.join(app, 'config/approved-prepared-libraries.json'), path.join(temp, 'config/approved-prepared-libraries.json'));
  fs.copyFileSync(path.join(app, 'src/calmframes/approvedPreparedCatalogs.ts'), path.join(temp, 'src/calmframes/approvedPreparedCatalogs.ts'));
  // Only metadata is needed: the exact catalog gate must reject before any media read.
  for (const entry of approvals) {
    const dir = path.join(temp, 'assets/raw/prepared-library', entry.bundleId);
    fs.mkdirSync(dir, { recursive: true });
    fs.copyFileSync(path.join(root, entry.bundleId, 'manifest.json'), path.join(dir, 'manifest.json'));
  }
  const file = path.join(temp, 'assets/raw/prepared-library', approvals[3].bundleId, 'manifest.json');
  const original = fs.readFileSync(file, 'utf8');
  for (const field of ['rendition', 'report']) {
    const m = JSON.parse(original);
    if (field === 'rendition') m.titles[0].renditions.wcag.sha256 = 'a'.repeat(64);
    else m.titles[0].verification.reportSha256 = 'a'.repeat(64);
    fs.writeFileSync(file, JSON.stringify(m));
    assert.throws(() => playbackProofModule(temp), /Catalog differs from its exact approval/);
  }
});
