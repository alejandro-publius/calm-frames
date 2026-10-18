/** Read-only native-input preflight. Never builds, installs, downloads or executes the player. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const PLAYER_INPUTS = [
  'src/w3cmedia/shakaplayer/dist/shaka-player.compiled.js',
  ...['Document', 'DOMParser', 'Element', 'Misc', 'TextDecoder', 'W3CMedia']
    .map(name => `src/w3cmedia/polyfills/${name}Polyfill.ts`),
];
export function checkNativeInputs(app = APP, nodeVersion = process.versions.node) {
  const problems = [];
  if (Number(nodeVersion.split('.')[0]) < 22) problems.push('Use Node 22 from .nvmrc before installing dependencies.');
  const dependencies = path.join(app, 'node_modules');
  if (!fs.existsSync(path.join(dependencies, '@amazon-devices/kepler-cli-platform/package.json'))) {
    problems.push('App dependencies are missing. In app/, run npm ci --ignore-scripts.');
  } else if (fs.lstatSync(dependencies).isSymbolicLink()) {
    problems.push('Use dependencies installed in this checkout: Metro cannot reliably follow a shared node_modules symlink. Run npm ci --ignore-scripts in app/.');
  }
  const missing = PLAYER_INPUTS.filter(name => !fs.existsSync(path.join(app, name)) || !fs.statSync(path.join(app, name)).isFile() || fs.statSync(path.join(app, name)).size === 0);
  if (missing.length) problems.push('Generated player files are missing. With the Vega SDK environment and JDK 21 configured, run npm run setup:player in app/. Headless tests do not generate these files.');
  if (!missing.length) {
    const syntax = spawnSync(process.execPath, ['--check', path.join(app, PLAYER_INPUTS[0])], { encoding: 'utf8', timeout: 15000 });
    if (syntax.error || syntax.status !== 0) problems.push('Generated Shaka JavaScript failed its syntax check. Re-run npm run setup:player before building.');
  }
  return { nativeInputs: problems.length ? 'blocked' : 'ready', missing, problems,
    scope: 'Input files only. SDK compatibility, native build and owner visual/audio acceptance remain separate checks.' };
}
if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = checkNativeInputs();
  console.log(JSON.stringify(result, null, 2));
  if (result.problems.length) process.exitCode = 1;
}
