/**
 * Which map the app plays a title against, and where it came from.
 *
 * Three places a map can come from, in this order:
 *
 *   registry  the signed index published beside the maps, looked up by the
 *             file's SHA-256. mapRegistry.ts does the checking;
 *   bundled   the map compiled into the package beside the offline title, the
 *             one that makes kid mode work with no network at all;
 *   catalog   a map text the catalog entry carried.
 *
 * The registry is asked first, because it is the only one of the three that
 * can say a map has been replaced since the catalog was written. The other two
 * are what the app already holds, and an index that says nothing about a file
 * is not a reason to throw them away.
 *
 * Everything this hands on is still checked by `verifyFlashMap` afterwards,
 * through `checkTitle` on the shelf and again in the player, so a map reached
 * through the index is held to every rule a map is held to, twice more.
 *
 * ## What a missing entry does, and what a tampered one does
 *
 * They are not the same thing and they do not do the same thing.
 *
 * - **Missing**: the index verified and lists no map for this file, or there
 *   was no index to read at all. That is the normal state of a file nobody has
 *   published yet, and it is also what a device in flight mode sees. It falls
 *   through to the bundled or catalog map, which is itself signed, bound to
 *   this file's hash and checked by the same reader. With no such map either,
 *   the title is pending, kid mode never lists a pending title, and the player
 *   refuses it, so the picture stays hidden exactly as a missing map has always
 *   left it.
 *
 * - **Tampered**: the index did not check out, or the map it named did not.
 *   That is an unsigned index, one signed by a key this app does not hold, one
 *   edited after signing, one nobody has rebuilt inside the staleness bound,
 *   an entry pointing outside the index, or a validly signed map that is not
 *   the one the index named. Nothing falls through: the title is failed, with
 *   the reason in the parent area, even when a perfectly good bundled map is
 *   sitting right there. An index that does not check out is somebody serving
 *   us something, and the answer to that is to stop rather than to keep
 *   playing off a different map.
 *
 * The cost of that second rule is a denial of service: whoever can serve a
 * broken index can stop a title playing. That is the direction to fail in.
 */

import React from 'react';
import {
  lookupMap,
  RegistryRefusal,
  registryRefusalMessage,
} from './mapRegistry';
import { MapRejection } from './flashMap';
import { OFFLINE_MAP_JSON } from './offlineMapText';
import { OFFLINE_TITLE_ID } from './offlineTitle';
import { beacon } from './timingLog';
import { CatalogTitle, CheckedTitle } from './titleStatus';

/** Where a map came from. `none` means nothing served one. */
export type MapSource = 'registry' | 'bundled' | 'catalog' | 'none';

export interface ResolvedMaps {
  /** The catalog entry, with `maps` replaced by whatever served them. */
  title: CatalogTitle;
  /** Which source served each profile's map. */
  sources: Record<string, MapSource>;
  /** Set when the index refused in a way that allows no fallback. */
  refusal?: RegistryRefusal;
  detail?: string;
  mapRejection?: MapRejection;
  /** True while a configured index has been asked and has not answered. */
  waiting?: boolean;
}

export interface MapSourceOptions {
  /**
   * Where the signed index is.
   *
   * Left out, no index is consulted and the app behaves as it did before this
   * existed: the bundled or catalog map, checked the same way. Nothing in this
   * repository sets it yet, because no index has been published: the pipeline
   * builds one and nothing has been deployed. Setting it is one prop.
   */
  registryUrl?: string;
  /** The public key this build trusts, for the index and the maps it names. */
  publicKeyBase64: string;
  /** Read at the moment of the lookup, not at render. */
  nowMs: () => number;
  /** The profiles the preset in force asks for. */
  profiles: string[];
  fetchText?: (url: string) => Promise<string | null>;
  maxRegistryAgeMs?: number;
  maxMapAgeMs?: number;
}

/**
 * The refusals that mean "the index says nothing about this file".
 *
 * Only these two fall through to a map the app already holds. Everything else
 * `RegistryRefusal` can be is evidence that what was served did not check out,
 * and blocks. The list is a constant rather than a condition written at the
 * call site, so there is one place to read what falls through.
 */
export const FALL_THROUGH_REFUSALS: RegistryRefusal[] = [
  'registry-missing',
  'not-listed',
];

export function fallsThroughToLocalMap(reason: RegistryRefusal): boolean {
  return FALL_THROUGH_REFUSALS.indexOf(reason) >= 0;
}

