#!/usr/bin/env bash
#
# Watch the pre-commit hook fail on purpose, then watch it pass. Run:
#
#   make hooks-selftest
#
# A green hook proves nothing on its own. This plants secrets of the shape
# gitleaks looks for, tries to commit them, and fails if a commit succeeds.
#
# It all happens in a throwaway repository under the system temp directory, so
# it cannot stage, commit or reset anything in your checkout while another lane
# is working in it. The hook and the scan script under test are the real files
# from scripts/, copied in.
#
# Two things this caught the first time it ran, which is the point of it:
#
#   - gitleaks ignores the AWS key from Amazon's own documentation
#     (AKIA...EXAMPLE). Its default config has stopwords for well known example
#     values, so a self test built on one passes while the hook does nothing.
#   - the secrets have to be built at run time rather than written in this file.
#     A literal private key header here would make this script itself a finding
#     every time anyone scans the repository.

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

must_commit() {
  local label="$1"
  if git commit -qm "$label" >/dev/null 2>&1; then
    echo "   passed: a clean commit is not blocked"
  else
    echo "   FAILED: the hook blocked a commit with nothing in it" >&2
    git commit -m "$label" || true
    fail=1
  fi
}

must_not_commit() {
  local label="$1"
  local output
  if output="$(git commit -m "$label" 2>&1)"; then
    echo "   FAILED: the commit went through. The hook is not blocking." >&2
    echo "$output" | sed 's/^/     /' >&2
    git reset --hard HEAD~1 >/dev/null 2>&1 || true
    fail=1
  else
    echo "   passed: the commit was blocked"
  fi
}

echo "1. a file with no secret in it should commit"
echo "the cover hides the picture before the flash" > notes.txt
git add notes.txt
must_commit "plain text"

echo "2. a map signing private key must not commit"
# Built here rather than written above, so this script never holds the literal.
begin="-----BEGIN ""OPENSSH PRIVATE KEY-----"
end="-----END ""OPENSSH PRIVATE KEY-----"
body="$(head -c 200 /dev/urandom | base64 | tr -d '\n' | cut -c1-160)"
{ echo "$begin"; echo "$body"; echo "$end"; } > team_key.pem
git add team_key.pem
must_not_commit "planted private key"
git rm -q --cached team_key.pem >/dev/null 2>&1 || true
rm -f team_key.pem

echo "3. a credentials file must not commit"
akia="AKIA$(head -c 40 /dev/urandom | base64 | tr -dc 'A-Z0-9' | cut -c1-16)"
secret="$(head -c 60 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | cut -c1-40)"
{
  echo "aws_access_key_id = $akia"
  echo "aws_secret_access_key = $secret"
} > credentials.txt
git add credentials.txt
must_not_commit "planted credentials"

echo
if [ "$fail" -ne 0 ]; then
  echo "hook selftest FAILED. Do not trust the hook until this passes." >&2
  exit 1
fi
echo "hook selftest passed: clean commits go through, a planted key is stopped."
