const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

/**
 * Metro configuration
 * https://reactnative.dev/docs/metro
 *
 * @type {import('@react-native/metro-config').MetroConfig}
 */
// Isolate this checkout from stale maps and other active worktrees.
const path = require('node:path');
const config = {
  fileMapCacheDirectory: path.join(__dirname, 'node_modules', '.cache', 'calm-frames-metro'),
  resolver: { useWatchman: false },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