/** What the shelf says about a title while the index has not answered. */
export const REGISTRY_WAITING =
  'The list of checked titles has not answered yet, so the picture stays hidden.';

async function defaultFetchText(url: string): Promise<string | null> {
  try {
    const response = await fetch(url, { headers: { 'cache-control': 'no-cache' } });
    if (!response.ok) {
      return null;
    }
    return await response.text();
  } catch {
    // No network is a missing index, which falls through to what is bundled.
    return null;
  }
}

/**
 * Where a map would come from with no index in the picture.
 *
 * The bundled map is told from a catalog one by being the text compiled into
 * this package for the offline title, which is the map that has to keep
 * working with the network off.
 */
export function localSource(title: CatalogTitle, profile: string): MapSource {
  const text = title.maps?.[profile];
  if (typeof text !== 'string' || text.length === 0) {
    return 'none';
  }
  if (title.id === OFFLINE_TITLE_ID && text === OFFLINE_MAP_JSON) {
    return 'bundled';
  }
  return 'catalog';
}

/** One line a reader can tell the three sources apart by. */
export function noteMapSource(
  titleId: string,
  profile: string,
  source: MapSource,
  detail?: string,
): void {
  console.info(
    `[mapSource] ${titleId} ${profile}: served by ${source}${
      detail ? `, ${detail}` : ''
    }`,
  );
  beacon('map.source', { titleId, profile, source, detail });
}

/** The answer with no index configured: today's behaviour, and synchronous. */
export function withoutRegistry(
  title: CatalogTitle,
  profiles: string[],
): ResolvedMaps {
  const sources: Record<string, MapSource> = {};
  for (const profile of profiles) {
    sources[profile] = localSource(title, profile);
  }
  return { title, sources };
}

/**
 * A fetch that reads each URL once and keeps what it read.
 *
 * Two jobs. It stops the index being fetched once per profile and once per
 * title, and it keeps the exact bytes `lookupMap` verified so those same bytes
 * can be handed on. Fetching the map again to get its text would be a second
 * answer to the same question, and a server free to give a different one.
 */
function readOnce(fetchText: (url: string) => Promise<string | null>) {
  const seen = new Map<string, string | null>();
  return {
    seen,
    fetchText: async (url: string): Promise<string | null> => {
      if (seen.has(url)) {
        return seen.get(url) ?? null;
      }
      const text = await fetchText(url);
      seen.set(url, text);
      return text;
    },
  };
}

function blocked(
  title: CatalogTitle,
  sources: Record<string, MapSource>,
  reason: RegistryRefusal,
  detail: string,
  mapRejection?: MapRejection,
): ResolvedMaps {
  // The maps go with it. A title the index refused is not played off anything.
  return {
    title: { ...title, maps: {} },
    sources,
    refusal: reason,
    detail,
    mapRejection,
  };
}

/**
 * Ask the index about one title, then fall through where that is allowed.
 *
 * `reader` is the shared once-only fetch, so a whole catalog pass reads the
 * index once.
 */
export async function resolveMaps(
  title: CatalogTitle,
  options: MapSourceOptions,
  reader = readOnce(options.fetchText ?? defaultFetchText),
): Promise<ResolvedMaps> {
  if (!options.registryUrl) {
    return withoutRegistry(title, options.profiles);
  }

  const maps: Partial<Record<string, string | null>> = { ...(title.maps ?? {}) };
  const sources: Record<string, MapSource> = {};

  for (const profile of options.profiles) {
    const verdict = await lookupMap({
      registryUrl: options.registryUrl,
      expectedSha256: title.sha256,
      profile,
      publicKeyBase64: options.publicKeyBase64,
      nowMs: options.nowMs(),
      maxRegistryAgeMs: options.maxRegistryAgeMs,
      maxMapAgeMs: options.maxMapAgeMs,
      fetchText: reader.fetchText,
    });

    if (verdict.ok) {
      const text = reader.seen.get(verdict.mapUrl);
      if (typeof text === 'string' && text.length > 0) {
        maps[profile] = text;
        sources[profile] = 'registry';
        noteMapSource(title.id, profile, 'registry', verdict.mapUrl);
        continue;
      }
      // The lookup read the map through this very reader, so there is no way
      // to be here with an accepted map and no bytes for it. Being here means
      // something replaced the reader underneath, and the answer to not
      // knowing what was checked is to serve nothing.
      noteMapSource(title.id, profile, 'none', 'the verified bytes went missing');
      return blocked(
        title,
        sources,
        'entry-unusable',
        'the map that was checked could not be read back',
      );
    }

    if (!fallsThroughToLocalMap(verdict.reason)) {
      noteMapSource(title.id, profile, 'none', verdict.reason);
      return blocked(
        title,
        sources,
        verdict.reason,
        verdict.detail,
        verdict.mapRejection,
      );
    }

    sources[profile] = localSource(title, profile);
    noteMapSource(title.id, profile, sources[profile], verdict.reason);
  }

  return { title: { ...title, maps }, sources };
}

