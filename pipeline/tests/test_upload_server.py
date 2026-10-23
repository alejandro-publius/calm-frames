"""The upload page: what it refuses, and what it never hands back.

Four things have to hold, and each one has been broken on purpose and watched
go red.

1. It does not reach AWS. Both locks are checked, both have to be open, and
   neither has ever been open here. The refusal is the one `make deploy`
   prints.
2. The anchored match is the same anchored match scripts/aws_guard.sh uses.
   That anchor exists because an unanchored one read the row in docs/STATUS.md
   that *describes* the line as the line itself, and one of the two locks was
   open for a day. A second copy of that check is a second chance to make the
   same mistake, so this file reads the pattern out of the shell script.
3. No route ever serves an uploaded file back, and the clip is deleted whatever
   happened.
4. A clip that could not be measured gives an error page, never an empty
   report. A file we cannot measure must never look like a clean bill of
   health.

Nothing here can reach an account: every test runs against a temporary
docs/STATUS.md, and the one case where both locks are open is only ever
checked as text.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from pipeline.upload_server import (
    MAX_UPLOAD_BYTES,
    STATUS_PATTERN,
    AwsLocks,
    aws_refusal,
    build_server,
    parse_multipart,
    read_aws_locks,
    safe_name,
)

REPO = Path(__file__).resolve().parents[2]
GUARD = REPO / "scripts" / "aws_guard.sh"
CONFIRMED_LINE = "AWS Paid plan: confirmed"


# ---------------------------------------------------------------------------
# The AWS locks
# ---------------------------------------------------------------------------


class TestItDoesNotReachAws:
    def test_neither_lock_is_open_in_this_repository(self):
        """The state of the real repository, asserted rather than assumed."""
        locks = read_aws_locks()
        assert not locks.status_confirmed, (
            "docs/STATUS.md now says the Paid plan is confirmed. If that is true, this "
            "test is the thing to change, deliberately, with the date."
        )
        assert not locks.open

    @pytest.mark.parametrize(
        "status_says, variable_set",
        [(False, False), (True, False), (False, True)],
    )
    def test_one_lock_is_never_enough(self, tmp_path: Path, status_says: bool, variable_set: bool):
        status = tmp_path / "STATUS.md"
        status.write_text(
            f"# Status\n\n{CONFIRMED_LINE} on 2026-01-01\n" if status_says else "# Status\n",
            encoding="utf-8",
        )
        locks = read_aws_locks(
            status, {"CHECKPOINT_D": "confirmed"} if variable_set else {}
        )
        assert not locks.open
        assert "blocked" in aws_refusal(locks).lower()

    def test_both_locks_open_is_the_only_way_through(self, tmp_path: Path):
        status = tmp_path / "STATUS.md"
        status.write_text(f"# Status\n\n{CONFIRMED_LINE} on 2026-01-01\n", encoding="utf-8")
        locks = read_aws_locks(status, {"CHECKPOINT_D": "confirmed"})
        assert locks.open

    def test_a_document_talking_about_the_line_is_not_the_line(self, tmp_path: Path):
        """The bug that was live for a day, in this copy of the check.

        docs/STATUS.md has a row telling you to add the line, and that row
        contains the line inside backticks and inside a table cell. An
        unanchored match reads it as the plan being confirmed.
        """
        status = tmp_path / "STATUS.md"
        status.write_text(
            "| Before any deploy | Put AWS on the Paid plan, then add "
            f"`{CONFIRMED_LINE}` to this file. | blocked |\n"
            f"Some prose mentioning {CONFIRMED_LINE} in passing.\n",
            encoding="utf-8",
        )
        locks = read_aws_locks(status, {"CHECKPOINT_D": "confirmed"})
        assert not locks.status_confirmed, (
            "a document that talks about the line was read as a document that says it"
        )
        assert not locks.open

    def test_the_anchor_is_the_shell_script_s_anchor(self):
        """The drift guard between the two copies of the lock.

        scripts/aws_guard.sh owns this. A second copy that anchored differently
        would be a second lock with a different shape, which is how the first
        one came to be open without anybody noticing.
        """
        if not GUARD.is_file():
            pytest.skip("the guard script is not in this checkout")
        shell = GUARD.read_text(encoding="utf-8")
        match = re.search(r"STATUS_PATTERN='([^']+)'", shell)
        assert match, "scripts/aws_guard.sh no longer sets STATUS_PATTERN"
        shell_pattern = match.group(1)

        assert shell_pattern.startswith("^"), "the shell pattern is no longer anchored"
        assert STATUS_PATTERN.pattern.startswith("^"), "this module's pattern is not anchored"

        # The same strings match and miss under both.
        cases = [
            (f"{CONFIRMED_LINE}\n", True),
            (f"{CONFIRMED_LINE} on 2026-01-01, by Alex\n", True),
            (f"  {CONFIRMED_LINE}\n", False),
            (f"| add `{CONFIRMED_LINE}` to this file |\n", False),
            ("AWS Paid plan: not yet\n", False),
        ]
        for text, expected in cases:
            mine = bool(STATUS_PATTERN.search(text))
            theirs = _shell_matches(shell_pattern, text)
            assert mine == expected, f"this module reads {text!r} as {mine}"
            assert mine == theirs, (
                f"the two copies of the lock disagree on {text!r}: "
                f"upload_server says {mine}, aws_guard.sh says {theirs}"
            )

    def test_the_refusal_says_what_make_deploy_says(self):
        text = aws_refusal(AwsLocks(False, False))
        for phrase in (
            "HUMAN CHECKPOINT D",
            "Paid plan",
            "budget alarm",
            "docs/STATUS.md says the plan is confirmed?",
            "CHECKPOINT_D=confirmed on this command?",
        ):
            assert phrase in text, f"the refusal no longer says {phrase!r}"

    def test_the_aws_backend_refuses_and_starts_nothing(self, capsys):
        from pipeline.upload_server import main

        assert main(["--backend", "aws"]) == 1
        assert "blocked" in capsys.readouterr().err.lower()


def _shell_matches(pattern: str, text: str) -> bool:
    """Run the shell script's own pattern through grep, as the script does."""
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
        handle.write(text)
        path = handle.name
    try:
        return (
            subprocess.run(
                ["grep", "-Eqi", pattern, path], capture_output=True
            ).returncode
            == 0
        )
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Reading a post
# ---------------------------------------------------------------------------


