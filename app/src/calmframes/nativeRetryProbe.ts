/** TEST BUILD ONLY. Synthetic UI failure; native Retry/teardown remain real. */
export function createNativeRetryProbe() {
  let consumed = false;
  return {
    used: () => consumed,
    trigger(eligible: boolean, pause: () => void, failCovered: () => void): boolean {
      if (!eligible || consumed) return false;
      // Consume before callbacks to prevent reentry or a second decoder's failure.
      consumed = true;
      try { pause(); } catch { /* Retain the covered failure even if native pause throws. */ }
      failCovered();
      return true;
    },
  };
}
// One explicit synthetic fault per process, never automatically retriggered by Retry.
export const nativeRetryProbe = createNativeRetryProbe();
