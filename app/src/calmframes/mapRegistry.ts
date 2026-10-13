/**
 * Finding a map from a file hash, and refusing to.
 *
 * A player that already knows where a title's map is does not need this. This
 * is for the other case: an app has a video file, it has its SHA-256, and it
 * wants to know whether a checked map for that file exists in a published set
 * at all. The answer comes from one signed index served beside the maps, keyed
 * by that hash. docs/SIDECAR_SPEC.md, section "The registry, version 1".
 *
 * Nothing here checks a signature by hand. The index is checked with the same
 * two pieces the map reader uses, `canonicalBytesWithout` and `verifyEd25519`,
 * because an index is signed by exactly the rule a map is signed by. The map it
 * points at is checked by `verifyFlashMap` in ./flashMap, the same function the
 * guard calls for a map found any other way, so a map reached through the index
 * is held to every rule a map is held to.
 *
 * The threat this is built for is somebody serving a modified index: one that
 * points a player at the wrong map, or says no map exists for a file that has
 * one. Whoever can serve the index can almost always serve the maps too, same
 * bucket, same origin, so neither half is trusted on its own:
 *
 * - the index is signed, so entries cannot be invented or edited. An attacker
 *   with the maps but not the key cannot write an entry at all;
 * - every entry is checked against the map it points at, and the map has to be
 *   the one the entry named, by its signature. That is what stops a swap to a
 *   different, still validly signed map of the same file, an older one with
 *   fewer segments, which the index signature alone would not catch because the
 *   attacker never had to touch the index;
 * - the index has a staleness bound of its own, because the one attack left to
 *   somebody who can serve both is replaying yesterday's set whole.
 *
 * Every refusal ends the same way a missing map does. The picture stays hidden.
 */

import {
  CanonicalJsonError,
  canonicalBytesWithout,
  JsonPlain,
  nodeToPlain,
  parseJsonNode,
} from './canonicalJson';
import { base64ToBytes, verifyEd25519 } from './ed25519';
import {
  MapRejection,
  parseCreatedUtc,
  rejectionMessage,
  VerifiedFlashMap,
  verifyFlashMap,
} from './flashMap';

export type RegistryRefusal =
  | 'registry-missing'
  | 'registry-unparseable'
  | 'registry-wrong-version'
  | 'registry-unsigned'
  | 'registry-unknown-key'
  | 'registry-bad-signature'
  | 'registry-stale'
  | 'not-listed'
  | 'entry-unusable'
  | 'map-refused'
  | 'not-the-listed-map';

/** The version of the index this reader understands. */
export const SUPPORTED_REGISTRY_VERSION = 1;

/**
 * Thirty days.
 *
 * Shorter than a map's ninety, on purpose. The index is rebuilt every time
 * anything is published, so thirty days is already generous, and this bound is
 * the only thing limiting how far back somebody who can serve the files can
 * replay a whole set of them.
 */
export const DEFAULT_MAX_REGISTRY_AGE_MS = 30 * 24 * 60 * 60 * 1000;

export interface RegistryEntry {
  /** SHA-256 of the video file this entry is filed under. */
  sha256: string;
  profile: string;
  /** Where the map is, relative to the index's own URL. */
  path: string;
  /** Base64 of the map's Ed25519 signature. The binding to the map. */
  signature: string;
  keyId: string;
  createdUtcMs: number;
  segmentCount: number | null;
  hiddenMs: number | null;
}

export interface VerifiedRegistry {
  createdUtcMs: number;
  keyId: string;
  entries: RegistryEntry[];
}

export type RegistryVerdict =
  | { ok: true; registry: VerifiedRegistry }
  | { ok: false; reason: RegistryRefusal; detail: string };

export type LookupVerdict =
  | { ok: true; map: VerifiedFlashMap; mapUrl: string; entry: RegistryEntry }
  | {
      ok: false;
      reason: RegistryRefusal;
      detail: string;
      /** Set when the index was fine and the map it pointed at was not. */
      mapRejection?: MapRejection;
    };

