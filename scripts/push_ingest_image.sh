#!/usr/bin/env bash
#
# Build the ingest image and push it to the ECR repository the stack made.
#
# Building bills nobody, so `make image` does that on its own and is the thing
# to run today. This script is the half that touches an AWS account: it reads
# the stack's outputs, logs docker in to ECR and pushes. It therefore sits
# behind the same two locks as every other command that reaches AWS, and checks
# them itself rather than trusting the caller, so running it directly is no way
# around them:
#
#   1. docs/STATUS.md says "AWS Paid plan: confirmed"
#   2. CHECKPOINT_D=confirmed on this command
#
#   make image-push CHECKPOINT_D=confirmed
#
# It needs the AWS CLI and docker. On a machine that is not ARM64, set
# DOCKER_BUILD="docker buildx build --platform linux/arm64" so the image
# matches the Fargate task, which is ARM64 because it is about 20 percent
# cheaper per hour.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK="${STACK:-CalmFramesStack}"
STATUS_FILE="$REPO/docs/STATUS.md"
# Anchored at the start of a line, exactly as scripts/aws_guard.sh reads it, so
# a document that talks about the line is not a document that says it. This
# copy was left unanchored when the guard's was fixed on Sep 17, so a row of
# docs/STATUS.md that quotes the line opened this lock on its own until Oct 9.
STATUS_PATTERN='^AWS Paid plan:[[:space:]]*confirmed'
DOCKER_BUILD="${DOCKER_BUILD:-docker build}"
DOCKERFILE="pipeline/infra/ingest/Dockerfile"

if ! { [ -f "$STATUS_FILE" ] && grep -Eqi "$STATUS_PATTERN" "$STATUS_FILE"; } \
   || [ "${CHECKPOINT_D:-}" != "confirmed" ]; then
  cat >&2 <<'REFUSED'
Pushing an image is blocked, for the same reason a deploy is.

An ECR push is an AWS API call against a real account, so it waits for HUMAN
CHECKPOINT D like everything else: docs/STATUS.md saying "AWS Paid plan:
confirmed", and CHECKPOINT_D=confirmed on the command line.

  make image        build it locally and look inside it. No AWS, no account.
  make image-smoke  run it with no credentials and read what it refuses to do.
REFUSED
  exit 1
fi

command -v aws >/dev/null || { echo "the AWS CLI is not installed" >&2; exit 2; }
command -v docker >/dev/null || { echo "docker is not running" >&2; exit 2; }

echo "reading the ECR repository from the $STACK outputs"
REPOSITORY_URI="$(aws cloudformation describe-stacks \
  --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='IngestImageRepository'].OutputValue" \
  --output text)"

if [ -z "$REPOSITORY_URI" ] || [ "$REPOSITORY_URI" = "None" ]; then
  echo "the stack has no IngestImageRepository output. Deploy the stack first." >&2
  exit 1
fi

REGISTRY="${REPOSITORY_URI%%/*}"
REVISION="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo unknown)"

echo "building $REPOSITORY_URI:$REVISION"
cd "$REPO"
# shellcheck disable=SC2086
$DOCKER_BUILD -f "$DOCKERFILE" \
  -t "$REPOSITORY_URI:$REVISION" \
  -t "$REPOSITORY_URI:latest" \
  .

echo "logging docker in to $REGISTRY"
aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRY"

# Both tags: latest is what the task definition pulls, and the revision tag is
# what tells you months later which commit is running.
docker push "$REPOSITORY_URI:$REVISION"
docker push "$REPOSITORY_URI:latest"

echo
echo "pushed:"
docker image inspect "$REPOSITORY_URI:latest" \
  --format '  {{.Architecture}}/{{.Os}}  {{len .RootFS.Layers}} layers  {{.Size}} bytes'
echo "  tags: $REVISION and latest"
echo
echo "The task definition pulls :latest, so the next upload uses this image."
