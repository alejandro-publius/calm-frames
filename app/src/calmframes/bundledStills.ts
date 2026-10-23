/**
 * Bundled copies of signed hold stills, for the device.
 *
 * The guard hands the cover the still exactly as the signed map carries it, a
 * JPEG data URI it has authenticated. The Vega image loader refuses data URIs,
 * so for the stills we ship we also bundle the same bytes as package assets
 * (eval/benign_story_stills.py writes them and the registry beside them). The
 * swap happens only on an exact match of the whole authenticated data URI, so
 * a bundled picture can never stand in for a still the map did not sign, and
 * a still with no bundled copy keeps the data URI, which fails closed to the
 * opaque black backing on a device that cannot draw it.
 */
import type { ImageSourcePropType } from 'react-native';
import { BENIGN_STORY_MAPS } from './benignStoryData';
import { BENIGN_STORY_STILLS } from './benignStoryStills';

let index: Map<string, ImageSourcePropType> | null = null;

function holdsOf(mapText: string): Array<Record<string, unknown>> {
  try {
    const map = JSON.parse(mapText) as Record<string, unknown>;
    const block = map.scene_holds as Record<string, unknown> | undefined;
    const holds = (block && Array.isArray(block.holds) ? block.holds : map.holds) as unknown;
    return Array.isArray(holds)
      ? holds.filter((hold): hold is Record<string, unknown> => !!hold && typeof hold === 'object')
      : [];
  } catch {
    return [];
  }
}

function build(): Map<string, ImageSourcePropType> {
  const out = new Map<string, ImageSourcePropType>();
  for (const [profile, entries] of Object.entries(BENIGN_STORY_STILLS)) {
    const text = BENIGN_STORY_MAPS[profile];
    if (typeof text !== 'string') {
      continue;
    }
    const holds = holdsOf(text);
    for (const entry of entries) {
      const hold = holds.find(
        (candidate) => candidate.start_ms === entry.startMs && candidate.end_ms === entry.endMs,
      );
      const uri = hold?.image_data_uri;
      if (typeof uri === 'string') {
        out.set(uri, entry.source);
      }
    }
  }
  return out;
}

/** The bundled copy of exactly this authenticated still, or nothing. */
export function bundledStillFor(imageDataUri: string | undefined): ImageSourcePropType | undefined {
  if (!imageDataUri) {
    return undefined;
  }
  if (!index) {
    index = build();
  }
  return index.get(imageDataUri);
}

/** Tests rebuild the index after swapping the registry. */
export function resetBundledStillsForTests(): void {
  index = null;
}
