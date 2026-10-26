/** Read-only summaries of existing approvals. No new signing or playback authority. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { checkApprovedCatalogs } from './approved_prepared_libraries.mjs';
import { checkPreparedDirectory, checkVerificationReport } from './check_prepared_library.mjs';
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PRESETS = ['wcag', 'broadcast', 'extra-cautious'];
const digest = (bytes, algorithm = 'sha256') => createHash(algorithm).update(bytes).digest('hex');
const need = (ok, message) => { if (!ok) throw new Error(message); };
const count = x => Number.isSafeInteger(x) && x >= 0 ? x : null;
const generator = value => value && typeof value.name === 'string' && typeof value.version === 'string' &&
  value.name.length > 0 && value.name.length <= 64 && value.version.length > 0 && value.version.length <= 64
  ? `${value.name} ${value.version}` : null;

/** Only called with catalog bytes checked against the existing approval registry. */
export function summarizeTitle(manifest, title, preset, reportBytes) {
  need(PRESETS.includes(preset), 'Unknown proof preset.');
  const report = checkVerificationReport(reportBytes, title.verification.reportSha256, [title]);
  const profiles = preset === 'wcag' ? ['wcag'] : ['wcag', 'broadcast'];
  const source = profiles.map(profile => {
    const map = JSON.parse(title.maps[profile].text);
    need(map.source.sha256 === title.sourceSha256 && Array.isArray(map.segments), 'Proof source differs from map.');
    need(digest(title.maps[profile].text) === title.maps[profile].sha256, 'Proof map bytes changed.');
    return { profile, mapSha256: title.maps[profile].sha256, findings: map.segments.length, analyzer: generator(map.generator) };
  });
  let output, frameCount = null, timingPreserved = false;
  if (report.recipe === 'baked-ambient-v1') {
    const proof = report.presets[preset];
    // Both profiles were measured even when the selected preset uses only WCAG.
    output = ['wcag', 'broadcast'].map(profile => {
      const analysis = JSON.parse(proof.outputAnalysis[profile].raw);
      return { profile, findings: count(analysis.segments.length), analyzer: generator(analysis.generator) };
    });
    frameCount = count(proof.timingAudio.frameCount);
    timingPreserved = proof.timingAudio.sourceEqualsOutput === true;
  } else {
    const clean = report.checks.find(check => check.name === `safe_rendition_clean:${preset}`);
    const timing = report.checks.find(check => check.name === `rendition_matches_source:${preset}`);
    // Historical reports record the preset check, not the output analyzer version.
    // Missing fields stay unknown; a passing check alone does not invent a number.
    output = [{ profile: preset, findings: count(clean?.data.violations), analyzer: null }];
    frameCount = count(timing?.data.rendition?.frame_count);
    timingPreserved = timing?.passed === true && frameCount !== null && frameCount === timing?.data.source?.frame_count;
  }
  return { version: 1, bundleId: manifest.bundleId, titleId: title.id, preset,
    sourceSha256: title.sourceSha256, renditionSha256: title.renditions[preset].sha256,
    durationMs: title.durationMs, renditionStartOffsetMs: title.renditions[preset].startOffsetMs,
    reportSha256: title.verification.reportSha256, checkedInputsSha256: title.verification.checkedInputsSha256,
    outcome: title.verification.outcome, source, output, frameCount, timingPreserved };
}

export function playbackProofModule(app = APP) {
  const approvals = checkApprovedCatalogs(app);
  const root = path.join(app, 'assets/raw/prepared-library');
  checkPreparedDirectory(root, { requireReports: true, requiredBundles: approvals.map(entry => entry.bundleId) });
  const registrations = [];
  for (const approval of approvals.filter(entry => entry.consumer)) {
    const manifest = JSON.parse(fs.readFileSync(path.join(root, approval.bundleId, 'manifest.json'), 'utf8'));
    for (const title of manifest.titles) {
      const bytes = fs.readFileSync(path.join(root, 'reports', `${title.verification.reportSha256}.json`));
      for (const preset of PRESETS) {
        const raw = JSON.stringify(summarizeTitle(manifest, title, preset, bytes));
        registrations.push({ raw, sha512: digest(raw, 'sha512') });
      }
    }
  }
  return '/** Generated from exact approved catalogs and checked reports. Never grants playback access. */\n' +
    `export const PLAYBACK_PROOF_RECORDS: readonly { raw: string; sha512: string }[] = ${JSON.stringify(registrations, null, 2)};\n`;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    need(process.argv.length === 3 && ['--write', '--check'].includes(process.argv[2]), 'Choose --write or --check.');
    const module = playbackProofModule(), target = path.join(APP, 'src/calmframes/approvedPlaybackProof.ts');
    if (process.argv[2] === '--write') {
      need(!fs.existsSync(target) || !fs.lstatSync(target).isSymbolicLink(), 'Generated proof cannot be a symlink.');
      fs.writeFileSync(target, module);
    }
    need(fs.readFileSync(target, 'utf8') === module, 'Playback proof differs from approved reports. Regenerate before building.');
    console.log('Playback proof reproduces from exact approved catalogs and reports.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