export interface VerifyRegistryOptions {
  /** The public key the app already holds, base64 of the 32 raw bytes. */
  publicKeyBase64: string;
  /** Milliseconds since the epoch, for the staleness check. */
  nowMs: number;
  /** An index made longer ago than this is treated as no index at all. */
  maxRegistryAgeMs?: number;
}

export interface LookupOptions extends VerifyRegistryOptions {
  /** Where the index is. Entry paths resolve against this. */
  registryUrl: string;
  /** SHA-256 of the file about to play, the key into the index. */
  expectedSha256: string;
  /** Which rule set to ask for. The pipeline publishes one map per profile. */
  profile?: string;
  /** Injected so tests do not need a network and a device does not need one. */
  fetchText: (url: string) => Promise<string | null>;
  /** Passed through to the map reader. */
  maxMapAgeMs?: number;
}

function refuse(reason: RegistryRefusal, detail: string): RegistryVerdict {
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

const SHA256_HEX = /^[0-9a-f]{64}$/;

/**
 * True when this entry path stays under the index it came from.
 *
 * An entry path is resolved against the index's own URL, so a path that is
 * absolute, carries a scheme, starts with a slash or steps up with `..` would
 * send the player to somewhere the index's publisher does not control. The
 * builder refuses to write one and this refuses to follow one, because the two
 * halves of a rule that only one half enforces is a rule that goes missing the
 * first time someone builds an index with something else.
 */
export function isInsideRegistry(path: string): boolean {
  if (!path || path.startsWith('/') || path.startsWith('\\')) {
    return false;
  }
  if (path.indexOf('\\') >= 0 || path.indexOf('://') >= 0) {
    return false;
  }
  if (/^[A-Za-z][A-Za-z0-9+.-]*:/.test(path)) {
    return false;
  }
  return path.split('/').every((part) => part !== '..' && part !== '');
}

/**
 * Where a map named by an entry actually lives.
 *
 * Written out rather than handed to URL, which is a polyfill on Vega and whose
 * behaviour on a relative path is the kind of thing that differs between two
 * of them. Null means the path was refused, and a refused path is never
 * fetched.
 */
export function resolveMapUrl(registryUrl: string, path: string): string | null {
  if (!isInsideRegistry(path)) {
    return null;
  }
  const withoutQuery = registryUrl.split('#')[0].split('?')[0];
  const cut = withoutQuery.lastIndexOf('/');
  if (cut < 0) {
    return path;
  }
  return `${withoutQuery.slice(0, cut + 1)}${path}`;
}

function readEntry(
  sha256: string,
  profile: string,
  value: JsonPlain | undefined,
): RegistryEntry | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  const path = asString(record.path);
  const signature = asString(record.signature);
  const createdText = asString(record.created_utc);
  const createdUtcMs = createdText ? parseCreatedUtc(createdText) : null;
  if (!path || !signature || createdUtcMs === null) {
    return null;
  }
  return {
    sha256,
    profile,
    path,
    signature,
    keyId: asString(record.key_id) ?? '',
    createdUtcMs,
    segmentCount: asNumber(record.segment_count),
    hiddenMs: asNumber(record.hidden_ms),
  };
}

/**
 * Check an index and say yes or no.
 *
 * `text` is the bytes as they were served, not a parsed object, because the
 * signature covers bytes. Pass null when there was nothing to read.
 */
