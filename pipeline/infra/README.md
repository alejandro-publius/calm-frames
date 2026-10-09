# The AWS side, from a fresh clone

Everything in here is written from the code and has never been deployed. No AWS
API call has been made from this repository, by a person or by CI. `make deploy`
refuses, and goes on refusing until two locks are open at once:

1. `docs/STATUS.md` contains the line `AWS Paid plan: confirmed`
2. `CHECKPOINT_D=confirmed` is set on that one command

That is HUMAN CHECKPOINT D. Until then the thing to run is `make synth`, which
writes the CloudFormation template from the code, offline, with no credentials.

## What gets created

| Piece | Why |
|---|---|
| Two private S3 buckets | `source` takes uploads and is never public. `delivery` holds the kid safe renditions, maps, posters and trickplay |
| One CloudFront distribution | reads `delivery` through origin access control, so the bucket stays private. Optionally signed URLs |
| One DynamoDB table, on demand | the catalog, the same fields as the local `catalog.json` |
| One ECR repository | the ingest image |
| One ECS cluster and one ARM64 Fargate task definition | the ingest container. Nothing runs until an upload arrives |
| One Lambda | an upload under `uploads/` starts one task |
| A VPC with `natGateways: 0` | public subnets only. A NAT gateway per zone would cost more than everything else here put together |
| A GitHub OIDC role | so a deploy from CI needs no stored AWS key. Only created when `githubRepo` is set |
| A 20 US dollar monthly budget | with alarms at 50 and 80 percent of actual spend and at a forecast of 100 percent |

The monthly cost estimate, its assumptions and what it leaves out are in
`docs/DECISIONS.md` under "What this stack costs a month". It is an estimate
from published prices, not a bill.

## Before the first deploy

You need:

- an AWS account on the Paid plan, with the credit request in;
- the AWS CLI, signed in (`aws sts get-caller-identity` works);
- Node 22 (`.nvmrc`) and Python 3.12 (`.python-version`);
- docker, for the ingest image;
- `pip install -r pipeline/infra/requirements.txt` in the venv.

### One time: bootstrap the account and region

CDK needs a small set of resources in each account and region it deploys to: an
S3 bucket for assets, an ECR repository for image assets, and four IAM roles
that CloudFormation assumes. That is what bootstrapping makes.

```
export AWS_REGION=us-east-1
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=$AWS_REGION

npx --yes aws-cdk@2.1142.0 bootstrap aws://$CDK_DEFAULT_ACCOUNT/$AWS_REGION
```

Three things worth knowing about that command:

- **It costs almost nothing and it is not free.** The bootstrap bucket holds the
  templates and assets of each deploy, a few megabytes, and the bootstrap ECR
  repository holds the image if you deploy one. Pennies a month, and it is
  inside the 20 dollar budget because the budget filters on the cost allocation
  tag rather than on the stack.
- **It creates IAM roles named `cdk-<qualifier>-*-<account>-<region>`.** Those
  are the names the GitHub deploy role in this stack is allowed to assume, and
  nothing else. See `_github_deploy_role` in `calm_frames_stack.py`.
- **Bootstrap is not undone by `make destroy`.** Removing it is a separate step,
  at the end of this file.

If your account already has a CDK bootstrap from another project, you do not
need a second one. Check with:

```
aws cloudformation describe-stacks --stack-name CDKToolkit \
  --query "Stacks[0].Outputs[?OutputKey=='BootstrapVersion'].OutputValue" --output text
```

Version 21 or later is what aws-cdk-lib 2.270 expects.

### Optional, before the first deploy: CloudFront signed URLs

Without this the distribution serves the delivery bucket to anyone with the
URL. With it, only a URL signed by your private key plays.

**This key is not the map signing key.** CloudFront needs RSA 2048; flash maps
are signed with Ed25519. Two key pairs, two jobs, and neither one is ever in
the repository. Mixing them up would put an RSA key where the app expects an
Ed25519 one and every title would fail to verify.

