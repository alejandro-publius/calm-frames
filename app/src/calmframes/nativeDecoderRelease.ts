/** Process-wide ownership barrier. A timeout or rejected teardown is never confirmation. */
export function createDecoderReleaseBarrier() {
  const releases = new WeakMap<object, {done: boolean; promise: Promise<boolean>}>();
  const pending = new Set<Promise<boolean>>();
  let uncertain = false;
  return {
    state: (media: object) => releases.get(media),
    release(media: object, destroy: () => Promise<void>): Promise<boolean> {
      const previous = releases.get(media);
      if (previous) return previous.promise;
      const record = {done: false, promise: Promise.resolve(false)};
      // Register ownership before calling native code, including synchronous throws.
      releases.set(media, record);
      record.promise = Promise.resolve().then(destroy).then(() => {
        record.done = true; return true;
      }, () => { uncertain = true; return false; }).finally(() => pending.delete(record.promise));
      pending.add(record.promise);
      return record.promise;
    },
    async wait(timeoutMs = 12000): Promise<boolean> {
      let timer: ReturnType<typeof setTimeout> | undefined;
      const drained = async () => {
        while (pending.size) await Promise.all([...pending]);
        return !uncertain;
      };
      try {
        return await Promise.race([drained(), new Promise<boolean>(resolve => {
          timer = setTimeout(() => resolve(false), timeoutMs);
        })]);
      } finally { if (timer !== undefined) clearTimeout(timer); }
    },
  };
}
export const nativeDecoderRelease = createDecoderReleaseBarrier();
