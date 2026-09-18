/**
 * Saying things out loud, for VoiceView.
 *
 * Two halves, and both are needed:
 *
 * - the card itself carries accessibilityLiveRegion="polite" and the web
 *   aria-live="polite" attribute, so a screen reader that watches the tree
 *   reads the card when it appears;
 * - AccessibilityInfo.announceForAccessibilityWithOptions with { queue: true }
 *   pushes the same words, queued rather than interrupting, so an announcement
 *   already in progress finishes first. A child hearing "flashing part coming
 *   up" cut off halfway is worse than hearing it a beat later.
 *
 * The app declares com.amazon.devconf.privilege.accessibility in
 * app/manifest.toml under [wants], and test/calmframes/manifest.test.ts fails
 * if that goes missing.
 *
 * Nothing here throws. An announcement that cannot be made is not a reason to
 * stop hiding flashing.
 */

import { AccessibilityInfo } from 'react-native';

interface AnnounceOptions {
  /** Repeat the same words even if they were the last thing said. */
  force?: boolean;
}

let lastSpoken = '';

/** Forget what was last said. Used between screens and by tests. */
export function resetAnnouncements(): void {
  lastSpoken = '';
}

export function announceForAccessibility(
  text: string,
  options: AnnounceOptions = {},
): boolean {
  const message = text.trim();
  if (message.length === 0) {
    return false;
  }
  if (!options.force && message === lastSpoken) {
    return false;
  }
  lastSpoken = message;

  try {
    const api = AccessibilityInfo as unknown as {
      announceForAccessibilityWithOptions?: (
        announcement: string,
        announceOptions: { queue?: boolean },
      ) => void;
      announceForAccessibility?: (announcement: string) => void;
    };
    if (typeof api.announceForAccessibilityWithOptions === 'function') {
      api.announceForAccessibilityWithOptions(message, { queue: true });
      return true;
    }
    if (typeof api.announceForAccessibility === 'function') {
      // Older runtimes have only the interrupting form. Still better than
      // silence.
      api.announceForAccessibility(message);
      return true;
    }
  } catch {
    // A device with no screen reader attached can reject the call. The cover
    // and the cards do not depend on it.
  }
  return false;
}
