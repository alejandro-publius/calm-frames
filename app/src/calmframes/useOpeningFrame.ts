import React from 'react';

interface OpeningMedia {
  readyState: number;
  getVideoPlaybackQuality(): { totalVideoFrames: number; droppedVideoFrames: number };
}
/** A presentation gate only. The independent signed-picture cover stays in force. */
export function hasOpeningFrame(media: OpeningMedia | null): boolean {
  if (!media || media.readyState < 2) return false;
  try {
    const quality = media.getVideoPlaybackQuality();
    return Number.isFinite(quality.totalVideoFrames) && Number.isFinite(quality.droppedVideoFrames) &&
      quality.totalVideoFrames > quality.droppedVideoFrames;
  } catch { return false; }
}
export default function useOpeningFrame({ media, enabled, verified, surfaceReady, onTimeout }: {
  media: React.MutableRefObject<OpeningMedia | null>; enabled: boolean; verified: boolean; surfaceReady: boolean; onTimeout: () => void;
}) {
  const [ready, setReady] = React.useState(false);
  const failure = React.useRef(onTimeout); failure.current = onTimeout;
  React.useEffect(() => {
    if (!enabled || ready) return;
    const timeout = setTimeout(() => failure.current(), 15000);
    return () => clearTimeout(timeout);
  }, [enabled, ready]);
  React.useEffect(() => {
    if (!enabled || ready || !verified || !surfaceReady) return;
    const check = () => { if (hasOpeningFrame(media.current)) setReady(true); };
    check();
    const poll = setInterval(check, 100);
    return () => clearInterval(poll);
  }, [enabled, ready, verified, surfaceReady, media]);
  return ready;
}
