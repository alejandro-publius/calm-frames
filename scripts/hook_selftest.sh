#!/usr/bin/env bash
#
# Watch the pre-commit hook fail on purpose, then watch it pass. Run:
#
#   make hooks-selftest
#
# A green hook proves nothing on its own. This plants a secret of the shape
# gitleaks looks for, tries to commit it, and fails if the commit succeeds.
#
# It all happens in a throwaway repository under the system temp directory, so
# it cannot stage, commit or reset anything in your checkout while another lane
# is working in it. The hook and the scan script under test are the real files
# from scripts/, copied in.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/scripts/git-hooks"
cp "$REPO/scripts/gitleaks_scan.sh" "$TMP/scripts/"
cp "$REPO/scripts/git-hooks/pre-commit" "$TMP/scripts/git-hooks/"
cp "$REPO/.gitleaks.toml" "$TMP/"
chmod +x "$TMP/scripts/gitleaks_scan.sh" "$TMP/scripts/git-hooks/pre-commit"

cd "$TMP" || exit 1
git init -q .
git config user.email "selftest@example.invalid"
git config user.name "hook selftest"
git config core.hooksPath scripts/git-hooks
git add -A >/dev/null
git commit -qm "scripts under test" --no-verify

fail=0

echo "1. a file with no secret in it should commit"
echo "the cover hides the picture before the flash" > notes.txt
git add notes.txt
if git commit -qm "plain text"; then
  echo "   passed: a clean commit is not blocked"
else
  echo "   FAILED: the hook blocked a commit with nothing in it" >&2
  fail=1
fi

echo "2. a file with an AWS key in it must not commit"
# Split so this line is not itself a finding when the scanner reads this file.
key="AKIA""IOSFODNN7EXAMPLE"
secret="wJalrXUtnFEMI""/K7MDENG/bPxRfiCYEXAMPLEKEY"
{
  echo "aws_access_key_id = $key"
  echo "aws_secret_access_key = $secret"
} > credentials.txt
git add credentials.txt
if git commit -qm "planted secret" >/dev/null 2>&1; then
  echo "   FAILED: the commit went through. The hook is not blocking." >&2
  fail=1
else
  echo "   passed: the commit was blocked"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "hook selftest FAILED. Do not trust the hook until this passes." >&2
  exit 1
fi
echo "hook selftest passed: clean commits go through, a planted key is stopped."
