/** Exact-byte build gate. Python preparation verifies media; this checks delivery. */
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkAmbientReport } from './ambient_report.mjs';
import { checkApprovedCatalogs } from './approved_prepared_libraries.mjs';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PREFIX = 'assets/raw/prepared-library/';
const SHA = /^[0-9a-f]{64}$/;
const ASSET = /^titles\/[0-9a-f]{64}\/(wcag|broadcast|extra-cautious)\.(mp4|json|vtt)$/;
const MAX_BYTES = 128 * 1024 * 1024;
const MAX_JSON = 16 * 1024 * 1024;
const MAX_REPORT = 4 * 1024 * 1024;
const PRESETS = ['wcag', 'broadcast', 'extra-cautious'];
const CORE_CHECKS = ['map_hash', 'map_signature', 'plan_matches_map', 'safe_rendition_clean',
  'rendition_matches_source', 'cover_proof', 'cover_model_clean', 'hls_rendition_clean', 'hls_timing_matches_master'];
const OUTCOMES = ['no flagged segments', 'cover proven drawn', 'cover not proven'];
// These are developer inputs, never runtime artwork, audio or prepared catalogs.
const BUILD_SOURCE = /\.(?:py|pyc|pyo|pyw|sh|bash|zsh|c|cc|cpp|cxx|h|hpp)$/i;
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');

function requireThat(value, message) {
  if (!value) throw new Error(message);
}

export function checkRuntimeAssetNames(names) {
  for (const name of names) {
    const canonical = path.posix.normalize('/' + name).slice(1);
    requireThat(!canonical.startsWith('assets/') || !BUILD_SOURCE.test(canonical),
      `Build-only source must not ship in assets: ${name}`);
  }
}

/** Check asset paths without executing generators or reading media bytes. */
export function checkRuntimeAssetDirectory(root = path.join(APP, 'assets')) {
  // Ancestor aliases (for example macOS /tmp) do not make the asset root a link.
  // Normalize trailing separators before lstat so a linked root cannot hide one.
  const assetRoot = path.resolve(root);
  const rootStat = fs.lstatSync(assetRoot);
  requireThat(!rootStat.isSymbolicLink(), 'Asset root must not be a symlink.');
  requireThat(rootStat.isDirectory(), 'Asset root must be a directory.');
  const names = [];
  const walk = (directory, prefix) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const name = prefix + entry.name;
      requireThat(!entry.isSymbolicLink(), 'Runtime assets must not be symlinks.');
      if (entry.isDirectory()) walk(path.join(directory, entry.name), name + '/');
      else {
        requireThat(entry.isFile(), 'Runtime assets must be regular files.');
        names.push(name);
      }
    }
  };
  walk(assetRoot, 'assets/');
  checkRuntimeAssetNames(names);
  return { files: names.length, build_sources: 'excluded' };
}

function record(value) {
  requireThat(value && typeof value === 'object' && !Array.isArray(value), 'Invalid prepared metadata.');
  return value;
}

function exactKeys(value, keys) {
  return Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
}

function verificationReference(title) {
  record(title);
  const value = record(title.verification);
  requireThat(exactKeys(value, ['reportSha256', 'checkedInputsSha256', 'outcome']) &&
    typeof value.reportSha256 === 'string' && SHA.test(value.reportSha256) &&
    typeof value.checkedInputsSha256 === 'string' && SHA.test(value.checkedInputsSha256) &&
    OUTCOMES.includes(value.outcome) && typeof title.sourceSha256 === 'string' && SHA.test(title.sourceSha256),
  'Invalid prepared verification reference.');
  return value;
}

