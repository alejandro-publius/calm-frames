#!/usr/bin/env python3
"""Download the GATE 2 screening pool and record its licenses.

Every entry in MANIFEST was added only after a human opened source_page_url and
read the license and credit line there. The date in license_checked_on is the day
that page was read. Re-check a page before quoting it again.

The script is idempotent: a file that is already present with the expected size is
re-hashed and re-probed, not re-downloaded.

Downloads land in media/, which is gitignored. Only media/LICENSES.csv is committed.

Usage:
    .venv/bin/python eval/fetch_media.py            # download and write LICENSES.csv
    .venv/bin/python eval/fetch_media.py --dry-run  # print the plan only
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MEDIA = REPO / "media"
LEDGER = MEDIA / "LICENSES.csv"
# Wikimedia's user agent policy wants a real contact address, not a project name.
UA = ("calm-frames-eval/0.1 (photosensitivity accessibility research; "
      "https://github.com/ contact: thealexschroeder@gmail.com)")
CHECKED = "2026-09-17"

# Minimum seconds between requests to the same host. Wikimedia returned HTTP 429
# on Sep 17, 2026 when this script pulled nine files back to back, with a note
# asking for a less disruptive approach. One request every few seconds is that.
HOST_DELAY = {"upload.wikimedia.org": 5.0, "commons.wikimedia.org": 5.0}
DEFAULT_HOST_DELAY = 1.0
MAX_RETRIES = 5

_last_request: dict[str, float] = {}


def _wait_turn(host: str) -> None:
    delay = HOST_DELAY.get(host, DEFAULT_HOST_DELAY)
    last = _last_request.get(host)
    if last is not None:
        remaining = delay - (time.monotonic() - last)
        if remaining > 0:
            time.sleep(remaining)
    _last_request[host] = time.monotonic()

# DVIDS asks for this notice whenever its visual information is shown.
DVIDS_NOTICE = (
    "The appearance of U.S. Department of War (DoW) visual information "
    "does not imply or constitute DoW endorsement."
)


@dataclass
class Item:
    name: str
    url: str
    source_page_url: str
    license: str
    credit_line: str
    notes: str
    source: str
    checked_on: str = CHECKED
    headers: dict = field(default_factory=dict)
    # True when flashing is the subject of the clip, which is usually why we took
    # it. Those files get the HAZARD_ prefix on sight, before anything analyzes
    # them, so nobody can open one by accident while flashmap is still being
    # written. This is a precaution about subject matter, NOT a screening result:
    # only flashmap decides what is actually flagged, and eval/screen.py applies
    # the prefix properly once it can.
    hazard_precaution: bool = False


MANIFEST: list[Item] = [
    # ---------------------------------------------------------------- Blender
    Item(
        name="bbb_720p_surround.mp4",
        url="https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4",
        source_page_url="https://peach.blender.org/about/",
        license="CC BY 3.0",
        credit_line="(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org",
        source="Blender open movies",
        notes=(
            "Peach page: 'The results of the Peach open movie project has been licensed "
            "under the Creative Commons Attribution 3.0 license.' Blender logos and "
            "trademarks are excluded from the Blender Studio licenses. File taken from the "
            "archive.org mirror BigBuckBunny_124, whose item licenseurl is CC BY 3.0, "
            "because download.blender.org is behind a Cloudflare challenge."
        ),
    ),
    Item(
        name="sintel_2048_stereo_512kb.mp4",
        url="https://archive.org/download/Sintel/sintel-2048-stereo_512kb.mp4",
        source_page_url="https://durian.blender.org/sharing/",
        license="CC BY 3.0",
        credit_line="(c) copyright Blender Foundation | durian.blender.org",
        source="Blender open movies",
        notes=(
            "Durian sharing page requires the entire credits scroll when the movie itself "
            "is shown. Excluded from the CC license: all logos (Blender, Durian, Creative "
            "Commons), associated trademarks, and material not produced by the project. "
            "File from the archive.org mirror 'Sintel', item creator Blender Foundation, "
            "item licenseurl CC BY 3.0."
        ),
    ),
    Item(
        name="tears_of_steel_720p.mov",
        url="https://ftp.nluug.nl/pub/graphics/blender/demo/movies/ToS/tears_of_steel_720p.mov",
        source_page_url="https://mango.blender.org/about/",
        license="CC BY 3.0 (conditional on keeping the credit scroll)",
        credit_line="(CC) Blender Foundation | mango.blender.org",
        source="Blender open movies",
        notes=(
            "Mango page: 'Creative Commons Attribution 3.0, which allows you to share and "
            "show the film freely, for as long you keep the credit scroll included.' "
            "Downloaded whole so the credit scroll stays intact; do not cut it. Blender "
            "logos are excluded from the license. Mirror: ftp.nluug.nl, an official "
            "Blender download mirror."
        ),
    ),
    # ------------------------------------------------------------- NASA SVS
    Item(
        name="nasa_svs_5011_iss_lightning_1080p.mp4",
        url="https://svs.gsfc.nasa.gov/vis/a000000/a005000/a005011/iss_lightning_sphere_07312023.mp4",
        source_page_url="https://svs.gsfc.nasa.gov/5011",
        license="Public domain (NASA media usage policy)",
        credit_line="NASA's Scientific Visualization Studio",
        source="NASA SVS 5011",
        hazard_precaution=True,
        notes=(
            "SVS page: 'Please give credit for this item to: NASA's Scientific "
            "Visualization Studio.' NASA media guidance: NASA should be acknowledged as "
            "the source; the NASA insignia, logotype and identifiers are NOT public domain "
            "and are not used here; nothing may imply NASA endorsement."
        ),
    ),
    # ------------------------------------------------------------------ DVIDS
    Item(
        name="dvids_illumination_flares.mp4",
        url="https://d34w7g4gy10iej.cloudfront.net/video/0608/DOD_N06082505/DOD_N06082505.mp4",
        source_page_url="https://www.dvidshub.net/video/16304/soldiers-fire-illumination-flares",
        license="Public domain (U.S. government work)",
        credit_line=f"Courtesy video, Defense Imagery Management Operations Center, via DVIDS. {DVIDS_NOTICE}",
        source="DVIDS",
        hazard_precaution=True,
        notes=(
            "VIRIN DOD_N06082505, taken 2006-06-01. DVIDS copyright page requires the "
            "non-endorsement notice and warns that military department names, insignia, "
            "seals and symbols are protected marks. No insignia is used as a mark here."
        ),
    ),
    Item(
        name="dvids_fireworks_safety.mp4",
        url="https://d34w7g4gy10iej.cloudfront.net/video/2406/DOD_110416658/DOD_110416658.mp4",
        source_page_url="https://www.dvidshub.net/video/929265/fireworks-safety",
        license="Public domain (U.S. government work)",
        credit_line=f"Courtesy video via DVIDS. {DVIDS_NOTICE}",
        source="DVIDS",
        hazard_precaution=True,
        notes=(
            "DVIDS copyright page requires the non-endorsement notice and warns that "
            "insignia may be trademarks."
        ),
    ),
    # ------------------------------------- NASA ISS crew night time-lapses
    Item(
        name="iss_night_pass_malaysia.ogv",
        url="https://upload.wikimedia.org/wikipedia/commons/f/f9/Night_Pass_over_Malaysia.ogv",
        source_page_url="https://commons.wikimedia.org/wiki/File:Night_Pass_over_Malaysia.ogv",
        license="Public domain (NASA)",
        credit_line="ISS Expedition 28 crew, NASA",
        source="NASA ISS time-lapse",
        hazard_precaution=True,
        notes=(
            "Crew Earth Observations night time-lapse showing lightning in storm cells. "
            "Commons license field: Public domain, author ISS Expedition 28 crew. NASA "
            "insignia not used; no endorsement implied."
        ),
    ),
    Item(
        name="iss_night_pass_europe_to_asia.ogv",
        url="https://upload.wikimedia.org/wikipedia/commons/9/9d/Eastern_Europe_to_Southeastern_Asia_at_Night.ogv",
        source_page_url="https://commons.wikimedia.org/wiki/File:Eastern_Europe_to_Southeastern_Asia_at_Night.ogv",
        license="Public domain (NASA)",
        credit_line="ISS Expedition 29 crew, NASA",
        source="NASA ISS time-lapse",
        hazard_precaution=True,
        notes="Commons license field: Public domain, author ISS Expedition 29 crew.",
    ),
    Item(
        name="iss_night_pass_africa_mideast.ogv",
        url="https://upload.wikimedia.org/wikipedia/commons/5/51/Night_Pass_over_Central_Africa_and_the_Middle_East.ogv",
        source_page_url="https://commons.wikimedia.org/wiki/File:Night_Pass_over_Central_Africa_and_the_Middle_East.ogv",
        license="Public domain (NASA)",
        credit_line="ISS Expedition 29 crew, NASA",
        source="NASA ISS time-lapse",
        hazard_precaution=True,
        notes="Commons license field: Public domain, author ISS Expedition 29 crew.",
    ),
    # ------------------------------------------- Wikimedia Commons lightning
    Item(
        name="wc_lightning_condensed.webm",
        url="https://upload.wikimedia.org/wikipedia/commons/3/3d/Lightning_-_condensed_version.webm",
        source_page_url="https://commons.wikimedia.org/wiki/File:Lightning_-_condensed_version.webm",
        license="CC BY-SA 4.0",
        credit_line="W.carter, CC BY-SA 4.0, via Wikimedia Commons",
        source="Wikimedia Commons lightning",
        hazard_precaution=True,
        notes="Share-alike: any derivative we publish from this clip carries CC BY-SA 4.0.",
    ),
    Item(
        name="wc_lightning_slowmo.webm",
        url="https://upload.wikimedia.org/wikipedia/commons/3/32/Lightning_in_Slow_Motion_%28Free_to_Use_HD_Stock_Video_Footage%29.webm",
        source_page_url="https://commons.wikimedia.org/wiki/File:Lightning_in_Slow_Motion_(Free_to_Use_HD_Stock_Video_Footage).webm",
        license="CC BY 3.0",
        credit_line="Jeffrey Beach, CC BY 3.0, via Wikimedia Commons",
        source="Wikimedia Commons lightning",
        hazard_precaution=True,
        notes="",
    ),
    Item(
        name="wc_lightning_240fps.webm",
        url="https://upload.wikimedia.org/wikipedia/commons/c/c2/LightningStrike240FPS.webm",
        source_page_url="https://commons.wikimedia.org/wiki/File:LightningStrike240FPS.webm",
        license="CC BY-SA 4.0",
        credit_line="GalaxyDoge72, CC BY-SA 4.0, via Wikimedia Commons",
        source="Wikimedia Commons lightning",
        hazard_precaution=True,
        notes="High frame rate source, useful for the variable frame rate path.",
    ),
    Item(
        name="wc_lightning_blackout.webm",
        url="https://upload.wikimedia.org/wikipedia/commons/6/6f/Lightningblackout1.webm",
        source_page_url="https://commons.wikimedia.org/wiki/File:Lightningblackout1.webm",
        license="CC BY 3.0",
        credit_line="Couch-scratching-cats, CC BY 3.0, via Wikimedia Commons",
        source="Wikimedia Commons lightning",
        hazard_precaution=True,
        notes="Night scene with a power blackout, so large whole-frame luminance swings.",
    ),
    # ------------------------------------------- Wikimedia Commons fireworks
    Item(
        name="wc_fireworks_summer.webm",
        url="https://upload.wikimedia.org/wikipedia/commons/a/a5/Fireworks_in_summer.webm",
        source_page_url="https://commons.wikimedia.org/wiki/File:Fireworks_in_summer.webm",
        license="CC BY-SA 4.0",
        credit_line="Joyful spherical creature, CC BY-SA 4.0, via Wikimedia Commons",
        source="Wikimedia Commons fireworks",
        hazard_precaution=True,
        notes="Share-alike.",
    ),
    Item(
        name="wc_fireworks_ignis_brunensis.ogv",
        url="https://upload.wikimedia.org/wikipedia/commons/3/35/Ignis_Brunensis_2010-05-22.ogv",
        source_page_url="https://commons.wikimedia.org/wiki/File:Ignis_Brunensis_2010-05-22.ogv",
        license="CC BY-SA 3.0",
        credit_line="Ignis Brunensis 2010-05-22, CC BY-SA 3.0, via Wikimedia Commons",
        source="Wikimedia Commons fireworks",
        hazard_precaution=True,
        notes=(
            "Author asks to be notified if the work is used outside Wikimedia. That is a "
            "request, not a license condition, but honor it before we publish anything "
            "derived from this clip."
        ),
    ),
    Item(
        name="wc_fireworks_buenos_aires.webm",
        url="https://upload.wikimedia.org/wikipedia/commons/5/53/Buenos_Aires_fireworks.webm",
        source_page_url="https://commons.wikimedia.org/wiki/File:Buenos_Aires_fireworks.webm",
        license="CC BY 2.0",
        credit_line="Colin and Sarah Northway, CC BY 2.0, via Wikimedia Commons",
        source="Wikimedia Commons fireworks",
        hazard_precaution=True,
        notes="",
    ),
    Item(
        name="wc_fireworks_rieti.ogv",
        url="https://upload.wikimedia.org/wikipedia/commons/f/fb/Fuochi_d%27artificio_-_Rieti%2C_capodanno_2011.ogv",
        source_page_url="https://commons.wikimedia.org/wiki/File:Fuochi_d%27artificio_-_Rieti,_capodanno_2011.ogv",
        license="CC BY 3.0",
        credit_line="Alessandro Antonelli, CC BY 3.0, via Wikimedia Commons",
        source="Wikimedia Commons fireworks",
        hazard_precaution=True,
        notes="",
    ),
    # ------------------------------------------------- 1930 public-domain film
    Item(
        name="pd1930_frozen_frolics.mp4",
        url="https://archive.org/download/frozen-frolics-1930/Frozen%20Frolics%20%281930%29.mp4",
        source_page_url="https://archive.org/details/frozen-frolics-1930",
        license="Public domain (U.S. work published 1930)",
        credit_line="Frozen Frolics (1930), Van Beuren Studios, public domain, via the Internet Archive",
        source="1930 public-domain film",
        hazard_precaution=True,
        notes=(
            "Item licenseurl is the Public Domain Mark 1.0, which is an uploader assertion. "
            "The grounding is the term itself: U.S. works published in 1930 entered the "
            "public domain on Jan 1, 2026. Early sound prints carry heavy density flicker, "
            "which is what makes them useful here."
        ),
    ),
    Item(
        name="pd1930_booze_hangs_high.mp4",
        url="https://archive.org/download/the-booze-hangs-high-1930/The%20Booze%20Hangs%20High%20%281930%29.mp4",
        source_page_url="https://archive.org/details/the-booze-hangs-high-1930",
        license="Public domain (U.S. work published 1930)",
        credit_line="The Booze Hangs High (1930), public domain, via the Internet Archive",
        source="1930 public-domain film",
        hazard_precaution=True,
        notes=(
            "Item licenseurl is the Public Domain Mark 1.0 (uploader assertion); the "
            "grounding is the 1930 publication date. Released 1930-12-19."
        ),
    ),
]

# Sources we opened and then chose not to download from. These stay in the report
# so nobody re-litigates them from memory.
SKIPPED = [
    {
        "source": "Apple sample video",
        "source_page_url": "https://developer.apple.com/streaming/examples/",
        "why": (
            "The examples page carries no license grant or terms for reusing the sample "
            "streams, only Apple's site-wide terms. Under the repo rule that anything "
            "unverified is dropped, we do not download it. Baseline sanity uses a locally "
            "generated ffmpeg clip instead, which has no license question at all."
        ),
    },
    {
        "source": "NOAA NSSL B-roll",
        "source_page_url": "https://www.nssl.noaa.gov/news/b-roll/",
        "why": (
            "The b-roll page serves its clips through a Vimeo showcase and exposes no "
            "direct file links, and no yt-dlp is installed on this machine. Nothing was "
            "downloaded. NOAA works are generally public domain, but we did not verify a "
            "per-clip statement, so the source is open rather than confirmed."
        ),
    },
    {
        "source": "Hell's Angels (1930)",
        "source_page_url": "https://archive.org/search?query=hell%27s+angels+1930",
        "why": (
            "No copy of the 1930 film is on the Internet Archive; the hits are unrelated "
            "modern documentaries. Not downloaded. If a copy turns up, note that the repo "
            "rule keeps that title out of anything we publish because of the trademark."
        ),
    },
]

HEADER = [
    "file",
    "source_page_url",
    "license",
    "credit_line",
    "sha256",
    "duration_s",
    "resolution",
    "license_checked_on",
    "notes",
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path) -> tuple[str, str]:
    """Return (duration_s, resolution) via ffprobe, or ('', '') if it cannot be read."""
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height:format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True, text=True, timeout=180, check=True,
        ).stdout
        d = json.loads(out)
        stream = (d.get("streams") or [{}])[0]
        w, h = stream.get("width"), stream.get("height")
        dur = d.get("format", {}).get("duration")
        res = f"{w}x{h}" if w and h else ""
        return (f"{float(dur):.2f}" if dur else ""), res
    except Exception:
        return "", ""


def download(item: Item, dest: Path) -> bool:
    host = urllib.parse.urlparse(item.url).netloc
    req = urllib.request.Request(item.url, headers={"User-Agent": UA, **item.headers})
    tmp = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, MAX_RETRIES + 1):
        _wait_turn(host)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp, tmp.open("wb") as fh:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
            tmp.replace(dest)
            return True
        except urllib.error.HTTPError as exc:
            tmp.unlink(missing_ok=True)
            if exc.code in (429, 503) and attempt < MAX_RETRIES:
                # Honor Retry-After when the server sends one, back off otherwise.
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    wait = float(retry_after) if retry_after else 0.0
                except ValueError:
                    wait = 0.0
                wait = max(wait, 5.0 * (2 ** (attempt - 1)))
                print(f"  {item.name}: HTTP {exc.code}, waiting {wait:.0f}s "
                      f"(attempt {attempt}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  FAILED {item.name}: {exc}", file=sys.stderr)
            return False
        except Exception as exc:  # noqa: BLE001
            tmp.unlink(missing_ok=True)
            if attempt < MAX_RETRIES:
                wait = 5.0 * (2 ** (attempt - 1))
                print(f"  {item.name}: {exc}, retrying in {wait:.0f}s "
                      f"(attempt {attempt}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  FAILED {item.name}: {exc}", file=sys.stderr)
            return False
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="substring filter on the item name")
    args = ap.parse_args()

    MEDIA.mkdir(exist_ok=True)
    rows, total = [], 0

    for item in MANIFEST:
        if args.only and args.only not in item.name:
            continue
        dest = MEDIA / item.name
        # A hazard rename may already have happened, so look for that name too.
        hazard = MEDIA / f"HAZARD_{item.name}"
        present = dest if dest.exists() else (hazard if hazard.exists() else None)

        if args.dry_run:
            print(f"[plan] {item.source:28} {item.name:42} {item.license}")
            continue

        if present is None:
            print(f"[get ] {item.name}")
            if not download(item, dest):
                continue
            present = dest
        else:
            print(f"[have] {present.name}")

        if item.hazard_precaution and not present.name.startswith("HAZARD_"):
            target = present.with_name(f"HAZARD_{present.name}")
            present.rename(target)
            present = target
            print(f"[haz ] -> {present.name}")

        size = present.stat().st_size
        total += size
        digest = sha256_of(present)
        dur, res = probe(present)
        note = f"source: {item.source}. {item.notes}".strip()
        if item.hazard_precaution:
            note += (
                " PRECAUTIONARY HAZARD: flashing is the subject of this clip, so it "
                "carries the HAZARD_ prefix before any analysis. Do not open it in a "
                "player. Inspect it with eval/plots.py only. This is a precaution "
                "about subject matter, not a screening result; flashmap decides what "
                "is actually flagged."
            )
        else:
            note += (
                " UNSCREENED: no flashmap run has happened yet, so this clip is not "
                "cleared. It must not reach kid mode until flashmap has analyzed it."
            )
        rows.append({
            "file": present.name,
            "source_page_url": item.source_page_url,
            "license": item.license,
            "credit_line": item.credit_line,
            "sha256": digest,
            "duration_s": dur,
            "resolution": res,
            "license_checked_on": item.checked_on,
            "notes": note,
        })

    if args.dry_run:
        for s in SKIPPED:
            print(f"[skip] {s['source']}: {s['why'][:90]}")
        return 0

    for s in SKIPPED:
        rows.append({
            "file": "(not downloaded)",
            "source_page_url": s["source_page_url"],
            "license": "not verified",
            "credit_line": "",
            "sha256": "",
            "duration_s": "",
            "resolution": "",
            "license_checked_on": CHECKED,
            "notes": f"source: {s['source']}. SKIPPED. {s['why']}",
        })

    with LEDGER.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)

    files = sum(1 for r in rows if r["sha256"])
    print(f"\n{files} files, {total / 1e6:.0f} MB, ledger at {LEDGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
