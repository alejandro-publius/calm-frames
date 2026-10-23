/** Reviewed, compiled presentation metadata only. This grants no media authority. */
import { loadSceneBridges, SceneBridgeAsset, SceneBridgeDocument } from './sceneBridges';

// Add exact JSON text and its reviewed SHA-512 only after creator/owner review.
// Acadia has no verified creator description and no eligible six-second cover.
// Test fixtures stay in tests and the local authoring editor.
const registrations: readonly { raw: string; sha512: string }[] = [];
const documents = registrations.map(entry => loadSceneBridges(entry.raw, entry.sha512));

export function sceneBridgesForAsset(asset: SceneBridgeAsset): SceneBridgeDocument | null {
  return documents.find(document => document &&
    document.titleId === asset.titleId &&
    document.sourceSha256 === asset.sourceSha256 &&
    document.renditionSha256 === asset.renditionSha256 &&
    document.durationMs === asset.durationMs &&
    document.renditionStartOffsetMs === asset.renditionStartOffsetMs) ?? null;
}
