/** Generate/check compiled inputs from exact, separately reviewed approval records.
 * This tool never grants approval, copies media, installs or edits the registry.
 */
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SHA = /^[0-9a-f]{64}$/;
const MAX_JSON = 16 * 1024 * 1024;
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const requireThat = (value, message) => { if (!value) throw new Error(message); };

export function readApprovalRegistry(app = APP) {
  const raw = fs.readFileSync(path.join(app, 'config/approved-prepared-libraries.json'));
  requireThat(raw.length <= 65536, 'The approval registry is too large.');
  const value = JSON.parse(raw);
  requireThat(value && value.version === 1 && Object.keys(value).sort().join() === 'catalogs,version' &&
    Array.isArray(value.catalogs) && value.catalogs.length <= 16, 'Invalid approval registry.');
  const seen = new Set();
  for (const entry of value.catalogs) {
    requireThat(entry && Object.keys(entry).sort().join() ===
      'approvalReference,bundleId,catalogSha256,consumer,label,publicKeyFingerprint' &&
      ['bundleId', 'catalogSha256', 'publicKeyFingerprint'].every(key => typeof entry[key] === 'string' && SHA.test(entry[key])) &&
      typeof entry.consumer === 'boolean' &&
      ['label', 'approvalReference'].every(key => typeof entry[key] === 'string' && entry[key].trim() && entry[key].length <= 300) &&
      !seen.has(entry.bundleId), 'Invalid or duplicate exact package approval.');
    seen.add(entry.bundleId);
  }
  return value.catalogs;
}

export function approvedCatalogModule(app = APP) {
  const entries = readApprovalRegistry(app);
  const ids = new Set();
  const catalogs = entries.map(entry => {
    const file = path.join(app, 'assets/raw/prepared-library', entry.bundleId, 'manifest.json');
    const stat = fs.lstatSync(file);
    requireThat(stat.isFile() && stat.nlink === 1 && stat.size <= MAX_JSON &&
      fs.realpathSync(file) === file, 'Approved catalog must be a bounded regular file.');
    const bytes = fs.readFileSync(file);
    requireThat(hash(bytes) === entry.catalogSha256, 'Catalog differs from its exact approval.');
    const raw = bytes.toString('utf8');
    const manifest = JSON.parse(raw);
    requireThat(manifest.bundleId === entry.bundleId &&
      hash(Buffer.from(manifest.publicKeyBase64, 'base64')) === entry.publicKeyFingerprint,
    'Signer or bundle differs from its exact approval.');
    requireThat(Array.isArray(manifest.titles) && manifest.titles.length > 0, 'Approved catalog has no titles.');
    for (const title of manifest.titles) {
      requireThat(!ids.has(title.id), 'Approved catalogs repeat a title identity.');
      ids.add(title.id);
    }
    return { ...entry, raw };
  });
  const module = '/** Generated from exact reviewed approvals. Never accepts runtime catalogs or keys. */\n' +
    `export const APPROVED_PREPARED_CATALOGS = ${JSON.stringify(catalogs, null, 2)};\n`;
  return { module, entries };
}

export function checkApprovedCatalogs(app = APP) {
  const result = approvedCatalogModule(app);
  requireThat(fs.readFileSync(path.join(app, 'src/calmframes/approvedPreparedCatalogs.ts'), 'utf8') === result.module,
    'Compiled approved catalogs differ from reviewed inputs. Run the generator after exact approval.');
  return result.entries;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    requireThat(process.argv.length === 3 && ['--check', '--write'].includes(process.argv[2]), 'Choose --check or --write.');
    if (process.argv[2] === '--write') {
      const { module } = approvedCatalogModule();
      const destination = path.join(APP, 'src/calmframes/approvedPreparedCatalogs.ts');
      requireThat(!fs.existsSync(destination) || !fs.lstatSync(destination).isSymbolicLink(), 'Generated output cannot be a symlink.');
      fs.writeFileSync(destination, module);
    }
    console.log(JSON.stringify({ approvedCatalogs: checkApprovedCatalogs().length, runtimeImport: false }));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