def multipart(filename: str, data: bytes, **fields: str) -> tuple[bytes, str]:
    boundary = "----calmframestest"
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
            f"{value}\r\n".encode()
        )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"clip\"; "
        f"filename=\"{filename}\"\r\nContent-Type: video/mp4\r\n\r\n".encode()
        + data
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


class TestReadingAPost:
    def test_it_finds_the_file_and_the_fields(self):
        body, content_type = multipart("clip.mp4", b"\x00\x01binary\xff", title="A name")
        upload = parse_multipart(body, content_type)
        assert upload.filename == "clip.mp4"
        assert upload.data == b"\x00\x01binary\xff"
        assert upload.fields["title"] == "A name"

    def test_a_post_with_no_file_is_refused(self):
        body = b"--x\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\nhi\r\n--x--\r\n"
        with pytest.raises(ValueError, match="no file"):
            parse_multipart(body, "multipart/form-data; boundary=x")

    def test_a_post_with_no_boundary_is_refused(self):
        with pytest.raises(ValueError, match="boundary"):
            parse_multipart(b"anything", "multipart/form-data")

    @pytest.mark.parametrize(
        "given, expected",
        [
            # Every path part is thrown away first, so only the last name is
            # left and there is nothing to climb with.
            ("../../etc/passwd", "passwd"),
            ("/tmp/HAZARD_x.mp4", "HAZARD_x.mp4"),
            ("..\\..\\windows\\x.mp4", "x.mp4"),
            ("a b;c&d|e.mp4", "a_b_c_d_e.mp4"),
            # This one keeps almost nothing, which is fine: the extension is
            # not load bearing. ffmpeg and flashmap read the container, not
            # the name.
            ("; rm -rf /.mp4", "mp4"),
            ("", "upload.bin"),
            ("...", "upload.bin"),
        ],
    )
    def test_a_name_cannot_climb_out_of_the_working_directory(self, given, expected):
        cleaned = safe_name(given)
        assert cleaned == expected
        assert "/" not in cleaned and "\\" not in cleaned
        assert not cleaned.startswith(".")
        assert not set(cleaned) & set(" ;&|$`\"'<>*?")


# ---------------------------------------------------------------------------
# The server itself
# ---------------------------------------------------------------------------


@pytest.fixture
def running_server():
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[0], server.server_address[1]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def post(url: str, body: bytes, content_type: str) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


