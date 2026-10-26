/**
 * Saying things out loud, for VoiceView.
 *
 * The consumer player announces its final visible copy explicitly and disables
 * live announcements on its card, so countdown ticks and duplicate speech do
 * not compete. Other callers retain the live-region fallback. Explicit callers
 * can request current status without queueing it behind superseded messages;
 * the default queue behavior remains available for other announcements.
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
  /** False for current player status so superseded messages do not queue. */
  queue?: boolean;
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
      api.announceForAccessibilityWithOptions(message, { queue: options.queue ?? true });
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
