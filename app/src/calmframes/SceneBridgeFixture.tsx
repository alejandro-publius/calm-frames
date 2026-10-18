/** Development-only static presentation. No player, media, storage or trust registration. */
import React, { useEffect, useState } from 'react';
import { BackHandler, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import CoverLayer from './CoverLayer';
import { CALM_TEXT, CALM_COLORS, scale } from './calmStyles';
import { loadSceneBridges, resolveSceneBridge, SceneBridgeAsset } from './sceneBridges';
import { trace } from './trace';

const raw = "{\"version\":1,\"titleId\":\"scene-bridge-static-test\",\"renditionStartOffsetMs\":0,\"sourceSha256\":\"0000000000000000000000000000000000000000000000000000000000000000\",\"renditionSha256\":\"1111111111111111111111111111111111111111111111111111111111111111\",\"durationMs\":10000,\"authorConfirmed\":true,\"testFixture\":true,\"entries\":[{\"startMs\":0,\"endMs\":8000,\"text\":\"Test fixture: a card displays one.\"}]}";
const checksum = "ff3c1088df608aad1a8ab197dead504121b083161f6533d21c6a0a26b9b99d66194798435e65856a335575c89f562675a4e8ce554075e7d3dcd2a8af0c6a9bf5";
const asset: SceneBridgeAsset = {"titleId": "scene-bridge-static-test", "renditionStartOffsetMs": 0, "sourceSha256": "0000000000000000000000000000000000000000000000000000000000000000", "renditionSha256": "1111111111111111111111111111111111111111111111111111111111111111", "durationMs": 10000};

const fixture = loadSceneBridges(raw, checksum);
const base = [{ startMs: 0, endMs: 8000 }];
export default function SceneBridgeFixture({ onBack }: { onBack: () => void }) {
  const [fallback, setFallback] = useState(false);
  const development = typeof __DEV__ !== 'undefined' && __DEV__;
  const bridge = resolveSceneBridge(fixture,
    fallback ? { ...asset, renditionSha256: '2'.repeat(64) } : asset, base, 4000);
  const presentationState = bridge ? 'test-text' : 'fallback';
  useEffect(() => {
    if (!development) return;
    trace('playback', `scene-bridge-fixture state=${presentationState} opaque_requested=true media=none`);
  }, [presentationState, development]);
  useEffect(() => {
    if (!development) return;
    const listener = BackHandler.addEventListener('hardwareBackPress', () => {
      trace('playback', 'scene-bridge-fixture dismissed'); onBack(); return true;
    });
    return () => listener.remove();
  }, [development, onBack]);
  if (!development) return null;
  return <View testID="scene-bridge-fixture" style={styles.screen}>
    <View style={StyleSheet.absoluteFill}><Text>1</Text></View>
    <CoverLayer visible calmFallback sceneBridge={bridge} testID="scene-bridge-fixture-cover" />
    <View style={styles.header}>
      <Text style={styles.title}>Development: scene bridge test</Text>
      <Text style={styles.body}>Static test text only. No video or audio plays.</Text>
    </View>
    <View style={styles.controls}>
      <CalmButton sound={false} label="Skip test and return" hasTVPreferredFocus testID="scene-bridge-fixture-back"
        onPress={() => { trace('playback', 'scene-bridge-fixture dismissed'); onBack(); }} />
      <CalmButton sound={false} label="Test stale identity" testID="scene-bridge-fixture-fallback" onPress={() => setFallback(true)} />
      <CalmButton sound={false} label="Show test text" testID="scene-bridge-fixture-valid" onPress={() => setFallback(false)} />
    </View>
  </View>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: CALM_COLORS.SURFACE },
  header: { position: 'absolute', left: scale(80), top: scale(60), right: scale(80), zIndex: 2 },
  title: { ...CALM_TEXT.section, color: CALM_COLORS.TEXT },
  body: { ...CALM_TEXT.body, color: CALM_COLORS.TEXT, marginTop: scale(16) },
  controls: { position: 'absolute', bottom: scale(80), left: scale(80), right: scale(80), zIndex: 2, flexDirection: 'row', gap: scale(20) },
});
