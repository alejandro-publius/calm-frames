"""The upload page: a judge drops in a clip and gets a report back.

    .venv/bin/python -m pipeline.upload_server            # http://127.0.0.1:8765
    .venv/bin/python -m pipeline.upload_server --port 9000

It runs on this machine and only on this machine. The clip is measured by the
pipeline's own analyzer door, ``FlashmapAdapter``, and the report is written by
``flashmap report``, so what a judge sees is what the pipeline sees.

Three rules it keeps.

**It never plays the clip and never hands it back.** There is no route that
serves an uploaded file, and there is no player on the page. The file is
written to a temporary directory, measured, and deleted as soon as the report
exists, whether the measurement worked or not. A clip somebody uploads may
well be a hazard file: that is the whole reason to measure it.

**It does not reach AWS, and says why.** This is deploy ready and has never
deployed. Anything that would need an account goes through the same two locks
as ``make deploy``: docs/STATUS.md has to say the Paid plan is confirmed, and
CHECKPOINT_D=confirmed has to be set for that one command. Neither has ever
been open in this repository. The locks are checked here as well as in
scripts/aws_guard.sh because a server cannot exec a CDK command to ask a
question, and pipeline/tests/test_upload_server.py holds the two copies
together: it reads the pattern out of the shell script and fails if this file
drifts from it.

**Nothing it cannot measure is called safe.** An analyzer that fails, times out
or is missing gives an error page. It never gives an empty report.

It binds to the loopback address unless told otherwise, and `--host` warns
when it is pointed anywhere else, because this page accepts a file from
whoever can reach it.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import socketserver
import sys
import tempfile
import subprocess
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import PipelineError
from .flashmap_adapter import FlashmapAdapter

REPO = Path(__file__).resolve().parent.parent
PAGE = Path(__file__).with_name("upload_page.html")
STATUS_FILE = REPO / "docs" / "STATUS.md"

# The twin of STATUS_PATTERN in scripts/aws_guard.sh. Anchored at the start of
# a line for the reason that script records: the row in docs/STATUS.md that
# tells you to add the line contains the line, inside backticks, and an
# unanchored match read that as the plan being confirmed. One of the two locks
# had been open for a day because of it.
STATUS_PATTERN = re.compile(r"^AWS Paid plan:[ \t]*confirmed", re.IGNORECASE | re.MULTILINE)

# A clip bigger than this is refused rather than buffered. A judge's clip is
# seconds long; anything at this size is a mistake or an attack on the disk.
MAX_UPLOAD_BYTES = 256 * 1024 * 1024

# Both profiles, so the report can say what each preset would hide instead of
# calling two of the three a lower bound.
PROFILES = ("wcag", "broadcast")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


# ---------------------------------------------------------------------------
# The AWS locks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AwsLocks:
    status_confirmed: bool
    variable_set: bool

    @property
    def open(self) -> bool:
        return self.status_confirmed and self.variable_set


def read_aws_locks(status_file: Path | None = None, environ: dict | None = None) -> AwsLocks:
    """Both locks, read the way scripts/aws_guard.sh reads them."""
    path = STATUS_FILE if status_file is None else status_file
    env = os.environ if environ is None else environ
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    return AwsLocks(
        status_confirmed=bool(STATUS_PATTERN.search(text)),
        variable_set=env.get("CHECKPOINT_D") == "confirmed",
    )


def aws_refusal(locks: AwsLocks) -> str:
    """The refusal, in the same shape and words `make deploy` prints."""
    status_line = (
        "yes"
        if locks.status_confirmed
        else "no. docs/STATUS.md has no line starting with 'AWS Paid plan: confirmed'"
    )
    variable_line = (
        "yes: CHECKPOINT_D=confirmed"
        if locks.variable_set
        else f"no. CHECKPOINT_D is {os.environ.get('CHECKPOINT_D', 'unset')}"
    )
    return (
        "Sending this to AWS is blocked.\n\n"
        "No AWS deploy happens until HUMAN CHECKPOINT D is confirmed: the account on the\n"
        "Paid plan, the $20 budget alarm in place, the credit request in.\n\n"
        f"  docs/STATUS.md says the plan is confirmed?  {status_line}\n"
        f"  CHECKPOINT_D=confirmed on this command?     {variable_line}\n\n"
        "What to do instead, today:\n\n"
        "  upload the clip on this page. It is measured on this machine, by the same\n"
        "  analyzer and the same pipeline code the ingest task would run, and the report\n"
        "  you get back is the same report.\n\n"
        "This page has never called AWS. Neither lock has ever been open in this\n"
        "repository. See scripts/aws_guard.sh, which refuses `make deploy` the same way."
    )


# ---------------------------------------------------------------------------
# Multipart, enough of it
# ---------------------------------------------------------------------------


@dataclass
class Upload:
    filename: str
    data: bytes
    fields: dict[str, str]


def parse_multipart(body: bytes, content_type: str) -> Upload:
    """Pull one file and the plain fields out of a multipart/form-data body.

    Small on purpose. The standard library's `cgi` module is deprecated and
    gone in 3.13, and `email` wants the whole thing decoded first, so this
    reads the two shapes the page actually posts and refuses anything else.
    """
    match = re.search(r'boundary="?([^";]+)"?', content_type, re.IGNORECASE)
    if not match:
        raise ValueError("this post has no multipart boundary")
    boundary = b"--" + match.group(1).strip().encode("latin-1")

    filename = ""
    data = b""
    fields: dict[str, str] = {}

    for part in body.split(boundary):
        if part in (b"", b"--", b"--\r\n", b"\r\n"):
            continue
        head, _, payload = part.partition(b"\r\n\r\n")
        if not _:
            continue
        payload = payload[:-2] if payload.endswith(b"\r\n") else payload
        headers = head.decode("latin-1", "replace")
        name_match = re.search(r'name="([^"]*)"', headers)
        if not name_match:
            continue
        name = name_match.group(1)
        file_match = re.search(r'filename="([^"]*)"', headers)
        if file_match:
            if file_match.group(1):
                filename = file_match.group(1)
                data = payload
        else:
            fields[name] = payload.decode("utf-8", "replace").strip()

    if not filename or not data:
        raise ValueError("no file was uploaded")
    return Upload(filename=filename, data=data, fields=fields)


def safe_name(filename: str) -> str:
    """A file name that cannot climb out of the working directory.

    The name comes from whoever posted it, so the path parts are thrown away
    and what is left is reduced to characters that mean nothing to a shell or a
    path. A name that empties out gets a plain one.
    """
    base = Path(filename.replace("\\", "/")).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base).lstrip(".")
    return cleaned[:120] or "upload.bin"


# ---------------------------------------------------------------------------
# Making the report
# ---------------------------------------------------------------------------


def build_report_for(clip: Path, work: Path, title: str) -> str:
    """Measure the clip and return the HTML report.

    The clip goes through ``FlashmapAdapter``, which is the pipeline's only
    door to the analyzer, so this page measures a file exactly as ingest would.
    """
    adapter = FlashmapAdapter()
    if not adapter.available():
        raise PipelineError(
            f"the analyzer does not answer here ({adapter.describe()}). Nothing was "
            "measured, so nothing is said about this clip."
        )

    maps: dict[str, Path] = {}
    for profile in PROFILES:
        out_path = work / f"{profile}.map.json"
        adapter.analyze(clip, profile=profile, out_path=out_path)
        maps[profile] = out_path

    report_path = work / "report.html"
    command = [
        sys.executable, "-m", "flashmap", "report", str(maps["wcag"]),
        "--out", str(report_path),
        "--title", title,
    ]
    for profile, path in maps.items():
        if profile != "wcag":
            command += ["--map", f"{profile}={path}"]
    licenses = REPO / "media" / "LICENSES.csv"
    if licenses.is_file():
        command += ["--license-csv", str(licenses)]

    result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if result.returncode != 0 or not report_path.is_file():
        raise PipelineError(
            "the report could not be written, so there is nothing to show:\n"
            + (result.stderr or result.stdout or "no output")
        )
    return report_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The server
# ---------------------------------------------------------------------------


def _page(bind_note: str) -> str:
    text = PAGE.read_text(encoding="utf-8")
    return text.replace("MAX_MB", str(MAX_UPLOAD_BYTES // (1024 * 1024))).replace(
        "BIND_NOTE", html.escape(bind_note)
    )


def _plain_page(heading: str, body: str) -> str:
    """An answer that is not a report: an error, or the AWS refusal."""
    return (
        "<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>"
        f"<title>{html.escape(heading)}</title>"
        "<style>body{margin:0;padding:40px 24px;background:#1F4D5C;color:#F3E8D3;"
        "font:16px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}"
        "main{max-width:760px;margin:0 auto}h1{font-size:28px}"
        "pre{background:#173B47;border:2px solid #66A0B4;border-radius:10px;padding:20px;"
        "white-space:pre-wrap;word-break:break-word;font-size:14px}"
        "a{color:#F3E8D3}</style></head><body><main>"
        f"<h1>{html.escape(heading)}</h1><pre>{html.escape(body)}</pre>"
        "<p><a href='/'>Back to the page</a></p></main></body></html>"
    )


class UploadHandler(BaseHTTPRequestHandler):
    server_version = "CalmFramesUpload/1.0"
    bind_note = f"{DEFAULT_HOST}:{DEFAULT_PORT}"
    keep_uploads = False

    def _send(self, status: int, body: str, content_type: str = "text/html; charset=utf-8"):
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        # The report is one file and nothing in it is fetched, so the page is
        # allowed to load nothing at all from anywhere.
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; img-src data:; style-src 'unsafe-inline'; form-action 'self'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802 - the name http.server calls
        if self.path in ("/", "/index.html"):
            self._send(200, _page(self.bind_note))
            return
        # There is deliberately no route that serves a file from disk. An
        # uploaded clip may be a hazard file, and this page never hands one
        # back.
        self._send(404, _plain_page("No such page", "This server has one page, at /."))

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/aws":
            locks = read_aws_locks()
            if not locks.open:
                self._send(503, _plain_page("Blocked", aws_refusal(locks)))
                return
            # Both locks open is not a state this repository has ever been in.
            # Even then this server does not deploy: it says what would have to
            # happen next, on a machine a person is sitting at.
            self._send(
                501,
                _plain_page(
                    "Not done from here",
                    "Both locks are open, and this page still does not call AWS.\n"
                    "Run `make deploy CHECKPOINT_D=confirmed ...` yourself, from a shell,\n"
                    "so that a person is the one who starts it.",
                ),
            )
            return

        if self.path != "/report":
            self._send(404, _plain_page("No such page", "Post a clip to /report."))
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            self._send(400, _plain_page("Nothing arrived", "That post had no body."))
            return
        if length > MAX_UPLOAD_BYTES:
            self._send(
                413,
                _plain_page(
                    "Too big",
                    f"That file is {length} bytes and the limit here is "
                    f"{MAX_UPLOAD_BYTES}. Nothing was written to disk.",
                ),
            )
            return

        body = self.rfile.read(length)
        try:
            upload = parse_multipart(body, self.headers.get("Content-Type", ""))
        except ValueError as exc:
            self._send(400, _plain_page("That is not a clip", str(exc)))
            return

        work = Path(tempfile.mkdtemp(prefix="calm-frames-upload-"))
        clip = work / safe_name(upload.filename)
        # The answer is built first, the clip is deleted second, and only then
        # does anything leave this process. Sending first and deleting after
        # would be the same in the end and untestable in the middle: a caller
        # that has the report in its hands could still find the clip on disk.
        try:
            clip.write_bytes(upload.data)
            title = upload.fields.get("title") or Path(upload.filename).stem
            outcome = (200, build_report_for(clip, work, title))
        except PipelineError as exc:
            outcome = (500, _plain_page("Nothing was measured", str(exc)))
        except Exception as exc:  # noqa: BLE001 - an error page, never a blank report
            outcome = (500, _plain_page("Nothing was measured", repr(exc)))
        finally:
            # The clip goes whatever happened. It may be a hazard file, and
            # nothing here needs it once the numbers are out.
            if not self.keep_uploads:
                shutil.rmtree(work, ignore_errors=True)
        self._send(*outcome)

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(f"{self.address_string()} {format % args}\n")


def build_server(host: str, port: int, *, keep_uploads: bool = False) -> ThreadingHTTPServer:
    handler = type(
        "BoundUploadHandler",
        (UploadHandler,),
        {"bind_note": f"http://{host}:{port}", "keep_uploads": keep_uploads},
    )
    socketserver.TCPServer.allow_reuse_address = True
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", default=DEFAULT_HOST, help="address to bind, loopback by default")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--backend",
        default="local",
        choices=("local", "aws"),
        help="where the measuring happens. aws is refused, see HUMAN CHECKPOINT D",
    )
    parser.add_argument(
        "--keep-uploads",
        action="store_true",
        help="do not delete the uploaded clip. For debugging only, and it leaves a file "
        "on disk that may be hazardous",
    )
    args = parser.parse_args(argv)

    if args.backend == "aws":
        locks = read_aws_locks()
        print(aws_refusal(locks), file=sys.stderr)
        return 1

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(
            f"warning: binding to {args.host}, so anyone who can reach this machine can "
            "upload a file to it.",
            file=sys.stderr,
        )

    server = build_server(args.host, args.port, keep_uploads=args.keep_uploads)
    print(f"Calm Frames upload page on http://{args.host}:{args.port}")
    print("Clips are measured here and deleted. Nothing is deployed and nothing is played.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
