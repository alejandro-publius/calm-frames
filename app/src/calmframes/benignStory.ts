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

/** The guard still supplies timing and refusals; only practice copy changes. */
export function benignStoryCard(card: Card): Card {
  if (card.kind === 'countdown') {
    return {
      ...card,
      title: 'A practice hold is coming',
      detail: 'No flashing. The gentle tone and captions continue.',
      announcement: 'A practice hold is coming. No flashing is present.',
    };
  }
  if (card.kind === 'covering') {
    return {
      ...card,
      title: 'Holding a calm scene',
      detail: 'Practice hold. No flashing is present.',
      announcement:
        'Holding a calm scene for practice. No flashing is present.',
    };
  }
  if (card.kind === 'after') {
    return {
      ...card,
      title: 'The story carries on',
      detail: 'That was a scheduled practice hold, not a detected flash.',
      announcement: 'The story carries on after a scheduled practice hold.',
    };
  }
  return card;
}
