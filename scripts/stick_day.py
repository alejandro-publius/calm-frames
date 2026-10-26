#!/usr/bin/env python3
"""Stick day: from an unopened box to GATE 1 footage, in about thirty minutes.

    make stick-day                  the device that is connected
    make stick-day STICK_DAY_ARGS="--target vvd"     the Vega Virtual Device
    make stick-day STICK_DAY_ARGS="--target stick"   a real Fire TV Stick

It runs the whole first session in order and stops at the first thing that is
wrong, rather than letting you find out after the camera is set up:

  1. preflight: packages built, marker clip present, device free
  2. developer mode: the button sequence and the two CLI commands
  3. the OS build on the device, refused if it is not Vega OS 1.2
  4. install the renamed build
  5. the ten minute layering test, with what to watch for while it runs
  6. the marker schedule run, with what to film, for how long, and where the
     files go afterwards

Everything except the parts a person has to do with a remote in their hand runs
against the Vega Virtual Device as well, which is how this was proven before the
stick existed. Anything that can only be answered by looking at a television is
printed as a question for the person, never guessed.

Safety: every clip this plays is calm by construction. The marker clip is one
pair of opposing luminance changes every six seconds, far under the three per
second WCAG counts as flashing. Never point a measurement run at flashing
content with the cover off. See docs/SAFETY.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = str(REPO / ".venv" / "bin" / "python")
VEGA = "source ~/vega/env >/dev/null 2>&1 && NO_COLOR=1 "

# The build the project is pinned to. docs/GATES.md HUMAN CHECKPOINT B.
REQUIRED_OS = "1.2"
REQUIRED_BUILD = "2101020054720"

# Developer mode, from https://developer.amazon.com/docs/vega/0.24/developer-mode.html
# Read again on Sep 17, 2026 rather than quoted from memory.
DEVELOPER_MODE_DOC = "https://developer.amazon.com/docs/vega/0.24/developer-mode.html"

ARCH_FOR = {"stick": "armv7", "vvd": "aarch64"}

OUT_DIR = REPO / "results" / "stick_day"


# ------------------------------------------------------------------ output


def heading(number: int, title: str, cost: str) -> None:
    print()
    print("=" * 72)
    # "about" only makes sense in front of a length of time.
    prefix = "about " if any(unit in cost for unit in ("min", "sec", "hour")) else ""
    print(f"{number}. {title}    ({prefix}{cost})")
    print("=" * 72)


def minutes_text(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f} seconds"
    return f"{seconds / 60:.0f} minutes"


def say(text: str = "") -> None:
    print(text)


def stop(reason: str, advice: str = "") -> None:
    print()
    print("-" * 72)
    print(f"STOP: {reason}")
    if advice:
        print()
        print(advice)
    print("-" * 72)


# ------------------------------------------------------------------- shell


def vega(arguments: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-lc", VEGA + "vega " + arguments],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run(command: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=REPO, text=True, timeout=timeout)


# --------------------------------------------------------------- preflight


def device_busy() -> str | None:
    """Is another lane using the device right now?

    Two runs cannot share it: the timing runner binds port 8000 to serve the
    clip, installs over the top of whatever is there and streams the log. The
    second one to start quietly ruins both. This looks for the signs rather
    than finding out halfway through a take.
    """
    port = subprocess.run(
        ["lsof", "-nP", "-iTCP:8000", "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
    )
    if port.returncode == 0 and port.stdout.strip():
        first = port.stdout.strip().splitlines()[-1].split()
        owner = f"{first[0]} (pid {first[1]})" if len(first) > 1 else port.stdout.strip()
        return f"port 8000 is already serving a run: {owner}"

    processes = subprocess.run(["ps", "-Ao", "pid,command"], capture_output=True, text=True)
    for line in processes.stdout.splitlines():
        if "stick_day.py" in line:
            continue
        for tool in ("vvd_timing_run.py", "vvd_smoke.py", "gate1_software.py"):
            if tool in line and "grep" not in line:
                return f"another run is in flight: {line.strip()[:120]}"
    return None


def preflight(args, target: str) -> dict:
    heading(1, "Preflight", "1 minute")

    facts: dict = {}
    problems: list[str] = []

    arch = ARCH_FOR[target]
    vpkg = args.vpkg or (REPO / f"app/build/{arch}-debug/calm-frames-app_{arch}.vpkg")
    facts["package"] = str(vpkg)
    if vpkg.exists():
        size_mb = vpkg.stat().st_size / 1_000_000
        built = datetime.fromtimestamp(vpkg.stat().st_mtime).strftime("%b %d %H:%M")
        say(f"  package      {vpkg.relative_to(REPO)}  ({size_mb:.1f} MB, built {built})")
    else:
        problems.append(
            f"no package at {vpkg}.\n"
            f"       Build one: cd app && npm run build:app  (or make release)"
        )

    # A debug build, because release builds strip console.log and the run's
    # evidence is what the app says about itself.
    if "debug" not in str(vpkg):
        say("  warning      this is not a debug package. Release builds strip")
        say("               console.log, so the run has less to say for itself.")

    schedule_path, clip_path = choose_schedule(args)
    facts["schedule"] = str(schedule_path) if schedule_path else None
    facts["clip"] = str(clip_path) if clip_path else None
    if schedule_path is None:
        problems.append(
            "no marker schedule found in eval/harness_runs/.\n"
            "       Make one: .venv/bin/python eval/marker_clip.py"
        )
    else:
        schedule = json.loads(schedule_path.read_text())
        markers = len(schedule["markers"])
        say(f"  schedule     {schedule_path.relative_to(REPO)}  ({markers} markers)")
        if clip_path is None or not clip_path.exists():
            problems.append(
                f"the schedule names {schedule['clip']['file_name']}, which is not in media/.\n"
                "       The clip is never committed. Make it again:\n"
                "       .venv/bin/python eval/marker_clip.py"
            )
        else:
            say(f"  clip         {clip_path.relative_to(REPO)}")
            say("               checking the clip against the schedule hash")
            digest = sha256_of(clip_path)
            if digest != schedule["clip"]["sha256"]:
                problems.append(
                    f"{clip_path.name} is not the clip this schedule was made for.\n"
                    f"       schedule: {schedule['clip']['sha256'][:16]}\n"
                    f"       file:     {digest[:16]}\n"
                    "       Numbers from a run against the wrong clip mean nothing.\n"
                    "       Rebuild both: .venv/bin/python eval/marker_clip.py"
                )
            else:
                say(f"               matches ({digest[:16]})")

    for tool in ("ffmpeg",):
        found = subprocess.run(["which", tool], capture_output=True, text=True)
        if found.returncode != 0:
            problems.append(f"{tool} is not installed. The clip is served as HLS, which needs it.")

    busy = None if args.ignore_busy else device_busy()
    facts["device_busy"] = busy
    if busy:
        problems.append(
            f"the device is busy: {busy}\n"
            "       This machine has one virtual device and several lanes. Wait for\n"
            "       the other run to finish, or pass --ignore-busy if you know it is\n"
            "       stale. Two runs at once ruin both."
        )

    if problems:
        stop(
            "preflight found something that would waste the session",
            "\n".join(f"  {index + 1}. {problem}" for index, problem in enumerate(problems)),
        )
        raise SystemExit(2)

    say("  all clear")
    return facts


def sha256_of(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def choose_schedule(args) -> tuple[Path | None, Path | None]:
    """The 50 marker schedule when it exists, because GATE 1 wants 50 trials."""
    if args.schedule:
        schedule = Path(args.schedule)
    else:
        candidates = [
            REPO / "eval/harness_runs/marker_schedule_50.json",
            REPO / "eval/harness_runs/marker_schedule.json",
        ]
        schedule = next((path for path in candidates if path.exists()), None)
    if schedule is None or not schedule.exists():
        return None, None
    data = json.loads(schedule.read_text())
    clip = Path(args.clip) if args.clip else REPO / "media" / data["clip"]["file_name"]
    return schedule, clip


# ---------------------------------------------------------- developer mode


def developer_mode(target: str, args) -> dict:
    heading(2, "Developer mode", "5 minutes, and only ever once per device")

    if target == "vvd":
        say("  The virtual device is already in developer mode. Nothing to do here.")
        say("  The steps below are what you will do to the stick, printed so this")
        say("  run proves the same path the stick takes.")
        say()

    say(f"  From {DEVELOPER_MODE_DOC}")
    say("  (read again on Sep 17, 2026, not quoted from memory)")
    say()
    say("  On the television, with the remote:")
    say()
    say("    1. Settings > My Fire TV > About")
    say("    2. move to your device's model name and press the centre button")
    say("       seven times. A notification appears after the seventh press.")
    say("    3. go back to My Fire TV > Developer options > Developer Mode")
    say("    4. choose Continue")
    say()
    say("  Then on this machine:")
    say()
    say("    source ~/vega/env")
    say("    vega devmode login")
    say("        follow the prompts. It needs an Amazon Developer account.")
    say("    vega devmode enable-device --code <the 6 digit code on the TV>")
    say()
    say("  Amazon's page says to check with 'vega device list'. Do not: it crashes")
    say("  with a TypeError on Vega CLI 1.3.4, which is the version we are pinned")
    say("  to. Use these instead:")
    say()
    say("    vega device is-connected")
    say("    vega device info")
    say()
    say("  Keep the stick on the same network as this machine, and leave it")
    say("  plugged into mains power rather than a television USB port.")

    if target == "vvd":
        if not device_connected():
            stop(
                "the virtual device is not connected",
                "  Start it, detached, and wait for the device rather than the VM:\n"
                "    .venv/bin/python eval/vvd_smoke.py --play-seconds 0\n"
                "  or: vega virtual-device start -t 300\n"
                "  then poll: vega device is-connected",
            )
            raise SystemExit(2)
        say()
        say("  Device is connected.")
        return {"developer_mode": "already on, virtual device"}

    say()
    deadline = time.time() + args.wait_minutes * 60
    say(f"  Waiting up to {args.wait_minutes} minutes for the stick to appear.")
    while time.time() < deadline:
        if device_connected():
            say("  Device is connected.")
            return {"developer_mode": "enabled and connected"}
        time.sleep(10)
    stop(
        "no device after waiting",
        "  Developer mode is per device and does not survive a factory reset.\n"
        "  If 'vega devmode enable-device' reported success and the device is\n"
        "  still not here, check both are on the same network, then rerun.",
    )
    raise SystemExit(2)


def device_connected() -> bool:
    return "is connected" in vega("device is-connected", timeout=120).stdout


# ------------------------------------------------------------ the OS check


def read_device_info(args) -> dict:
    """What the device says about itself.

    --device-info-file takes a saved copy instead of asking the device. That is
    how the refusal below gets tested without a stick on the wrong OS: feed it
    the info of a device that should be refused and watch it refuse.
    """
    if args.device_info_file:
        return json.loads(Path(args.device_info_file).read_text())
    result = vega("device info", timeout=120)
    text = result.stdout.strip()
    start = text.find("{")
    if start < 0:
        stop("vega device info said nothing that looks like JSON", f"  it said: {text[:300]}")
        raise SystemExit(2)
    return json.loads(text[start:])


def check_os(info: dict) -> dict:
    heading(3, "The OS build on the device", "30 seconds")

    description = str(info.get("buildDescription", ""))
    simulated = bool(info.get("simulated"))
    version_match = re.search(r"OS\s+(\d+\.\d+)", description)
    build_match = re.search(r"/(\d+)\)", description)
    version = version_match.group(1) if version_match else None
    build = build_match.group(1) if build_match else None

    say(f"  reports      {description or '(nothing)'}")
    say(f"  architecture {info.get('architecture', '?')}")
    say(f"  simulated    {'yes, this is the virtual device' if simulated else 'no, this is real hardware'}")
    say(f"  devmode      {'on' if info.get('inDeveloperMode') else 'off'}")

    fallback = (
        "  The fallback is SDK 0.23.\n"
        "\n"
        "    source ~/vega/env\n"
        "    vega sdk list-remote            find the 0.23 line\n"
        "    vega sdk install <0.23 version>\n"
        "    vega sdk use <0.23 version>\n"
        "    cd app && npm run build:app     rebuild against 0.23\n"
        "\n"
        "  Expect work, not a switch: the app is written against SDK 0.24 and\n"
        "  React Native 0.83, and docs/DECISIONS.md records that pin. Before you\n"
        "  spend the evening on it, try the other direction on the television:\n"
        "  Settings > My Fire TV > About > Check for Updates, then rerun this."
    )

    if version is None:
        stop(
            "could not read an OS version from the device",
            f"  buildDescription was: {description!r}\n\n" + fallback,
        )
        raise SystemExit(3)

    if version != REQUIRED_OS:
        stop(
            f"this device is on Vega OS {version}, and the build needs {REQUIRED_OS}",
            fallback,
        )
        raise SystemExit(3)

    if simulated:
        say()
        say(f"  Vega OS {version}. Build {build}, which is the virtual device's own")
        say(f"  build and not the stick's. The stick has to be build {REQUIRED_BUILD},")
        say("  and that is checked strictly on real hardware.")
        return {"os_version": version, "build": build, "simulated": True, "build_checked": False}

    if build != REQUIRED_BUILD:
        stop(
            f"this stick is on Vega OS {version} build {build}, and the project is "
            f"pinned to build {REQUIRED_BUILD}",
            "  A different build of the same OS version has moved things under us\n"
            "  before. Check for an update on the television first:\n"
            "  Settings > My Fire TV > About > Check for Updates.\n"
            "\n" + fallback,
        )
        raise SystemExit(3)

    say()
    say(f"  Vega OS {version}, build {build}. This is the one.")
    return {"os_version": version, "build": build, "simulated": False, "build_checked": True}


# --------------------------------------------------------------- install


def install(target: str, facts: dict, args) -> dict:
    heading(4, "Install the build", "2 minutes")

    vpkg = Path(facts["package"])
    package_id = read_package_id()
    say(f"  package id   {package_id}")
    if package_id.startswith("com.amazon"):
        stop(
            "the package id starts with com.amazon",
            "  Developer mode will not sideload one of those. The id lives in\n"
            "  app/manifest.toml and belongs to the app lane.",
        )
        raise SystemExit(2)
    say("               does not start with com.amazon, so developer mode will take it")
    say()
    say(f"  installing   vega run-app {vpkg.relative_to(REPO)}")

    if args.dry_run:
        say("  (dry run, nothing installed)")
        return {"installed": False, "dry_run": True}

    result = vega(f"run-app {vpkg}", timeout=900)
    output = result.stdout + result.stderr
    if "Successfully launched" not in output:
        stop(
            "the app did not launch",
            "  vega said:\n" + "\n".join(f"    {line}" for line in output.strip().splitlines()[-12:]),
        )
        raise SystemExit(4)
    say("  launched.")
    if target == "stick":
        say()
        say("  Look at the television now. If the screen is black, press any button")
        say("  on the remote: a freshly launched app can start in the background.")
    return {"installed": True, "package_id": package_id}


def read_package_id() -> str:
    for line in (REPO / "app" / "manifest.toml").read_text().splitlines():
        match = re.match(r'\s*id\s*=\s*"([^"]+)"', line)
        if match:
            return match.group(1)
    return "unknown"


# --------------------------------------------------------- layering test


def layering(target: str, facts: dict, args) -> dict:
    heading(5, "The layering test, captions on", minutes_text(args.layering_seconds))

    say("  Before it starts, on the television:")
    say()
    say("    1. start any title and turn captions ON in the player")
    say("    2. turn the volume up enough to hear it from where you are sitting")
    say("    3. film the screen, or sit where you can watch it without moving")
    say()
    say("  A full screen cover toggles every 5 seconds over a playing title.")
    say("  Watch for exactly three things, and write down what you saw:")
    say()
    say("    a. is the picture FULLY hidden every single time the cover comes on?")
    say("       Look at the edges and the corners. Video plays on a hardware layer")
    say("       and the cover is a view on top of it, so a gap at one edge, or one")
    say("       toggle in twenty that leaves a sliver, is the thing this test exists")
    say("       to catch. Partly hidden is a fail.")
    say()
    say("    b. do the captions stay readable ABOVE the cover, the whole time?")
    say("       Not behind it, not dimmed, not gone. Sound and captions carrying on")
    say("       while the picture is hidden is the promise this product makes.")
    say()
    say("    c. does the audio keep going, with no gap, dropout or stutter,")
    say("       through every toggle?")
    say()
    say("  Any crash, any black screen that does not come back, or any change in")
    say("  the picture position when the cover lifts: write it down too.")
    say()

    if target == "vvd":
        say("  On the virtual device nobody can answer a, b or c by looking: the app")
        say("  draws on a GPU layer that both screen grabs and QEMU's screendump")
        say("  come back black from. What this run proves here is the other half:")
        say("  that the cover toggles on schedule, that playback keeps running under")
        say("  it, and that nothing crashes. The three questions above need the")
        say("  stick and a pair of eyes.")
        say()

    if args.skip_layering:
        say("  (skipped: --skip-layering)")
        return {"ran": False, "skipped": True}
    if args.dry_run:
        say("  (dry run, not started)")
        return {"ran": False, "dry_run": True}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "layering.json"
    command = [
        PY,
        str(REPO / "eval/vvd_timing_run.py"),
        "--mode", "layering",
        "--seconds", str(args.layering_seconds),
        "--clip", facts["clip"],
        "--schedule", facts["schedule"],
        "--vpkg", facts["package"],
        "--out", str(out),
    ]
    say(f"  running for {args.layering_seconds:.0f} s. Leave it alone.")
    result = run(command, timeout=int(args.layering_seconds) + 900)
    if result.returncode != 0 or not out.exists():
        say()
        say("  The layering run did not produce a summary. That is a result too:")
        say("  record it as inconclusive rather than rerunning until it looks good.")
        return {"ran": True, "ok": False, "out": str(out)}

    summary = json.loads(out.read_text())
    on = summary["cover"]["on_events"]
    off = summary["cover"]["off_events"]
    updates = summary["timeupdate"]["count"]
    say()
    say(f"  cover toggled on {on} times and off {off} times")
    say(f"  the player reported its position {updates} times during the run")
    if updates == 0:
        say()
        say("  Playback did not run in this take. The cover behaved, but the test")
        say("  says nothing about sound continuing, because there was no sound.")
        say("  Record it as inconclusive and take it again.")
    say(f"  written to {out.relative_to(REPO)}")
    say()
    say("  Write what you saw into docs/GATES.md under the layering test, in the")
    say("  same words as a, b and c above. An unrecorded answer is a lost session.")
    return {
        "ran": True,
        "ok": updates > 0,
        "cover_on": on,
        "cover_off": off,
        "timeupdates": updates,
        "out": str(out),
    }


# ------------------------------------------------------- the marker run


def marker_run(target: str, facts: dict, args) -> dict:
    heading(6, "The marker schedule run, filmed at 240 fps", "8 minutes")

    schedule = json.loads(Path(facts["schedule"]).read_text())
    markers = len(schedule["markers"])
    clip_seconds = schedule["clip"]["duration_s"]
    patch = schedule["reference_patch"]
    film_seconds = int(clip_seconds) + 20

    say("  What GATE 1 measures: was the cover fully on at least 150 ms before the")
    say(f"  marker appeared, in at least 48 of 50 trials. This schedule has {markers}.")
    say()
    say("  Set up before you start:")
    say()
    say("    1. the television in game mode, motion smoothing OFF. Smoothing invents")
    say("       frames between real ones, and an invented frame is exactly the thing")
    say("       a 240 fps recording must not contain.")
    say("    2. the phone on something that does not move, framing the WHOLE screen")
    say("       with a little room around it. Both of these have to be in frame:")
    say(f"         - the reference patch, {patch['width']} by {patch['height']} pixels at")
    say(f"           x={patch['x']}, y={patch['y']}, top left. The cover leaves it")
    say("           uncovered on purpose, so the recording can show the screen was")
    say("           live while the rest was hidden.")
    say("         - the middle of the screen, where the markers appear.")
    say("    3. the phone camera set to 240 fps, and locked: fixed exposure, fixed")
    say("       focus, HDR off. Auto exposure hunting across a bright marker will")
    say("       ruin the very frames being measured.")
    say("    4. room lights off, or steady. Anything on a dimmer beats against the")
    say("       shutter at 240 fps.")
    say()
    say("  What to film, and for how long:")
    say()
    say(f"    one take, {film_seconds} seconds: start recording about 10 seconds before")
    say(f"    the run starts, let all {markers} markers play ({clip_seconds:.0f} s of clip),")
    say("    and keep recording about 10 seconds after the last one. Do not stop and")
    say("    start: one continuous take is what lets every marker be lined up against")
    say("    the same clock.")
    say()
    say("  One thing to do with your ears, not the camera:")
    say()
    say("    listen for the chime. It sounds two seconds of media time before each")
    say("    cover goes on, and it has never been heard on a device: the sound is")
    say("    ours, it is bundled at assets/raw/sound/calm-chime.mp3, and the audio")
    say("    path is AudioPlayer from react-native-w3cmedia, which nothing has")
    say("    exercised on hardware. If you hear nothing, that is a finding and not")
    say("    a fault in the run: write it down and carry on. The cover does not")
    say("    depend on it.")
    say()
    say("    While you are there: is it the right loudness against the film, and")
    say("    is two seconds the right warning for a child. Both were chosen here")
    say("    and neither has been heard by anyone.")
    say()
    say("  Where the files go afterwards:")
    say()
    today = datetime.now().strftime("%Y-%m-%d")
    say(f"    the recording   media/gate1/{today}_take1.mov")
    say("                    media/ is gitignored, so the video stays out of git and")
    say("                    off GitHub. Keep it, it is the evidence.")
    say(f"    the app's view  {(OUT_DIR / 'timing_events.json').relative_to(REPO)}")
    say("                    written by this run, one line per event, media time")
    say("                    paired with wall clock time on every one.")
    say(f"    the analysis    {(OUT_DIR / 'gate1.json').relative_to(REPO)}")
    say("    the numbers     docs/GATES.md, with the date and the take number.")
    say()
    say("    mkdir -p media/gate1   # this run does not touch your phone")
    say()

    if args.skip_timing:
        say("  (skipped: --skip-timing)")
        return {"ran": False, "skipped": True}
    if args.dry_run:
        say("  (dry run, not started)")
        return {"ran": False, "dry_run": True}

    if target == "stick":
        say("  Start recording on the phone NOW. The run starts in 10 seconds.")
        for remaining in range(10, 0, -1):
            print(f"    {remaining} ", end="\r", flush=True)
            time.sleep(1)
        print("    go   ")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "timing.json"
    seconds = args.timing_seconds or (clip_seconds + 15)
    command = [
        PY,
        str(REPO / "eval/vvd_timing_run.py"),
        "--mode", "timing",
        "--seconds", str(seconds),
        "--guard-band-ms", str(args.guard_band_ms),
        "--clip", facts["clip"],
        "--schedule", facts["schedule"],
        "--vpkg", facts["package"],
        "--out", str(out),
    ]
    say(f"  running for {seconds:.0f} s.")
    result = run(command, timeout=int(seconds) + 900)
    events = OUT_DIR / "timing_events.json"
    if result.returncode != 0 or not events.exists():
        say()
        say("  The run produced no events. Nothing to analyze, and nothing to line")
        say("  the recording up against. Keep the footage, note the take as void.")
        return {"ran": True, "ok": False, "out": str(out)}

    analysis = OUT_DIR / "gate1.json"
    run(
        [
            PY,
            str(REPO / "eval/gate1_rehearsal.py"),
            "--events", str(events),
            "--schedule", facts["schedule"],
            "--guard-band-ms", str(args.guard_band_ms),
            "--out", str(analysis),
        ],
        timeout=300,
    )
    if not analysis.exists():
        return {"ran": True, "ok": False, "out": str(out)}

    # eval/gate1_rehearsal.py belongs to another lane and its fields move as
    # they sharpen what the rehearsal is allowed to claim. Read it by asking
    # rather than by assuming, so a field they rename does not end a session
    # with a stack trace after the camera has already been packed away.
    result_data = json.loads(analysis.read_text())

    def field(*names, default="not reported"):
        for name in names:
            if name in result_data:
                return result_data[name]
        return default

    counted = field("markers_counted", "markers_reached_during_run")
    say()
    say("  What the app believed it did:")
    say(f"    markers in the schedule       {field('markers_in_schedule')}")
    say(f"    markers the run reached       {counted}")
    if field("markers_not_counted", default=0):
        say(f"    markers not counted          {field('markers_not_counted')}")
    say(f"    covered 150 ms or more early  {field('markers_covered_in_time')}")
    say(f"    worst lead                    {field('worst_lead_ms')} ms")
    interval = field("wilson_95_interval", default={}) or {}
    if interval.get("low") is not None:
        say(f"    Wilson 95% interval           {interval['low']} to {interval['high']}")
    say()
    if not counted:
        say("  Nothing was counted. The run reached no marker, so there is no number")
        say("  here and none should be quoted. Check the clip played at all before")
        say("  taking another take.")
    say("  This is not GATE 1 either way. It is what the app believed about media")
    say("  time. A cover the app scheduled correctly but the compositor drew late")
    say("  passes here and fails on camera. GATE 1 is the footage.")
    return {
        "ran": True,
        "ok": bool(counted),
        "analysis": str(analysis),
        "covered_in_time": field("markers_covered_in_time"),
        "counted": counted,
        "worst_lead_ms": field("worst_lead_ms"),
    }


# ------------------------------------------------------------------- main


def closing(target: str, session: dict) -> None:
    heading(7, "What is left, and what is not built", "read this before you pack up")

    say("  Done in this session:")
    for key in ("developer_mode", "os", "install", "layering", "timing"):
        entry = session.get(key)
        if entry:
            say(f"    {key}: {summarize(entry)}")
    say()
    say("  Still needs a person:")
    say("    - the three layering answers, from looking at the television")
    say("    - the 240 fps take, and a second take if the first one moved")
    say("    - the numbers written into docs/GATES.md")
    say()
    say("  Not built in this repository yet, so plan for it:")
    say("    - nothing here reads the 240 fps footage. The analysis that turns a")
    say("      recording into 'covered 150 ms early in 48 of 50' is still to be")
    say("      written, and it is what GATE 1 actually needs. What exists today is")
    say("      the app's own view of the same run, which is a rehearsal.")
    if target == "vvd":
        say("    - the virtual device cannot be filmed: the app draws on a GPU layer")
        say("      that screen grabs and QEMU's screendump both miss. This target is")
        say("      proven here for everything except what a camera sees.")
    say()
    say(f"  Session written to {(OUT_DIR / 'session.json').relative_to(REPO)}")


def summarize(entry: dict) -> str:
    if not isinstance(entry, dict):
        return str(entry)
    parts = [f"{key}={value}" for key, value in entry.items() if not isinstance(value, (dict, list))]
    return ", ".join(parts[:5])


def main() -> int:
    # This is a checklist someone reads while it runs, often through tee or a
    # log file. Python buffers a pipe in blocks, so without this the first
    # several minutes look like nothing is happening.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--target", choices=["auto", "stick", "vvd"], default="auto")
    parser.add_argument("--vpkg", type=Path, default=None)
    parser.add_argument("--schedule", type=Path, default=None)
    parser.add_argument("--clip", type=Path, default=None)
    parser.add_argument("--layering-seconds", type=float, default=600.0,
                        help="the layering test. Ten minutes by default, which is the test")
    parser.add_argument("--timing-seconds", type=float, default=None,
                        help="the marker run. Defaults to the clip length plus 15 s")
    parser.add_argument("--guard-band-ms", type=int, default=500)
    parser.add_argument("--wait-minutes", type=float, default=10.0,
                        help="how long to wait for a stick to appear after developer mode")
    parser.add_argument("--skip-layering", action="store_true")
    parser.add_argument("--skip-timing", action="store_true")
    parser.add_argument("--ignore-busy", action="store_true",
                        help="run even though another lane looks like it is using the device")
    parser.add_argument("--dry-run", action="store_true",
                        help="print every step and touch nothing")
    parser.add_argument("--device-info-file", type=Path, default=None,
                        help="use a saved 'vega device info' instead of asking the device")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    print()
    print("Calm Frames stick day")
    print(f"started {started.isoformat(timespec='seconds')}")
    print()
    print("The plan, and what it should cost:")
    print("  1. preflight                     1 min")
    print("  2. developer mode                5 min   remote in hand")
    print("  3. the OS build                 30 sec")
    print("  4. install                       2 min")
    print(f"  5. layering test                {args.layering_seconds / 60:.0f} min   watching the screen")
    print("  6. marker run, filmed            8 min   camera rolling, and listen")
    print("                                           for the chime, never yet heard")
    print("                                  -------")
    print("                                  ~27 min to GATE 1 footage")

    target = args.target
    if target == "auto":
        info = read_device_info(args) if (args.device_info_file or device_connected()) else {}
        target = "vvd" if info.get("simulated") else "stick"
        print()
        print(f"target: {target} (chosen from what is connected)")
    else:
        print()
        print(f"target: {target}")

    session: dict = {
        "started_utc": started.isoformat(timespec="seconds"),
        "target": target,
        "what_this_is": (
            "A stick day session. On the virtual device it proves every step that "
            "does not need eyes on a television."
        ),
    }

    if args.ignore_busy:
        print("note: --ignore-busy, so the device sharing check is skipped.")

    facts = preflight(args, target)
    session["preflight"] = facts

    session["developer_mode"] = developer_mode(target, args)
    session["os"] = check_os(read_device_info(args))
    session["install"] = install(target, facts, args)
    session["layering"] = layering(target, facts, args)
    session["timing"] = marker_run(target, facts, args)

    session["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    minutes = (datetime.now(timezone.utc) - started).total_seconds() / 60
    session["minutes"] = round(minutes, 1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "session.json").write_text(json.dumps(session, indent=2) + "\n")

    closing(target, session)
    print()
    print(f"Took {minutes:.1f} minutes.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        print("stopped by hand. Nothing was left half installed: rerun when ready.")
        raise SystemExit(130) from None
