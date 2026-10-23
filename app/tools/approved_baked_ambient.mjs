/** Generate exact metadata only from already approved catalogs and verified reports. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { readApprovalRegistry, checkApprovedCatalogs } from './approved_prepared_libraries.mjs';
import { checkAmbientReport } from './ambient_report.mjs';
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hash = (s, algorithm='sha256') => createHash(algorithm).update(s).digest('hex');
export function bakedAmbientModule(app = APP) {
  checkApprovedCatalogs(app);
  const registrations = [];
  for (const entry of readApprovalRegistry(app)) {
    const root = path.join(app, 'assets/raw/prepared-library');
    const manifest = JSON.parse(fs.readFileSync(path.join(root, entry.bundleId, 'manifest.json'), 'utf8'));
    for (const title of manifest.titles) {
      if (!/^[a-f0-9]{64}$/.test(title.verification?.reportSha256)) throw new Error('Invalid ambient report identity.');
      const file = path.join(root, 'reports', `${title.verification.reportSha256}.json`);
      const stat = fs.lstatSync(file);
      if (!stat.isFile() || stat.nlink !== 1 || stat.size > 4*1024*1024 || fs.realpathSync(file) !== file) throw new Error('Invalid ambient report input.');
      const raw = fs.readFileSync(file, 'utf8');
      if (hash(raw) !== title.verification.reportSha256) throw new Error('Ambient report hash changed.');
      if (JSON.parse(raw).recipe !== 'baked-ambient-v1') continue;
      const report = checkAmbientReport(raw, [title]);
      if (report.publicKeyFingerprint !== entry.publicKeyFingerprint) throw new Error('Ambient signer differs from exact catalog approval.');
      for (const proof of Object.values(report.presets)) registrations.push({ raw: proof.metadataRaw, sha512: hash(proof.metadataRaw, 'sha512') });
    }
  }
  return "/** Generated only from exact approved catalogs and their checked ambient reports. */\n"+
    "import { loadBakedAmbient } from './bakedAmbient';\n"+
    `const registrations: readonly { raw: string; sha512: string }[] = ${JSON.stringify(registrations, null, 2)};\n`+
    "const documents = registrations.map(entry => loadBakedAmbient(entry.raw, entry.sha512));\n"+
    "export function bakedAmbientForRendition(renditionSha256?: string, preset?: string) {\n"+
    "  return documents.find(document => document?.renditionSha256 === renditionSha256 && document?.preset === preset) ?? null;\n}\n";
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 3 || !['--write','--check'].includes(process.argv[2])) throw new Error('Choose --write or --check.');
    const result = bakedAmbientModule(), file = path.join(APP, 'src/calmframes/approvedBakedAmbient.ts');
    if (process.argv[2] === '--write') {
      if (fs.existsSync(file) && fs.lstatSync(file).isSymbolicLink()) throw new Error('Generated output cannot be a symlink.');
      fs.writeFileSync(file, result);
    }
    if (fs.readFileSync(file, 'utf8') !== result) throw new Error('Compiled ambient metadata differs from exact approved catalogs.');
    console.log('Compiled ambient metadata matches exact approved catalogs.');
  } catch(error) { console.error(error.message); process.exitCode=1; }
}
