/** Pack, install and check the actual source package without registry access. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import {
  existsSync, lstatSync, mkdtempSync, readFileSync, realpathSync, rmSync, statSync,
  symlinkSync, writeFileSync, mkdirSync,
} from 'node:fs';
import { createRequire } from 'node:module';
import { basename, delimiter, dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { MIRRORED } from './sync.mjs';

export const PACKAGE_NAME = '@calm-frames/flash-guard';
export const REQUIRED_EXPORTS = [
  'useFlashGuard', 'CoverLayer', 'CalmCard', 'SafeMediaControlHandler',
  'verifyFlashMap', 'kidModeTitles', 'SceneHold', 'FlashGuardOptions',
  'FlashGuardState', 'CoverLayerProps', 'SeekEngine', 'Card',
];
export const PEERS = [
  'react', 'react-native', '@amazon-devices/react-native-w3cmedia',
  '@amazon-devices/kepler-media-controls', '@amazon-devices/react-linear-gradient',
  '@amazon-devices/react-native-kepler', '@amazon-devices/react-native-svg',
];
export const EXPECTED_FILES = [
  'package.json', 'README.md', 'LICENSE', 'src/index.ts', 'src/pixelUtils.ts',
  'src/mirror.json', ...MIRRORED.map((name) => `src/engine/${name}`),
];

function inside(root, path) {
  const rel = relative(root, path);
  return rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel);
}

export function assertPackedFiles(paths) {
  assert.equal(new Set(paths).size, paths.length, 'duplicate packed path');
  assert.deepEqual([...paths].sort(), [...EXPECTED_FILES].sort(),
    'packed file inventory must include only the public source package');
}

export function assertPackageManifest(manifest) {
  assert.equal(manifest.name, PACKAGE_NAME, 'wrong package name');
  for (const field of ['main', 'types', 'react-native']) {
    assert.equal(manifest[field], 'src/index.ts', `${field} must resolve to packed source`);
  }
  assert.equal(manifest.license, 'Apache-2.0');
  assert.equal(manifest.dependencies, undefined, 'runtime libraries must remain peers');
  assert.deepEqual(Object.keys(manifest.peerDependencies ?? {}).sort(), [...PEERS].sort(),
    'declare all required Vega peers');
}

export function assertPeerCompatibility(manifest, versions, semver) {
  for (const peer of PEERS) {
    assert(semver.satisfies(versions[peer], manifest.peerDependencies[peer]),
      `current peer does not satisfy declared range: ${peer}`);
  }
}

export function publicExports(ts, source) {
  const parsed = ts.createSourceFile('index.ts', source, ts.ScriptTarget.Latest, true);
  const names = parsed.statements.flatMap((statement) =>
    ts.isExportDeclaration(statement) && statement.exportClause &&
    ts.isNamedExports(statement.exportClause)
      ? statement.exportClause.elements.map((one) => one.name.text) : []);
  for (const name of REQUIRED_EXPORTS) {
    assert(names.includes(name), `missing public export: ${name}`);
  }
  return names;
}

export function assertDependencyClosure(packageRoot, ts, sourceFiles) {
  const canonicalRoot = realpathSync(packageRoot);
  const sourceRoot = realpathSync(join(canonicalRoot, 'src'));
  for (const file of sourceFiles) {
    const installedPath = join(packageRoot, file);
    assert(lstatSync(installedPath).isFile(), `packed source must be a regular file: ${file}`);
    const path = realpathSync(installedPath);
    assert(inside(sourceRoot, path), `source escaped installed package: ${file}`);
    const source = readFileSync(path, 'utf8');
    assert(!source.includes('\0'), `binary source in package: ${file}`);
    assert(!/-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----/.test(source),
      `private key in packed source: ${file}`);
    for (const imported of ts.preProcessFile(source, true, true).importedFiles) {
      const specifier = imported.fileName;
      if (!specifier.startsWith('.')) {
        const peer = specifier.startsWith('@')
          ? specifier.split('/').slice(0, 2).join('/') : specifier.split('/')[0];
        assert(PEERS.includes(peer), `undeclared external import: ${specifier}`);
        continue;
      }
      const base = resolve(dirname(path), specifier);
      assert(inside(sourceRoot, base), `relative import escaped package: ${specifier}`);
      const target = [base, `${base}.ts`, `${base}.tsx`, join(base, 'index.ts'),
        join(base, 'index.tsx')].find((candidate) =>
        existsSync(candidate) && lstatSync(candidate).isFile());
      assert(target, `missing packed dependency: ${file} -> ${specifier}`);
      assert(inside(sourceRoot, realpathSync(target)), `dependency escaped package: ${specifier}`);
      assert(sourceFiles.includes(relative(canonicalRoot, target).split(sep).join('/')),
        `dependency was not in packed source inventory: ${specifier}`);
    }
  }
}

export function assertInstalledEntry(entry, installedRoot) {
  assert.equal(realpathSync(entry), join(realpathSync(installedRoot), 'src', 'index.ts'),
    'consumer must resolve the installed tarball, not repository source');
}

function command(binary, args, cwd, env) {
  return execFileSync(binary, args, { cwd, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

/** Reuse only existing peer/type packages after the clean offline install. */
function linkPeers(consumer, appRoot) {
  const versions = {};
  for (const peer of [...PEERS, '@types/react']) {
    const source = join(appRoot, 'node_modules', peer);
    assert(existsSync(join(source, 'package.json')), `install app dependencies first: missing ${peer}`);
    versions[peer] = JSON.parse(readFileSync(join(source, 'package.json'), 'utf8')).version;
    const target = join(consumer, 'node_modules', peer);
    mkdirSync(dirname(target), { recursive: true });
    symlinkSync(realpathSync(source), target, 'dir');
  }
  return versions;
}