export function checkVerificationReport(raw, digest, titles) {
  requireThat(raw.length <= MAX_REPORT && sha(raw) === digest,
    'Verification report bytes differ from the recorded report hash.');
  const text = raw.toString('utf8');
  requireThat(!/-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(text), 'A verification report must not contain a private key.');
  // Python's historical VerifyReport writer permits infinite PSNR values.
  // Rewrite only unquoted numeric tokens, retaining Infinity as a number.
  // Quoted paths/details and the original hashed bytes remain untouched.
  const compatible = text.replace(/"(?:\\.|[^"\\])*"|(?<=[\s[:,])(-?Infinity)(?=[\s,}\]])/g,
    (token, infinite) => infinite ? (infinite.startsWith('-') ? '-1e999' : '1e999') : token);
  const report = record(JSON.parse(compatible));
  if (report.recipe === 'baked-ambient-v1') return checkAmbientReport(text, titles);
  requireThat(exactKeys(report, ['sha256', 'source_path', 'presets', 'passed', 'outcome', 'started_at', 'finished_at', 'checks']) &&
    report.passed === true && typeof report.source_path === 'string' && report.source_path.length > 0 &&
    Array.isArray(report.presets) && report.presets.length === PRESETS.length &&
    report.presets.every((preset, index) => preset === PRESETS[index]) &&
    typeof report.started_at === 'number' && Number.isFinite(report.started_at) &&
    typeof report.finished_at === 'number' && Number.isFinite(report.finished_at) &&
    Array.isArray(report.checks) && report.checks.length > 0,
  'The verification report is not a complete passing report.');
  const names = [];
  const flagged = [];
  const drawn = new Set();
  for (const item of report.checks) {
    const check = record(item);
    requireThat(exactKeys(check, ['name', 'passed', 'detail', 'data']) &&
      typeof check.name === 'string' && check.name.length > 0 && check.passed === true &&
      typeof check.detail === 'string', 'The verification report is not a complete passing report.');
    record(check.data);
    names.push(check.name);
    if (check.name.startsWith('plan_matches_map:')) {
      if (Object.hasOwn(check.data, 'stored')) {
        requireThat(typeof check.data.stored === 'number' && Number.isFinite(check.data.stored),
          'The verification report has an invalid plan measurement.');
      }
      if (check.data.stored > 0) flagged.push(check.name.slice('plan_matches_map:'.length));
    }
    if (check.name.startsWith('cover_actually_drawn:')) drawn.add(check.name.slice('cover_actually_drawn:'.length));
  }
  const required = ['source_hash', ...PRESETS.flatMap((preset) => CORE_CHECKS.map((name) => `${name}:${preset}`))];
  requireThat(new Set(names).size === names.length && required.every((name) => names.includes(name)),
    'The verification report is missing required unique checks.');
  const outcome = flagged.length === 0 ? 'no flagged segments' :
    flagged.every((preset) => drawn.has(preset)) ? 'cover proven drawn' : 'cover not proven';
  requireThat(titles.every((title) => report.sha256 === title.sourceSha256 &&
    report.outcome === verificationReference(title).outcome && outcome === report.outcome),
  'The verification report source or outcome differs from its title.');
  return report;
}

function compactJson(raw) {
  // Preserve JSON number tokens (Python's 500.0 versus JavaScript's 500) and
  // escaped map text while removing insignificant whitespace from sorted JSON.
  let quoted = false;
  let escaped = false;
  let result = '';
  for (const char of raw) {
    if (quoted || !/\s/.test(char)) result += char;
    if (escaped) escaped = false;
    else if (quoted && char === '\\') escaped = true;
    else if (char === '"') quoted = !quoted;
  }
  return result;
}

