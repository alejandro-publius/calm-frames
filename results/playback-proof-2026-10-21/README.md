# Playback Proof experiment

Isolated branch `codex/playback-proof-2026-10-21`, based on the submission
baseline `4e01b4b` and the separate reviewer-doc correction `bf2f615`.
No prepared media, signing approvals, guard, simulator or demo recording changed.
This experiment is not installed or merged into the submission candidate.

In a prepared title's Details, choose More info, then Playback proof & details.
Source, Prepared and Selection buttons show one stage at a time without playback
or animation. Back restores focus to the opener. The existing detailed record
remains below the summary.

The compiler reads the existing exact catalog approvals, checks the complete
prepared namespace and each report, and produces per-title, per-preset records.
Acadia includes full output-analysis records. The ordinary verification reports
record output finding counts but do not record the output analyzer version;
the UI says so rather than copying the source version into that field.
The generated record is checked against the selected edition, map identities,
report and actual source findings. It cannot authorize playback or remove cover.
Native bytes are checked at build time, not hashed again by this screen.

```sh
cd app
node tools/playback_proof.mjs --write
node tools/playback_proof.mjs --check
node --test tools/playback_proof.test.mjs
```

Normal native prebuild, release preparation (including package reuse), and CI
check that the committed summary reproduces. There is no new signer or runtime
catalog import. Altered or missing evidence cannot become a matching proof card.
Source and rendition substitutions still hit the existing no-media refusal.

[verification.json](verification.json) records the checks and limitations.
The full app run in the isolated checkout hit four existing path-sensitive
assertions because it reads the baseline's installed dependencies through a
symlink. The corresponding baseline suites pass with their normal paths.
No snapshots were rewritten to conceal this difference. TypeScript passes with
`--preserveSymlinks`; a fresh-dependency CI run remains needed. Native layout,
remote scrolling and focus must be reviewed after coordination with the demo task.
No clinical safety or individual comfort result follows from this evidence.
