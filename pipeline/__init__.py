"""Calm Frames ingest and verify pipeline.

Lane 3. Everything here runs the same locally and inside the ingest container
that the Fargate task starts, so nothing may depend on being on a developer's
Mac.

Module map:

- ``hashing``          source SHA-256, the key everything else is filed under
- ``ffmpegtool``       the only place that starts ffmpeg or ffprobe
- ``probe``            real frame timestamps, colour tags, resolution, duration
- ``flashmap_adapter`` the only place that knows the flashmap CLI and the map
                       file format, so tests can run against a fake analyzer
- ``hideplan``         segments plus guard band, merged, red always opaque
- ``render``           kid safe rendition and the cover model used by verify
- ``posters``          calm moment picking and poster extraction
- ``bif``              BIF trickplay writer and reader
- ``state``            the ledger that makes a re-run skip finished work
- ``catalog``          the catalog entry a title gets once verify passes
- ``ingest``           the orchestrator
- ``verify``           the step that blocks publishing
"""

__all__ = [
    "PipelineError",
    "VERSION",
]

# Bumped when a change invalidates work already on disk. Every step fingerprint
# includes it, so raising it makes the next run redo everything.
VERSION = "1"


class PipelineError(RuntimeError):
    """Any failure that should stop a title reaching kid mode."""
