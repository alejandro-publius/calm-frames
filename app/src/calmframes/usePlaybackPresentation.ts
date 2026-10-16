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

/**
 * The covering and countdown cards while playback is paused.
 *
 * Paused means paused: nothing is playing, so the card must not say the
 * sound continues. It says the picture stays hidden and what Play does, and
 * for a countdown how long remains before the flashing, with Skip as before.
 */
export function pausedCard(card: Card, paused: boolean): Card {
  if (!paused || (card.kind !== 'covering' && card.kind !== 'countdown')) { return card; }
  const seconds = card.secondsLeft;
  const before = seconds === undefined ? 'Paused before the flashing.'
    : `Paused, ${seconds} second${seconds === 1 ? '' : 's'} before the flashing.`;
  const detail = card.kind === 'covering'
    ? 'Paused. The picture stays hidden. Press Play to continue.'
    : `${before} Press Play to continue, or Skip to jump past it.`;
  return { ...card, detail, announcement: `${card.title}. ${detail}` };
}