/** A reader is either a bounded regular file or a fixed archive member. */
export function checkPreparedNamespace(names, read, expectedCatalogSha256, { requireReports = false, requiredBundles = [] } = {}) {
  requireThat(new Set(names).size === names.length, 'Duplicate prepared package member.');
  const all = new Set(names);
  const allowed = new Set(['catalog.json', 'catalog.ts']);
  let total = 0;
  const cache = new Map();
  const bytes = (name, limit = MAX_BYTES) => {
    requireThat(all.has(name), `Missing prepared asset: ${name}`);
    if (!cache.has(name)) {
      const value = read(name, limit);
      requireThat(value.length <= limit, 'Prepared asset exceeds its byte limit.');
      total += value.length;
      requireThat(total <= MAX_BYTES, 'Prepared library exceeds its package budget.');
      // Retain only small metadata, not the videos.
      if (name.endsWith('.json') || name === 'catalog.ts') cache.set(name, value);
      return value;
    }
    return cache.get(name);
  };
  const catalogBytes = bytes('catalog.json', MAX_JSON);
  const catalogSha256 = sha(catalogBytes);
  if (expectedCatalogSha256 !== undefined) {
    requireThat(catalogSha256 === expectedCatalogSha256,
      'Packaged prepared catalog differs from the current build input.');
  }
  const raw = catalogBytes.toString('utf8');
  const catalog = record(JSON.parse(raw));
  const module = '/** Generated by pipeline.packaged_library. Verify before building the app. */\n' +
    `export const PACKAGED_LIBRARY_JSON = ${JSON.stringify(raw)};\n` +
    `export const PACKAGED_LIBRARY_SHA256 = ${JSON.stringify(sha(catalogBytes))};\n`;
  requireThat(bytes('catalog.ts', MAX_JSON * 2).toString('utf8') === module,
    'Compiled prepared catalog differs from the reviewed catalog.');
  if (all.has('.local-library.lock')) {
    allowed.add('.local-library.lock');
    requireThat(bytes('.local-library.lock', 0).length === 0, 'Unexpected export lock data.');
  }
  const empty = catalog.version === 1 && Array.isArray(catalog.titles) &&
    catalog.titles.length === 0 && Object.keys(catalog).length === 2;
  const bundles = [...new Set(names.filter((name) => name.includes('/') && !name.startsWith('reports/'))
    .map((name) => name.split('/')[0]))];
  requireThat(requiredBundles.every(bundle => bundles.includes(bundle)), 'A compiled prepared bundle is missing from delivery.');
  const reportReferences = new Map();
  requireThat(!empty || bundles.length === 0, 'An empty catalog contains undisclosed media.');
  if (!empty) requireThat(SHA.test(catalog.bundleId) && bundles.includes(catalog.bundleId), 'Missing active prepared bundle.');
  for (const bundleId of bundles) {
    requireThat(SHA.test(bundleId), 'Unexpected prepared directory.');
    const manifestPath = `${bundleId}/manifest.json`;
    allowed.add(manifestPath);
    const manifestBytes = bytes(manifestPath, MAX_JSON);
    const manifestText = manifestBytes.toString('utf8');
    const manifest = record(JSON.parse(manifestText));
    requireThat(manifest.version === 1 && manifest.assetRoot === PREFIX.slice(0, -1) &&
      manifest.bundleId === bundleId && Array.isArray(manifest.titles) &&
      manifest.titles.length > 0 && manifest.titles.length <= 16, 'Invalid prepared manifest.');
    const body = manifestText.replace(/^  "bundleId": "[0-9a-f]{64}",\n/m, '');
    requireThat(body !== manifestText && sha(compactJson(body)) === bundleId,
      'Prepared manifest content does not match its immutable directory.');
    if (bundleId === catalog.bundleId) requireThat(manifestBytes.equals(catalogBytes), 'Active prepared manifest differs from catalog.');
    for (const title of manifest.titles) {
      const digest = verificationReference(title).reportSha256;
      if (!reportReferences.has(digest)) reportReferences.set(digest, []);
      reportReferences.get(digest).push(title);
    }
    const files = record(manifest.files);
    requireThat(Object.keys(files).length > 0 && Object.keys(files).length <= 16 * 9,
      'Invalid prepared asset inventory.');
    for (const [relative, digest] of Object.entries(files)) {
      requireThat(ASSET.test(relative) && typeof digest === 'string' && SHA.test(digest),
        'A prepared asset path or digest is invalid.');
      const member = `${bundleId}/${relative}`;
      allowed.add(member);
      requireThat(sha(bytes(member)) === digest, `Prepared asset changed: ${relative}`);
    }
  }
  const presentReports = new Set();
  for (const name of names.filter((value) => value.startsWith('reports/'))) {
    const match = /^reports\/([0-9a-f]{64})\.json$/.exec(name);
    requireThat(match && reportReferences.has(match[1]), 'An unreferenced verification report is present.');
    const digest = match[1];
    checkVerificationReport(bytes(name, MAX_REPORT), digest, reportReferences.get(digest));
    allowed.add(name);
    presentReports.add(digest);
  }
  const missing = [...reportReferences.keys()].filter((digest) => !presentReports.has(digest)).sort();
  requireThat(!requireReports || missing.length === 0, `Original verification reports are missing: ${missing.join(', ')}`);
  requireThat(names.every((name) => allowed.has(name)) && names.length === allowed.size,
    'The prepared namespace contains missing or unreviewed files.');
  return { titles: catalog.titles.length, bundles: bundles.length, bytes: total, catalogSha256,
    verification_reports: { required: reportReferences.size, present: presentReports.size, missing } };
}

