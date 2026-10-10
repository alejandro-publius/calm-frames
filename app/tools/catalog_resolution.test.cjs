const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const { resolve } = require('metro-resolver');
const { getDefaultConfig } = require('@react-native/metro-config');

test('the compiled catalog import resolves to its TypeScript module in Metro', () => {
  const root = path.resolve(__dirname, '..');
  const originModulePath = path.join(root, 'src/calmframes/packagedLibrary.ts');
  const source = fs.readFileSync(originModulePath, 'utf8');
  const specifier = source.match(/import \{ PACKAGED_LIBRARY_JSON \} from '([^']+)'/)[1];
  const config = getDefaultConfig(root).resolver;
  const context = {
    ...config,
    originModulePath,
    assetExts: new Set(config.assetExts),
    preferNativePlatform: true,
    getPackageForModule: () => null,
    fileSystemLookup: (file) => {
      if (!fs.existsSync(file)) return { exists: false };
      return { exists: true, type: fs.statSync(file).isFile() ? 'f' : 'd', realPath: fs.realpathSync(file) };
    },
  };
  // The previous extensionless import selects catalog.json, whose default
  // object has no PACKAGED_LIBRARY_JSON export. Jest selected .ts instead.
  assert.equal(resolve(context, specifier.replace(/\.ts$/, ''), 'kepler').filePath,
    path.join(root, 'assets/raw/prepared-library/catalog.json'));
  assert.equal(resolve(context, specifier, 'kepler').filePath,
    path.join(root, 'assets/raw/prepared-library/catalog.ts'));
});
