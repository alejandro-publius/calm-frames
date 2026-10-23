/**
 * What a poster on the shelf shows.
 *
 * Pure functions of a checked title, so the shelf's first frame can be tested
 * without a television, and so KidHomeScreen draws what these return rather
 * than deciding anything itself.
 */

import {
  BENIGN_STORY_SHELF_QUALIFIER,
  benignStoryPoster,
  isBundledBenignStory,
} from './benignStory';
import { CatalogTitle, CheckedTitle } from './titleStatus';

/**
 * The still on a poster, or nothing.
 *
 * A poster the catalog published comes first. Otherwise the only still the
 * shelf draws is Harbor's own first signed scene still. The prepared Harbor and
 * the gradient carry no signed still, and they do not borrow Harbor's: those
 * stills belong to another file's signature and carry its burned-in "benign
 * demo" label. A title without a still keeps the plain block.
 */
export function shelfPoster(entry: CheckedTitle): string | undefined {
  if (entry.status !== 'verified') {
    return undefined;
  }
  return entry.title.posterUrl || benignStoryPoster(entry);
}

export interface ShelfLabel {
  /** The title as a person would say it. */
  name: string;
  /** What kind of copy it is, drawn on its own line under the name. */
  qualifier?: string;
}

/** A trailing "(...)" with something in front of it, as catalog titles write it. */
const TRAILING_QUALIFIER = /^(.*\S)\s*\(([^()]+)\)\s*$/;

/**
 * A poster's two lines: the name, then what it is.
 *
 * The catalog writes both on one line, "Harbor story (prepared locally)", and
 * the details page, the parent area and the player keep that full title. The
 * shelf splits it, so the first thing read is a name and the second line says
 * which copy it is. Harbor's second line is written here rather than split
 * out, because it has to say that its holds are practice.
 */
export function shelfLabel(title: CatalogTitle): ShelfLabel {
  const match = TRAILING_QUALIFIER.exec(title.title);
  const name = (match ? match[1] : title.title).trim();
  if (isBundledBenignStory(title)) {
    return { name, qualifier: BENIGN_STORY_SHELF_QUALIFIER };
  }
  if (!match) {
    return { name };
  }
  const qualifier = match[2].trim();
  return {
    name,
    qualifier: `${qualifier.charAt(0).toUpperCase()}${qualifier.slice(1)}`,
  };
}

/** Both lines as VoiceView reads them, before the poster's status. */
export function spokenShelfLabel(label: ShelfLabel): string {
  return label.qualifier ? `${label.name}, ${label.qualifier}` : label.name;
}
