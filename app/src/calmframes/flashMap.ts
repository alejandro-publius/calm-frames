/**
 * Reading a flash map, and refusing one.
 *
 * docs/SIDECAR_SPEC.md sets the rules a reader must follow, and the first one
 * is fail closed: a map that is missing, unparseable, the wrong version,
 * unsigned, signed by a key we do not hold, or bound to a different file is
 * not a map. When that happens the picture stays hidden and a card says the
 * title is not checked yet. Kid mode never lists a title whose map did not
 * verify.
 *
 * Every rejection has a name, because the parent area shows the reason and
 * because a test exists for each one.
 *
 * Staleness is ours, not the spec's. A map records when it was made. The
 * analyzer, the profile and the thresholds all move during a project, so a map
 * that has not been refreshed inside `maxAgeMs` is treated as unchecked rather
 * than trusted. The default is deliberately long, and the parent area shows
 * the date the map was made.
 */

import {
  canonicalBytesWithout,
  CanonicalJsonError,
  JsonPlain,
  nodeToPlain,
  parseJsonNode,
} from './canonicalJson';
import { CoverReason, FlashSegment } from './coverSchedule';
import { base64ToBytes, verifyEd25519 } from './ed25519';

export type MapRejection =
  | 'missing'
  | 'unparseable'
  | 'wrong-version'
  | 'unsigned'
  | 'unknown-key'
  | 'bad-signature'
  | 'wrong-file'
  | 'stale';

export interface FlashMapSource {
  path: string;
  sha256: string;
  durationMs: number | null;
}

export interface FlashMapWindow {
  name: string;
  /** Window width as a fraction of the picture width, 0 to 1. */
  widthFraction: number;
}

export interface VerifiedFlashMap {
  segments: FlashSegment[];
  source: FlashMapSource;
  profileName: string;
  /** Total milliseconds the map itself says are flagged, before guard bands. */
  hiddenMs: number;
  createdUtcMs: number;
  keyId: string;
  /** Every area window the analysis used, for the room comparison. */
  windows: FlashMapWindow[];
}

export type MapVerdict =
  | { ok: true; map: VerifiedFlashMap }
  | { ok: false; reason: MapRejection; detail: string };

export interface VerifyMapOptions {
  /**
   * The public key the app already holds, base64 of the 32 raw bytes.
   *
   * The map carries a copy of its own public key, but a self check only proves
   * the map is internally consistent. Trust comes from this one.
   */
  publicKeyBase64: string;
  /**
   * SHA-256 of the file we are about to play, from the catalog entry the
   * pipeline published. A map that describes a different file tells us nothing
   * about this one.
   */
  expectedSha256: string;
  /** Milliseconds since the epoch, for the staleness check. */
  nowMs: number;
  /** A map made longer ago than this is treated as unchecked. */
  maxAgeMs?: number;
}

/** Ninety days. Long enough for a season, short enough to notice a stale shelf. */
export const DEFAULT_MAX_MAP_AGE_MS = 90 * 24 * 60 * 60 * 1000;

/** The version of the sidecar this reader understands. */
export const SUPPORTED_MAP_VERSION = 1;

function reject(reason: MapRejection, detail: string): MapVerdict {
  return { ok: false, reason, detail };
}

function asRecord(value: JsonPlain | undefined): { [key: string]: JsonPlain } | null {
  if (value === null || value === undefined || typeof value !== 'object') {
    return null;
  }
  if (Array.isArray(value)) {
    return null;
  }
  return value;
}

function asNumber(value: JsonPlain | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function asString(value: JsonPlain | undefined): string | null {
  return typeof value === 'string' ? value : null;
}

/**
 * Parse an RFC 3339 timestamp in UTC.
 *
 * Date.parse would take a much wider set of strings, including local-time ones
 * whose meaning depends on the device clock's zone. The sidecar spec says UTC,
 * seconds precision, so that is all this accepts.
 */
export function parseCreatedUtc(text: string): number | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?Z$/.exec(
    text,
  );
  if (!match) {
    return null;
  }
  const value = Date.UTC(
    Number(match[1]),
    Number(match[2]) - 1,
    Number(match[3]),
    Number(match[4]),
    Number(match[5]),
    Number(match[6]),
    match[7] ? Math.round(Number(match[7]) * 1000) : 0,
  );
  return Number.isFinite(value) ? value : null;
}

function readSegments(value: JsonPlain | undefined): FlashSegment[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  const segments: FlashSegment[] = [];
  for (const entry of value) {
    const record = asRecord(entry);
    if (!record) {
      return null;
    }
    const startMs = asNumber(record.start_ms);
    const endMs = asNumber(record.end_ms);
    if (startMs === null || endMs === null || endMs <= startMs || startMs < 0) {
      return null;
    }
    const reasonText = asString(record.reason);
    // Three words are understood. Anything else is treated as red, so a reason
    // this build has not seen gets the opaque cover rather than the dim one.
    // `pattern` is read as itself rather than falling into that default,
    // because a pattern is opaque AND is not a red flash, and reading it as red
    // put red flashing in the parent's record for a title that had none.
    const reason: CoverReason =
      reasonText === 'general'
        ? 'general'
        : reasonText === 'pattern'
          ? 'pattern'
          : 'red';
    segments.push({ startMs, endMs, reason });
  }
  return segments.sort((a, b) => a.startMs - b.startMs);
}

function readWindows(profile: { [key: string]: JsonPlain }): FlashMapWindow[] {
  const windows: FlashMapWindow[] = [];
  const list = profile.area_windows;
  if (!Array.isArray(list)) {
    return windows;
  }
  for (const entry of list) {
    const record = asRecord(entry);
    if (!record) {
      continue;
    }
    const name = asString(record.name);
    const widthPx = asNumber(record.width_px);
    if (name === null || widthPx === null) {
      continue;
    }
    windows.push({ name, widthFraction: widthPx });
  }
  return windows;
}

