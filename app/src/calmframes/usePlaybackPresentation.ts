/** Read-only playback state for labels. Never seeks or changes the safety cover. */
import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import { RefObject, useEffect, useState } from 'react';
import { Card } from './cards';

export function usePlaybackPaused(mediaRef: RefObject<VideoPlayer | null>, ready: boolean): boolean {
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    const media = mediaRef.current;
    if (!ready || !media) { return; }
    const update = () => setPaused(media.paused === true && !media.ended);
    update();
    media.addEventListener?.('pause', update);
    media.addEventListener?.('play', update);
    media.addEventListener?.('ended', update);
    return () => {
      media.removeEventListener?.('pause', update);
      media.removeEventListener?.('play', update);
      media.removeEventListener?.('ended', update);
    };
  }, [mediaRef, ready]);
  return paused;
}

export function pausedCard(card: Card, paused: boolean): Card {
  if (!paused || (card.kind !== 'covering' && card.kind !== 'countdown')) { return card; }
  const seconds = card.secondsLeft;
  const beforeHold = seconds === undefined ? 'Paused before the hold.'
    : `Paused with ${seconds} second${seconds === 1 ? '' : 's'} before the hold.`;
  const detail = card.kind === 'covering'
    ? 'Paused. Sound resumes when you press Play.'
    : `${beforeHold} Press Play to continue, or Skip to jump past it.`;
  return { ...card, detail, announcement: `${card.title}. ${detail}` };
}