class TestTheServer:
    def test_the_page_is_there(self, running_server):
        status, page = get(running_server + "/")
        assert status == 200
        assert "Check a clip" in page
        assert "never shows a frame" in page
        assert "MAX_MB" not in page, "the page still has its placeholder in it"
        assert "BIND_NOTE" not in page

    def test_the_aws_button_is_refused(self, running_server):
        status, page = post(running_server + "/aws", b"", "application/x-www-form-urlencoded")
        assert status == 503
        assert "HUMAN CHECKPOINT D" in page
        assert "has never called AWS" in page

    def test_there_is_no_route_that_serves_a_file(self, running_server):
        """An uploaded clip may be a hazard file. Nothing hands one back.

        A file is really put on disk, in the directory uploads land in, and
        then asked for by every spelling of its path. Asking only for names
        that are not there would pass against a server that happily serves
        anything that is: it would be testing the file system, not the route.
        """
        secret = "THIS-SHOULD-NEVER-BE-SERVED-8f21c0"
        planted = Path(tempfile.gettempdir()) / "calm-frames-upload-planted.txt"
        planted.write_text(secret, encoding="utf-8")
        here = Path(__file__).resolve()
        try:
            paths = [
                "/upload.mp4",
                "/static/clip.mp4",
                "/report",
                f"/{planted.name}",
                str(planted),
                "/.." + str(planted),
                "/../../.." + str(planted),
                f"/..{here}",
                "/pipeline/upload_server.py",
                "/../pipeline/upload_server.py",
            ]
            for path in paths:
                status, body = get(running_server + path)
                assert status == 404, f"GET {path} answered {status}, not 404"
                assert secret not in body, f"GET {path} handed back a file from disk"
                assert "def do_GET" not in body, f"GET {path} handed back source"
        finally:
            planted.unlink(missing_ok=True)

    def test_a_post_that_is_not_a_clip_gives_an_error_and_not_a_report(self, running_server):
        status, page = post(running_server + "/report", b"not multipart", "text/plain")
        assert status == 400
        assert "That is not a clip" in page
        assert "data:image/png" not in page, "an error must never come back as a report"

    def test_something_that_cannot_be_measured_is_never_called_safe(
        self, running_server, monkeypatch
    ):
        """A file that is not a video gets an error page, not an empty report.

        The dangerous failure here is the quiet one: a report with no spans in
        it, for a file the analyzer never read, looks exactly like a calm
        title.
        """
        body, content_type = multipart("clip.mp4", b"this is not a video at all")
        status, page = post(running_server + "/report", body, content_type)
        assert status == 500
        assert "Nothing was measured" in page
        assert "data:image/png" not in page
        assert "below the thresholds" not in page

    def test_a_clip_that_is_too_big_never_touches_the_disk(self, running_server):
        """Announced size alone is enough to refuse: nothing is read first."""
        request = urllib.request.Request(
            running_server + "/report",
            data=b"",
            headers={
                "Content-Type": "multipart/form-data; boundary=x",
                "Content-Length": str(MAX_UPLOAD_BYTES + 1),
            },
            method="POST",
        )
        request.data = b"x"
        # urllib sets its own Content-Length, so drive the socket directly.
        import http.client

        host = running_server.removeprefix("http://")
        connection = http.client.HTTPConnection(host, timeout=20)
        connection.putrequest("POST", "/report")
        connection.putheader("Content-Type", "multipart/form-data; boundary=x")
        connection.putheader("Content-Length", str(MAX_UPLOAD_BYTES + 1))
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 413
        assert b"Too big" in response.read()
        connection.close()


class TestAMeasuredClip:
    """The whole way through, on a clip made here and deleted here."""

    def test_a_calm_clip_comes_back_as_a_self_contained_report(
        self, running_server, tmp_path: Path
    ):
        if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
            pytest.skip("ffmpeg and ffprobe are needed to make a clip")
        from .clips import make_calm_clip

        clip = make_calm_clip(tmp_path / "calm.mp4", seconds=2)
        body, content_type = multipart("calm.mp4", clip.read_bytes(), title="A calm clip")
        status, page = post(running_server + "/report", body, content_type)

        assert status == 200, page[:600]
        assert page.startswith("<!doctype html>")
        assert "A calm clip" in page
        assert "data:image/png;base64," in page
        assert "never shows a frame of the film" in page
        for outside in ("src='http", 'src="http', "<script", "<iframe"):
            assert outside not in page, f"the report is not self contained: {outside}"

    def test_the_uploaded_clip_is_gone_before_the_answer_arrives(
        self, running_server, tmp_path: Path
    ):
        """Not "gone eventually": gone by the time the report is in your hands.

        The server deletes the clip before it writes the response, so this can
        be asserted the moment the answer arrives with no waiting and no
        polling. An earlier version sent first and deleted after, and this test
        caught it as a race.
        """
        if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
            pytest.skip("ffmpeg and ffprobe are needed to make a clip")
        from .clips import make_calm_clip

        before = set(Path(tempfile.gettempdir()).glob("calm-frames-upload-*"))
        clip = make_calm_clip(tmp_path / "calm2.mp4", seconds=2)
        body, content_type = multipart("calm2.mp4", clip.read_bytes())
        status, _ = post(running_server + "/report", body, content_type)
        assert status == 200
        after = set(Path(tempfile.gettempdir()).glob("calm-frames-upload-*"))
        assert not (after - before), (
            "the uploaded clip is still on disk. It may be a hazard file, and nothing "
            "needs it once the numbers are out."
        )

    def test_a_clip_that_could_not_be_measured_is_deleted_too(self, running_server):
        before = set(Path(tempfile.gettempdir()).glob("calm-frames-upload-*"))
        body, content_type = multipart("clip.mp4", b"not a video")
        status, _ = post(running_server + "/report", body, content_type)
        assert status == 500
        after = set(Path(tempfile.gettempdir()).glob("calm-frames-upload-*"))
        assert not (after - before), "a clip that failed to measure was left on disk"
