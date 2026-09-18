#!/usr/bin/env bash
#
# The gate in front of every command that would reach an AWS account.
#
# The rule for this project is synthesize only until HUMAN CHECKPOINT D is
# confirmed: the account on the Paid plan, the $20 budget alarm in place, the
# credit request in. Until then nothing may call AWS, and `make synth` is the
# thing that actually runs.
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
# A variable alone cannot open it, and a document alone cannot open it. Neither
# lock has ever been opened in this repository.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACTION="${1:-deploy}"

STATUS_FILE="$REPO/docs/STATUS.md"
# Anchored at the start of a line, so a document that talks about the line is
# not a document that says it.
STATUS_PATTERN='^AWS Paid plan:[[:space:]]*confirmed'

CDK="${CDK:-npx --yes aws-cdk@2.1032.0}"
STACK="${STACK:-CalmFramesStack}"
CONTEXT="-c calmframes:budgetEmail=${BUDGET_EMAIL:-} -c calmframes:githubRepo=${GITHUB_REPO:-}"

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
  echo "Running: $CDK $* $CONTEXT"
  cd "$REPO/pipeline/infra" || exit 1
  # shellcheck disable=SC2086
  exec $CDK "$@" $CONTEXT
fi

cat >&2 <<REFUSED
make $ACTION is blocked.

No AWS deploy happens until HUMAN CHECKPOINT D is confirmed: the account on the
Paid plan, the \$20 budget alarm in place, the credit request in.

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

make destroy leaves nothing billable: every stateful resource in the stack is
set to Delete. See pipeline/infra/calm_frames_stack.py.
REFUSED
exit 1
