#!/usr/bin/env bash
#
# One way to run gitleaks, used by `make scan`, by the pre-commit hook and by
# anyone who wants to check the tree by hand. CI runs the same version with the
# same config, so a clean run here means a clean run there.
#
#   scripts/gitleaks_scan.sh dir       scan the whole working tree
#   scripts/gitleaks_scan.sh staged    scan what is staged for commit
#
# The version is pinned to the one .github/workflows/ci.yml downloads. A
# different version can have different rules, and then a commit that passes
# here fails in CI, which teaches people to ignore the hook.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PINNED_VERSION="8.30.1"
MODE="${1:-dir}"

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
  dir)
    exec "$GITLEAKS" dir "$REPO" --config "$REPO/.gitleaks.toml" --no-banner --redact
    ;;
  staged)
    exec "$GITLEAKS" git "$REPO" --staged --config "$REPO/.gitleaks.toml" --no-banner --redact
    ;;
  *)
    echo "usage: $0 [dir|staged]" >&2
    exit 2
    ;;
esac
