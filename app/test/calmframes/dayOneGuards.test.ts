/**
 * Calm Frames day-one guards.
 *
 * These rules come from docs/BUILD_PROMPT.md phase 1.2 and exist because
 * breaking them costs us a working app on SDK 0.24 with React Native 0.83:
 *
 * - headless task and service components can crash the app at launch;
 * - developer mode refuses to sideload a package whose id starts with
 *   com.amazon;
 * - the personalization and account login service components are gone, so the
 *   feature flags that guard their leftover call sites must stay off.
 *
 * Each assertion here has been seen to fail: break the manifest or a flag on
 * purpose and this suite goes red.
 */
import { readFileSync } from 'fs';
import { join } from 'path';

// AppConfig reads the device model at import time. The global mock in
// jest.setup.ts resolves a promise instead of returning a string, so give this
// suite a model that looks like the stick we target.
jest.mock('@amazon-devices/react-native-device-info', () => ({
  getModel: jest.fn(() => 'AFTCA002'),
}));

const appRoot = join(__dirname, '..', '..');
const manifest = readFileSync(join(appRoot, 'manifest.toml'), 'utf8');
const appJson = JSON.parse(readFileSync(join(appRoot, 'app.json'), 'utf8'));

// The global mock in jest.setup.ts replaces AppConfig, so read the real one.
const appConfig = jest.requireActual('../../src/config/AppConfig');

const packageId = manifest.match(/^id = "([^"]+)"/m)?.[1];

describe('manifest components', () => {
  it('declares no task components', () => {
    expect(manifest).not.toContain('[[components.task]]');
    expect(manifest).not.toContain('[tasks]');
    expect(manifest).not.toContain('[[tasks.work]]');
  });

  it('declares no service components', () => {
    expect(manifest).not.toContain('[[components.service]]');
    expect(manifest).not.toContain('[[offers.service]]\nid = "io.github');
  });

  it('declares exactly one interactive component', () => {
    const interactive = manifest.match(/\[\[components\.interactive\]\]/g) ?? [];
    expect(interactive).toHaveLength(1);
  });

  it('keeps no live TV sync source', () => {
    expect(manifest).not.toContain('sync_source');
    expect(manifest).not.toContain('livetv://');
  });
});

describe('package id', () => {
  it('is set', () => {
    expect(packageId).toBeTruthy();
  });

  it('does not start with com.amazon, which developer mode refuses', () => {
    expect(packageId?.startsWith('com.amazon')).toBe(false);
  });

  it('is not the sample id', () => {
    expect(packageId).not.toBe('com.amazondeveloper.keplervideoapp');
    expect(manifest).not.toContain('keplervideoapp');
  });

  it('matches the component that app.json registers', () => {
    expect(appJson.name).toBe(`${packageId}.main`);
    expect(manifest).toContain(`id = "${packageId}.main"`);
  });
});

describe('modules the build injects from package.json', () => {
  // react-native build-kepler adds one [[needs.module]] entry per installed
  // @amazon-devices package. Adding a dependency back therefore makes the app
  // declare that it needs the module for a feature we removed.
  const removedFeatureModules = [
    'headless_task_manager',
    'kepler_channel',
    'kepler_epg_sync_scheduler',
    'kepler_media_account_login',
    'kepler_media_content_launcher',
  ];

  it.each(removedFeatureModules)('does not declare %s', (moduleName) => {
    expect(manifest).not.toContain(moduleName);
  });
});

describe('feature flags for removed service components', () => {
  it('keeps content personalization off', () => {
    expect(appConfig.isContentPersonalizationEnabled()).toBe(false);
  });

  it('keeps account login off', () => {
    expect(appConfig.isAccountLoginEnabled()).toBe(false);
  });
});
