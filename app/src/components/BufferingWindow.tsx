// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

/**
 * The loading presentation, made quiet.
 *
 * The sample drew a looping spinner on a full-screen layer the moment a wait
 * began. In the player that layer was 40 per cent black over the picture, and
 * the player shows it on every waiting and seeking event and removes it on
 * every playing and seeked event. Holding a seek key could therefore dim and
 * undim the whole picture several times a second, which is the kind of change
 * this app exists to keep off the screen.
 *
 * What it does now:
 *
 * - No animation of any kind, so there is nothing for reduced motion to stop.
 * - A wait shorter than REVEAL_DELAY_MS shows nothing new. Playback is never
 *   held back by this; only the status waits.
 * - Once shown, the status stays at least MIN_VISIBLE_MS, so a wait that ends
 *   just after it appears cannot make it blink. With both rules the status
 *   changes at most twice in any one second.
 * - The only words are a short factual status, "Loading" unless the caller
 *   passes its own, or none when something else on screen already explains
 *   the wait.
 * - "overlay" presentation draws no backdrop at all, so the scene behind it,
 *   picture, cover or card, stays exactly as it was. "screen" presentation
 *   keeps the sample's backdrop for screens that have nothing to show yet: an
 *   opaque backdrop appears at once, because it replaces a scene that does not
 *   exist, and a translucent one waits with the status, because it would dim a
 *   scene that does.
 *
 * It never covers or uncovers video. What the viewer may see of a title is the
 * cover's decision alone, made by the flash guard from the signed map. It takes
 * no focus and no presses, and it sits below the error screen, so a genuine
 * error and its way back stay usable.
 */

import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { announceForAccessibility } from '../calmframes/announce';
import {
  CALM_COLORS,
  CALM_SPACE,
  CALM_TEXT,
  scale,
} from '../calmframes/calmStyles';
import { COLORS } from '../styles/Colors';

/** A wait must last this long before any status appears. */
export const REVEAL_DELAY_MS = 1_000;
/** Once shown, the status stays at least this long. */
export const MIN_VISIBLE_MS = 500;
/** The default status. */
export const LOADING_TEXT = 'Loading';
/** Below the error screen, which is drawn at 6. */
export const BUFFERING_Z_INDEX = 5;

export type BufferingPresentation = 'screen' | 'overlay';

interface BufferingWindowProps {
  testID?: string;
  /**
   * Screen presentation only: the backdrop. Defaults to black. Opaque colours
   * show at once; translucent ones wait with the status.
   */
  backgroundColor?: string;
  /** "screen" by default, for callers that have nothing to show yet. */
  presentation?: BufferingPresentation;
  /**
   * Whether a wait is under way. Callers that mount the window only while
   * waiting can leave it out. Callers that keep it mounted get the minimum
   * display time, which needs the window to outlive the wait.
   */
  visible?: boolean;
  /** A short factual status, or null when the screen already explains the wait. */
  statusText?: string | null;
}

/**
 * True unless the colour is plainly see-through: "transparent", an rgba or
 * hsla value with alpha below 1, or a hex value with an alpha digit below full.
 */
export function isOpaqueColor(color: string): boolean {
  const value = color.trim().toLowerCase();
  if (value === 'transparent') {
    return false;
  }
  const functional = /^(?:rgba|hsla)\(([^)]*)\)$/.exec(value);
  if (functional) {
    const parts = functional[1].split(/[,/]/).map((part) => part.trim());
    if (parts.length < 4) {
      return true;
    }
    const alpha = parts[3].endsWith('%')
      ? parseFloat(parts[3]) / 100
      : parseFloat(parts[3]);
    return !(alpha < 1);
  }
  const hex = /^#([0-9a-f]{4}|[0-9a-f]{8})$/.exec(value);
  if (hex) {
    const digits = hex[1];
    const alpha = digits.length === 4 ? digits.slice(3) : digits.slice(6);
    return alpha === 'f' || alpha === 'ff';
  }
  return true;
}

/**
 * Whether the status is showing: only after REVEAL_DELAY_MS of continuous
 * waiting, and then for at least MIN_VISIBLE_MS. A wait that resumes while the
 * status is still showing keeps it without a gap.
 */
function useRevealedWait(visible: boolean): boolean {
  const [revealed, setRevealed] = useState(false);
  const revealedAt = useRef(0);

  useEffect(() => {
    if (visible) {
      if (revealed) {
        return;
      }
      const timer = setTimeout(() => {
        revealedAt.current = Date.now();
        setRevealed(true);
      }, REVEAL_DELAY_MS);
      return () => clearTimeout(timer);
    }
    if (!revealed) {
      return;
    }
    const shownFor = Date.now() - revealedAt.current;
    const timer = setTimeout(
      () => setRevealed(false),
      Math.max(0, MIN_VISIBLE_MS - shownFor),
    );
    return () => clearTimeout(timer);
  }, [visible, revealed]);

  return revealed;
}

const BufferingWindow = React.memo(
  ({
    testID = undefined,
    backgroundColor = undefined,
    presentation = 'screen',
    visible = true,
    statusText = LOADING_TEXT,
  }: BufferingWindowProps) => {
    const revealed = useRevealedWait(visible);
    const backdrop = backgroundColor || styles.container.backgroundColor;
    const showBackdrop =
      presentation === 'screen' &&
      (isOpaqueColor(backdrop) ? visible : revealed);
    const status = statusText?.trim() ? statusText.trim() : null;
    const showStatus =
      revealed &&
      status !== null &&
      (presentation === 'overlay' || showBackdrop);

    useEffect(() => {
      if (showStatus && status) {
        announceForAccessibility(status);
      }
    }, [showStatus, status]);

    if (!showBackdrop && !showStatus) {
      return null;
    }

    const plate = showStatus ? (
      <View
        testID="buffering-status"
        style={styles.plate}
        accessible
        accessibilityRole="text"
        accessibilityLiveRegion="polite"
        accessibilityLabel={status ?? undefined}
        aria-live="polite">
        <Text style={styles.statusText}>{status}</Text>
      </View>
    ) : null;

    if (presentation === 'overlay') {
      return (
        <View
          testID={testID || 'buffering-view'}
          style={styles.overlay}
          pointerEvents="none">
          {plate}
        </View>
      );
    }

    return (
      <View
        testID={testID || 'buffering-view'}
        style={{
          ...styles.container,
          backgroundColor: backdrop,
        }}>
        {plate}
      </View>
    );
  },
);

export const styles = StyleSheet.create({
  container: {
    width: '100%',
    height: '100%',
    top: 0,
    left: 0,
    position: 'absolute',
    flex: 1,
    backgroundColor: COLORS.BLACK,
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: BUFFERING_Z_INDEX,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: BUFFERING_Z_INDEX,
  },
  // The same plate as the player's paused label, in a fixed place in the
  // middle of the screen, clear of the card above and the captions below.
  plate: {
    backgroundColor: CALM_COLORS.SURFACE,
    borderRadius: scale(12),
    paddingVertical: scale(CALM_SPACE.TIGHT),
    paddingHorizontal: scale(CALM_SPACE.BLOCK),
  },
  statusText: {
    ...CALM_TEXT.supporting,
    color: CALM_COLORS.TEXT,
    textAlign: 'center',
  },
});
export default BufferingWindow;
