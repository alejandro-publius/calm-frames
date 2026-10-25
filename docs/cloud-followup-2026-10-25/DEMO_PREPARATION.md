# Production inputs prepared, generation still parked

Original item 16 remains partial. The existing renderer already checks exact
source/package identity, raw capture receipts, hashes, full credits, native
ambient audio and immutable input snapshots. It was not rebuilt or replaced.
The [new input plan](../../results/cloud-followup-2026-10-25/demo-input-plan.json)
derives shot intervals and all eight unchanged narration cues from the existing
approved timeline. It is deliberately not a runnable render manifest.

The old timeline names source `12125b2970342b5376b0bc7964383e547b407376`.
The current product is not yet accepted or packaged, so the plan leaves accepted
source and package identity unset. The supplied fbe53bf JPEGs and transcripts
are reference evidence only; they cannot become current-source moving footage.
No missing asset has been represented as present.

| Needed raw native take | Minimum usable duration | Purpose and acceptance boundary |
|---|---:|---|
| `native_home` | 10 seconds | Current Home and deliberate browsing; preserve actual focus and opening behavior. |
| `native_details` | 12 seconds | McWay Details and Watch; do not hide waiting or insert a mock native screen. |
| `native_ambient` | 70 seconds | One uninterrupted natural-speed app passage with its actual app audio, occupying timeline 45 to 115 seconds. No loop, stretch, replacement sound or hidden cut. |
| `native_return` | 20 seconds | Same fictional profile/edition, real Resume or Start over, retaining protection. |
| `native_proof` | 9 seconds | Actual Playback Proof and its non-authorizing role. |

Each take needs the full accepted source SHA, installed package SHA-256, original
raw-take SHA-256 and a hashed JSON capture receipt. The receipt fields and exact
matching values are enforced by the existing
[renderer](../cloud-integration-2026-10-23/demo/render_demo.py). Capture scope is
app window and app audio only, with fictional profiles and no PIN entry or
private household material. The raw duration may need handles beyond the minimum
usable segment; do not generate a false 70-second take from a short source.

Five illustrations and narration clips n01 through n08 are still absent.
Illustrations must be labelled story art, never native captures. The six-second
closing credit hold and full source/license credits must remain. The approved
script, calm built-in voice selection and budget decisions already exist.
Reconcile the script once against the accepted product, show material changes,
then resume generation. Secure API access is a later-stage requirement; do not
paste a key or regenerate speech now.

## Ready commands once those actual inputs exist

Use a private copy of the historical timeline. Replace its stale source/package
fields and populate only verified asset paths, hashes and capture receipts.
Retain the approved cue text and script hash unless a revision is reviewed.
From the repository root, with `CALM_DEMO_MANIFEST` and `CALM_DEMO_OUTPUT` set to
the actual private paths:

```sh
python3 docs/cloud-integration-2026-10-23/demo/render_demo.py \
  --manifest "$CALM_DEMO_MANIFEST" --check-only
python3 docs/cloud-integration-2026-10-23/demo/render_demo.py \
  --manifest "$CALM_DEMO_MANIFEST" --outdir "$CALM_DEMO_OUTPUT" --render
```

Run sequentially and stop on error. Inspect the output receipt, exact file and
subtitles, then use the repository's normal video gate and full human listening/
viewing review. No source test or synthetic TEST ONLY encode supplies that
acceptance. Purchase, public upload and submission changes remain outside this
pass. No 111 MB archive is required: current accepted-build raw takes are the
missing inputs, not a repeat of the old screenshot handoff.
