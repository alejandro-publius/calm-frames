# Judging package

Start with [the offline guide](index.html) or [its Markdown alternative](GUIDE.md).
Everything needed for the guide's runtime is inside this directory. There is no
installation, external font, analytics, video, autoplay or remote fetch. Keep the
directory intact. Optional original-source and credit links open external sites
only when followed.

| Reviewer need | Artifact |
|---|---|
| Product walkthrough and quickstart | [Guide](GUIDE.md) |
| Official-criteria mapping and gaps | [Rubric matrix](RUBRIC_MATRIX.md) |
| Intended benefit without invented validation | [Impact and differentiation](IMPACT_AND_DIFFERENTIATION.md) |
| Primary-source provenance and live-access limits | [Source register](PRIMARY_SOURCES.md) |
| Code-grounded system explanation | [Architecture](ARCHITECTURE.md) |
| Reproducible recorded developer issues | [Friction draft](FRICTION_LOG_DRAFT.md), [product feedback](PRODUCT_FEEDBACK_DRAFT.md) |
| Proposed README, Devpost and screenshot copy | [Presentation drafts](PRESENTATION_DRAFTS.md) |
| Claude's replacement-video handoff | [Demo evidence brief](DEMO_EVIDENCE_BRIEF.md) |
| Claim-to-file and number-to-key audit | [Claims ledger](CLAIMS_LEDGER.md) |
| Mac integration and factual gaps | [Handoff](HANDOFF.md) |
| Guide checks, rendered views and factual review | [Validation](validation/README.md) |

The package is based on `13551e4`, describing validated source `d96c088`, while
preserving submitted baseline `bf2f615`. It reuses the reviewer-page implementation
from `3db0505`. Newer Claude benchmarks are unavailable. No new application tests,
native observations or video work are claimed.

`assets.json` records byte identities for reused assets. `evidence/` includes
selected release fields, historical source excerpts and code excerpts. Host paths,
device/account metadata and logs are omitted from the selected release JSON.
`validation/` contains checks and web-guide renders, clearly separated from native
screenshots in `assets/`.

All authored Markdown has a readable HTML counterpart in `reading/`. The optional
authoring script `render_reading.cjs` uses the environment's existing `marked`
package (17.0.5 in this task); the generated guide needs no package at runtime.
After editing a document, regenerate its readable copy and rerun bounded link and
browser checks. Do not rebuild the app or rerun benchmarks for a documentation change.
