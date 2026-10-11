"""Current benign native smoke entrypoint; historical VVD helpers retained.

The old sample-home D-pad script is obsolete and could select the wrong title.
CLI execution now uses benign_native_smoke: a read-only preflight by default,
with explicit --device and --execute required for a current Harbor session.
Historical results/vvd_smoke.json is never overwritten by this entrypoint.

start_virtual_device is retained for the separate existing fuzz harness.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VEGA = "source ~/vega/env >/dev/null 2>&1 && NO_COLOR=1 "


def vega(arguments: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-lc", VEGA + "vega " + arguments],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def virtual_device_running() -> bool:
    result = vega("virtual-device status", timeout=120)
    return '"running":true' in result.stdout.replace(" ", "")


def device_connected() -> bool:
    result = vega("device is-connected", timeout=120)
    return "is connected" in result.stdout


def wait_for_device(wait_seconds: int = 300) -> bool:
    """QEMU reports running as soon as it starts, well before the guest has
    booted and the device adapter can see it, so wait for the device itself."""
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if device_connected():
            return True
        time.sleep(5)
    return False


def start_virtual_device(wait_seconds: int = 300) -> bool:
    if virtual_device_running():
        return wait_for_device(wait_seconds)
    print("starting the virtual device")
    # Detach it, so it keeps running after this script exits.
    subprocess.Popen(
        ["bash", "-lc", VEGA + "exec vega virtual-device start -t 300"],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if virtual_device_running():
            return wait_for_device(int(max(deadline - time.time(), 60)))
        time.sleep(10)
    return False


def main() -> int:
    if __package__:
        from .benign_native_smoke import main as benign_main
    else:
        from benign_native_smoke import main as benign_main
    return benign_main()


if __name__ == "__main__":
    raise SystemExit(main())
