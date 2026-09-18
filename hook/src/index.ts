/**
 * Calm Frames flash guard, for any Vega app that plays video through
 * @amazon-devices/react-native-w3cmedia.
 *
 * Give it the player and where the map is. It verifies the map, works out
 * which spans of the title have to be hidden, drives the cover, shows and
 * announces the cards, and hands back the one function every seek path has to
 * use.
 *
 *     const guard = useFlashGuard({
 *       mediaRef: videoRef,
 *       mapUrls: { wcag: title.mapUrl },
 *       expectedSha256: title.sha256,
 *       publicKeyBase64: OUR_PUBLIC_KEY,
 *       ready: isVideoInitialized,
 *     });
 *
 *     <CoverLayer visible={guard.covered} mode={guard.coverMode} />
 *     <CalmCard card={guard.card} onSkip={guard.skipTo} />
 *
 * See README.md for the four line integration and docs/INTEGRATION_DIFF.md in
 * the Calm Frames repository for the same change made against a clean
 * vega-video-sample checkout.
 */

export { announceForAccessibility, resetAnnouncements } from './engine/announce';
export { default as CalmCard } from './engine/CalmCard';
export type { CalmCardProps } from './engine/CalmCard';
export { CALM_COLORS, CALM_SPACE, CALM_TYPE } from './engine/calmStyles';
export {
  AFTER_CARD_MS,
  cardAt,
  cardChanged,
  COUNTDOWN_LEAD_MS,
  NO_CARD,
} from './engine/cards';
export type { Card, CardKind } from './engine/cards';

// The map registry: given a file this app already has, find out whether a
// checked map exists for it. lookupMap does the whole job, verifying the index,
// re-checking the map it names through the same signature path the player uses,
// and refusing with a reason rather than guessing.
export {
  DEFAULT_MAX_REGISTRY_AGE_MS,
  SUPPORTED_REGISTRY_VERSION,
  entryFor,
  isInsideRegistry,
  lookupMap,
  registryRefusalMessage,
  resolveMapUrl,
  verifyRegistry,
} from './engine/mapRegistry';
export type {
  LookupOptions,
  LookupVerdict,
  RegistryEntry,
  RegistryRefusal,
  RegistryVerdict,
  VerifiedRegistry,
  VerifyRegistryOptions,
} from './engine/mapRegistry';
export { default as CoverLayer, COVER_Z_INDEX } from './engine/CoverLayer';
export type { CoverLayerProps, ReferencePatch } from './engine/CoverLayer';
export {
  buildCoverIntervals,
  DEFAULT_GUARD_BAND_MS,
  DEFAULT_MIN_COVER_MS,
  intervalAt,
  isCovered,
  millisecondsUntilNextCover,
  nextIntervalAfter,
  totalCoveredMs,
} from './engine/coverSchedule';
export type {
  CoverInterval,
  CoverReason,
  CoverScheduleOptions,
  FlashSegment,
} from './engine/coverSchedule';
export {
  DEFAULT_MAX_MAP_AGE_MS,
  rejectionMessage,
  SUPPORTED_MAP_VERSION,
  verifyFlashMap,
} from './engine/flashMap';
export type {
  MapRejection,
  MapVerdict,
  VerifiedFlashMap,
  VerifyMapOptions,
} from './engine/flashMap';
export {
  clampSettings,
  coverOptionsFor,
  DEFAULT_SETTINGS,
  mapCoversRoom,
  PRESET_NAMES,
  PRESETS,
  roomFieldFraction,
  unionSegments,
} from './engine/household';
export type { HouseholdSettings, PresetName } from './engine/household';
export {
  addHideEntry,
  describeHideEntry,
  emptyHideLog,
  totalHiddenMs,
} from './engine/hideLog';
export type { HideCause, HideLogEntry, HideLogStore } from './engine/hideLog';
export { SafeMediaControlHandler } from './engine/SafeMediaControlHandler';
export {
  createSeekEngine,
  isPreviewAllowed,
  planSeek,
  SEEK_SOURCES,
} from './engine/seekSafety';
export type { SeekEngine, SeekPlan, SeekSource } from './engine/seekSafety';
export { checkTitle, checkTitles, kidModeTitles } from './engine/titleStatus';
export type { CatalogTitle, CheckedTitle, TitleStatus } from './engine/titleStatus';
export { useCoverHarness } from './engine/useCoverHarness';
export type { MediaElementLike } from './engine/useCoverHarness';
export { useFlashGuard } from './engine/useFlashGuard';
export type { FlashGuardOptions, FlashGuardState } from './engine/useFlashGuard';
