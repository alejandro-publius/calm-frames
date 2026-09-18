#!/usr/bin/env bash
#
# The gate on the demo video file, before it is uploaded anywhere.
#
#   eval/check_video.sh path/to/final_video.mp4
#   eval/check_video.sh --selftest
#
# docs/BUILD_PROMPT.md 7.5 and the checklist at the end of docs/VIDEO_SCRIPT.md
# both say the same thing: flashmap check on the final video file returns zero
# violations, and the result is committed. This is that check, written down so
# it is one command on the day rather than a command somebody remembers.
#
# Two gates, both hard:
#
#   1. flashmap finds no segment over the WCAG general or red flash threshold.
#      Exit 1 from flashmap means it found some. Exit 2 means it could not tell,
#      and that is a failure here too: treating "could not tell" as a pass is
#      the hole this project keeps pointing at.
#   2. the file is under three minutes, because judges do not have to watch
#      past 3:00 and the script is written to 2:53.
#
# It writes what it found to results/video_check.json, so the claim "the video
# passes" is a file somebody can read rather than a sentence somebody wrote.
# Until this has been run on a real cut, that file does not exist and no
# document may carry a number from it.
#
# Exit codes: 0 every gate passed. 1 a gate failed. 2 the check could not run,
# which includes flashmap not being able to measure the file. Anything that is
# not 0 blocks the upload.
#
# SAFETY. This script never opens a video in a player. It decodes, measures and
# prints. The self test builds a strobe on purpose, so that clip is hazardous by
# design: it is written outside the repository with a HAZARD_ name and owner
# only permissions, it is measured, and it is deleted in a trap before this
# script returns. Nobody looks at it.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PROFILE="wcag"
OUT=""
MAX_SECONDS=180
SKIP_DURATION=0
SELFTEST=0
VIDEO=""

usage() {
  cat <<'USAGE'
Check the final demo video before it is uploaded.

  eval/check_video.sh VIDEO [options]
  eval/check_video.sh --selftest

Options:
  --out FILE          where to write the record. Default results/video_check.json
  --profile NAME      which flashmap profile to measure against. Default wcag
  --max-seconds N     length limit in seconds. Default 180, which is 3:00
  --skip-duration     do not check the length, and record that it was skipped
  --selftest          prove this script fails on a flashing file and passes on
                      a calm one. Builds both, measures both, deletes both
  -h, --help          this text

Exit codes: 0 passed, 1 a gate failed, 2 the check could not run.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --out) shift; OUT="${1:-}" ;;
    --profile) shift; PROFILE="${1:-wcag}" ;;
    --max-seconds) shift; MAX_SECONDS="${1:-180}" ;;
    --skip-duration) SKIP_DURATION=1 ;;
    --selftest) SELFTEST=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "check_video: unknown option $1" >&2; usage >&2; exit 2 ;;
    *)
      if [ -n "$VIDEO" ]; then
        echo "check_video: one video at a time, got $VIDEO and $1" >&2
        exit 2
      fi
      VIDEO="$1"
      ;;
  esac
  shift
done

# ------------------------------------------------------------------ tools

pick_python() {
  if [ -n "${PY:-}" ] && [ -x "${PY}" ]; then
    echo "$PY"
  elif [ -x "$REPO/.venv/bin/python" ]; then
    echo "$REPO/.venv/bin/python"
  else
    command -v python3 || true
  fi
}

PYTHON="$(pick_python)"
if [ -z "$PYTHON" ]; then
  echo "check_video: no python found. Try PY=/path/to/python" >&2
  exit 2
fi

# Run the command, do not just import the name. `import flashmap` succeeds from
# the repository root on any Python 3.3 or later even with nothing installed,
# because flashmap/ is a directory on sys.path and that is a namespace package.
# It has no code in it, so the import says yes and `python -m flashmap` then
# fails. This guard was written the weak way first and a mutation run caught it.
if ! "$PYTHON" -m flashmap --version >/dev/null 2>&1; then
  echo "check_video: $PYTHON cannot run flashmap." >&2
  echo "  python -m pip install -e '$REPO/flashmap[dev]'" >&2
  echo "  or point this at the project venv: PY=$REPO/.venv/bin/python" >&2
  exit 2
fi

sha256_of() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo ""
  fi
}

# ------------------------------------------------------------------ the check