export function checkPreparedDirectory(root = path.join(APP, PREFIX), options = {}) {
  requireThat(fs.realpathSync(root) === path.resolve(root), 'Prepared root must not be a symlink.');
  const names = [];
  let entries = 0;
  const walk = (directory, prefix = '', depth = 0) => {
    requireThat(depth <= 4, 'Unexpected prepared directory depth.');
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      requireThat(++entries <= 10_000, 'Prepared namespace has too many entries.');
      const relative = prefix + entry.name;
      const full = path.join(directory, entry.name);
      const stat = fs.lstatSync(full);
      requireThat(!stat.isSymbolicLink(), 'Prepared assets must not be symlinks.');
      if (stat.isDirectory()) walk(full, relative + '/', depth + 1);
      else {
        requireThat(stat.isFile() && stat.nlink === 1, 'Prepared assets must be owned regular files.');
        names.push(relative);
      }
    }
  };
  walk(root);
  return checkPreparedNamespace(names, (name, limit) => {
    const full = path.join(root, name);
    requireThat(fs.statSync(full).size <= limit, 'Prepared asset exceeds its byte limit.');
    return fs.readFileSync(full);
  }, undefined, options);
}

export function checkPreparedPackage(packagePath, expectedCatalogSha256, options = {}) {
  const tarOptions = { timeout: 30_000, env: { ...process.env, LC_ALL: 'C', LANG: 'C' } };
  const listing = execFileSync('tar', ['-tf', packagePath], { ...tarOptions, maxBuffer: 1024 * 1024 }).toString('utf8');
  const verbose = execFileSync('tar', ['-tvf', packagePath], { ...tarOptions, maxBuffer: 2 * 1024 * 1024 }).toString('utf8');
  const members = listing.split('\n').filter(Boolean);
  const details = verbose.split('\n').filter(Boolean);
  requireThat(members.length === details.length, 'Ambiguous prepared archive listing.');
  checkRuntimeAssetNames(members.filter((_, index) => details[index][0] !== 'd'));
  const names = [];
  for (const [index, member] of members.entries()) {
    const canonical = path.posix.normalize('/' + member).slice(1).replace(/\/$/, '');
    const inNamespace = canonical === PREFIX.slice(0, -1) || canonical.startsWith(PREFIX);
    const ancestor = canonical === 'assets' || canonical === 'assets/raw';
    if (!inNamespace && !ancestor && !member.startsWith(PREFIX)) continue;
    requireThat(member.replace(/\/$/, '') === canonical,
      'Noncanonical prepared archive member.');
    const kind = details[index][0];
    requireThat(kind === (member.endsWith('/') || ancestor || canonical === PREFIX.slice(0, -1) ? 'd' : '-'),
      'Prepared archive members must be regular files and directories.');
    if (inNamespace && kind === '-') names.push(member.slice(PREFIX.length));
  }
  return checkPreparedNamespace(names, (name, limit) =>
    execFileSync('tar', ['-xOf', packagePath, PREFIX + name],
      { ...tarOptions, maxBuffer: Math.max(4096, limit + 1) }), expectedCatalogSha256, options);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    requireThat(args.filter((arg) => arg === '--require-reports').length <= 1, 'Choose --require-reports only once.');
    const strict = { requireReports: args.includes('--require-reports') };
    const options = args.filter((arg) => arg !== '--require-reports');
    requireThat(options.length === 0 || options[0] === '--packages', 'Choose --packages and/or --require-reports.');
    const runtimeAssets = checkRuntimeAssetDirectory();
    const result = checkPreparedDirectory(undefined, strict);
    const approved = checkApprovedCatalogs(APP);
    result.approvedBundles = approved.map(entry => entry.bundleId);
    strict.requiredBundles = result.approvedBundles;
    if (options[0] === '--packages') {
      const kind = options[1]?.toLowerCase();
      requireThat(kind === 'debug' || kind === 'release', 'Choose Debug or Release packages.');
      const allArches = ['armv7', 'aarch64', 'x86_64'];
      const target = options.slice(2);
      requireThat(target.length === 0 ||
        (target.length === 2 && target[0] === '--arch' && allArches.includes(target[1])),
      'Choose --arch armv7, aarch64 or x86_64, or omit it to check all packages.');
      const arches = target.length ? [target[1]] : allArches;
      for (const arch of arches) {
        checkPreparedPackage(path.join(APP, `build/${arch}-${kind}/calm-frames-app_${arch}.vpkg`), result.catalogSha256, strict);
      }
    }
    console.log(JSON.stringify({ prepared_library: 'checked', runtime_assets: runtimeAssets, ...result }));
  } catch (error) {
    console.error(`Prepared library check failed: ${error.message}`);
    process.exitCode = 1;
  }
}
