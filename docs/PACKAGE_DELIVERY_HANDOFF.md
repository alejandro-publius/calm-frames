# Verified package delivery handoff

This implements a generic operator review path and a data-driven compiled TV list.
It does not implement on-device file import. Exact approval is still required for
each bundle, catalog and public key, followed by a checked app build/install.
The sole consumer approval remains the original Acadia package. Acadia is explicitly
labeled an existing approved fixture in staging; this is not evidence of a new title.

Worktree: `/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-package-staging`.
Branch: `codex/package-staging-2026-10-18`, based on `076247a`.

## Implemented behavior

`pipeline.package_delivery` validates an exported package through the existing strict
checker: original verification reports, signed maps, source identity, byte hashes,
paths, rendition metadata and package bounds. It records a receipt in a separate
operator workspace without changing exported media, app assets or trust records.

An exact match against `app/config/approved-prepared-libraries.json` reports
`approved_for_build`. Otherwise it reports `ready_for_approval`, with the exact
identity tuple and an explicit unknown-signer blocker where applicable. Both states
have `can_watch: false` and `installed_by_staging: false`. Signature validity under
a declared key is not approval. Invalid packages fail closed as `blocked`.

Repeated staging of unchanged bytes reuses the ticket. Replaced packages invalidate
the old review and must be canceled before a fresh review. `check` revalidates the
current files, identities and approvals; it never accepts a cached status as authority.
Cancellation revokes the ticket without deleting package files or changing TV content.

The local intake page adds Stage delivery review, Recheck delivery files and Cancel
delivery review after export. It has no Watch or Install action. A failed recheck
changes the display to blocked while retaining the cancellation handle. Canceling
the entire intake also cancels its delivery review. The existing polling focus
restoration remains: a removed control falls back to its import article, or the
title input if that import was removed. Native TV routes are unchanged.

The TV consumer list now reads generated approved catalogs instead of filtering for
one hardcoded source hash. `app/tools/approved_prepared_libraries.mjs` generates/checks
that module from exact approval data and package manifest bytes. The build gate
checks every approved catalog digest and public-key fingerprint, the generated text,
required delivered bundles, and the unchanged 64 MiB combined package bound.
Existing exact-route verification still selects the key; route-supplied catalogs or
keys cannot enter the list. Harbor remains a regression fixture outside the consumer list.

## Run the existing approved fixture now

No server restart, key or native action is needed. From this worktree:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/flashmap/src:$PWD" /Users/alexvintera/calm-frames/.venv/bin/python -m pipeline.package_delivery check \
  --staging-root /Users/alexvintera/Documents/Codex/2026-10-15/task/delivery-staging-acadia-fixture/reviews \
  --ticket c557e314876a4270bae9c0dbb382c7a3
```

The fixture package is at the sibling directory
`delivery-staging-acadia-fixture/package`. It is a byte copy of the existing approved
Acadia bundle and original report, with the existing canonical catalog module.
The [recorded fixture result](../results/package-delivery-2026-10-18/acadia-fixture-stage.json)
contains all file hashes. Stage, repeated stage and check returned identical results.

For another completed export, the generic commands are:

```sh
python -m pipeline.package_delivery inspect --package /absolute/export --expected-source FULL_SOURCE_SHA256
python -m pipeline.package_delivery stage --package /absolute/export --expected-source FULL_SOURCE_SHA256 --staging-root /absolute/separate-reviews
python -m pipeline.package_delivery check --staging-root /absolute/separate-reviews --ticket RETURNED_TICKET
python -m pipeline.package_delivery cancel --staging-root /absolute/separate-reviews --ticket RETURNED_TICKET
```

Use the project Python environment with `flashmap/src` and the repository on
`PYTHONPATH`. Paths must be real directories, not symlink aliases. Existing exports
are inputs; these commands do not acquire, analyze, sign or regenerate video.

The already running intake server was preserved and still runs its previous code.
To use the new web controls later, start this checkout's existing `pipeline.local_intake
serve` command with a separate local workspace and unused loopback port, or arrange
a controlled restart of the existing service. Do not claim that running server was
upgraded by these source edits. CLI staging works independently now.

## Actual operator steps for a future exact-approved title

1. Stage and review the complete exported package. Resolve any integrity failures;
   do not substitute a passing signature for an approval decision.
2. Obtain approval for the precise `bundleId`, `catalogSha256`, public-key fingerprint,
   content and consumer membership. A familiar signer alone never approves a new
   bundle. The receipt's `approval_request` lists the three exact identity fields;
   the staging tool does not write an approval record.
3. In an isolated integration checkout, copy only the approved immutable bundle
   directory and its referenced original reports into `app/assets/raw/prepared-library/`.
   Preserve all retained bundles/reports and the existing root `catalog.json` and
   `catalog.ts`; do not replace the primary regression catalog with the new export.
4. Add the reviewed tuple, `consumer`, a display label and the actual approval
   reference to `app/config/approved-prepared-libraries.json`. This is a reviewed
   approval-data change, not a runtime user import. No handwritten title-specific
   TypeScript, key dispatch or Home filtering is needed.
5. Run `node app/tools/approved_prepared_libraries.mjs --write`, then
   `node app/tools/check_prepared_library.mjs --require-reports`, focused app tests,
   TypeScript and lint. The generator refuses a changed approved manifest/signer;
   the strict delivery check refuses missing reports, tampered bytes and over-budget
   combined delivery. Stop on failure; do not remove checks or silently drop old titles.
6. Build/install through the existing separately reviewed workflow, then verify
   selection, exact media identity and remote return focus. No such build/install
   happened in this pass.

The exact remaining trust decision for any future title is step 2. No new signer,
catalog membership or Prairie package was approved here. Prairie remains frozen and
outside the consumer list. Guarded resume was not added; existing seek/cover guards
and playback behavior are unchanged.

## Validation and limits

- 55 Python intake/delivery tests passed: real signed Acadia fixture, repeated and
  replaced packages, wrong source, wrong signer after rehash, changed media/catalog,
  missing reports, symlinks, cancellation and failed recheck state recovery.
- 9 approval-generation tests and 23 existing delivery-gate tests passed: exact
  catalog/key identity, duplicate approvals, altered/missing generated module,
  symlink rejection, report identity, byte inventory and package boundaries.
- 59 app tests passed across packaged library, Home selection, prepared analysis
  and Parents navigation. Runtime unapproved catalog/key substitutions stay rejected.
- TypeScript passes with `--preserveSymlinks`, needed only because this isolated
  checkout reuses the existing node_modules directory through a symlink. Without
  that flag the compiler reports four unrelated Redux/Immer inferred-type path
  portability errors. No dependencies were installed and no application type was
  changed to hide them.
- Focused ESLint, Ruff, inline HTML JavaScript syntax and diff whitespace checks pass.
- Strict delivery check: four retained bundles, four original reports, 28,551,507
  bytes; the consumer registry contains only the same exact Acadia approval.

This is source and headless contract evidence. It does not establish new native
playback, visible focus, rendered browser usability or audio quality. No device,
app restart, recording, capture, network configuration, detector work or new asset
search occurred. Concurrent Claude submission edits were left untouched. No push.