check_one() {
  # check_one VIDEO OUT_JSON. Prints what it found and returns 0, 1 or 2.
  local video="$1"
  local out="$2"
  local status=0

  if [ ! -f "$video" ]; then
    echo "check_video: no such file: $video" >&2
    return 2
  fi

  echo "Calm Frames video check"
  echo "  file:    $video"
  echo "  profile: $PROFILE"
  echo

  # Gate 2 first, because it is cheap and a wrong-length cut is a re-edit
  # rather than a re-shoot.
  local duration="null"
  local duration_verdict="skipped"
  if [ "$SKIP_DURATION" -eq 1 ]; then
    echo "length:  not checked, --skip-duration was passed"
  elif ! command -v ffprobe >/dev/null 2>&1; then
    echo "check_video: ffprobe is not on PATH, so the length cannot be checked." >&2
    echo "  install ffmpeg, or pass --skip-duration and say so in the record." >&2
    return 2
  else
    duration="$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$video" 2>/dev/null | head -1)"
    case "$duration" in
      ''|N/A|n/a)
        echo "check_video: ffprobe could not read a duration from $video" >&2
        return 2
        ;;
    esac
    if awk -v d="$duration" -v m="$MAX_SECONDS" 'BEGIN { exit !(d > 0 && d <= m) }'; then
      duration_verdict="pass"
      printf 'length:  %.2f s, under the %s s limit\n' "$duration" "$MAX_SECONDS"
    else
      duration_verdict="fail"
      status=1
      printf 'length:  %.2f s, OVER the %s s limit\n' "$duration" "$MAX_SECONDS"
    fi
  fi
  echo

  local map="${out%.json}.map.json"
  mkdir -p "$(dirname "$out")"

  local flashmap_out flashmap_exit
  flashmap_out="$("$PYTHON" -m flashmap check "$video" --profile "$PROFILE" --json "$map" 2>&1)"
  flashmap_exit=$?
  echo "$flashmap_out"
  echo

  local flash_verdict
  case "$flashmap_exit" in
    0) flash_verdict="pass" ;;
    1) flash_verdict="fail"; [ "$status" -lt 1 ] && status=1 ;;
    *) flash_verdict="could not tell"; status=2 ;;
  esac

  local segments="null"
  if [ -f "$map" ]; then
    segments="$("$PYTHON" -c "
import json, sys
try:
    document = json.load(open(sys.argv[1]))
except Exception:
    print('null')
else:
    print(len(document.get('segments') or []))
" "$map")"
  fi

  local verdict="pass"
  [ "$status" -ne 0 ] && verdict="fail"

  "$PYTHON" - "$out" <<PY
import datetime, json, os, subprocess, sys

out = sys.argv[1]
record = {
    "recorded_utc": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat(),
    "what_this_is": (
        "The gate on the demo video file: flashmap over the finished cut, plus its "
        "length. Written by eval/check_video.sh. A pass here is about this file and "
        "nothing else."
    ),
    "video": os.path.basename("$video"),
    "video_sha256": "$(sha256_of "$video")",
    "video_bytes": os.path.getsize("$video") if os.path.exists("$video") else None,
    "profile": "$PROFILE",
    "flashmap_version": __import__("flashmap").__version__,
    "flashmap_exit": $flashmap_exit,
    "flashmap_verdict": "$flash_verdict",
    "segments_over_threshold": $segments,
    "duration_s": $duration,
    "duration_limit_s": $MAX_SECONDS,
    "duration_verdict": "$duration_verdict",
    "verdict": "$verdict",
    "map": (
        os.path.relpath("$map", "$REPO")
        if os.path.abspath("$map").startswith(os.path.abspath("$REPO") + os.sep)
        else "$map"
    ),
}
with open(out, "w", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2, sort_keys=True)
    handle.write("\n")
print(f"record written to {out}")
PY

  if [ "$status" -eq 0 ]; then
    echo
    echo "PASS. Commit $out and $map alongside the video link."
  else
    echo
    echo "BLOCKED. Do not upload this cut."
    if [ "$flash_verdict" = "fail" ]; then
      echo "  Read $map for where the flashing is, and re-edit. Do not play it back to find it."
    fi
  fi
  return "$status"
}

# ------------------------------------------------------------------ self test