export function verifyRegistry(
  text: string | null | undefined,
  options: VerifyRegistryOptions,
): RegistryVerdict {
  if (text === null || text === undefined || text.trim().length === 0) {
    return refuse('registry-missing', 'no index was found beside the maps');
  }

  let plain: { [key: string]: JsonPlain } | null;
  let signedBytes: Uint8Array;
  try {
    const node = parseJsonNode(text);
    plain = asRecord(nodeToPlain(node));
    signedBytes = canonicalBytesWithout(node, 'signature');
  } catch (error) {
    const message =
      error instanceof CanonicalJsonError ? error.message : String(error);
    return refuse('registry-unparseable', message);
  }
  if (!plain) {
    return refuse('registry-unparseable', 'the index is not a JSON object');
  }

  const version = asNumber(plain.version);
  if (version !== SUPPORTED_REGISTRY_VERSION) {
    return refuse(
      'registry-wrong-version',
      `this build reads index version ${SUPPORTED_REGISTRY_VERSION}, the index says ${String(
        plain.version,
      )}`,
    );
  }

  const signature = asRecord(plain.signature);
  if (!signature) {
    return refuse('registry-unsigned', 'the index carries no signature');
  }
  if (asString(signature.algorithm) !== 'ed25519') {
    return refuse(
      'registry-unsigned',
      `unknown signature algorithm ${String(signature.algorithm)}`,
    );
  }
  const signatureValue = asString(signature.value);
  const indexPublicKey = asString(signature.public_key);
  if (!signatureValue || !indexPublicKey) {
    return refuse('registry-unsigned', 'the signature has no value or no public key');
  }
  if (indexPublicKey !== options.publicKeyBase64) {
    return refuse(
      'registry-unknown-key',
      'the index was signed by a key this app does not hold',
    );
  }
  const signatureBytes = base64ToBytes(signatureValue);
  const publicKeyBytes = base64ToBytes(options.publicKeyBase64);
  if (!signatureBytes || !publicKeyBytes) {
    return refuse('registry-unsigned', 'the signature or the key is not base64');
  }
  if (!verifyEd25519(signatureBytes, signedBytes, publicKeyBytes)) {
    return refuse('registry-bad-signature', 'the signature does not match the index');
  }

  const createdText = asString(plain.created_utc);
  const createdUtcMs = createdText ? parseCreatedUtc(createdText) : null;
  if (createdUtcMs === null) {
    return refuse('registry-unparseable', 'the index has no usable created_utc');
  }
  const maxAgeMs = options.maxRegistryAgeMs ?? DEFAULT_MAX_REGISTRY_AGE_MS;
  if (options.nowMs - createdUtcMs > maxAgeMs) {
    return refuse(
      'registry-stale',
      `the index was made ${new Date(createdUtcMs).toISOString()} and has not been rebuilt`,
    );
  }

  const files = asRecord(plain.files);
  if (!files) {
    return refuse('registry-unparseable', 'the index has no files object');
  }
  const entries: RegistryEntry[] = [];
  for (const sha256 of Object.keys(files)) {
    if (!SHA256_HEX.test(sha256)) {
      // A key that is not a hash cannot be looked up by one, and an index that
      // carries one was not built by the tool that should have built it.
      return refuse(
        'registry-unparseable',
        `${sha256} is not a lowercase hex SHA-256`,
      );
    }
    const block = asRecord(files[sha256]);
    const maps = block ? asRecord(block.maps) : null;
    if (!maps) {
      return refuse('registry-unparseable', `${sha256.slice(0, 16)} has no maps`);
    }
    for (const profile of Object.keys(maps)) {
      const entry = readEntry(sha256, profile, maps[profile]);
      if (!entry) {
        return refuse(
          'registry-unparseable',
          `${sha256.slice(0, 16)} at profile ${profile} is not a usable entry`,
        );
      }
      entries.push(entry);
    }
  }

  return {
    ok: true,
    registry: {
      createdUtcMs,
      keyId: asString(signature.key_id) ?? '',
      entries,
    },
  };
}

/** The entry for a file and a profile, or null when the index has none. */
export function entryFor(
  registry: VerifiedRegistry,
  sha256: string,
  profile: string,
): RegistryEntry | null {
  const wanted = sha256.toLowerCase();
  for (const entry of registry.entries) {
    if (entry.sha256 === wanted && entry.profile === profile) {
      return entry;
    }
  }
  return null;
}