/** Every title in a catalog, sharing one read of the index. */
export async function resolveCatalog(
  entries: CatalogTitle[],
  options: MapSourceOptions,
): Promise<ResolvedMaps[]> {
  const reader = readOnce(options.fetchText ?? defaultFetchText);
  const done: ResolvedMaps[] = [];
  for (const entry of entries) {
    done.push(await resolveMaps(entry, options, reader));
  }
  return done;
}

/** A title the index refused, as the parent area lists it. */
export function refusedTitle(resolved: ResolvedMaps): CheckedTitle {
  const reason: RegistryRefusal = resolved.refusal ?? 'registry-unparseable';
  return {
    title: resolved.title,
    status: 'failed',
    rejection: resolved.mapRejection,
    reason: registryRefusalMessage(reason, resolved.mapRejection),
    segments: [],
    hiddenMs: 0,
    verifiedProfiles: [],
  };
}

/**
 * A title whose index has been asked and has not answered.
 *
 * Pending, not verified, so it is off the shelf until the answer is in. A
 * title listed on the strength of the bundled map and then refused by the
 * index a moment later would be playable in the window between the two.
 */
export function waitingTitle(title: CatalogTitle): CheckedTitle {
  return {
    title,
    status: 'pending',
    reason: REGISTRY_WAITING,
    segments: [],
    hiddenMs: 0,
    verifiedProfiles: [],
  };
}

function answerKey(title: CatalogTitle, profileKey: string): string {
  return `${title.id}|${title.sha256}|${profileKey}`;
}

/**
 * The catalog, with the index asked about every title in it.
 *
 * With no index configured this is the catalog itself and nothing happens,
 * which is what keeps a screen that never sets `registryUrl` exactly as it
 * was. With one configured, every title reads as waiting until the answer is
 * in.
 */
export function useMapSources(
  entries: CatalogTitle[],
  options: MapSourceOptions,
): ResolvedMaps[] {
  const {
    registryUrl,
    publicKeyBase64,
    profiles,
    maxRegistryAgeMs,
    maxMapAgeMs,
  } = options;
  const profileKey = profiles.join(',');
  // Read through refs, so a caller handing over a new function on every render
  // does not ask the index again on every render.
  const nowRef = React.useRef(options.nowMs);
  nowRef.current = options.nowMs;
  const fetchRef = React.useRef(options.fetchText);
  fetchRef.current = options.fetchText;

  const [answered, setAnswered] = React.useState<Record<string, ResolvedMaps>>({});

  const local = React.useMemo(
    () => entries.map((entry) => withoutRegistry(entry, profiles)),
    // profiles is rebuilt by the caller on every render; its contents are what
    // matter.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [entries, profileKey],
  );

  React.useEffect(() => {
    if (!registryUrl) {
      setAnswered((previous) =>
        Object.keys(previous).length === 0 ? previous : {},
      );
      return undefined;
    }
    let cancelled = false;
    void (async () => {
      const done = await resolveCatalog(entries, {
        registryUrl,
        publicKeyBase64,
        nowMs: () => nowRef.current(),
        profiles: profileKey.length > 0 ? profileKey.split(',') : [],
        fetchText: fetchRef.current,
        maxRegistryAgeMs,
        maxMapAgeMs,
      });
      if (cancelled) {
        return;
      }
      const next: Record<string, ResolvedMaps> = {};
      for (const one of done) {
        next[answerKey(one.title, profileKey)] = one;
      }
      setAnswered(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [
    entries,
    profileKey,
    registryUrl,
    publicKeyBase64,
    maxRegistryAgeMs,
    maxMapAgeMs,
  ]);

  return React.useMemo(
    () =>
      local.map((one) => {
        const answer = answered[answerKey(one.title, profileKey)];
        if (answer) {
          return answer;
        }
        return registryUrl ? { ...one, waiting: true } : one;
      }),
    [local, answered, profileKey, registryUrl],
  );
}