selftest() {
  # A green check on a file nobody has measured proves nothing, so this feeds
  # the real thing a strobe and watches it go red, then a calm clip and watches
  # it go green.
  if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "check_video: the self test needs ffmpeg to build its two clips" >&2
    return 2
  fi

  local tmp_base scratch
  tmp_base="${TMPDIR:-/tmp}"
  tmp_base="${tmp_base%/}"
  scratch="$(mktemp -d "$tmp_base/calm-video-selftest.XXXXXX")" || return 2
  chmod 700 "$scratch"
  # A trap rather than a tidy-up at the end: the strobe must not survive a
  # crash, a failed assertion or a ctrl-c. The path is baked into the trap
  # rather than read from the variable, because the variable is local to this
  # function and the trap fires after it has gone.
  trap "rm -rf '$scratch'" EXIT INT TERM

  case "$(cd "$scratch" && pwd -P)" in
    "$REPO"|"$REPO"/*)
      echo "check_video: the scratch directory landed inside the repository, refusing" >&2
      return 2
      ;;
  esac

  local hazard="$scratch/HAZARD_selftest_strobe.mp4"
  local calm="$scratch/selftest_calm.mp4"

  echo "Building two clips under $scratch"
  echo "  $(basename "$hazard"): a full frame strobe, hazardous by design, deleted before this returns"
  echo "  $(basename "$calm"): a slow luminance ramp, nothing over the thresholds"
  echo

  # Three frames on, three frames off at 30 fps is five flashes a second over
  # the whole picture, which is over the general flash rule on both counts:
  # more than three flashes in a second, over a quarter of the field.
  ffmpeg -nostdin -loglevel error -y -f lavfi -i "color=c=black:s=256x144:r=30:d=4" \
    -vf "geq=lum='if(gt(mod(floor(N/3),2),0),235,16)':cb='128':cr='128'" \
    -c:v libx264 -preset ultrafast -pix_fmt yuv420p -an "$hazard" || return 2
  chmod 600 "$hazard"

  # Not a still frame. A still would pass a checker that had been broken to
  # fail anything that moves, so the calm clip breathes: one cycle every ten
  # seconds, which is nowhere near three flashes a second.
  ffmpeg -nostdin -loglevel error -y -f lavfi -i "color=c=gray:s=256x144:r=30:d=4" \
    -vf "geq=lum='110+24*sin(2*PI*N/300)':cb='128':cr='128'" \
    -c:v libx264 -preset ultrafast -pix_fmt yuv420p -an "$calm" || return 2

  local failures=0

  echo "--- 1 of 2: the strobe. This has to be blocked. ---"
  echo
  if check_one "$hazard" "$scratch/hazard_check.json"; then
    echo
    echo "SELF TEST FAILED: the strobe was passed. The check is not checking." >&2
    failures=$((failures + 1))
  else
    echo
    echo "as expected: the strobe was blocked"
  fi
  echo

  echo "--- 2 of 2: the calm clip. This has to pass. ---"
  echo
  if check_one "$calm" "$scratch/calm_check.json"; then
    echo
    echo "as expected: the calm clip passed"
  else
    echo
    echo "SELF TEST FAILED: a calm clip was blocked. The check fails everything." >&2
    failures=$((failures + 1))
  fi
  echo

  rm -f "$hazard"
  if [ -n "$(find "$scratch" -name 'HAZARD_*' -print -quit 2>/dev/null)" ]; then
    echo "SELF TEST FAILED: a HAZARD_ file outlived the job that made it." >&2
    failures=$((failures + 1))
  else
    echo "as expected: no HAZARD_ file survived"
  fi

  echo
  if [ "$failures" -eq 0 ]; then
    echo "SELF TEST PASSED: blocked the strobe, passed the calm clip, left nothing behind."
    return 0
  fi
  echo "SELF TEST FAILED: $failures problem(s) above." >&2
  return 1
}

# ------------------------------------------------------------------ run

if [ "$SELFTEST" -eq 1 ]; then
  if [ -n "$VIDEO" ]; then
    echo "check_video: --selftest takes no video, it builds its own" >&2
    exit 2
  fi
  selftest
  exit $?
fi

if [ -z "$VIDEO" ]; then
  usage >&2
  exit 2
fi

[ -n "$OUT" ] || OUT="$REPO/results/video_check.json"
check_one "$VIDEO" "$OUT"
exit $?
