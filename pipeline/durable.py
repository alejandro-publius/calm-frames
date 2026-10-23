"""Atomic, durable replacement of small state files, and the locks preparation takes.

Every file that decides what a later run trusts or what a reader may publish (the
step ledger, a catalog entry, the kid mode index, a verify report, a local receipt)
is written with ``atomic_write_bytes``: a new temporary file beside the target,
created exclusively and never through a link, flushed to the device, renamed over
the old file, and then the directory flushed so the rename itself survives a power
loss. A reader sees the old bytes or the new bytes, never a mixture.

Media and other step outputs are not written this way. They do not need to be: the
ledger records the SHA-256 of every output when its step commits, so an output that
was torn, lost or changed afterwards no longer matches its record and is rebuilt.
What they do need, before a title is published, is to be on the device, which is
what ``sync_files`` is for.

Filesystem limits, stated rather than assumed:

- A rename is atomic only within one filesystem, so the temporary file always sits
  in the target's own directory.
- On macOS, fsync() hands data to the drive but does not ask the drive to empty its
  own cache. F_FULLFSYNC does, and is used where the platform offers it, falling
  back to fsync() when a filesystem refuses it.
- Some network and FUSE filesystems cannot fsync a directory. That refusal is
  tolerated, and on such a filesystem a rename may not survive a power loss even
  though the file contents do.
- Locks are flock(2) locks. They are advisory, they protect only against other
  processes that take the same lock, and on NFS they may be emulated or visible to
  one client only. Two machines sharing one work directory are not serialized.
- None of this was measured by cutting power. The guarantee is the operating
  system's fsync contract, nothing stronger.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import os
import secrets
import stat
import sys
import time
from pathlib import Path
from typing import Iterable, Iterator

from . import PipelineError

# How many unique temporary names to try before giving up. A collision needs the
# same process id and the same 64 random bits, so one attempt is all it ever takes.
TEMPORARY_ATTEMPTS = 8
# How often a waiting lock is retried. Only the shared index lock waits at all.
LOCK_POLL_S = 0.02

_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
# Errors a filesystem gives when it cannot flush a directory at all.
_UNSUPPORTED = {errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOTTY, errno.EBADF}


class LockBusy(PipelineError):
    """Another process holds the lock this one needs."""


def fsync_fd(fd: int) -> None:
    """Put this file's data on the device, past the drive's own cache where possible."""
    if sys.platform == "darwin" and hasattr(fcntl, "F_FULLFSYNC"):
        try:
            fcntl.fcntl(fd, fcntl.F_FULLFSYNC)
            return
        except OSError:
            pass
    os.fsync(fd)


def fsync_directory(directory: str | Path) -> bool:
    """Make a rename or a new name in this directory durable.

    Returns False when the filesystem cannot flush a directory at all. Any other
    failure is raised, because it means the directory could not even be opened.
    """
    fd = os.open(directory, os.O_RDONLY | _DIRECTORY | _CLOEXEC)
    try:
        fsync_fd(fd)
    except OSError as exc:
        if exc.errno in _UNSUPPORTED:
            return False
        raise
    finally:
        os.close(fd)
    return True


def atomic_write_bytes(path: str | Path, data: bytes) -> Path:
    """Replace ``path`` with ``data`` so that a crash leaves the old or the new file.

    The temporary file is created with O_EXCL and O_NOFOLLOW under a name nobody else
    can predict, so a planted file or link at a fixed ``.tmp`` name is never written
    through. Renaming over a link replaces the link itself, never its target. Creation
    mode is 0666 less the umask, the same as an ordinary ``write_text``.
    """
    path = Path(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    fd = -1
    for _ in range(TEMPORARY_ATTEMPTS):
        candidate = directory / f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
        try:
            fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW | _CLOEXEC, 0o666)
        except FileExistsError:
            continue
        temporary = candidate
        break
    if temporary is None:
        raise PipelineError(f"could not create a temporary file beside {path.name}")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            fsync_fd(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
    fsync_directory(directory)
    return path


def atomic_write_text(path: str | Path, text: str) -> Path:
    return atomic_write_bytes(path, text.encode("utf-8"))


def sync_files(paths: Iterable[str | Path]) -> int:
    """Flush existing regular files, and the directories that name them, to the device.

    Called before a title is published, so a verified verdict can never be on disk
    while the bytes it vouches for are still only in memory. Links are refused
    rather than followed. Returns how many files were flushed.
    """
    files: list[Path] = []
    seen: set[Path] = set()
    for item in paths:
        path = Path(item)
        if path in seen:
            continue
        seen.add(path)
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            continue
        if stat.S_ISREG(info.st_mode):
            files.append(path)
    for path in files:
        fd = os.open(path, os.O_RDONLY | _NOFOLLOW | _CLOEXEC)
        try:
            fsync_fd(fd)
        finally:
            os.close(fd)
    for directory in sorted({path.parent for path in files}):
        fsync_directory(directory)
    return len(files)


@contextlib.contextmanager
def exclusive_lock(path: str | Path, *, what: str, wait_s: float = 0.0) -> Iterator[None]:
    """Hold an exclusive flock on ``path`` for the duration of the block.

    The lock file is created if needed and never removed, because removing a lock
    file is how two processes end up holding two different locks. It must be an
    owned regular file: a link, a hard link or anything else is refused. With
    ``wait_s`` of zero a busy lock is refused at once; otherwise it is retried every
    ``LOCK_POLL_S`` until the deadline, and never longer.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_RDWR | _NOFOLLOW | _CLOEXEC, 0o600)
    except OSError as exc:
        raise PipelineError(f"the {what} lock could not be opened as an owned file") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise PipelineError(f"the {what} lock is not an owned regular file")
        deadline = time.monotonic() + max(0.0, wait_s)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    raise LockBusy(f"the {what} is busy in another process") from exc
                time.sleep(LOCK_POLL_S)
        yield
    finally:
        os.close(fd)
