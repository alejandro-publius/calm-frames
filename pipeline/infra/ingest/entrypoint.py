#!/usr/bin/env python3
"""What one Fargate task does with one uploaded file.

    download the upload  ->  run the same pipeline a laptop runs  ->
    publish only what verify passed  ->  write one catalog row

The rules it keeps, and why each one is here rather than in a comment on a
bucket policy:

**Fail closed, in the cloud too.** The player already refuses a title whose map
does not verify. This refuses earlier: if ``entry.json`` does not say verified,
nothing at all is uploaded and the task exits non-zero. A title nobody can play
is better than a title nobody checked.

**The upload list is an allowlist.** Named paths per preset, never a directory
walk of the title. Two things in the work directory must never reach a bucket
the internet can read through CloudFront: the source master, which is the
original flashing video, and ``verify/cover_model_*.mp4``, which is that same
video with covers drawn on it and so is just as hazardous outside the player.
A denylist would be one forgotten filename away from publishing either.

**The key is nobody's argument.** The private signing key, when there is one at
all, comes from an SSM SecureString at run time, lands in a file only this user
can read, and is deleted before the task exits. It is never printed, never put
in an environment variable the console shows, and never written into the work
directory that gets uploaded.

**A hostile object key cannot escape.** An S3 key is arbitrary bytes. Only its
last component is used for the local filename, and anything that is not a plain
name is refused before a byte is downloaded.

Environment, all set by the stack in ``calm_frames_stack.py``:

    CALM_FRAMES_SOURCE_BUCKET       where the upload landed
    CALM_FRAMES_SOURCE_KEY          the object key, under uploads/
    CALM_FRAMES_DELIVERY_BUCKET     where publishable artifacts go
    CALM_FRAMES_CATALOG_TABLE       the DynamoDB catalog
    CALM_FRAMES_PRESETS             comma separated, default "wcag"
    CALM_FRAMES_SIGNING_KEY_PARAM   optional SSM parameter holding the private
                                    key PEM. Without it the maps are unsigned
                                    and every player will refuse them, which the
                                    log says in as many words.
    CALM_FRAMES_WORKDIR             default /work
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

# The uploads prefix in the source bucket. The stack filters its notification on
# the same string, so an object anywhere else should never reach this task.
UPLOAD_PREFIX = "uploads/"

# What may be published, per preset, as paths relative to the title directory.
# Anything not named here stays in the task.
PUBLISHABLE_PER_PRESET = (
    "maps/{preset}.json",
    "plans/{preset}.json",
    "bif/{preset}.bif",
    "bif/{preset}.json",
    "posters/{preset}.json",
)
PUBLISHABLE_DIRS_PER_PRESET = (
    "safe/{preset}/hls",
    "posters/{preset}",
)
PUBLISHABLE_FILES_PER_PRESET = ("safe/{preset}/safe.mp4",)
PUBLISHABLE_TITLE_FILES = ("entry.json", "verify/report.json")

# A plain file name: letters, digits, dot, dash, underscore, space. No slash, no
# backslash, no leading dot, nothing that means "the directory above".
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,200}$")

CONTENT_TYPES = {
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".m4s": "video/iso.segment",
    ".mp4": "video/mp4",
    ".json": "application/json",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bif": "application/octet-stream",
}


class TaskRefused(Exception):
    """Something was wrong before any work started, or wrong enough to stop."""


@dataclass
class Settings:
    source_bucket: str
    source_key: str
    delivery_bucket: str
    catalog_table: str
    presets: list[str]
    signing_key_param: str
    workdir: Path

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        env = dict(os.environ if env is None else env)

        def required(name: str) -> str:
            value = (env.get(name) or "").strip()
            if not value:
                raise TaskRefused(f"{name} is not set, so there is nothing to do")
            return value

        presets = [p.strip() for p in (env.get("CALM_FRAMES_PRESETS") or "wcag").split(",") if p.strip()]
        if not presets:
            raise TaskRefused("CALM_FRAMES_PRESETS is empty")
        return cls(
            source_bucket=required("CALM_FRAMES_SOURCE_BUCKET"),
            source_key=required("CALM_FRAMES_SOURCE_KEY"),
            delivery_bucket=required("CALM_FRAMES_DELIVERY_BUCKET"),
            catalog_table=required("CALM_FRAMES_CATALOG_TABLE"),
            presets=presets,
            signing_key_param=(env.get("CALM_FRAMES_SIGNING_KEY_PARAM") or "").strip(),
            workdir=Path(env.get("CALM_FRAMES_WORKDIR") or "/work"),
        )


def local_name_for(key: str) -> str:
    """The file name to download an object key into, or a refusal.

    S3 keys are arbitrary UTF-8. ``uploads/../../etc/passwd`` and
    ``uploads/a/../../b`` are both legal keys, so the last component is taken
    and then checked, rather than trusted because it came from our own bucket.
    """
    if not key.startswith(UPLOAD_PREFIX):
        raise TaskRefused(f"the key {key!r} is not under {UPLOAD_PREFIX}")
    segments = key.split("/")
    # Taking the last component would already be safe, since nothing here joins
    # the key onto a path. It is refused anyway: our uploader never makes a key
    # with an empty or dot segment in it, so one that arrives is either a
    # mistake or an attempt, and neither should be reasoned about further.
    if any(segment in ("", ".", "..") for segment in segments[1:-1]):
        raise TaskRefused(f"the key {key!r} has a dot or empty path segment in it")
    name = segments[-1]
    if not SAFE_NAME.match(name) or name in (".", ".."):
        raise TaskRefused(f"the key {key!r} does not end in a plain file name")
    return name


def content_type_for(path: Path) -> str:
    return CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")


def publishable_paths(title_root: Path, presets: Iterable[str]) -> list[Path]:
    """Every file that may leave the task, as absolute paths that exist.

    Built from the allowlist above. A preset the run did not produce simply
    contributes nothing, so a partial run publishes the presets it finished and
    not the ones it did not.
    """
    found: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        if path.is_file() and path not in seen:
            seen.add(path)
            found.append(path)

    for name in PUBLISHABLE_TITLE_FILES:
        add(title_root / name)
    for preset in presets:
        for template in PUBLISHABLE_PER_PRESET + PUBLISHABLE_FILES_PER_PRESET:
            add(title_root / template.format(preset=preset))
        for template in PUBLISHABLE_DIRS_PER_PRESET:
            directory = title_root / template.format(preset=preset)
            if directory.is_dir():
                for child in sorted(directory.rglob("*")):
                    add(child)
    return found


def is_publishable(entry: dict[str, Any]) -> bool:
    """The one condition for uploading anything: verify said yes.

    ``verified`` and ``status`` are both checked because only verify writes both
    and a half written entry should not publish a title.
    """
    return bool(entry.get("verified")) and entry.get("status") == "verified"


def fetch_signing_key(ssm, parameter: str, directory: Path) -> tuple[Path, Path]:
    """Put the signing key on disk for the length of this task, and no longer.

    ``WithDecryption`` is what makes this a SecureString read rather than a
    plaintext one. The value is never printed and never returned, only the
    paths. The public half is derived here rather than stored anywhere, because
    a public key that came from the same private key cannot disagree with it,
    and verify needs one to check what the analyzer signed.
    """
    from cryptography.hazmat.primitives import serialization  # noqa: PLC0415

    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    response = ssm.get_parameter(Name=parameter, WithDecryption=True)
    pem = response["Parameter"]["Value"]
    if "PRIVATE KEY" not in pem:
        raise TaskRefused(f"the parameter {parameter} does not hold a private key PEM")
    path = directory / "signing_key.pem"
    # Open with the mode set from the start. Writing first and chmodding after
    # leaves a window where the file is readable.
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w") as stream:
        stream.write(pem)

    private_key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    public_path = directory / "signing_key.pub.pem"
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return path, public_path


def upload_title(s3, delivery_bucket: str, title_root: Path, sha256: str, paths: Iterable[Path]) -> list[str]:
    """Copy the allowed files to the delivery bucket, under titles/<sha256>/."""
    keys: list[str] = []
    for path in paths:
        relative = path.relative_to(title_root).as_posix()
        key = f"titles/{sha256}/{relative}"
        s3.upload_file(
            str(path),
            delivery_bucket,
            key,
            ExtraArgs={"ContentType": content_type_for(path)},
        )
        keys.append(key)
    return keys


def catalog_item(entry: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """One DynamoDB row, with the same fields as the local catalog.

    The absolute paths the local run wrote are of no use to a player, so the row
    carries the delivery keys instead.
    """
    return {
        "sha256": entry["sha256"],
        "title": entry.get("title", ""),
        "source_name": entry.get("source_name", ""),
        "duration_s": json.dumps(entry.get("duration_s", 0)),
        "width": entry.get("width", 0),
        "height": entry.get("height", 0),
        "status": entry.get("status", "pending"),
        "verified": bool(entry.get("verified")),
        "presets": sorted((entry.get("renditions") or {}).keys()),
        "delivery_keys": keys,
    }


def run(settings: Settings, clients: dict[str, Any], ingest_main) -> int:
    """The task, with its AWS clients and the pipeline handed in.

    Everything that talks to AWS or does real work arrives as an argument, so
    the test can drive the whole path against moto and a pipeline that writes a
    known title.
    """
    from pipeline.hashing import sha256_file  # noqa: PLC0415
    from pipeline.layout import TitleLayout  # noqa: PLC0415

    name = local_name_for(settings.source_key)
    incoming = settings.workdir / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    source_path = incoming / name

    print(f"downloading s3://{settings.source_bucket}/{settings.source_key}")
    clients["s3"].download_file(settings.source_bucket, settings.source_key, str(source_path))

    key_dir = settings.workdir / "keys"
    key_path: Path | None = None
    public_path: Path | None = None
    try:
        if settings.signing_key_param:
            key_path, public_path = fetch_signing_key(
                clients["ssm"], settings.signing_key_param, key_dir
            )
            print(f"signing with the key in {settings.signing_key_param}")
        else:
            print(
                "no CALM_FRAMES_SIGNING_KEY_PARAM is set, so the maps will be "
                "unsigned and every player will refuse them"
            )

        argv = [
            str(source_path),
            "--workdir",
            str(settings.workdir),
            "--presets",
            ",".join(settings.presets),
        ]
        if key_path is not None:
            argv += ["--key", str(key_path)]
        if public_path is not None:
            argv += ["--pub", str(public_path)]
        code = ingest_main(argv)
    finally:
        # Whatever happened, the key does not outlive the run. The directory
        # goes too, so nothing is left for a later step to pick up.
        if key_dir.exists():
            shutil.rmtree(key_dir, ignore_errors=True)

    sha256 = sha256_file(source_path)
    layout = TitleLayout(settings.workdir, sha256)
    entry_path = layout.entry_path
    if not entry_path.is_file():
        raise TaskRefused(f"the pipeline wrote no catalog entry for {sha256[:12]}")
    entry = json.loads(entry_path.read_text())

    if not is_publishable(entry):
        print(
            f"verify did not pass for {sha256[:12]} (status "
            f"{entry.get('status')!r}), so nothing is published",
            file=sys.stderr,
        )
        return 1 if code == 0 else code

    paths = publishable_paths(layout.root, settings.presets)
    keys = upload_title(clients["s3"], settings.delivery_bucket, layout.root, sha256, paths)
    clients["dynamodb"].put_item(
        TableName=settings.catalog_table,
        Item=to_dynamodb(catalog_item(entry, keys)),
    )
    print(f"published {len(keys)} object(s) for {sha256[:12]}")
    return code


def to_dynamodb(item: dict[str, Any]) -> dict[str, Any]:
    """The low level attribute shape, so the task needs no extra dependency."""

    def encode(value: Any) -> dict[str, Any]:
        if isinstance(value, bool):
            return {"BOOL": value}
        if isinstance(value, (int, float)):
            return {"N": str(value)}
        if isinstance(value, list):
            return {"L": [encode(element) for element in value]}
        if isinstance(value, dict):
            return {"M": {key: encode(element) for key, element in value.items()}}
        if value is None:
            return {"NULL": True}
        return {"S": str(value)}

    return {key: encode(value) for key, value in item.items()}


def main(argv: list[str] | None = None) -> int:
    try:
        settings = Settings.from_env()
    except TaskRefused as error:
        print(f"ingest task refused to start: {error}", file=sys.stderr)
        return 2

    import boto3  # noqa: PLC0415

    from pipeline.ingest import main as ingest_main  # noqa: PLC0415

    clients = {
        "s3": boto3.client("s3"),
        "ssm": boto3.client("ssm"),
        "dynamodb": boto3.client("dynamodb"),
    }
    try:
        return run(settings, clients, ingest_main)
    except TaskRefused as error:
        print(f"ingest task stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
