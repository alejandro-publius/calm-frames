/** No ambient candidate has approval. Never populate this from a route or device storage.
 * Activation needs exact catalog/rendition approval plus a reviewed metadata SHA-512.
 */
import { loadBakedAmbient } from './bakedAmbient';
const registrations: readonly { raw: string; sha512: string }[] = [];
const documents = registrations.map(entry => loadBakedAmbient(entry.raw, entry.sha512));
export function bakedAmbientForRendition(renditionSha256?: string, preset?: string) {
  return documents.find(document => document?.renditionSha256 === renditionSha256 && document?.preset === preset) ?? null;
}
