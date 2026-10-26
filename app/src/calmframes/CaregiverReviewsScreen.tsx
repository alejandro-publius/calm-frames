/** Mounted only inside unlocked Parents. No media, signer or household writes. */
import React, {useEffect, useLayoutEffect, useRef, useState} from 'react';
import {BackHandler, ScrollView, StyleSheet, Text, View} from 'react-native';
import CalmButton from './CalmButton';
import CalmPageHeader from './CalmPageHeader';
import ReadingStop from './ReadingStop';
import {CALM_SPACE, CALM_TEXT, COASTAL_COLORS, scale} from './calmStyles';
import {loadReviewInbox, readReviewFile, ReviewFile, ReviewReader} from './caregiverReviewInbox';

export default function CaregiverReviewsScreen({onBack, reader}: {onBack(): void; reader?: ReviewReader}) {
  const [files, setFiles] = useState<ReviewFile[]>([]), [selected, setSelected] = useState<ReviewFile>();
  const [status, setStatus] = useState('Loading caregiver reviews.'), [refresh, setRefresh] = useState(0);
  const [backFocus, setBackFocus] = useState(true), [returnFile, setReturnFile] = useState<string>();
  const generation = useRef<object | undefined>(undefined);
  const scroll = useRef<ScrollView>(null);
  useLayoutEffect(() => {if (selected) scroll.current?.scrollTo({y: 0, animated: false});}, [selected]);
  const leave = () => {if (selected) {setReturnFile(selected.name); setSelected(undefined);} else onBack();};
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {leave(); return true;});
    return () => sub.remove();
  });
  useEffect(() => {
    const version = {}; generation.current = version; let current = true; setFiles([]); setSelected(undefined); setStatus('Loading caregiver reviews.');
    loadReviewInbox(reader).then(result => {
      if (!current || generation.current !== version) return;
      setFiles(result.files);
      setStatus(result.refused ? 'Some reports could not be opened. Export them again from the caregiver computer.'
        : result.files.length ? 'Choose a caregiver review.' : 'No caregiver reviews are staged on this TV.');
    }).catch(() => {if (current) setStatus('The review inbox could not be read. Check the staged reports, then refresh.');});
    return () => {current = false; generation.current = undefined;};
  }, [reader, refresh]);
  const choose = async (file: ReviewFile) => {
    const version = generation.current;
    try {
      const current = await readReviewFile(file.name, reader);
      if (current.text !== file.text) throw new Error('Changed review');
      if (generation.current === version) {setBackFocus(true); setSelected(current);}
    } catch {if (generation.current === version) {setSelected(undefined); setStatus('This review changed or could not be read. Refresh before choosing it again.');}}
  };
  return <ScrollView ref={scroll} testID="caregiver-reviews" style={styles.screen} contentContainerStyle={styles.content}>
    <CalmPageHeader onBack={leave} backTestID="caregiver-reviews-back" preferredBack={backFocus && !returnFile} onBackFocus={() => setBackFocus(false)} />
    <Text accessibilityRole="header" style={[CALM_TEXT.screen, styles.text]}>Personal file reviews</Text>
    <ReadingStop testID="caregiver-reviews-limits" flush>
      <Text style={[CALM_TEXT.body, styles.text]}>These reports come from the caregiver computer. This TV has not rechecked the original video. A report does not add a playable title.</Text>
      <Text style={[CALM_TEXT.body, styles.text]}>Use only non-DRM files you own or have permission to process. Analysis is not medical safety or comfort validation.</Text>
    </ReadingStop>
    {selected ? <View style={styles.section}>
      <Text accessibilityRole="header" style={[CALM_TEXT.section, styles.text]}>{selected.review.title}</Text>
      <ReadingStop testID="caregiver-review-summary" flush>
        <Text style={[CALM_TEXT.body, styles.text]}>{`Reported duration: ${(selected.review.durationMs / 1000).toFixed(1)} seconds`}</Text>
        <Text style={[CALM_TEXT.body, styles.text]}>{`Original file SHA-256: ${selected.review.sourceSha256}`}</Text>
        {selected.review.plans.map(plan => <Text key={plan.preset} style={[CALM_TEXT.body, styles.text]}>{`${({'wcag': 'WCAG', 'broadcast': 'Broadcast', 'extra-cautious': 'Extra cautious'})[plan.preset]}: ${plan.intervals} reported replacement intervals, ${(plan.coveredMs / 1000).toFixed(1)} seconds`}</Text>)}
        <Text style={[CALM_TEXT.body, styles.text]}>Playback remains unavailable. An existing authorized signer, exact edition approval and a checked app build are still required.</Text>
      </ReadingStop>
      <CalmButton label="Back to reviews" onPress={leave} testID="caregiver-review-close" />
    </View> : <>
      <Text accessibilityLiveRegion="polite" style={[CALM_TEXT.body, styles.text]}>{status}</Text>
      {files.map(file => <CalmButton key={file.name} label={file.review.title} accessibilityLabel={`Read caregiver review: ${file.review.title}`}
        hasTVPreferredFocus={returnFile === file.name} onFocus={() => setReturnFile(undefined)}
        testID={`caregiver-review-${file.name}`} onPress={() => choose(file)} />)}
      <CalmButton label="Refresh reviews" testID="caregiver-reviews-refresh" onPress={() => setRefresh(value => value + 1)} />
    </>}
  </ScrollView>;
}
const styles = StyleSheet.create({
  screen: {flex: 1, backgroundColor: COASTAL_COLORS.BACKGROUND},
  content: {paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y), gap: scale(CALM_SPACE.ROW)},
  text: {color: COASTAL_COLORS.TEXT},
  section: {gap: scale(CALM_SPACE.ROW)},
});
