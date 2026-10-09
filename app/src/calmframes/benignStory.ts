/** A packaged rehearsal of scene continuity, with openly synthetic holds. */
import { Card } from './cards';
import {
  BENIGN_STORY_MAPS,
  BENIGN_STORY_PUBLIC_KEY,
  BENIGN_STORY_SHA256,
} from './benignStoryData';
import { CatalogTitle } from './titleStatus';
import { HouseholdSettings } from './household';

export const BENIGN_STORY_ID = 'calm-frames-benign-story';
export const BENIGN_STORY_URI =
  'file:///pkg/assets/raw/benign-story/harbor.precovered.mp4';
export const BENIGN_STORY_LABEL = 'Benign demo: practice holds, no flashing';

export function benignStoryTitle(): CatalogTitle {
  return {
    id: BENIGN_STORY_ID,
    title: 'Harbor story (benign demo)',
    uri: BENIGN_STORY_URI,
    sha256: BENIGN_STORY_SHA256,
    maps: BENIGN_STORY_MAPS,
    durationMs: 20_000,
    bifFromSafeRendition: true,
    textTrack: [
      {
        label: 'English practice captions',
        language: 'en',
        uri: 'file:///pkg/assets/raw/benign-story/harbor.vtt',
        mimeType: 'text/vtt',
      },
    ],
  };
}

/** An arbitrary catalog entry or route cannot grant itself the demo key. */
export function isBundledBenignStory(title: {
  id?: string;
  uri?: string;
  sha256?: string;
}): boolean {
  return (
    title.id === BENIGN_STORY_ID &&
    title.uri === BENIGN_STORY_URI &&
    title.sha256 === BENIGN_STORY_SHA256
  );
}

export function bundledTitlePublicKey(
  title: { id?: string; uri?: string; sha256?: string },
  fallback: string,
): string {
  return isBundledBenignStory(title) ? BENIGN_STORY_PUBLIC_KEY : fallback;
}

/** This packaged rendition uses the widest demo covers for every household. */
export function benignStorySettings(
  title: { id?: string; uri?: string; sha256?: string },
  settings: HouseholdSettings,
): HouseholdSettings {
  return isBundledBenignStory(title)
    ? { ...settings, preset: 'extra-cautious' }
    : settings;
}

/**
 * Whole seconds, worded the way the real after card words them.
 *
 * cards.ts keeps its own copy private and is mirrored into hook/, so this one
 * is repeated here and benignStory.test.tsx holds the two to the same numbers.
 */
function secondsPhrase(milliseconds: number): string {
  const seconds = Math.max(1, Math.round(milliseconds / 1000));
  return `${seconds} second${seconds === 1 ? '' : 's'}`;
}

/**
 * The guard still supplies timing and refusals; only practice copy changes.
 *
 * The cards follow the real pattern a family meets on a checked title: the
 * countdown with the live seconds and what Skip does, the hold itself, then
 * how long it lasted. Each one says practice, and none of them says anything
 * was hidden, because these holds are scheduled and nothing here flashes.
 */
export function benignStoryCard(card: Card): Card {
  if (card.kind === 'countdown') {
    const seconds = Math.max(0, card.secondsLeft ?? 0);
    const left = `${seconds} second${seconds === 1 ? '' : 's'}`;
    return {
      ...card,
      title: 'Practice hold coming up',
      detail: `In ${left}. Press Skip to jump past it.`,
      announcement: `Practice hold coming up in ${left}. Press Skip to jump past it.`,
    };
  }
  if (card.kind === 'covering') {
    return {
      ...card,
      title: 'Holding a calm scene',
      detail: 'Practice hold. Sound and captions keep playing.',
      announcement:
        'Holding a calm scene for practice. Sound and captions keep playing.',
    };
  }
  if (card.kind === 'after') {
    const title = card.interval
      ? `Held ${secondsPhrase(card.interval.endMs - card.interval.startMs)} for practice`
      : 'Held a calm scene for practice';
    const detail = 'Sound and captions kept playing. No flashing was present.';
    return {
      ...card,
      title,
      detail,
      announcement: `${title}. ${detail}`,
    };
  }
  return card;
}
