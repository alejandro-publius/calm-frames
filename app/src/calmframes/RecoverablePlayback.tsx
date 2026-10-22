import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { BackHandler, useKeplerAppStateManager } from '@amazon-devices/react-native-kepler';
import { CheckpointIdentity, checkpointIdentityKey, PlaybackCheckpoint } from './playbackCheckpoint';
import { deviceCheckpointStore } from './playbackCheckpointStorage';
import CoastalWorld, { WorldAppearance, WORLD } from './CoastalWorld';
import { CoastalAppearance } from './CoastalAppearance';
import { islandKind } from './CoastalIsland';
import { CALM_FLOW, CALM_SPACE, CALM_TEXT, heroTitleTypography, scale } from './calmStyles';
import CalmPageHeader from './CalmPageHeader';
import CalmButton from './CalmButton';
export interface RecoveryBinding {
  identity: CheckpointIdentity;
  start: PlaybackCheckpoint | null;
  retry(checkpoint: PlaybackCheckpoint): void;
}
export function resumeTime(ms: number): string {
  const seconds = Math.floor(ms / 1000); return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}
/** No player exists while the user chooses. Back/background invalidates pending loads. */
export default function RecoverablePlayback({identity, title, menuArt, onBack, children}: {
  identity: CheckpointIdentity; title: string; menuArt?: string; onBack(): void;
  children(binding: RecoveryBinding, generation: number): React.ReactNode;
}) {
  const [state, setState] = useState<{phase: 'loading' | 'choice' | 'playing'; checkpoint: PlaybackCheckpoint | null; generation: number}>(
    {phase: 'loading', checkpoint: null, generation: 0});
  const alive = useRef(true), phase = useRef(state.phase); phase.current = state.phase;
  const manager = useKeplerAppStateManager();
  const key = checkpointIdentityKey(identity);
  const leave = () => {if (alive.current) {alive.current = false; onBack();}};
  useEffect(() => {
    alive.current = true;
    let pending = true;
    const reader = deviceCheckpointStore.open(identity);
    const finish = (checkpoint: PlaybackCheckpoint | null) => {
      if (!pending || !alive.current) return;
      pending = false; reader.close();
      setState({phase: checkpoint ? 'choice' : 'playing', checkpoint, generation: 0});
    };
    // Optional storage cannot leave ordinary playback waiting indefinitely.
    const timeout = setTimeout(() => finish(null), 1000);
    reader.load().then(finish);
    const back = BackHandler.addEventListener('hardwareBackPress', () => {
      if (phase.current === 'playing') return false;
      leave(); return true;
    });
    const lifecycle = manager.addAppStateListener('change', next => {
      if (next === 'background' && phase.current !== 'playing') leave();
    });
    return () => {alive.current = false; pending = false; reader.close(); clearTimeout(timeout); back.remove(); lifecycle.remove();};
    // This component is keyed by exact identity; callbacks belong to that route.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  if (state.phase === 'playing') return <>{children({identity, start: state.checkpoint,
    retry: checkpoint => {
      if (alive.current) setState(current => ({phase: 'playing', checkpoint, generation: current.generation + 1}));
    }}, state.generation)}</>;
  const choose = (resume: boolean) => {
    if (!alive.current || state.phase !== 'choice') return;
    if (!resume) deviceCheckpointStore.open(identity).clear();
    setState(current => ({...current, phase: 'playing', checkpoint: resume ? current.checkpoint : null}));
  };
  return <CoastalAppearance.Provider value><WorldAppearance.Provider value>
    <View style={styles.screen} testID="playback-resume-choice">
      <CoastalWorld detail destination={islandKind(menuArt)} />
      <CalmPageHeader onBack={leave} backTestID="resume-back" preferredBack={state.phase === 'loading'} />
      <View style={styles.copy}>
        <Text style={[styles.title, heroTitleTypography(title)]}>{title}</Text>
        {state.phase === 'loading' ? <Text style={styles.detail} accessibilityLiveRegion="polite">Opening your video...</Text> :
          <View style={styles.actions}>
            <CalmButton primary hasTVPreferredFocus sound={false} label={`Resume at ${resumeTime(state.checkpoint!.positionMs)}`}
              testID="resume-playback" onPress={() => choose(true)} />
            <CalmButton sound={false} label="Start over" testID="resume-start-over" onPress={() => choose(false)} />
          </View>}
      </View>
    </View>
  </WorldAppearance.Provider></CoastalAppearance.Provider>;
}
const styles = StyleSheet.create({
  screen: {flex: 1, backgroundColor: WORLD.BACKGROUND, paddingHorizontal: scale(CALM_SPACE.SAFE_X), paddingVertical: scale(CALM_SPACE.SAFE_Y)},
  copy: {marginLeft: scale(40), paddingTop: scale(CALM_FLOW.HERO_TOP), width: scale(CALM_FLOW.HERO_TITLE_WIDTH)},
  title: {color: WORLD.TEXT, marginBottom: scale(32)},
  detail: {...CALM_TEXT.supporting, color: WORLD.TEXT},
  actions: {flexDirection: 'row', gap: scale(20)},
});