/**
 * Check a map and say yes or no.
 *
 * `text` is the bytes as they were written, not a parsed object, because the
 * signature covers bytes. Pass null when there was nothing to read.
 */
export function verifyFlashMap(
  text: string | null | undefined,
  options: VerifyMapOptions,
): MapVerdict {
  if (text === null || text === undefined || text.trim().length === 0) {
    return reject('missing', 'no map was found for this title');
  }

  let plain: { [key: string]: JsonPlain } | null;
  let signedBytes: Uint8Array;
  let node;
  try {
    node = parseJsonNode(text);
    plain = asRecord(nodeToPlain(node));
    signedBytes = canonicalBytesWithout(node, 'signature');
  } catch (error) {
    const message =
      error instanceof CanonicalJsonError ? error.message : String(error);
    return reject('unparseable', message);
  }
  if (!plain) {
    return reject('unparseable', 'the map is not a JSON object');
  }

  const version = asNumber(plain.version);
  if (version !== SUPPORTED_MAP_VERSION) {
    return reject(
      'wrong-version',
      `this build reads version ${SUPPORTED_MAP_VERSION}, the map says ${String(
        plain.version,
      )}`,
    );
  }

  const signature = asRecord(plain.signature);
  if (!signature) {
    return reject('unsigned', 'the map carries no signature');
  }
  if (asString(signature.algorithm) !== 'ed25519') {
    return reject(
      'unsigned',
      `unknown signature algorithm ${String(signature.algorithm)}`,
    );
  }
  const signatureValue = asString(signature.value);
  const mapPublicKey = asString(signature.public_key);
  const keyId = asString(signature.key_id) ?? '';
  if (!signatureValue || !mapPublicKey) {
    return reject('unsigned', 'the signature has no value or no public key');
  }
  if (mapPublicKey !== options.publicKeyBase64) {
    return reject(
      'unknown-key',
      'the map was signed by a key this app does not hold',
    );
  }

  const signatureBytes = base64ToBytes(signatureValue);
  const publicKeyBytes = base64ToBytes(options.publicKeyBase64);
  if (!signatureBytes || !publicKeyBytes) {
    return reject('unsigned', 'the signature or the key is not base64');
  }
  if (!verifyEd25519(signatureBytes, signedBytes, publicKeyBytes)) {
    return reject('bad-signature', 'the signature does not match the map');
  }

  const source = asRecord(plain.source);
  const sha256 = source ? asString(source.sha256) : null;
  const path = source ? asString(source.path) : null;
  if (!source || !sha256 || !path) {
    return reject('unparseable', 'the map has no usable source block');
  }
  if (sha256.toLowerCase() !== options.expectedSha256.toLowerCase()) {
    return reject(
      'wrong-file',
      'the map is bound to a different file than the one about to play',
    );
  }

  const createdText = asString(plain.created_utc);
  const createdUtcMs = createdText ? parseCreatedUtc(createdText) : null;
  if (createdUtcMs === null) {
    return reject('unparseable', 'the map has no usable created_utc');
  }
  const maxAgeMs = options.maxAgeMs ?? DEFAULT_MAX_MAP_AGE_MS;
  if (options.nowMs - createdUtcMs > maxAgeMs) {
    return reject(
      'stale',
      `the map was made ${new Date(createdUtcMs).toISOString()} and has not been refreshed`,
    );
  }

  const segments = readSegments(plain.segments);
  if (!segments) {
    return reject('unparseable', 'the map has no usable segment list');
  }

  const profile = asRecord(plain.profile);
  const summary = asRecord(plain.summary);
  const picture = asRecord(plain.picture);
  const pictureWidth = picture ? asNumber(picture.width) : null;
  const windows = profile ? readWindows(profile) : [];

  return {
    ok: true,
    map: {
      segments,
      source: {
        path,
        sha256: sha256.toLowerCase(),
        durationMs: source ? asNumber(source.duration_ms) : null,
      },
      profileName: (profile ? asString(profile.name) : null) ?? 'unknown',
      hiddenMs: (summary ? asNumber(summary.hidden_ms) : null) ?? 0,
      createdUtcMs,
      keyId,
      windows: windows.map((window) => ({
        name: window.name,
        // width_px is in analysis pixels on the picture, so turn it into a
        // fraction of the picture width. Without a picture block there is
        // nothing to divide by, and a window with an unknown size is reported
        // as covering the whole picture, which is the least strict reading and
        // so the one that makes a household setting look stricter.
        widthFraction:
          pictureWidth && pictureWidth > 0
            ? window.widthFraction / pictureWidth
            : 1,
      })),
    },
  };
}

/** Plain wording for a rejection, shown on the card and in the parent area. */
export function rejectionMessage(reason: MapRejection): string {
  switch (reason) {
    case 'missing':
      return 'This title is not checked yet, so the picture stays hidden.';
    case 'stale':
      return 'This title was checked too long ago, so the picture stays hidden.';
    case 'unsigned':
      return 'This title has no signed check, so the picture stays hidden.';
    case 'unknown-key':
      return 'This title was checked by someone we do not know, so the picture stays hidden.';
    case 'bad-signature':
      return 'The check for this title was changed after it was signed, so the picture stays hidden.';
    case 'wrong-file':
      return 'The check for this title belongs to a different file, so the picture stays hidden.';
    case 'wrong-version':
      return 'The check for this title is in a newer format than this app reads, so the picture stays hidden.';
    case 'unparseable':
    default:
      return 'The check for this title could not be read, so the picture stays hidden.';
  }
}
