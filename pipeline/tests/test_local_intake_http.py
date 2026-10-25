"""Real local file-to-review checks with generated steady-color, silent media.

No video is played, signed, shipped or downloaded. Temporary files are owned
by pytest. The encryption fixture uses public dummy values, not a DRM service.
"""

import hashlib
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from pipeline.ffmpegtool import run_ffmpeg

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def media(tmp_path):
    clear = tmp_path / "steady-color.mp4"
    run_ffmpeg([
        "-v", "error", "-f", "lavfi", "-i", "color=c=0x6faea8:s=160x90:r=12:d=1",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
        "-shortest", "-c:v", "libx264", "-threads", "1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-movflags", "+faststart", str(clear),
    ], timeout_s=20)
    return clear


class LocalServer:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.port = 0

    def start(self):
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            self.port = reserved.getsockname()[1]
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(REPO / "flashmap/src"), str(REPO)]))
        self.process = subprocess.Popen(
            [sys.executable, "-m", "pipeline.local_intake", "serve", "--root", str(self.root),
             "--port", str(self.port)], cwd=REPO, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            assert self.process.poll() is None, "Local intake server did not start"
            try:
                if self.request("GET", "/jobs")[0] == 200:
                    return
            except OSError:
                time.sleep(0.05)
        raise AssertionError("Local intake server was not ready within the startup bound")

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate(timeout=3)

    def request(self, method, path, data=None, **headers):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            if method == "POST":
                headers.setdefault("Origin", f"http://127.0.0.1:{self.port}")
            connection.request(method, path, body=data, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            value = json.loads(raw) if response.getheader("Content-Type") == "application/json" else raw.decode()
            return response.status, value, dict(response.getheaders())
        finally:
            connection.close()

    def upload(self, data, *, permission=True, **headers):
        boundary = "calm-frames-generated-fixture-boundary"
        parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\nFictional pond\r\n'.encode()]
        if permission:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="permission"\r\n\r\nconfirmed\r\n'.encode())
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="fixture.mp4"\r\nContent-Type: video/mp4\r\n\r\n'.encode())
        parts.extend([data, f"\r\n--{boundary}--\r\n".encode()])
        return self.request("POST", "/jobs", b"".join(parts), **{"Content-Type": f"multipart/form-data; boundary={boundary}", **headers})

    def settled(self, job_id):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            status, value, _ = self.request("GET", "/jobs")
            assert status == 200
            job = next(j for j in value["jobs"] if j["id"] == job_id)
            if job["status"] not in {"queued", "checking", "analyzing", "preparing", "exporting"}:
                return job
            time.sleep(0.1)
        raise AssertionError("Generated fixture did not finish within the analysis bound")


@pytest.fixture
def server(tmp_path):
    running = LocalServer(tmp_path / "imports")
    try:
        running.start()
        yield running
    finally:
        running.stop()


def test_real_file_to_durable_caregiver_review_without_signer(server, media):
    data = media.read_bytes()
    assert server.upload(data, permission=False)[0] == 400
    assert server.request("GET", "/jobs")[1]["jobs"] == []
    assert not list(server.root.glob("*/original.mp4"))
    assert server.upload(data, Origin="https://unrelated.invalid")[0] == 403

    status, created, _ = server.upload(data)
    assert status == 200
    job = server.settled(created["id"])
    assert job["status"] == "review", job.get("error")
    assert job["review"]["analysis_complete"] is True
    assert job["review"]["frame_count"] == 12
    assert job["review"]["duration_ms"] == 1000
    assert job["playable"] is False
    review_path = f'/jobs/{job["id"]}/review'
    status, report, headers = server.request("GET", review_path)
    assert status == 200
    assert headers["Content-Disposition"].startswith("attachment;")
    assert headers["Cache-Control"] == "no-store"
    assert report["source"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert report["tv_playback_authorized"] is False
    assert str(server.root) not in json.dumps(report)
    assert server.request("GET", f'/jobs/{job["id"]}/original.mp4')[0] == 404

    original = server.root / job["id"] / "original.mp4"
    original.write_bytes(b"changed fixture only")
    assert server.request("GET", review_path)[0] == 400
    original.write_bytes(data)
    assert server.request("POST", f'/jobs/{job["id"]}/approve')[1]["status"] == "signing_blocked"
    server.stop()
    server.start()
    assert server.request("GET", review_path)[1] == report
    assert server.request("GET", "/jobs")[1]["jobs"][0]["status"] == "signing_blocked"
    assert not list(server.root.rglob("package/catalog.json"))


def test_real_encrypted_file_is_refused_without_decode_or_decryption(server, media, tmp_path):
    encrypted = tmp_path / "encrypted-fixture.mp4"
    run_ffmpeg([
        "-v", "error", "-i", str(media), "-c", "copy", "-encryption_scheme", "cenc-aes-ctr",
        "-encryption_key", "00" * 16, "-encryption_kid", "11" * 16, str(encrypted),
    ], timeout_s=20)
    status, created, _ = server.upload(encrypted.read_bytes())
    assert status == 200
    job = server.settled(created["id"])
    assert job["status"] == "failed"
    assert "DRM" in job["error"] or "Encrypted" in job["error"]
    assert job["playable"] is False
    assert not list((server.root / job["id"]).rglob("wcag.json"))
    assert server.request("GET", f'/jobs/{job["id"]}/review')[0] == 400


def test_unreadable_job_does_not_break_the_real_review_server(server, media):
    status, created, _ = server.upload(media.read_bytes())
    assert status == 200
    job = server.settled(created['id'])
    assert job['status'] == 'review'
    review_url = f'/jobs/{job["id"]}/review'
    original_report = server.request('GET', review_url)[1]
    broken_id = 'c' * 32
    broken = server.root / broken_id
    broken.mkdir(mode=0o700)
    (broken / 'original.mp4').write_bytes(b'owned incomplete fixture, not playable')
    (broken / 'job.json').write_text('{')
    status, response, _ = server.request('GET', '/jobs')
    assert status == 200
    assert {row['id']: row['status'] for row in response['jobs']} == {
        job['id']: 'review', broken_id: 'unreadable',
    }
    assert str(server.root) not in json.dumps(response)
    server.stop()
    server.start()
    assert server.request('GET', review_url)[1] == original_report
    assert server.request('GET', f'/jobs/{broken_id}/review')[0] == 400
    assert server.request('POST', f'/jobs/{broken_id}/retry')[0] == 400
    assert (broken / 'job.json').read_text() == '{'
    assert server.request('POST', f'/jobs/{broken_id}/delete')[0] == 200
    assert not broken.exists()
    assert server.request('GET', review_url)[1] == original_report
    assert media.read_bytes() == (server.root / job['id'] / 'original.mp4').read_bytes()
