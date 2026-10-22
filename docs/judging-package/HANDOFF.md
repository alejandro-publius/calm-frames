# One Mac integration handoff

## What is complete

The package under `docs/judging-package` includes the offline guide, Markdown alternative, rubric matrix, impact/source brief, curated friction and product-feedback drafts, proposed presentation copy, replacement-demo evidence brief, claims ledger, source excerpts, asset provenance and browser-validation artifacts. The reviewer-page code is reused from `3db0505`; app, pipeline, benchmark and video work is unchanged.

This branch starts at `13551e45bd853c392489dbecce7158a04036f615`. Its evidence names upgraded source `d96c0886227f7dcfc5ae6584132a86b193359215` and submitted candidate `bf2f615e6fad0d73442fe2b9acab3067bf311e7e`. Only files under `docs/judging-package` should be in the package commit. The exact local branch and final commit are returned with the handoff in chat.

## Inspect on the Mac

1. Obtain this local commit through the normal authorized workspace transfer. It has not been pushed; a GitHub fetch cannot retrieve an unpublished cloud commit. Alternatively transfer the complete `docs/judging-package` directory, preserving its children.
2. Preserve your current work and use your own integration branch. Inspect the proposed commit with `git show --stat <PACKAGE_COMMIT>` and confirm every changed path begins `docs/judging-package/`.
3. If the commit object is available locally, cherry-pick only `<PACKAGE_COMMIT>` onto the intended review branch. Do not cherry-pick the earlier `3db0505` package merely to obtain this directory: its reuse is already incorporated here. Do not reset the integration branch or replace app/media outputs.
4. Open `docs/judging-package/index.html`, or read `GUIDE.md`. Keep the directory intact. Review the desktop and narrow **web-guide renders** in `validation/`; they are not native captures.
5. Inspect [the validation and factual-audit notes](validation/README.md), `validation/checks.json`, `assets.json`, `CLAIMS_LEDGER.md` and the factual gaps below. Browser checks cover this guide only.

The guide uses ordinary files and no network-backed runtime. If your browser permits local files, no server or installation is needed. The managed cloud browser disallows file URLs, so cloud rendering used a temporary loopback HTTP server. That policy is not an Amazon SDK defect and does not change the guide's runtime design.

## Factual gaps before public use

- The official rules could not be read live through this cloud proxy. Recheck the current Devpost judging section and update `PRIMARY_SOURCES.md` and `RUBRIC_MATRIX.md` if it differs from the dated record.
- W3C and Epilepsy Foundation primary-source pages also could not be re-read live. The package labels the repository's existing excerpts and avoids prevalence or medical-outcome numbers.
- Owner visual/audio acceptance, physical Fire TV work and complete VoiceView acceptance remain outside this package.
- Claude's newer benchmark results are unavailable in this snapshot. Do not insert estimates or reuse older results as if they were those new measurements.
- The replacement demo remains Claude's work. The included brief is a plan, not proof of recording or publication.
- Original uncropped Mac captures and the rollback application package are not bundled. Historical receipts do not prove current hosted CI or deployment state.

## Ownership and approval boundaries

Claude owns app code, pipeline changes, native review, benchmarks and the replacement video. This package proposes README and Devpost copy without editing the live versions. The submitted baseline, integration branch, signing configuration and media remain intact. No push, merge, publish or live-submission action has occurred or is implied by these integration instructions.

When integrating, retain exact source labels on screenshots, the credits, the current-source verification gap, the limits and the distinction between submitted and upgraded builds. Later factual updates should add their own evidence and commit identity rather than overwrite historical receipts.
