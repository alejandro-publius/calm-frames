# Legacy Metro image-size adapter

The SDK's transitive Metro 0.54.1 calls `require('image-size')` as a function
with a Buffer or synchronous filename. Official image-size 2.x instead exports
a named parser and an asynchronous file API. This private local package restores
the legacy call shape without copying any image parsers. Buffer and filename
parsing both delegate to the exact official `image-size@2.0.4`, installed under
the explicit `image-size-modern` npm alias. Its ICNS fix addresses
[GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr).

Synchronous filename reads keep the legacy 512 KiB header limit, handle partial
reads, and close the file in a finally block on success or failure. Callback
filenames use the upstream bounded asynchronous file API. The `types` property
comes from upstream. The adapter does not change the current Metro bundler,
native image decoding, signed map verification or safety thresholds.

The app declares the local adapter under the `image-size` dependency key and
scopes its override to Metro 0.54.1. The local package keeps its own name and
version; the separate official parser keeps its registry version and integrity
in the lockfile and dependency audit. No audit exceptions are added.

Tests in `test/calmframes/imageSizeLegacy.test.ts` exercise legacy Buffer,
filename and callback callers, actual Metro asset building, file cleanup and
the malformed ICNS regression. The malformed parser runs only in a child
process with a hard timeout; timeout is a test failure, never a passing reject.
