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

The default prepares WCAG, broadcast and extra-cautious renditions. To choose a
subset, add `--presets wcag,broadcast`. All requested presets must finish normal
verification. There is no skip-verify option or threshold override here.

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
separate from the pipeline's ordinary `catalog.json` and is **not automatically
connected to the app shelf**. Refresh it after changing or moving artifacts:

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
