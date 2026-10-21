# Prepare a local library receipt

This AWS-free workflow prepares one video through the existing analyzer,
signed-map, rendition and verification pipeline. Nothing plays automatically,
and nothing deploys or starts a server.

From the repository root, use the pinned Python environment, install flashmap
and have ffmpeg plus ffprobe on PATH. Keep your signing private key outside the
checkout and the artifact workspace. Use its matching public key; the command
does not create, copy or export either key.

```sh
.venv/bin/python -m pipeline.local_library prepare /path/to/video.mp4 \
    --workdir /path/to/local-library \
    --key /private/path/team_key.pem --pub /private/path/team_key.pub.pem \
    --title "A local title"
```

The default prepares WCAG, broadcast and extra-cautious renditions using the
app-v1 recipe: Standard uses WCAG; Broadcast and Extra cautious use the union of
WCAG and Broadcast, with the app's own guard bands and minimum cover lengths.
All maps use an explicit 85 inch / 4 foot room, covering the current selectable
room sizes. The pre-covered picture and opaque live fallback use the same plan.
Per-interval scene descriptors are omitted for these union plans; ordinary
signed ingest and the labelled Harbor practice demo still support scene images.
To choose a subset, add `--presets wcag,broadcast`; required union maps must be
present together. All requested presets must finish normal verification. There
is no skip-verify option or threshold override here.

The command prints JSON and saves `local-receipts/<source-sha256>.json` in the
workspace. A ready receipt means **ready for local playback of the prepared
rendition**, not clinical safety or real-TV validation. It includes the source
hash, title, requested presets, actual verification outcome, checked-artifact
hashes and relative paths for the safe MP4, prepared HLS, signed map and report.
No original media, cover model or key path is offered as a playback artifact.
The source must remain outside the workspace.

Exit status is `0` for ready, `1` for a failed preparation or publication guard,
and `2` for an invalid request, inaccessible workspace or overlapping import.
Failed receipts contain no playable artifacts. A failed reimport withdraws its
older ready item before any pipeline work begins. Open its verification report
when present to inspect measurement failures, then fix the input or keys and
run the command again.

`local-library.json` is a deterministic snapshot of ready receipts only. It is
separate from the pipeline's ordinary `catalog.json`. It is not a served index;
use the explicit package export below to connect it to the app shelf. Refresh
it after changing or moving artifacts:

```sh
.venv/bin/python -m pipeline.local_library catalog \
    --workdir /path/to/local-library
```

Refresh checks the current report, complete preset/source identity, pipeline
record and checked input bytes. Missing, altered, malformed or unsafe-path
records are excluded. The snapshot is point-in-time bookkeeping, not an
authentication boundary or a replacement for signature checks during playback.
Do not copy the entire workspace into a serving directory: it also contains
the pipeline's private work files and cover models. Use only the receipt's
prepared artifact allowlist.

For local use, read the verification report and its outcome first. Select a
requested preset and use its `artifacts[preset].safe_master`, or package only
its prepared HLS files with the signed map in a player integration that keeps
normal signature and fail-closed checks. Do not open the original video or
cover model as a shortcut. Native image, caption and timing composition on a
physical television still need measurement.

Imports through this wrapper share a nonblocking OS file lock. A second import
into the same workspace refuses until the first finishes. Do not run the older
ingest CLI or other writers against that workspace concurrently: they do not
participate in this wrapper lock. Receipt count, workspace file count and JSON
metadata size are bounded in `pipeline/local_library.py`.


## Include prepared titles in a Vega build

```sh
.venv/bin/python -m pipeline.packaged_library export \
    --workdir /path/to/local-library --pub /private/path/team_key.pub.pem \
    --output app/assets/raw/prepared-library
.venv/bin/python -m pipeline.packaged_library check \
    --output app/assets/raw/prepared-library
cd app && npm run build:debug
```

The exporter rechecks receipts, signatures, current bytes and the complete app
cover schedule. Export requires all three presets. It copies only prepared
MP4s, signed maps and bounded external WebVTT captions, never original media or
a private key. The compiled catalog contains the reviewed public key, original
source identity, separate rendition identities, timing offsets and exact paths.
The app accepts that key only for an exact compiled title/preset membership.

The namespace is limited to 16 titles and 128 MiB, including retained immutable
generations. Unknown files, aliases and modified generations are rejected.
Previous generations remain so a concurrent build cannot lose referenced media.
When the namespace reaches its limit, export into a fresh directory and review
that replacement; the exporter does not delete old generations automatically.
Do not add notes or other files within this namespace.

`npm run build:debug` and `npm run build:release` check the source assets before
building and each architecture's actual archive afterward. The archive check
also binds its catalog to the current build input. Normal runtime map checks
remain required. Package checks are delivery evidence, not TV timing evidence.

The committed example is an owned, non-flashing Harbor story imported through
normal analysis with neutral captions and no sham detector intervals. Reproduce
it with a fresh work directory (this rotates its temporary signer):

```sh
.venv/bin/python -m eval.prepare_owned_harbor \
    --workdir build/owned-harbor-new \
    --output app/assets/raw/prepared-library
```

The temporary private key is deleted when preparation exits. Its public half
and the normal receipts stay in the work directory. The separate bundled
`Harbor story (benign demo)` intentionally uses labelled practice holds; do not
present those holds as detector findings.
