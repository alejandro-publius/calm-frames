/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/**
 * Debug-only breadcrumbs for a device log: which screen is up, what has
 * focus, and whether a hold still loaded. Nothing in the picture changes.
 *
 * The device drops the app's console output under load, so these lines are
 * evidence only when they arrive; their absence proves nothing. Release
 * builds strip console output and never print them.
 */
export const TRACE_PREFIX = 'CALM_TRACE';

let traceEnabled = true;

/** jest.setup.ts turns this off, so unit tests stay quiet. */
export function setTraceEnabled(enabled: boolean): void {
  traceEnabled = enabled;
}

export function trace(kind: 'screen' | 'focus' | 'still' | 'image' | 'prepared-playback' | 'seek' | 'playback', detail?: string): void {
  if (!traceEnabled) {
    return;
  }
  if (typeof __DEV__ === 'undefined' || !__DEV__) {
    return;
  }
  console.warn(`${TRACE_PREFIX} ${kind} ${detail ?? ''}`.trim());
}
