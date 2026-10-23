# Otter grooming candidate: unsigned assessment

Recommendation: do not integrate. Licensing and estimated size are workable,
but the unchanged app policy would conceal most of the selected land excerpt.
No key was generated or accessed, no signatures or package were produced, and
no app, trust, settings, existing media or simulator state changed. The first
otter candidate and its isolated signer remain untouched.

The creator-uploaded source is Uusijani's "Otter (Lutra lutra) grooming", CC0 1.0:
https://commons.wikimedia.org/wiki/File:Otter_(Lutra_lutra)_grooming.webm
Credit: Video: Uusijani / Wikimedia Commons (CC0 1.0).
The original's 62,674,585 bytes match published SHA-1
`52f237645e7016f276f2383b1271a5238adbcebd`.

Original SHA-256:
`3083988ff7c574821fb40bea3c7a053db5625f5106f3c68e1231d2935b410b29`

The selected excerpt is source 00:30-00:46, 16 seconds, 1280x720, 25 fps, H.264
CRF 20. Original and derivative have no audio stream. The derivative is
9,624,827 bytes; three similar renditions would occupy about 28.87 MB within the
remaining 38.56 MB namespace budget. This is a size estimate, not a prepared
bundle measurement. Derivative SHA-256:
`5afbfc7e5a9cae48d42153f4e0ab23fe7a7d7d509f1da864c5cfe52194d33f45`

## Headless detector results

Eight unsigned runs used the unchanged WCAG/broadcast profiles, each with and
without the 85 inch / 4 foot room window. Original: 2,346 frames; derivative:
400 frames. Working width was 192 pixels. Missing matrix tags used the existing
HD BT.709 inference; no interpretation rule was changed. No image was displayed.

| Input | WCAG baseline flagged union | WCAG with room | Broadcast baseline | Broadcast with room |
| --- | ---: | ---: | ---: | ---: |
| Original, 93.840 seconds | 51.400 s | 80.320 s | 25.560 s | 79.040 s |
| Excerpt, 16 seconds | 3.600 s | 12.680 s | 0 s | 12.120 s |

The existing `build_app_playback_plan` calculated the union and normal guard
bands, without signing or rendering. Standard uses the room-aware WCAG map;
Broadcast and Extra cautious combine both room-aware maps.

| Excerpt preset | Covered | Uncovered | Uncovered share |
| --- | ---: | ---: | ---: |
| Standard | 14.440 s | 1.560 s | 9.75% |
| Broadcast | 14.440 s | 1.560 s | 9.75% |
| Extra cautious | 15.440 s | 0.560 s | 3.50% |

The full original's longest uncovered run is 4.760 seconds in Standard,
4.720 in Broadcast and 3.720 in Extra cautious. Its current full-source plan
therefore does not indicate a sustained 12-20-second usable interval.
This is not a clinical determination of unsafe footage. Baseline and strict-room
results differ substantially; a zero broadcast-baseline result does not erase
the other profile findings or authorize bypassing app policy. The maps do not
locate all findings spatially or prove a detector bug.

The [receipt](../../results/otter-grooming-candidate-2026-10-16/receipt.json) and
[assessment](../../results/otter-grooming-candidate-2026-10-16/assessment.json)
retain exact hashes, metadata, unsigned outputs and all post-guard intervals.
No further package work is recommended for this candidate. A separate bounded
detector-validation review may be more useful than repeated blind clip searches;
any new source still requires unchanged-policy evaluation before preparation.
