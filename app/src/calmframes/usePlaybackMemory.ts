import { useEffect, useRef } from 'react';
import { CaptionChoice, CheckpointIdentity, checkpointIdentityKey, PlaybackCheckpoint, validateCheckpoint } from './playbackCheckpoint';
import { deviceCheckpointStore } from './playbackCheckpointStorage';
import { isPlayerOwnTrack, TextTrackListLike } from './defaultCaptions';
import { CAPTION_DISABLE_ID } from '../constants';
export function readCaptionChoice(tracks?: TextTrackListLike): CaptionChoice | null {
  for (let i = 0; i < (tracks?.length ?? 0); i++) {
    const track = tracks?.[i];
    if (track && !isPlayerOwnTrack(track) && track.mode === 'showing' && track.language && track.label) {
      return {language: track.language, label: track.label};
    }
  }
  return null;
}
/** Match catalog caption metadata, never a native track ID from a previous player. */
export function restoreCaptionChoice(tracks: TextTrackListLike | undefined, choice: CaptionChoice | null): string | null {
  let chosen: string | null = choice === null ? CAPTION_DISABLE_ID : null;
  for (let i = 0; i < (tracks?.length ?? 0); i++) {
    const track = tracks?.[i];
    if (!track || isPlayerOwnTrack(track)) continue;
    const match = choice !== null && choice.language === track.language && choice.label === track.label && chosen === null;
    track.mode = match ? 'showing' : 'hidden';
    if (match) chosen = track.id;
  }
  return chosen;
}
interface MemoryMedia {
  currentTime: number; readyState: number; seeking?: boolean; paused?: boolean; ended?: boolean;
  textTracks?: unknown;
  addEventListener(type: string, fn: () => void): void;
  removeEventListener(type: string, fn: () => void): void;
}
export function usePlaybackMemory(options: {
  identity?: CheckpointIdentity; initial?: PlaybackCheckpoint | null;
  media: React.MutableRefObject<MemoryMedia | null>; initialized: boolean;
  verified: boolean; enabled: boolean; ended: boolean;
}) {
  const latest = useRef(options); latest.current = options;
  const last = useRef<PlaybackCheckpoint | null>(options.initial ?? null);
  const session = useRef<ReturnType<typeof deviceCheckpointStore.open> | null>(null);
  const lastWrite = useRef(0);
  const key = options.identity ? checkpointIdentityKey(options.identity) : '';
  useEffect(() => {
    if (!options.identity) return;
    const writer = deviceCheckpointStore.open(options.identity); session.current = writer;
    return () => {writer.close(); if (session.current === writer) session.current = null;};
    // Identity is reconstructed and validated before entering the player.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const capture = (force = false) => {
    const current = latest.current, media = current.media.current;
    if (!current.identity || !media || !current.enabled || !current.verified || current.ended ||
        media.ended || media.seeking !== false || media.readyState < 2 || typeof media.paused !== 'boolean') return;
    try {
      // Use an actual reported playhead only, never the guard's extrapolated clock.
      const checkpoint = validateCheckpoint({version: 1, identity: current.identity,
        positionMs: media.currentTime * 1000, captions: readCaptionChoice(media.textTracks as TextTrackListLike | undefined),
        paused: media.paused, savedAt: Date.now()});
      last.current = checkpoint;
      if (force || checkpoint.savedAt - lastWrite.current >= 2000) {
        lastWrite.current = checkpoint.savedAt; session.current?.save(checkpoint);
      }
    } catch { /* Invalid/near-end positions do not replace the last usable checkpoint. */ }
  };
  const captureRef = useRef(capture); captureRef.current = capture;
  useEffect(() => {
    const media = options.media.current;
    if (!options.initialized || !media || !options.identity) return;
    const position = () => captureRef.current();
    const pause = () => captureRef.current(true);
    media.addEventListener('timeupdate', position); media.addEventListener('pause', pause);
    return () => {media.removeEventListener('timeupdate', position); media.removeEventListener('pause', pause);};
  }, [options.initialized, options.media, key, options.identity]);
  useEffect(() => {
    if (options.ended) {last.current = null; session.current?.clear();}
  }, [options.ended]);
  return {last, capture: () => captureRef.current(true)};
}
