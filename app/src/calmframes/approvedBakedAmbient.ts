/** Generated only from exact approved catalogs and their checked ambient reports. */
import { loadBakedAmbient } from './bakedAmbient';
const registrations: readonly { raw: string; sha512: string }[] = [];
const documents = registrations.map(entry => loadBakedAmbient(entry.raw, entry.sha512));
export function bakedAmbientForRendition(renditionSha256?: string, preset?: string) {
  return documents.find(document => document?.renditionSha256 === renditionSha256 && document?.preset === preset) ?? null;
}
