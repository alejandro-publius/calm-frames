#!/usr/bin/env bash
#
# The gate in front of every command that would reach an AWS account.
#
# The rule for this project is synthesize only until HUMAN CHECKPOINT D is
# confirmed: the account on the Paid plan and the $20 budget alarm in place.
# (It also asked for the $150 credit request to be in. That form closed on
# Oct 7, 2026, and Alex waived the clause; docs/GATES.md has the entry.) Until
# then nothing may call AWS, and `make synth` is the thing that actually runs.
#
# Two locks, both of which have to be open:
#
#   1. docs/STATUS.md has a line saying the Paid plan is confirmed. That file is
#      the project's record of what is true, so the record has to say it before
#      the machine acts on it. The line to add, when it is true, at the start of
#      a line of its own, with no bullet, no table cell and no backticks around
#      it:
#
#      AWS Paid plan: confirmed
#
#      The match is anchored for a reason found on Sep 17, 2026: the row in
#      docs/STATUS.md that tells you to add the line contained the line, inside
#      backticks, and an unanchored grep read that as the plan being confirmed.
#      One of the two locks had been open since the day it was written. A test
#      would have caught it, and now there is one, in
#      pipeline/tests/test_aws_guard.py.
#
#   2. CHECKPOINT_D=confirmed is set on the command line, by a person, for that
#      one command:
#
#          make deploy CHECKPOINT_D=confirmed
#
# A variable alone cannot open it, and a document alone cannot open it. The
# committed docs/STATUS.md never says the line, on purpose, and a test keeps it
# that way. Both locks were opened once, on Oct 9, 2026, in a separate deploy
# worktree whose docs/STATUS.md carried the line and was never committed; that
# deploy is recorded in results/aws_deploy_2026-10-09.json.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTION="${1:-deploy}"

STATUS_FILE="$REPO/docs/STATUS.md"
# Anchored at the start of a line, so a document that talks about the line is
# not a document that says it.
STATUS_PATTERN='^AWS Paid plan:[[:space:]]*confirmed'

# The CLI has to be able to read what the pinned library writes. aws-cdk-lib
# 2.270.0 writes cloud assembly schema 54 and declares 2.1142.0 as the oldest
# CLI that reads it; the 2.1032.0 this line used to name stops right after
# synth with "Cloud assembly schema version mismatch". The Oct 9 deploy ran on
# 2.1142.0. pipeline/tests/test_aws_guard.py checks this pin against the
# library and against the other two places it is written.
CDK="${CDK:-npx --yes aws-cdk@2.1142.0}"
STACK="${STACK:-CalmFramesStack}"
CONTEXT="-c calmframes:budgetEmail=${BUDGET_EMAIL:-} -c calmframes:githubRepo=${GITHUB_REPO:-}"

