# Woodland candidate: silent review copy

The owner selected the Lee Point Australian woodland candidate and requested a
silent option. This is a scene/preparation choice, not picture, comfort or
medical acceptance. The app still contains the Prairie Creek Forest preview.
No media, catalog, signer, trust root or package budget changed.

## Candidate identity

The local review copy is `lee-point-woodland-300s-silent-review.mp4`, SHA-256
`66d44d0888b0bc2bbc6da55614babcbf88108632b282275f115000cc5a85d9d3`.
It is not a downloadable repository release or an approved TV edition.
The [machine record](../results/woodland-silent-review-2026-10-26.json)
records its exact identity and checks.

The prepared input's encoded video packets and timestamps were copied unchanged;
all <!--n results/woodland-silent-review-2026-10-26.json:video_packets -->7500<!--/n-->
match. Audio was replaced with silent stereo AAC, retaining an audio track for
the existing player path. All decoded PCM samples are zero. The natural-speed
picture remains <!--n results/woodland-silent-review-2026-10-26.json:duration_seconds -->300<!--/n-->
seconds at <!--n results/woodland-silent-review-2026-10-26.json:video_fps -->25<!--/n-->
frames per second. A middle frame was inspected; no picture-quality or comfort
acceptance follows. Dense foliage remains visibly soft at the existing delivery
bitrate. No analyzer or full preparation rerun was performed.

The original and excerpt hashes were reverified against the prior handoff.
That handoff reports passing preparation on a different exact file with an
unapproved temporary signer. Its maps cannot authorize this changed file, and
no private key was read or copied. Exact approved preparation, delivery checks
and native observation remain necessary before activation.

## Attribution and rights record

Gary wanders a lot, "Australia NT Lee Point woodland 4K - earmarked for clearing",
[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), via
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Lee_Point_woodland_in_the_Northern_Territory,_Australia.webm).
Changed: excerpted at natural speed, downsampled and re-encoded by the earlier
preparation; this review copy replaces the original audio with silence.
No endorsement implied. Retain attribution, license/source links and the change
notice with any later distribution. The current Commons record still marks its
external license review pending; the prior handoff reports checking the original
YouTube license statement. No new license or rights grant is inferred here.

## Smallest remaining packaging decision

The candidate occupies
<!--n results/woodland-silent-review-2026-10-26.json:output_bytes -->18253867<!--/n-->
bytes. The existing namespace has only
<!--n results/woodland-silent-review-2026-10-26.json:budget_review.current_headroom_bytes -->4962041<!--/n-->
bytes free. The [exporter](../pipeline/packaged_library.py) writes separate
per-preset media; the [package checker](../app/tools/check_prepared_library.mjs)
counts actual files and rejects aliases. Byte-identical profiles are not an
existing supported deduplication route.

[Fresh-directory replacement](../pipeline/LOCAL_LIBRARY.md) is supported, but
removing the two non-consumer generations and replacing the old Forest bundle
would leave only
<!--n results/woodland-silent-review-2026-10-26.json:budget_review.headroom_if_nonconsumer_and_old_forest_replaced_bytes -->20965926<!--/n-->
bytes. That can hold one copy before metadata overhead, but the current
three-copy layout needs
<!--n results/woodland-silent-review-2026-10-26.json:budget_review.candidate_three_copies_bytes -->54761601<!--/n-->
bytes. Nothing was removed. A reviewed shared-rendition packaging design is the
smallest identified route that could preserve the other titles and existing
budget. It needs separate architecture/trust review before implementation;
there is no budget increase or duplicate-bundling approval.

Item 7 stays partial. Sea Otters still lacks a qualifying source; exhausted
searches were not repeated. The silent candidate is ready for owner picture
review, while packaging and approved signing remain separate blockers.
