"""Where every artifact for a title lives.

One work directory holds every title, each under its source SHA-256:

    <workdir>/catalog.json                 the index kid mode reads
    <workdir>/.catalog.json.lock           serializes updates to that index
    <workdir>/titles/<sha256>/
        .ingest.lock                       one preparation of this title at a time
        state.json                         the ledger
        probe.json                         frame timestamps, colour tags, size
        luma.json                          luminance over time
        still.png                          the cover still, from a calm moment
        work/analysis/<preset>.json        the analyzer's own map, before scene holds
        maps/<preset>.json                 the signed map that ships
        plans/<preset>.json                the hide plan
        safe/<preset>/safe.mp4             the kid safe master
        safe/<preset>/hls/master.m3u8      the rendition the player streams
        bif/<preset>.bif                   trickplay, from the safe rendition
        bif/<preset>.json                  which moment each frame came from
        posters/<preset>/poster_NN.jpg     posters, from calm moments
        verify/cover_model_<preset>.mp4    the cover schedule over the original
        verify/report.json                 why publishing was allowed or not
        entry.json                         the catalog entry for this title

Nothing outside this module builds one of these paths by hand.
"""

from __future__ import annotations

from pathlib import Path


class TitleLayout:
    def __init__(self, workdir: str | Path, sha256: str) -> None:
        self.workdir = Path(workdir)
        self.sha256 = sha256
        self.root = self.workdir / "titles" / sha256

    # Work directory level
    @property
    def index_path(self) -> Path:
        return self.workdir / "catalog.json"

    @property
    def index_lock_path(self) -> Path:
        return self.workdir / ".catalog.json.lock"

    # Title level
    @property
    def ingest_lock_path(self) -> Path:
        return self.root / ".ingest.lock"

    @property
    def probe_path(self) -> Path:
        return self.root / "probe.json"

    @property
    def luma_path(self) -> Path:
        return self.root / "luma.json"

    @property
    def luma_metadata_path(self) -> Path:
        return self.root / "work" / "luma_metadata.txt"

    @property
    def still_path(self) -> Path:
        return self.root / "still.png"

    @property
    def still_manifest_path(self) -> Path:
        return self.root / "still.json"

    @property
    def entry_path(self) -> Path:
        return self.root / "entry.json"

    @property
    def verify_dir(self) -> Path:
        return self.root / "verify"

    @property
    def verify_report_path(self) -> Path:
        return self.verify_dir / "report.json"

    # Per preset
    def map_path(self, preset: str) -> Path:
        return self.root / "maps" / f"{preset}.json"

    def analysis_map_path(self, preset: str) -> Path:
        # Kept apart from the published map, so each file has exactly one step that
        # writes it and a cached hash of the analysis is never overwritten in place.
        return self.root / "work" / "analysis" / f"{preset}.json"

    def plan_path(self, preset: str) -> Path:
        return self.root / "plans" / f"{preset}.json"

    def safe_dir(self, preset: str) -> Path:
        return self.root / "safe" / preset

    def safe_master(self, preset: str) -> Path:
        return self.safe_dir(preset) / "safe.mp4"

    def hls_dir(self, preset: str) -> Path:
        return self.safe_dir(preset) / "hls"

    def master_playlist(self, preset: str) -> Path:
        return self.hls_dir(preset) / "master.m3u8"

    def bif_path(self, preset: str) -> Path:
        return self.root / "bif" / f"{preset}.bif"

    def bif_manifest(self, preset: str) -> Path:
        return self.root / "bif" / f"{preset}.json"

    def bif_work_dir(self, preset: str) -> Path:
        return self.root / "work" / "bif" / preset

    def posters_dir(self, preset: str) -> Path:
        return self.root / "posters" / preset

    def posters_manifest(self, preset: str) -> Path:
        return self.root / "posters" / f"{preset}.json"

    def cover_model_path(self, preset: str) -> Path:
        return self.verify_dir / f"cover_model_{preset}.mp4"

    def scene_manifest(self, preset: str) -> Path:
        return self.root / "scene_holds" / preset / "manifest.json"

    def scene_image(self, preset: str, index: int) -> Path:
        return self.root / "scene_holds" / preset / f"hold_{index:03d}.jpg"

    def verify_map_path(self, preset: str, kind: str) -> Path:
        return self.verify_dir / f"{kind}_{preset}.json"

    def relative(self, path: str | Path) -> str:
        path = Path(path)
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)