```
openssl genrsa -out ~/.calm-frames/keys/cloudfront_2026-10.pem 2048
chmod 600 ~/.calm-frames/keys/cloudfront_2026-10.pem
openssl rsa -pubout -in ~/.calm-frames/keys/cloudfront_2026-10.pem \
  -out ~/.calm-frames/keys/cloudfront_2026-10.pub.pem
```

Pass the public half at deploy time with
`-c calmframes:signingPublicKey="$(cat ~/.calm-frames/keys/cloudfront_2026-10.pub.pem)"`
and the distribution gets a key group and a trusted key group on its default
behavior. The private half signs URLs wherever the player asks for one, and
never leaves the machine that holds it. docs/SECURITY.md covers what a leaked
signed URL does and does not give away.

### Optional: let the task sign maps

The ingest task signs nothing by default. An unsigned map is refused by every
player, which is the right default for a key this valuable: publishing nothing
beats putting a private key in the cloud.

If you do want titles built on AWS to be playable without a laptop in the loop,
put the Ed25519 private key in an SSM SecureString and name it at deploy time:

```
aws ssm put-parameter --name /calm-frames/signing-key --type SecureString \
  --value file://~/.calm-frames/keys/team_key.pem
```

then add `-c calmframes:signingKeyParameter=/calm-frames/signing-key`. The task
role can read that one parameter and decrypt it only through SSM. Read the "A
signing key in the cloud" part of docs/SECURITY.md before you do this: it makes
the key a hot key, and the judged release should not be signed by one.

## The deploy

```
make deploy CHECKPOINT_D=confirmed \
    BUDGET_EMAIL=you@example.com \
    GITHUB_REPO=alejandro-publius/calm-frames
```

That runs two steps, in this order, both behind the same locks:

1. `cdk deploy CalmFramesStack`, which asks you to approve the IAM changes. The
   prompt is deliberate. Read the diff: it is the only time anyone sees what
   permissions are being created.
2. `scripts/push_ingest_image.sh`, which builds the ingest image, logs docker in
   to the new ECR repository and pushes it as `latest` and as the short commit
   hash. The task definition pulls `latest`.

The order matters: the ECR repository does not exist until the stack does.
Nothing runs between the two steps, because the task only starts when an object
lands under `uploads/`.

On a machine that is not ARM64, build through buildx so the image matches the
task:

```
make deploy CHECKPOINT_D=confirmed \
    DOCKER_BUILD="docker buildx build --platform linux/arm64" ...
```

### Then try one title

```
aws s3 cp media/YOUR_TITLE.mp4 \
    s3://$(aws cloudformation describe-stacks --stack-name CalmFramesStack \
      --query "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue" \
      --output text)/uploads/YOUR_TITLE.mp4
```

The upload starts one task. Follow it in CloudWatch Logs under the
`IngestTaskLogs` group. When it finishes, the delivery bucket holds
`titles/<sha256>/...` and the catalog table holds one row.

If verify refused the title, the task publishes nothing at all and exits
non-zero, and the log says which check failed. That is the pipeline working, not
the pipeline broken.

## Taking it down

```
make destroy CHECKPOINT_D=confirmed
```

Every stateful resource in the stack has `RemovalPolicy.DESTROY` and the buckets
have `auto_delete_objects`, so nothing is left billing. A test asserts that
(`test_destroying_the_stack_leaves_nothing_behind`).

The CDK bootstrap is separate, and worth removing if this was the only stack in
the account:

```
aws s3 rm s3://cdk-<qualifier>-assets-<account>-<region> --recursive
aws cloudformation delete-stack --stack-name CDKToolkit
```

Check the bill a day later either way. A budget alarm is a warning, not a brake.

## What can be checked without an account

| Command | What it proves |
|---|---|
| `make synth` | the template builds from the code, with zero NAT gateways |
| `make test-pipeline` | the template's contents, and the container's rules, against moto |
| `make image` | the image builds for ARM64 |
| `make image-smoke` | the container refuses to start with nothing configured |
| `make image-context` | what the build would send to the docker daemon |
| `make deploy` | that it refuses, which is the point |

What none of them prove is in docs/SECURITY.md under "What has never been run".
