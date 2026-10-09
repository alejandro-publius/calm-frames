/**
 * What a poster on the shelf shows.
 *
 * Pure functions of a checked title, so the shelf's first frame can be tested
 * without a television, and so KidHomeScreen draws what these return rather
 * than deciding anything itself.
 */

import { benignStoryPoster } from './benignStory';
import { CheckedTitle } from './titleStatus';

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
