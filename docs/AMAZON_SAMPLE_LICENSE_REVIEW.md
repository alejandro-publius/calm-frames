# Amazon sample license notice review

Reviewed October 10, 2026 against Calm Frames checkpoint `d451a90`. This records
source provenance and an unresolved inconsistency in Amazon's public sample.
It does not establish that redistribution is prohibited or that the sample's
root license overrides a file-specific notice. No upstream request has been sent.

## Verified source and notices

Calm Frames copied `AmazonAppDev/vega-video-sample` at `v0.24-RN83`, commit
[`ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`](https://github.com/AmazonAppDev/vega-video-sample/tree/ef8e4da89b22ef7973d0d41beedfa2b42f7bb272).
The following public upstream files were fetched directly and inspected during
this review:

- [Root LICENSE](https://raw.githubusercontent.com/AmazonAppDev/vega-video-sample/ef8e4da89b22ef7973d0d41beedfa2b42f7bb272/LICENSE)
  grants MIT No Attribution (MIT-0), including permission to copy, modify,
  publish, and distribute. The local copy is [`app/LICENSE`](../app/LICENSE).
- [Tracked ShakaPlayer.ts](https://raw.githubusercontent.com/AmazonAppDev/vega-video-sample/ef8e4da89b22ef7973d0d41beedfa2b42f7bb272/src/w3cmedia/shakaplayer/ShakaPlayer.ts)
  begins with `AMAZON PROPRIETARY/CONFIDENTIAL` and says use must comply with
  an accompanying `LICENSE.TXT`. The same notice remains in the local
  [`ShakaPlayer.ts`](../app/src/w3cmedia/shakaplayer/ShakaPlayer.ts).
- [Supplied Shaka integration archive](https://raw.githubusercontent.com/AmazonAppDev/vega-video-sample/ef8e4da89b22ef7973d0d41beedfa2b42f7bb272/shaka-setup/shaka-rel-v4.8.5-r1.2.tar.gz)
  is byte-identical to the tracked local archive. It contains <!--n results/cloud_continuation_2026-10-10.json:license_review.notice_source_files -->13<!--/n--> source files
  carrying that notice, including all <!--n results/cloud_continuation_2026-10-10.json:license_review.polyfill_source_files -->6<!--/n--> polyfills, `PlayerInterface.ts`,
  `ShakaPlayer.ts`, and <!--n results/cloud_continuation_2026-10-10.json:license_review.sample_components -->5<!--/n--> example components. No archive member supplies
  a LICENSE or NOTICE file.
- The [root LICENSE.TXT URL](https://raw.githubusercontent.com/AmazonAppDev/vega-video-sample/ef8e4da89b22ef7973d0d41beedfa2b42f7bb272/LICENSE.TXT)
  returned HTTP 404. This checks that exact path; it does not prove that
  applicable terms cannot exist elsewhere.

| Fetched upstream file | Bytes | SHA-256 |
|---|---:|---|
| `LICENSE` | <!--n results/cloud_continuation_2026-10-10.json:license_review.upstream_files.0.bytes -->951<!--/n--> | `b536616d94ecb64a8b08ed9ef4def0693ff7665348255ef0dd672c3ff951d432` |
| `src/w3cmedia/shakaplayer/ShakaPlayer.ts` | <!--n results/cloud_continuation_2026-10-10.json:license_review.upstream_files.1.bytes -->17057<!--/n--> | `dfab51c125235a0ffc7c4dec9b1e0dd86fec52475f74bcb2bb9c2287dc80a574` |
| `shaka-setup/shaka-rel-v4.8.5-r1.2.tar.gz` | <!--n results/cloud_continuation_2026-10-10.json:license_review.upstream_files.2.bytes -->71978<!--/n--> | `f5e475b8a3793e56b2f888936f05424f672658abeac6c55e3d0e7073e06a8b8e` |

The same three paths fetched from upstream `main` returned those same hashes
on October 10. The table identifies upstream bytes; it does not claim the
locally modified player wrapper is identical to upstream.

## How these files enter the app

[`build.sh`](../app/shaka-setup/build.sh) extracts the supplied archive and
builds the Shaka integration. [`copyOutputs.sh`](../app/shaka-setup/copyOutputs.sh)
copies its source and polyfills into `app/src/w3cmedia/`, preserves the separately
tracked player wrapper, and removes five example components. In the archive,
the affected DOM parser is `shaka-rel/src/polyfills/DOMParserPolyfill.ts`.
Its extracted destination is generated and is not tracked separately by Git.

The wrapper imports and installs the polyfills. `VideoHandler.ts` imports that
wrapper at module scope and constructs it for adaptive playback. These files
cannot be classified as unused just because the recorded demo uses a particular
playback route.

This review preserved every notice and changed no native source, archive,
dependency, or package input. The private draft release and source history
already contain the integration; this review does not change their access.

## Resolution options

The smallest resolution is an explicit upstream clarification or corrected
notice identifying which terms apply to the wrapper and the archive's source.
The public MIT-0 grant is relevant evidence, but the contradictory file-specific
reference remains unresolved in this review.

Oct 11: sending the request below is on Alex's dated list in docs/STATUS.md,
by Oct 13, because an answer has to have time to arrive before the repository
goes public on Oct 21. NOTICE and the README's licence table now state the
conflict in the open, so a public reader meets it from us rather than from
the file headers, whichever way the answer goes.

Replacing the old `xmldom` package with the maintained MIT-licensed
`@xmldom/xmldom` can address dependency advisories after compatibility testing.
It does not resolve Amazon's wrapper or polyfill notices. Likewise, independently
replacing only the DOM parser leaves the other affected files and the archive.

Removing or replacing the entire integration would require a separate playback
change and native validation. Removing files from a new commit would also leave
their earlier versions in repository history and existing release artifacts.
Do not remove notices, invent `LICENSE.TXT`, or treat a regenerated build as a
new license grant.

## Draft clarification request (not sent)

> In `AmazonAppDev/vega-video-sample` at `v0.24-RN83`
> (`ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`), the root LICENSE grants MIT-0,
> but `src/w3cmedia/shakaplayer/ShakaPlayer.ts` and 13 source files inside
> `shaka-setup/shaka-rel-v4.8.5-r1.2.tar.gz` say
> "AMAZON PROPRIETARY/CONFIDENTIAL" and refer to an accompanying LICENSE.TXT.
> The archive contains no license file, and the root LICENSE.TXT URL returns
> 404. Could you confirm whether MIT-0 covers these integration files and their
> redistribution in source and compiled Vega applications, or provide the
> applicable LICENSE.TXT and clarify the conflicting notices? We have preserved
> the existing notices.
