/** Read-only playback state for labels. Never seeks or changes the safety cover. */
import { VideoPlayer } from '@amazon-devices/react-native-w3cmedia';
import { RefObject, useEffect, useState } from 'react';
import { announceForAccessibility } from './announce';
import { Card, NO_CARD, SKIP_MARGIN_MS } from './cards';

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

/** Consumer copy only. It never decides whether the picture is covered. */
export function playbackCard(card: Card, state: {
  paused: boolean;
  covered: boolean;
  buffering: boolean;
  slow?: boolean;
  ended: boolean;
  practice?: boolean;
  oceanVisible?: boolean;
}): Card {
  if (state.ended || card.kind === 'after') return NO_CARD;
  if (card.kind !== 'countdown' && card.kind !== 'covering') return card;
  const title = state.practice
    ? (state.covered ? 'Practice cover' : 'Practice ahead')
    : (state.covered ? state.oceanVisible ? 'Scene replaced' : 'Scene hidden' : 'Scene ahead');
  const detail = state.paused ? 'Paused' : state.buffering ? 'Loading' : state.slow ? 'Playback slow' : '';
  const guidance = state.paused
    ? 'Paused. Press Play to continue, or Skip to jump past this scene.'
    : state.buffering ? 'Waiting for playback. You can skip past this scene.'
    : state.slow ? 'Playback is progressing slowly. You can wait or go back.'
    : state.practice ? 'This is a planned practice scene. You can skip ahead.'
    : 'You can skip past this scene.';
  return { ...card, title, detail, announcement: `${title}. ${guidance}`,
    skipToMs: card.skipToMs ?? (card.interval ? card.interval.endMs + SKIP_MARGIN_MS : undefined) };
}

/** Let fleeting noncritical status settle before speaking, never before acting. */
export const CARD_ANNOUNCEMENT_SETTLE_MS = 600;
export function usePlaybackCardAnnouncement(card: Card, urgent = false): void {
  const message = card.announcement;
  const immediate = urgent || card.kind === 'checking' || card.kind === 'unverified';
  useEffect(() => {
    if (!message) return;
    const speak = () => announceForAccessibility(message, { queue: false });
    if (immediate) { speak(); return; }
    const timer = setTimeout(speak, CARD_ANNOUNCEMENT_SETTLE_MS);
    return () => clearTimeout(timer);
  }, [message, immediate]);
}
