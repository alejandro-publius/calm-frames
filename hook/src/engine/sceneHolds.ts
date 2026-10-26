/**
 * Mirrored from app/src/calmframes by hook/tools/sync.mjs. Do not edit here:
 * edit the app copy and run `node hook/tools/sync.mjs`.
 */
/** Signed scene stills are presentation only. They never change the hide schedule. */
import { JsonPlain } from './canonicalJson';
import { CoverInterval, FlashSegment } from './coverSchedule';
import { base64ToBytes } from './ed25519';

export interface SceneHold {
  /** Source-map time, before the rendition offset is subtracted. */
  startMs: number;
  endMs: number;
  frameMs: number | null;
  imageDataUri: string;
}

export const MAX_SCENE_HOLDS = 32;
export const MAX_SCENE_HOLD_BYTES = 128 * 1024;
export const MAX_SCENE_HOLD_ENCODED_TOTAL = 2 * 1024 * 1024;
export const MAX_SCENE_HOLD_DIMENSION = 1280;
export const MAX_SCENE_HOLD_LOOKBACK_MS = 5000;
// Leave room for the ordinary map, but refuse enormous text before JSON or hashing.
export const MAX_SCENE_MAP_TEXT_LENGTH =
  MAX_SCENE_HOLD_ENCODED_TOTAL + 256 * 1024;
const JPEG_PREFIX = 'data:image/jpeg;base64,';

/** Check the JPEG envelope and dimensions before giving it to the image decoder. */
function isBoundedJpeg(bytes: Uint8Array): boolean {
  if (
    bytes.length < 4 ||
    bytes[0] !== 0xff ||
    bytes[1] !== 0xd8 ||
    bytes[bytes.length - 2] !== 0xff ||
    bytes[bytes.length - 1] !== 0xd9
  ) {
    return false;
  }
  let cursor = 2;
  while (cursor < bytes.length - 2) {
    if (bytes[cursor] !== 0xff) {
      return false;
    }
    while (bytes[cursor] === 0xff) {
      cursor += 1;
    }
    const marker = bytes[cursor++];
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd8)) {
      continue;
    }
    if (marker === 0xda || marker === 0xd9 || cursor + 2 > bytes.length) {
      return false;
    }
    const length = bytes[cursor] * 256 + bytes[cursor + 1];
    if (length < 2 || cursor + length > bytes.length) {
      return false;
    }
    const isFrame =
      marker >= 0xc0 &&
      marker <= 0xcf &&
      marker !== 0xc4 &&
      marker !== 0xc8 &&
      marker !== 0xcc;
    if (isFrame) {
      if (length < 8) {
        return false;
      }
      const height = bytes[cursor + 3] * 256 + bytes[cursor + 4];
      const width = bytes[cursor + 5] * 256 + bytes[cursor + 6];
      return (
        width > 0 &&
        height > 0 &&
        width <= MAX_SCENE_HOLD_DIMENSION &&
        height <= MAX_SCENE_HOLD_DIMENSION
      );
    }
    cursor += length;
  }
  return false;
}

/** Missing is legacy. An invalid optional field refuses the whole signed map. */
export function readSceneHolds(
  value: JsonPlain | undefined,
  segments: FlashSegment[],
  durationMs: number | null,
): SceneHold[] | null {
  if (value === undefined) {
    return [];
  }
  if (
    !value ||
    typeof value !== 'object' ||
    Array.isArray(value) ||
    value.version !== 1 ||
    !Array.isArray(value.holds) ||
    value.holds.length > MAX_SCENE_HOLDS
  ) {
    return null;
  }
  const result: SceneHold[] = [];
  let encodedTotal = 0;
  for (const item of value.holds) {
    if (!item || typeof item !== 'object' || Array.isArray(item)) {
      return null;
    }
    const {
      start_ms: startMs,
      end_ms: endMs,
      frame_ms: frameValue,
      image_data_uri: imageDataUri,
    } = item;
    // Keep the parsed value separate from its typed form. The property runner
    // compiles without strict null checks, so narrowing JsonPlain after a null
    // comparison alone does not leave a numeric timestamp there.
    const frameMs: number | null =
      typeof frameValue === 'number' ? frameValue : null;
    if (
      typeof startMs !== 'number' ||
      !Number.isFinite(startMs) ||
      startMs < 0 ||
      typeof endMs !== 'number' ||
      !Number.isFinite(endMs) ||
      endMs <= startMs ||
      (durationMs !== null && durationMs > 0 && endMs > durationMs) ||
      (result.length > 0 && startMs < result[result.length - 1].endMs) ||
      (frameValue !== null && typeof frameValue !== 'number') ||
      (frameMs !== null &&
        (typeof frameMs !== 'number' ||
          !Number.isFinite(frameMs) ||
          frameMs < 0 ||
          frameMs >= startMs ||
          startMs - frameMs > MAX_SCENE_HOLD_LOOKBACK_MS)) ||
      typeof imageDataUri !== 'string' ||
      !imageDataUri.startsWith(JPEG_PREFIX)
    ) {
      return null;
    }
    // Every still belongs to a covered segment of this map, and a source frame
    // cannot be taken from one of the map's own flagged parts.
    if (
      !segments.some(
        (segment) => segment.startMs >= startMs && segment.endMs <= endMs,
      ) ||
      (frameMs !== null &&
        segments.some(
          (segment) => frameMs >= segment.startMs && frameMs < segment.endMs,
        ))
    ) {
      return null;
    }
    encodedTotal += imageDataUri.length;
    const payload = imageDataUri.slice(JPEG_PREFIX.length);
    if (
      encodedTotal > MAX_SCENE_HOLD_ENCODED_TOTAL ||
      payload.length > Math.ceil(MAX_SCENE_HOLD_BYTES / 3) * 4 ||
      payload.length % 4 !== 0 ||
      !/^[A-Za-z0-9+/]+={0,2}$/.test(payload)
    ) {
      return null;
    }
    const bytes = base64ToBytes(payload);
    if (
      !bytes ||
      bytes.length > MAX_SCENE_HOLD_BYTES ||
      !isBoundedJpeg(bytes)
    ) {
      return null;
    }
    result.push({ startMs, endMs, frameMs, imageDataUri });
  }
  return result;
}

/** A partial or merged match is black, even if the current moment fits a still. */
export function sceneHoldForInterval(
  holds: SceneHold[],
  interval: CoverInterval | null | undefined,
  renditionStartOffsetMs = 0,
): SceneHold | undefined {
  if (!interval || !Number.isFinite(renditionStartOffsetMs)) {
    return undefined;
  }
  return holds.find(
    (hold) =>
      Math.max(0, hold.startMs - renditionStartOffsetMs) <= interval.startMs &&
      hold.endMs - renditionStartOffsetMs >= interval.endMs,
  );
}
