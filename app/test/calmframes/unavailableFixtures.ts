import { MapRejection, rejectionMessage } from '../../src/calmframes/flashMap';
import { CheckedTitle } from '../../src/calmframes/titleStatus';

/** Existing reader messages, plus the generic and viewing-settings refusals. */
export function unavailableVariants(base: CheckedTitle): Array<[string, CheckedTitle]> {
  const rejections: MapRejection[] = ['missing', 'stale', 'unsigned', 'unknown-key',
    'bad-signature', 'wrong-file', 'wrong-version', 'unparseable'];
  return [
    ...rejections.map((rejection): [string, CheckedTitle] => [rejection, {
      ...base, status: rejection === 'missing' ? 'pending' : 'failed',
      rejection, reason: rejectionMessage(rejection), segments: [],
    }]),
    ['viewing-settings', { ...base, status: 'pending', segments: [],
      reason: 'This title is unavailable with your current viewing settings.' }],
    ['generic', { ...base, status: 'failed', segments: [],
      reason: 'This title is unavailable. The picture stays hidden.' }],
  ];
}