function checkConsumerTypes(consumer, installedRoot, ts) {
  const names = publicExports(ts, readFileSync(join(installedRoot, 'src/index.ts'), 'utf8'));
  const fixture = join(consumer, 'consumer.ts');
  writeFileSync(fixture, `import { ${names.join(', ')} } from '${PACKAGE_NAME}';\n`);
  const options = {
    target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.Node10, jsx: ts.JsxEmit.React,
    strict: true, noEmit: true, skipLibCheck: true, esModuleInterop: true,
    allowSyntheticDefaultImports: true, types: ['react'],
    typeRoots: [join(consumer, 'node_modules/@types')], lib: ['lib.es2020.d.ts'],
  };
  const resolved = ts.resolveModuleName(PACKAGE_NAME, fixture, options, ts.sys).resolvedModule;
  assert(resolved, 'TypeScript cannot resolve the installed package');
  assertInstalledEntry(resolved.resolvedFileName, installedRoot);
  const program = ts.createProgram([fixture], options);
  const diagnostics = ts.getPreEmitDiagnostics(program);
  assert.equal(diagnostics.length, 0, ts.formatDiagnosticsWithColorAndContext(diagnostics, {
    getCanonicalFileName: (file) => file, getCurrentDirectory: () => consumer,
    getNewLine: () => '\n',
  }));
  const entry = program.getSourceFile(resolved.resolvedFileName);
  const symbol = entry && program.getTypeChecker().getSymbolAtLocation(entry);
  assert(symbol, 'installed entry has no public module symbol');
  const exported = program.getTypeChecker().getExportsOfModule(symbol).map((one) => one.name);
  assert.deepEqual(exported.sort(), [...names].sort(), 'installed public exports differ');
  return names.length;
}

/** Exercise the installed resolver with React Native's actual default fields. */
function checkMetroSources(consumer, installedRoot, appRequire, ts, sourceFiles) {
  const metro = appRequire('metro-resolver');
  const config = appRequire('@react-native/metro-config').getDefaultConfig(consumer).resolver;
  const lookup = (path) => {
    try {
      return { exists: true, type: statSync(path).isDirectory() ? 'd' : 'f',
        realPath: realpathSync(path) };
    } catch { return { exists: false }; }
  };
  const getPackage = (path) => {
    try { return JSON.parse(readFileSync(path, 'utf8')); } catch { return null; }
  };
  const context = {
    allowHaste: false, assetExts: new Set(config.assetExts), customResolverOptions: {},
    disableHierarchicalLookup: false, doesFileExist: (path) => {
      const entry = lookup(path);
      return entry.exists && entry.type === 'f';
    },
    extraNodeModules: null, dev: true, getPackage, fileSystemLookup: lookup,
    getPackageForModule: (path) => {
      let directory = lookup(path).type === 'd' ? path : dirname(path);
      while (basename(directory) !== 'node_modules') {
        const packageJson = getPackage(join(directory, 'package.json'));
        if (packageJson) return { rootPath: directory, packageJson,
          packageRelativePath: relative(directory, path) };
        const parent = dirname(directory);
        if (parent === directory) break;
        directory = parent;
      }
      return null;
    },
    mainFields: config.resolverMainFields, originModulePath: join(consumer, 'consumer.ts'),
    nodeModulesPaths: [], preferNativePlatform: true, resolveAsset: () => null,
    redirectModulePath: (path) => path, resolveHasteModule: () => null,
    resolveHastePackage: () => null, sourceExts: config.sourceExts,
    unstable_conditionNames: config.unstable_conditionNames,
    unstable_conditionsByPlatform: config.unstable_conditionsByPlatform,
    unstable_enablePackageExports: config.unstable_enablePackageExports,
    unstable_incrementalResolution: false,
    unstable_logWarning: (message) => { throw new Error(message); }, isESMImport: true,
  };
  const entry = metro.resolve(context, PACKAGE_NAME, 'vega');
  assert.equal(entry.type, 'sourceFile', 'Metro must select source, not an asset');
  assertInstalledEntry(entry.filePath, installedRoot);
  const sourceRoot = realpathSync(join(installedRoot, 'src'));
  for (const file of sourceFiles) {
    const originModulePath = join(installedRoot, file);
    const imports = ts.preProcessFile(readFileSync(originModulePath, 'utf8'), true, true).importedFiles;
    for (const { fileName } of imports.filter((one) => one.fileName.startsWith('.'))) {
      const resolved = metro.resolve({ ...context, originModulePath }, fileName, 'vega');
      assert.equal(resolved.type, 'sourceFile', `Metro did not resolve source: ${fileName}`);
      assert(inside(sourceRoot, realpathSync(resolved.filePath)),
        `Metro dependency escaped the installed package: ${fileName}`);
    }
  }
}

