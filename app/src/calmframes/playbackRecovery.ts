/** Explicit, bounded recovery of one newly created native player. No automatic retry. */
export type RecoveryPhase = 'covered' | 'seeking' | 'confirming' | 'ready' | 'failed' | 'canceled';
export interface RecoveryMedia {
  currentTime: number;
  readyState: number;
  seeking?: boolean;
  paused?: boolean;
  pause(): void;
  play(): Promise<unknown>;
  addEventListener(type: string, listener: () => void): void;
  removeEventListener(type: string, listener: () => void): void;
}
export const RECOVERY_TIMEOUT_MS = 12000;
// Engineering tolerance for native seek position reports, not a protection margin.
export const RECOVERY_POSITION_TOLERANCE_MS = 250;
export function recoverPlayback(deps: {
  media: RecoveryMedia;
  positionMs: number;
  paused: boolean;
  /** True only for the current foreground instance with current guard verification. */
  current: () => boolean;
  /** Resolves when the opaque recovery view has mounted. This is not pixel proof. */
  presentCover: () => Promise<void>;
  /** Must use useFlashGuard.requestSeek; never write currentTime here. */
  seek: (positionMs: number) => Promise<unknown>;
  phase: (value: RecoveryPhase) => void;
}) {
  let stopped = false, seekIssued = false, seekReturned = false, seekSettled = false, confirming = false;
  let freshTimeline = false;
  let seekGeneration = 0;
  const { media } = deps;
  const valid = () => !stopped && deps.current();
  const listeners: [string, () => void][] = [];
  let timer: ReturnType<typeof setTimeout> | undefined;
  const detach = () => {
    if (timer !== undefined) clearTimeout(timer);
    listeners.forEach(([name, fn]) => media.removeEventListener(name, fn));
  };
  const stop = (phase: 'failed' | 'canceled') => {
    if (stopped) return;
    stopped = true; detach();
    try { media.pause(); } catch { /* Keep the cover and refuse recovery. */ }
    deps.phase(phase);
  };
  const targetReady = () => Number.isFinite(media.currentTime) && media.readyState >= 2 &&
    media.seeking === false && Math.abs(media.currentTime * 1000 - deps.positionMs) <= RECOVERY_POSITION_TOLERANCE_MS;
  const confirm = async () => {
    if (!valid() || !seekReturned || !seekSettled || !freshTimeline || !targetReady() || confirming) return;
    const confirmedSeek = seekGeneration;
    confirming = true; deps.phase('confirming');
    try {
      if (!deps.paused) await media.play();
      if (!valid()) { media.pause(); return; }
      // A pending native play can outlive a new seek or loss of decoded data.
      // Its resolution cannot authorize releasing an obsolete confirmation.
      if (confirmedSeek !== seekGeneration || !seekSettled || !freshTimeline ||
          media.seeking !== false || media.readyState < 2) { stop('failed'); return; }
      // The signed schedule remains independent after this presentation barrier opens.
      stopped = true; detach(); deps.phase('ready');
    } catch { stop('failed'); }
  };
  const listen = (name: string, fn: () => void) => { listeners.push([name, fn]); media.addEventListener(name, fn); };
  deps.phase('covered');
  try {
    media.pause();
    listen('seeking', () => { if (seekIssued) { seekGeneration += 1; seekSettled = false; freshTimeline = false; } });
    listen('seeked', () => {
      if (valid() && seekIssued && targetReady()) { seekSettled = true; confirm(); }
    });
    listen('timeupdate', () => {
      if (!valid()) return;
      // Native implementations may deliver timeupdate before seeked. Both must
      // belong to this issued seek and report its settled target.
      if (seekIssued && targetReady()) { freshTimeline = true; confirm(); }
    });
    listen('error', () => stop('failed'));
    listen('ended', () => stop('failed'));
    timer = setTimeout(() => stop('failed'), RECOVERY_TIMEOUT_MS);
    (async () => {
      try {
        await deps.presentCover();
        if (!valid()) return;
        if (!Number.isFinite(deps.positionMs) || deps.positionMs < 0) { stop('failed'); return; }
        deps.phase('seeking'); seekIssued = true;
        await deps.seek(deps.positionMs);
        if (!valid()) return;
        seekReturned = true; confirm();
      } catch { stop('failed'); }
    })();
  } catch { stop('failed'); }
  return { cancel: () => stop('canceled') };
}