# The map signing key the ingest task reads from SSM, if it has one. The stack
# only wires a key in when this context is passed, so a deploy without it takes
# the wiring out again: the task loses its read on the parameter and goes back
# to publishing nothing. On Oct 9 the key was added by putting the -c inside
# the CDK variable, which is easy to forget the next time. Now it is a variable
# of its own, and every deploy and diff says which way it is going.
SIGNING_KEY_PARAMETER="${SIGNING_KEY_PARAMETER:-}"
if [ -n "$SIGNING_KEY_PARAMETER" ]; then
  # SSM's own rule for a name: letters, digits, _ . - and / between levels.
  # Anything else is refused, because the value is split into words on the CDK
  # command line and ends up in an IAM resource ARN, where a * would let the
  # task read every parameter in the account.
  if ! [[ "$SIGNING_KEY_PARAMETER" =~ ^/?[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$ ]]; then
    echo "aws_guard: SIGNING_KEY_PARAMETER is not an SSM parameter name: '$SIGNING_KEY_PARAMETER'" >&2
    echo "  use letters, digits, _ . - and /, for example /calm-frames/cloud-signing-key" >&2
    exit 2
  fi
  CONTEXT="$CONTEXT -c calmframes:signingKeyParameter=$SIGNING_KEY_PARAMETER"
fi

say_which_key() {
  if [ -n "$SIGNING_KEY_PARAMETER" ]; then
    echo "Signing key: the task may read the SSM parameter $SIGNING_KEY_PARAMETER and signs maps with it."
  else
    echo "Signing key: none. SIGNING_KEY_PARAMETER is not set, so this template gives the task no key."
    echo "  A stack that has one loses it on this deploy and publishes nothing until it is put back."
    echo "  The Oct 9 stack has one: add SIGNING_KEY_PARAMETER=/calm-frames/cloud-signing-key to keep it."
  fi
}

status_says_confirmed() {
  [ -f "$STATUS_FILE" ] && grep -Eqi "$STATUS_PATTERN" "$STATUS_FILE"
}

variable_set() {
  [ "${CHECKPOINT_D:-}" = "confirmed" ]
}

if status_says_confirmed; then
  status_line="yes: $(grep -Eim1 "$STATUS_PATTERN" "$STATUS_FILE")"
  status_ok=1
else
  status_line="no. docs/STATUS.md has no line starting with 'AWS Paid plan: confirmed'"
  status_ok=0
fi

if variable_set; then
  variable_line="yes: CHECKPOINT_D=confirmed"
  variable_ok=1
else
  variable_line="no. CHECKPOINT_D is ${CHECKPOINT_D:-unset}"
  variable_ok=0
fi

if [ "$status_ok" = 1 ] && [ "$variable_ok" = 1 ]; then
  case "$ACTION" in
    deploy)  set -- deploy "$STACK" ;;
    destroy) set -- destroy "$STACK" --force ;;
    diff)    set -- diff "$STACK" ;;
    # Pushing the ingest image is an AWS call like any other, so it waits for
    # the same two locks. The script it runs checks them a second time, so
    # running that script directly is no way around this one.
    image)
      echo "HUMAN CHECKPOINT D is confirmed in docs/STATUS.md and on this command line."
      exec "$REPO/scripts/push_ingest_image.sh"
      ;;
    *) echo "aws_guard: unknown action '$ACTION'" >&2; exit 2 ;;
  esac
  echo "HUMAN CHECKPOINT D is confirmed in docs/STATUS.md and on this command line."
  case "$ACTION" in
    deploy|diff) say_which_key ;;
  esac
  echo "Running: $CDK $* $CONTEXT"
  # cdk.json runs the app as `python3 app.py`, and on a fresh clone the python3
  # on PATH is whatever the machine has, which here is 3.9 and has no
  # aws-cdk-lib in it. Put the project venv first when there is one, so the
  # template the CDK synthesizes during a deploy is built by the same
  # interpreter `make synth` uses. Without a venv this changes nothing.
  if [ -x "$REPO/.venv/bin/python3" ]; then
    PATH="$REPO/.venv/bin:$PATH"
    export PATH
  fi
  cd "$REPO/pipeline/infra" || exit 1
  # shellcheck disable=SC2086
  exec $CDK "$@" $CONTEXT
fi

cat >&2 <<REFUSED
make $ACTION is blocked.

No AWS deploy happens until HUMAN CHECKPOINT D is confirmed: the account on the
Paid plan and the \$20 budget alarm in place.

  docs/STATUS.md says the plan is confirmed?  $status_line
  CHECKPOINT_D=confirmed on this command?     $variable_line

What to do instead, today:

  make synth        write the CloudFormation template from the code. It needs
                    no credentials, calls nothing, and is what proves the stack
                    is ready. Output lands in pipeline/infra/cdk.out.
  make test-pipeline
                    the CDK unit tests, including zero NAT gateways and the
                    budget alarm.

When the account really is on the Paid plan:

  1. add the line "AWS Paid plan: confirmed" to docs/STATUS.md, at the start of
     a line of its own, with the date and who confirmed it after it. Not in a
     table cell and not inside backticks: the match is anchored, so a sentence
     about the line does not count as the line;
  2. run: make $ACTION CHECKPOINT_D=confirmed BUDGET_EMAIL=you@example.com GITHUB_REPO=owner/repo
     and, when the task should sign maps, SIGNING_KEY_PARAMETER=/name/of/the/parameter.

make destroy removes every stateful resource in the stack: each is set to
Delete (see pipeline/infra/calm_frames_stack.py). The few things that live
outside the stack are listed under "Taking it down" in pipeline/infra/README.md.
REFUSED
exit 1
