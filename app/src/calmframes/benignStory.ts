/** A packaged rehearsal of scene continuity, with openly synthetic holds. */
import { Card } from './cards';
import {
  BENIGN_STORY_MAPS,
  BENIGN_STORY_PUBLIC_KEY,
  BENIGN_STORY_SHA256,
} from './benignStoryData';
import { JsonPlain, nodeToPlain, parseJsonNode } from './canonicalJson';
import { CatalogTitle, CheckedTitle } from './titleStatus';
import { HouseholdSettings } from './household';

export const BENIGN_STORY_ID = 'calm-frames-benign-story';
export const BENIGN_STORY_URI =
  'file:///pkg/assets/raw/benign-story/harbor.precovered.mp4';
export const BENIGN_STORY_LABEL = 'Practice holds';
/** Harbor's second line on the shelf, under its name. */
export const BENIGN_STORY_SHELF_QUALIFIER = 'Practice holds demo';

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

/** The map every preset verifies, so a verified Harbor always checked it. */
const POSTER_MAP_PROFILE = 'wcag';
const JPEG_DATA_URI = 'data:image/jpeg;base64,';

function field(value: JsonPlain | undefined, key: string): JsonPlain | undefined {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value[key]
    : undefined;
}

/**
 * The first scene still in a map, read with the parser the verifier uses.
 *
 * This checks no signature. benignStoryPoster hands it out only for a title
 * whose check passed on this exact text, and that check is where the
 * signature and the still's own size and format were tested.
 */
function firstSceneStill(text: string): string | undefined {
  try {
    const holds = field(
      field(nodeToPlain(parseJsonNode(text)), 'scene_holds'),
      'holds',
    );
    const uri = Array.isArray(holds)
      ? field(holds[0], 'image_data_uri')
      : undefined;
    return typeof uri === 'string' && uri.startsWith(JPEG_DATA_URI)
      ? uri
      : undefined;
  } catch {
    return undefined;
  }
}

/** Read the first time a shelf asks. The compiled map never changes. */
let compiledStill: { uri: string | undefined } | null = null;

/**
 * Harbor's poster: the first signed still in its own map.
 *
 * Only for the bundled story, only once its check has passed, and only when
 * the map text that passed is the compiled one the still is read from. A
 * title that only claims Harbor's id, a check that did not pass, or a map
 * that came from anywhere else gets no picture, so the poster is never a
 * still nobody signed. No new image ships for it: the still is one of the two
 * the signed map already carries for its practice holds, and it shows the
 * same scene as the film. The player supplies the practice label.
 */
export function benignStoryPoster(entry: CheckedTitle): string | undefined {
  if (
    entry.status !== 'verified' ||
    !isBundledBenignStory(entry.title) ||
    !entry.verifiedProfiles.includes(POSTER_MAP_PROFILE) ||
    entry.title.maps?.[POSTER_MAP_PROFILE] !== BENIGN_STORY_MAPS[POSTER_MAP_PROFILE]
  ) {
    return undefined;
  }
  if (!compiledStill) {
    compiledStill = {
      uri: firstSceneStill(BENIGN_STORY_MAPS[POSTER_MAP_PROFILE]),
    };
  }
  return compiledStill.uri;
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
      detail: 'A practice hold. Sound and captions keep playing.',
      announcement:
        'Holding a calm scene for practice. Sound and captions keep playing.',
    };
  }
  if (card.kind === 'after') {
    const title = card.interval
      ? `Held ${secondsPhrase(card.interval.endMs - card.interval.startMs)} for practice`
      : 'Held a calm scene for practice';
    const detail = 'A practice hold. Nothing flashed, and sound and captions kept playing.';
    return {
      ...card,
      title,
      detail,
      announcement: `${title}. ${detail}`,
    };
  }
  return card;
}