export async function checkPackage({
  hookRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..'),
  appRoot = resolve(hookRoot, '..', 'app'),
} = {}) {
  assert.equal(Number(process.versions.node.split('.')[0]), 22, 'use the pinned Node 22 runtime');
  const appRequire = createRequire(join(appRoot, 'package.json'));
  const ts = appRequire('typescript');
  const scratch = mkdtempSync(join(tmpdir(), 'calm-hook-package-'));
  const env = { ...process.env, PATH: `${dirname(process.execPath)}${delimiter}${process.env.PATH ?? ''}` };
  const npm = join(dirname(process.execPath), 'npm');
  try {
    const packed = JSON.parse(command(npm,
      ['pack', '--offline', '--ignore-scripts', '--json', '--pack-destination', scratch],
      hookRoot, env))[0];
    assertPackedFiles(packed.files.map((one) => one.path));
    const consumer = join(scratch, 'consumer');
    mkdirSync(consumer);
    writeFileSync(join(consumer, 'package.json'), JSON.stringify({ name: 'calm-hook-offline-consumer',
      version: '1.0.0', private: true }));
    command(npm, ['install', '--offline', '--ignore-scripts', '--legacy-peer-deps',
      '--no-audit', '--no-fund', '--package-lock=false', join(scratch, packed.filename)], consumer, env);
    const installedRoot = join(consumer, 'node_modules', PACKAGE_NAME);
    const installedManifest = JSON.parse(readFileSync(join(installedRoot, 'package.json'), 'utf8'));
    assertPackageManifest(installedManifest);
    assert.equal(readFileSync(join(installedRoot, 'LICENSE'), 'utf8'),
      readFileSync(join(appRoot, '..', 'LICENSE'), 'utf8'), 'packed licence must match the repository');
    const consumerRequire = createRequire(join(consumer, 'package.json'));
    assertInstalledEntry(consumerRequire.resolve(PACKAGE_NAME), installedRoot);
    const sourceFiles = EXPECTED_FILES.filter((one) => /\.tsx?$/.test(one));
    assertDependencyClosure(installedRoot, ts, sourceFiles);
    const peerVersions = linkPeers(consumer, appRoot);
    assertPeerCompatibility(installedManifest, peerVersions, appRequire('semver'));
    const exports = checkConsumerTypes(consumer, installedRoot, ts);
    checkMetroSources(consumer, installedRoot, appRequire, ts, sourceFiles);
    const babel = appRequire('@babel/core');
    for (const file of sourceFiles) {
      const transformed = babel.transformFileSync(join(installedRoot, file), {
        babelrc: false, configFile: false,
        presets: [appRequire.resolve('@react-native/babel-preset')],
      });
      assert(transformed?.code, `React Native could not transform packed source: ${file}`);
    }
    return { package: PACKAGE_NAME, files: packed.files.length, exports,
      offline_install: true, real_current_vega_peer_types: true,
      typescript: ts.version, metro_resolution: true, react_native_transform: true };
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  checkPackage().then((report) => console.log(JSON.stringify(report, null, 2))).catch((error) => {
    console.error(error.stack ?? error);
    process.exitCode = 1;
  });
}
