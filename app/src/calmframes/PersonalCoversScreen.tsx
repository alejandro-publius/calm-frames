/** Mounted only inside the unlocked parent area; never previews the media. */
import React, { useEffect, useRef, useState } from 'react';
import { BackHandler, ScrollView, StyleSheet, Text, View } from 'react-native';
import CalmButton from './CalmButton';
import { CALM_TEXT, COASTAL_COLORS, scale } from './calmStyles';
import { deviceHouseholdStorage, HouseholdStorage } from './householdStorage';
import { loadPersonalCovers, savePersonalCovers } from './personalCoverStorage';
import { MAX_PERSONAL_COVERS, PersonalCoverAsset, PersonalCoverRecord, personalAssetKey } from './personalCovers';

export function coverTime(ms: number): string {
  const rounded = Math.round(ms);
  const fraction = rounded % 1000;
  return `${Math.floor(rounded / 60000)}:${String(Math.floor(rounded / 1000) % 60).padStart(2, '0')}${fraction ? `.${String(fraction).padStart(3, '0')}` : ''}`;
}

export default function PersonalCoversScreen({ asset, title, onBack,
  storage = deviceHouseholdStorage,
}: { asset: PersonalCoverAsset; title: string; onBack: () => void; storage?: HouseholdStorage }) {
  const assetKey = personalAssetKey(asset);
  const [loadedRecord, setRecord] = useState<PersonalCoverRecord>();
  const record = loadedRecord && personalAssetKey(loadedRecord.asset) === assetKey ? loadedRecord : undefined;
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [startMs, setStart] = useState(0);
  const [endMs, setEnd] = useState(Math.min(5000, Math.floor(asset.durationMs)));
  const [retry, setRetry] = useState(0);
  const [addFocusGeneration, setAddFocusGeneration] = useState(0);
  useEffect(() => {
    let live = true;
    setRecord(undefined);
    setError('');
    loadPersonalCovers(asset, storage).then((value) => {
      if (live) {
        setRecord(value);
        if (retry > 0) setAddFocusGeneration((generation) => generation + 1);
      }
    }).catch(() => {
      if (live) setError('Your saved extra covers could not be read. Playback stays blocked. Retry before making changes.');
    });
    return () => { live = false; };
    // All identity fields are encoded in assetKey.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetKey, storage, retry]);
  useEffect(() => {
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!savingRef.current) onBack();
      return true;
    });
    return () => subscription.remove();
  }, [onBack]);
  const write = async (next: PersonalCoverRecord, restoreAddFocus = false) => {
    if (savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    setError('');
    try {
      await savePersonalCovers(next, storage);
      setRecord(next);
      if (restoreAddFocus) setAddFocusGeneration((generation) => generation + 1);
    } catch {
      // A rejected write can still have reached storage. Re-read before another edit
      // so retrying cannot silently overwrite or duplicate a committed addition.
      setRecord(undefined);
      setError('Could not confirm your saved changes. Retry loading before making another change.');
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  };
  const invalid = startMs >= endMs;
  return <ScrollView style={styles.screen} contentContainerStyle={styles.content} testID="personal-covers">
    <CalmButton label="Back to Parents" onPress={onBack} disabled={saving} hasTVPreferredFocus={addFocusGeneration === 0 && !(error && !record)} testID="extra-back" />
    <Text style={styles.heading}>Extra picture covers</Text>
    <Text style={styles.body}>{title}</Text>
    <Text style={styles.body}>Choose times from a creator or your own notes. No video plays here. These household additions stay on this device and apply only to this exact prepared edition.</Text>
    <Text style={styles.body}>The checked covers always remain. Each addition includes half a second on either side, within the video. Removing an addition restores the checked covers.</Text>
    {error ? <Text style={styles.body} accessibilityLiveRegion="polite" testID="extra-error">{error}</Text> : null}
    {!record ? <View>
      <Text style={styles.body}>{error ? 'Extra covers unavailable' : 'Loading extra covers…'}</Text>
      {error ? <CalmButton hasTVPreferredFocus label="Retry loading" onPress={() => setRetry((value) => value + 1)} testID="extra-retry" /> : null}
    </View> : <View>
      <Text style={styles.body} testID="extra-draft">From {coverTime(startMs)} to {coverTime(endMs)} · video ends at {coverTime(asset.durationMs)}</Text>
      <View style={styles.row}>
        <CalmButton label="Start −1 second" disabled={saving || startMs === 0} onPress={() => setStart(Math.max(0, startMs - 1000))} testID="extra-start-less" />
        <CalmButton label="Start +1 second" disabled={saving || startMs >= asset.durationMs - 1} onPress={() => setStart(Math.min(Math.floor(asset.durationMs) - 1, startMs + 1000))} testID="extra-start-more" />
      </View>
      <View style={styles.row}>
        <CalmButton label="End −1 second" disabled={saving || endMs <= 1} onPress={() => setEnd(Math.max(1, endMs - 1000))} testID="extra-end-less" />
        <CalmButton label="End +1 second" disabled={saving || endMs === Math.floor(asset.durationMs)} onPress={() => setEnd(Math.min(Math.floor(asset.durationMs), endMs + 1000))} testID="extra-end-more" />
      </View>
      {invalid ? <Text style={styles.body}>Choose a start before the end.</Text> : null}
      <CalmButton key={`add-${addFocusGeneration}`} hasTVPreferredFocus={addFocusGeneration > 0} label={saving ? 'Saving…' : 'Add these times'} disabled={saving || invalid || record.additions.length >= MAX_PERSONAL_COVERS}
        onPress={() => write({ ...record, additions: [...record.additions, { startMs, endMs }] })} testID="extra-add" />
      <Text style={styles.heading}>Saved additions</Text>
      {record.additions.length === 0 ? <Text style={styles.body}>No extra covers. The checked covers still apply.</Text> : null}
      {record.additions.length >= MAX_PERSONAL_COVERS ? <Text style={styles.body}>The list is full. Remove one of your additions before adding another.</Text> : null}
      {record.additions.map((cover, index) => <View key={`${index}-${cover.startMs}-${cover.endMs}`} style={styles.row}>
        <CalmButton label={`Remove addition ${index + 1}: ${coverTime(cover.startMs)} to ${coverTime(cover.endMs)}`} disabled={saving}
          onPress={() => write({ ...record, additions: record.additions.filter((_, at) => at !== index) }, true)} testID={`extra-remove-${index}`} />
      </View>)}
    </View>}
  </ScrollView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COASTAL_COLORS.BACKGROUND },
  content: { padding: scale(60), paddingBottom: scale(100) },
  heading: { ...CALM_TEXT.section, color: COASTAL_COLORS.TEXT, marginVertical: scale(18) },
  body: { ...CALM_TEXT.body, color: COASTAL_COLORS.TEXT, marginVertical: scale(10) },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: scale(20), marginVertical: scale(8) },
});