/**
 * The signature a map carries, read out of its text.
 *
 * Only ever called on text `verifyFlashMap` has already accepted, so this is
 * reading a field off a checked map, not a second opinion on whether it is one.
 */
function mapSignatureValue(text: string): string | null {
  try {
    const plain = asRecord(nodeToPlain(parseJsonNode(text)));
    const signature = plain ? asRecord(plain.signature) : null;
    return signature ? asString(signature.value) : null;
  } catch {
    return null;
  }
}

/**
 * Hand a file hash and an index URL, get back a verified map or a refusal.
 *
 * This is the whole feature. Any Vega app with a video file can call it, and
 * everything it hands back has been through both checks: the index signature
 * and the map's own.
 */
export async function lookupMap(options: LookupOptions): Promise<LookupVerdict> {
  const profile = options.profile ?? 'wcag';
  const registryText = await options.fetchText(options.registryUrl);
  const verdict = verifyRegistry(registryText, options);
  if (!verdict.ok) {
    return verdict;
  }

  const entry = entryFor(verdict.registry, options.expectedSha256, profile);
  if (!entry) {
    return {
      ok: false,
      reason: 'not-listed',
      detail: `the index lists no ${profile} map for this file`,
    };
  }

  const mapUrl = resolveMapUrl(options.registryUrl, entry.path);
  if (!mapUrl) {
    return {
      ok: false,
      reason: 'entry-unusable',
      detail: `the entry points outside the index: ${entry.path}`,
    };
  }

  const mapText = await options.fetchText(mapUrl);
  const mapVerdict = verifyFlashMap(mapText, {
    publicKeyBase64: options.publicKeyBase64,
    expectedSha256: options.expectedSha256,
    nowMs: options.nowMs,
    maxAgeMs: options.maxMapAgeMs,
  });
  if (!mapVerdict.ok) {
    return {
      ok: false,
      reason: 'map-refused',
      detail: mapVerdict.detail,
      mapRejection: mapVerdict.reason,
    };
  }

  // The map verifies. It still has to be the map the index named, or a second
  // validly signed map of the same file, an older one with fewer segments,
  // would be as good as the current one to anyone serving the files.
  if (mapSignatureValue(mapText ?? '') !== entry.signature) {
    return {
      ok: false,
      reason: 'not-the-listed-map',
      detail: 'the map that came back is not the one the index named',
    };
  }

  return { ok: true, map: mapVerdict.map, mapUrl, entry };
}

/** Plain wording for a refusal, shown on the card and in the parent area. */
export function registryRefusalMessage(
  reason: RegistryRefusal,
  mapRejection?: MapRejection,
): string {
  switch (reason) {
    case 'registry-missing':
      return 'The library is not responding. The picture stays hidden.';
    case 'registry-stale':
      return 'The library needs an update. The picture stays hidden.';
    case 'registry-unsigned':
      return 'The library is missing playback information. The picture stays hidden.';
    case 'registry-unknown-key':
      return 'The library comes from an unsupported source. The picture stays hidden.';
    case 'registry-bad-signature':
      return 'The library information appears to have changed. The picture stays hidden.';
    case 'registry-wrong-version':
      return 'The library needs a newer version of Calm Frames. The picture stays hidden.';
    case 'not-listed':
      return 'This title is still being prepared. The picture stays hidden for now.';
    case 'entry-unusable':
      return 'This title uses an unsupported location. The picture stays hidden.';
    case 'not-the-listed-map':
      return 'The playback information does not match the library. The picture stays hidden.';
    case 'map-refused':
      return mapRejection
        ? rejectionMessage(mapRejection)
        : 'The playback information could not be opened. The picture stays hidden.';
    case 'registry-unparseable':
    default:
      return 'The library information could not be opened. The picture stays hidden.';
  }
}
