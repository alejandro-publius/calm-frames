#!/usr/bin/env bash
#
# Install the git hooks for this checkout. Run: make hooks
#
# Hooks are not cloned with a repository, so every checkout installs its own.
# This points core.hooksPath at scripts/git-hooks, which means the hooks are
# version controlled and a change to them reaches everyone on their next
# install, rather than sitting in one person's .git directory.
#
# It refuses to install when gitleaks is missing. The hook fails closed, so
# installing it on a machine with no gitleaks would block every commit rather
# than scanning them, and the person would learn to pass --no-verify.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="scripts/git-hooks"

cd "$REPO" || exit 1

if ! command -v gitleaks >/dev/null 2>&1 && [ ! -x "$REPO/.cache/gitleaks/gitleaks" ]; then
  cat >&2 <<'MISSING'
Not installing the hooks: gitleaks is not on this machine.

The pre-commit hook fails closed. Installing it now would block every commit
instead of scanning it. Install gitleaks first:

  brew install gitleaks

then run: make hooks
MISSING
  exit 1
fi

chmod +x "$REPO/scripts/git-hooks/"* "$REPO/scripts/gitleaks_scan.sh"

current="$(git config --local core.hooksPath || true)"
git config --local core.hooksPath "$HOOKS_DIR"

echo "core.hooksPath is now $HOOKS_DIR (it was: ${current:-unset})."
echo "Installed:"
for hook in "$REPO/scripts/git-hooks/"*; do
  [ -f "$hook" ] || continue
  echo "  $(basename "$hook")"
done
echo
echo "A hook nobody has watched fail is not a hook. Prove this one blocks a"
echo "real secret, in a throwaway repository that cannot touch your work:"
echo "  make hooks-selftest"
echo
echo "The same scan runs in CI on every push. The hook only moves it earlier."
