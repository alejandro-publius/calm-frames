"""Drive the Vega Virtual Device through QEMU's QMP socket.

The Vega CLI can install and launch an app on the virtual device, but it has no
command for pressing remote buttons or capturing the screen. The virtual device
is QEMU, and it opens a QMP socket, so we can do both from here:

    python3 eval/vvd_control.py keys down ret
    python3 eval/vvd_control.py shot /tmp/home.png
    python3 eval/vvd_control.py motion --seconds 4

"keys" sends remote button presses, "shot" saves a screenshot, and "motion"
takes two screenshots a few seconds apart and reports how much of the picture
changed, which is how we check that video is really playing rather than sitting
on a still frame.

Safety: this tool only reads the screen. Anything it captures while real
flashing content could be on screen must be handled under the rules in
docs/SAFETY.md, which means looking at numbers and plots, not playing frames
back at speed.
"""

from __future__ import annotations

import argparse
import glob
import json
import socket
import struct
import sys
import time
import zlib
from pathlib import Path

DEFAULT_SOCKET_GLOB = "/tmp/qmp-socket-*.sock"

# QEMU key names for the remote buttons we use. The virtual device maps the
# keyboard arrows, Enter and Escape to the D-pad, select and back.
KEY_ALIASES = {
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "ok": "ret",
    "select": "ret",
    "enter": "ret",
    "ret": "ret",
    "back": "esc",
    "esc": "esc",
    "home": "home",
    "space": "spc",
}


def find_socket(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    matches = sorted(glob.glob(DEFAULT_SOCKET_GLOB))
    if not matches:
        raise SystemExit(
            "No QMP socket found. Start the virtual device first with "
            "'vega virtual-device start'."
        )
    if len(matches) > 1:
        print(f"note: several QMP sockets found, using {matches[0]}", file=sys.stderr)
    return matches[0]


class Qmp:
    """A small QMP client. QMP speaks one JSON object per line."""

    def __init__(self, path: str, timeout: float = 20.0) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect(path)
        self.buf = b""
        self._read_message()  # the greeting
        self.command("qmp_capabilities")

    def _read_message(self) -> dict:
        while b"\n" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise SystemExit("QMP connection closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return json.loads(line)

    def command(self, name: str, **arguments) -> dict:
        payload = {"execute": name}
        if arguments:
            payload["arguments"] = arguments
        self.sock.sendall((json.dumps(payload) + "\n").encode())
        while True:
            message = self._read_message()
            if "error" in message:
                raise SystemExit(f"QMP error on {name}: {message['error']}")
            if "return" in message:
                return message["return"]
            # events (for example RESUME) are not replies, so keep reading

    def press(self, key: str, hold_ms: int = 60) -> None:
        qcode = KEY_ALIASES.get(key.lower(), key.lower())
        for down in (True, False):
            self.command(
                "input-send-event",
                events=[
                    {
                        "type": "key",
                        "data": {"down": down, "key": {"type": "qcode", "data": qcode}},
                    }
                ],
            )
            if down:
                time.sleep(hold_ms / 1000)

    def screenshot(self, destination: Path) -> Path:
        """Save a screenshot. QEMU writes PPM, so convert it to PNG."""
        destination = destination.expanduser().resolve()
        ppm = destination.with_suffix(".ppm")
        self.command("screendump", filename=str(ppm))
        # screendump returns once the file is written, but the file lands on the
        # host, so wait for it to be non-empty before reading it.
        for _ in range(50):
            if ppm.exists() and ppm.stat().st_size > 0:
                break
            time.sleep(0.1)
        if destination.suffix.lower() == ".ppm":
            return ppm
        png = ppm_to_png(ppm, destination)
        ppm.unlink(missing_ok=True)
        return png

    def close(self) -> None:
        self.sock.close()


def read_ppm(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if not data.startswith(b"P6"):
        raise SystemExit(f"{path} is not a binary PPM file")
    fields: list[bytes] = []
    index = 2
    while len(fields) < 3:
        while index < len(data) and data[index : index + 1].isspace():
            index += 1
        if data[index : index + 1] == b"#":
            while data[index : index + 1] not in (b"\n", b""):
                index += 1
            continue
        start = index
        while index < len(data) and not data[index : index + 1].isspace():
            index += 1
        fields.append(data[start:index])
    width, height, maxval = (int(f) for f in fields)
    if maxval != 255:
        raise SystemExit(f"{path} has an unsupported max value {maxval}")
    return width, height, data[index + 1 :]


def ppm_to_png(ppm: Path, png: Path) -> Path:
    """Write a PNG without needing Pillow, so this tool has no dependencies."""
    width, height, pixels = read_ppm(ppm)
    raw = bytearray()
    stride = width * 3
    for row in range(height):
        raw.append(0)  # filter type 0
        raw.extend(pixels[row * stride : (row + 1) * stride])

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    png.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )
    return png


def mean_abs_difference(first: Path, second: Path) -> float:
    """Mean absolute difference per channel, 0 to 255, between two PPM files."""
    width_a, height_a, pixels_a = read_ppm(first)
    width_b, height_b, pixels_b = read_ppm(second)
    if (width_a, height_a) != (width_b, height_b):
        raise SystemExit("screenshots have different sizes")
    step = 7  # sampling keeps this quick on a 1080p frame
    total = 0
    count = 0
    for index in range(0, min(len(pixels_a), len(pixels_b)), step):
        total += abs(pixels_a[index] - pixels_b[index])
        count += 1
    return total / max(count, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", help="path to the QMP socket")
    sub = parser.add_subparsers(dest="command", required=True)

    keys = sub.add_parser("keys", help="press remote buttons in order")
    keys.add_argument("keys", nargs="+", help="up down left right ok back")
    keys.add_argument("--gap-ms", type=int, default=600, help="wait between presses")

    shot = sub.add_parser("shot", help="save a screenshot")
    shot.add_argument("path", type=Path)

    motion = sub.add_parser(
        "motion", help="measure how much the picture changes over a few seconds"
    )
    motion.add_argument("--seconds", type=float, default=4.0)
    motion.add_argument("--keep", type=Path, help="directory to keep the frames in")

    args = parser.parse_args()
    qmp = Qmp(find_socket(args.socket))
    try:
        if args.command == "keys":
            for key in args.keys:
                qmp.press(key)
                print(f"pressed {key}")
                time.sleep(args.gap_ms / 1000)
            return 0

        if args.command == "shot":
            saved = qmp.screenshot(args.path)
            print(f"saved {saved}")
            return 0

        if args.command == "motion":
            directory = args.keep or Path("/tmp")
            directory.mkdir(parents=True, exist_ok=True)
            first = qmp.screenshot(directory / "vvd_motion_a.ppm")
            time.sleep(args.seconds)
            second = qmp.screenshot(directory / "vvd_motion_b.ppm")
            difference = mean_abs_difference(first, second)
            print(
                json.dumps(
                    {
                        "seconds_apart": args.seconds,
                        "mean_abs_difference": round(difference, 3),
                        "frames": [str(first), str(second)],
                    }
                )
            )
            return 0
    finally:
        qmp.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
