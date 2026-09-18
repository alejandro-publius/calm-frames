#!/usr/bin/env bash
#
# One way to run gitleaks, used by `make scan`, by the pre-commit hook and by
# anyone who wants to check by hand. CI runs the same version with the same
# config, so a clean run here means a clean run there.
#
#   scripts/gitleaks_scan.sh committed   what a fresh clone holds. This is CI.
#   scripts/gitleaks_scan.sh staged      what is staged for commit. The hook.
#   scripts/gitleaks_scan.sh tree        the whole working directory as it is
#
# "committed" is the default because it is the one that answers the question
# people actually have, which is whether the repository leaks anything. A scan
# of the working directory also walks .venv, node_modules, app/build, coverage
# output and the media pool: about a gigabyte that no clone ever sees, several
# minutes, and findings in other people's vendored test fixtures that nobody
# can act on. "tree" is still there for when you want it.
#
# The version is pinned to the one .github/workflows/ci.yml downloads. A
# different version can have different rules, and then a commit that passes
# here fails in CI, which teaches people to ignore the hook.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PINNED_VERSION="8.30.1"
MODE="${1:-committed}"

find_gitleaks() {
  if [ -x "$REPO/.cache/gitleaks/gitleaks" ]; then
    echo "$REPO/.cache/gitleaks/gitleaks"
    return 0
  fi
  if command -v gitleaks >/dev/null 2>&1; then
    command -v gitleaks
    return 0
  fi
  return 1
}

GITLEAKS="$(find_gitleaks)" || {
  cat >&2 <<'MISSING'
gitleaks is not installed, so the secret scan cannot run.

This fails rather than passing quietly. A scan that silently skips is worse
than no scan, because everyone downstream believes it ran.

Install it:

  brew install gitleaks

or put a release binary at .cache/gitleaks/gitleaks in this checkout
(https://github.com/gitleaks/gitleaks/releases, version 8.30.1 is what CI uses).
MISSING
  exit 2
}

FOUND_VERSION="$("$GITLEAKS" version 2>/dev/null | tr -d '[:space:]')"
if [ "$FOUND_VERSION" != "$PINNED_VERSION" ]; then
  echo "note: gitleaks $FOUND_VERSION is installed, CI runs $PINNED_VERSION." >&2
  echo "      Results can differ between versions." >&2
fi

case "$MODE" in
  committed)
    # Scan exactly what a clone gets: the committed tree at HEAD, unpacked
    # somewhere clean. Same command CI runs, same content CI has.
    work="$(mktemp -d)"
    trap 'rm -rf "$work"' EXIT
    git -C "$REPO" archive HEAD | tar -x -C "$work" || exit 1
    echo "Scanning the committed tree at $(git -C "$REPO" rev-parse --short HEAD)."
    "$GITLEAKS" dir "$work" --config "$REPO/.gitleaks.toml" --no-banner --redact
    status=$?
    if [ "$status" -ne 0 ]; then
      echo "" >&2
      echo "Rerun with -v to see the findings:" >&2
      echo "  gitleaks dir $work --config $REPO/.gitleaks.toml --redact -v" >&2
      echo "(that directory is deleted when this exits, so copy the command first)" >&2
    fi
    exit "$status"
    ;;
  staged)
    exec "$GITLEAKS" git "$REPO" --staged --config "$REPO/.gitleaks.toml" --no-banner --redact
    ;;
  tree)
    echo "Scanning the whole working directory, including files no clone has."
    echo "This walks .venv, node_modules and the media pool. Expect minutes."
    exec "$GITLEAKS" dir "$REPO" --config "$REPO/.gitleaks.toml" --no-banner --redact -v
    ;;
  *)
    echo "usage: $0 [committed|staged|tree]" >&2
    exit 2
    ;;
esac
