# The AWS side, from a fresh clone

This stack has been deployed once. On Oct 9, 2026, after Alex confirmed HUMAN
CHECKPOINT D, `CalmFramesStack` went up in us-east-1 from a detached worktree at
commit c5724de. It was created at 00:21 PDT, updated at 00:33 to wire in the
cloud demo signing key, and has been `UPDATE_COMPLETE` since. A calm 12 second
marker clip went through it twice that night. Unsigned, it was analyzed and then
refused, which is the fail closed rule working on AWS. Signed, it was published
to the delivery bucket, the catalog table and CloudFront. The record of that
night, with every account identifier left out, is
`results/aws_deploy_2026-10-09.json`. docs/GATES.md and docs/SECURITY.md quote
it, and docs/DECISIONS.md has the choices made along the way.

`make deploy` still refuses unless two locks are open at once:

1. `docs/STATUS.md` contains the line `AWS Paid plan: confirmed`, at the start of
   a line of its own
2. `CHECKPOINT_D=confirmed` is set on that one command

That is HUMAN CHECKPOINT D. The committed `docs/STATUS.md` never has the line,
and `pipeline/tests/test_aws_guard.py` keeps it that way. On Oct 9 the line went
into the deploy worktree's own copy of the file, which was never committed. Do
the same next time. Without the locks, the thing to run is `make synth`, which
writes the CloudFormation template from the code, offline, with no credentials.

## What gets created

| Piece | Why |
|---|---|
| Two private S3 buckets | `source` takes uploads and is never public. `delivery` holds the kid safe renditions, maps, posters and trickplay |
| One CloudFront distribution | reads `delivery` through origin access control, so the bucket stays private. Optionally signed URLs; the Oct 9 stack has none |
| One DynamoDB table, on demand | the catalog, the same fields as the local `catalog.json` |
| One ECR repository | the ingest image |
| One ECS cluster and one ARM64 Fargate task definition | the ingest container. Nothing runs until an upload arrives |
| One Lambda | an upload under `uploads/` starts one task |
| A VPC with `natGateways: 0` | public subnets only. A NAT gateway per zone would cost more than everything else here put together |
| A GitHub OIDC role | so a deploy from CI needs no stored AWS key. Only created when `githubRepo` is set. The Oct 9 deploy left it empty, so this role does not exist |
| A 20 US dollar monthly budget | with alarms at 50 and 80 percent of actual spend and at a forecast of 100 percent. It counts only costs tagged `Project=calm-frames`, so the tag has to be activated first (below) |

The CDK adds two Lambda functions of its own, for the bucket notifications and
for emptying the buckets on delete, which is why the stack lists three.

The monthly cost estimate, its assumptions and what it leaves out are in
`docs/DECISIONS.md` under "What this stack costs a month". It is an estimate
from published prices, not a bill.

## Before the first deploy

You need:

- an AWS account on the Paid plan (the $150 credit request the checkpoint once
  asked for is void: the form closed on Oct 7, 2026, and docs/GATES.md has the
  waiver);
- the AWS CLI, signed in (`aws sts get-caller-identity` works);
- Node 22 (`.nvmrc`) on `PATH`, and the project venv for `python3` (see "The
  deploy");
- docker, for the ingest image;
- `pip install -r pipeline/infra/requirements.txt` in the venv.

### One time: the ECS service-linked role

In an account that has never used ECS, make its service-linked role before the
first deploy:

```
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com
```

A first cluster created by CloudFormation without that role is reported to fail,
and a failure rolls back the whole stack, the slow CloudFront distribution
included. On Oct 9 it was made at 00:15 PDT, before the bootstrap. It costs
nothing.

### One time: bootstrap the account and region

CDK needs a small set of resources in each account and region it deploys to: an
S3 bucket for assets, an ECR repository for image assets, and the IAM roles that
CloudFormation and the CLI assume. That is what bootstrapping makes.

```
cd ~        # any directory without a cdk.json in it
export AWS_REGION=us-east-1
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

npx --yes aws-cdk@2.1142.0 bootstrap aws://$CDK_DEFAULT_ACCOUNT/$AWS_REGION --tags Project=calm-frames
```

What each part of that is for, all learned on Oct 9:

- **Run it from a directory without a `cdk.json`.** Inside `pipeline/infra` the
  CLI picks up the app's `cdk.json`, and without an environment on the command
  line it runs the app to find one, which needs the venv, Node 22 and the
  stack's context. A neutral directory keeps bootstrapping to just that.
- **Export `AWS_REGION`.** The CLI resolves its own region and writes it over any
  `CDK_DEFAULT_REGION` you export. On the machine used on Oct 9 a fresh terminal
  resolved us-west-2, so without `AWS_REGION=us-east-1` the bootstrap and the
  stack would have gone there. Keep it exported for `make deploy` too.
- **`--tags Project=calm-frames`**, so the bootstrap bucket and repository carry
  the tag the budget counts. Without it they sit outside the budget.
- **The version it needs is 6 or later, and 8 for the lookup role.** The stack's
  template checks for 6, and the availability zone lookup the VPC does uses the
  lookup role that version 8 added. CLI 2.1142.0 bootstraps version 32, which is
  what us-east-1 has now.
- **Write the CLI version out in full.** In zsh an unquoted `$CDK` is not split
  into words, so `$CDK bootstrap` fails where the literal command works.

Three things worth knowing about what it makes:

- **It costs almost nothing and it is not free.** The bootstrap bucket holds the
  templates and assets of each deploy, a few megabytes. The bootstrap ECR
  repository stays empty here, because the ingest image goes to the stack's own
  repository. Pennies a month, inside the 20 dollar budget once the tag above is
  on it and activated.
- **It creates IAM roles named `cdk-<qualifier>-*-<account>-<region>`.** Those
  are the names the GitHub deploy role in this stack is allowed to assume, and
  nothing else. See `_github_deploy_role` in `calm_frames_stack.py`. The
  CloudFormation execution role it makes has AdministratorAccess by default,
  and the CLI says so when it runs.
- **Bootstrap is not undone by `make destroy`.** Removing it is a separate step,
  at the end of this file.

If your account already has a CDK bootstrap from another project, you do not
need a second one. Check its version with:

```
aws cloudformation describe-stacks --stack-name CDKToolkit \
  --query "Stacks[0].Outputs[?OutputKey=='BootstrapVersion'].OutputValue" --output text
```

### One time: let the budget see the costs

The budget filters on the cost allocation tag `Project`, and AWS ignores a user
tag for billing until it is activated. A new tag can take up to a day to show up
for activation after it is first put on a resource. Then, as the root user or a
user with billing access: Billing and Cost Management, Cost allocation tags,
User-defined, select `Project`, Activate. Until then the budget's alarms cannot
fire. At 02:50 PDT on Oct 9, Cost Explorer listed no `Project` tag at all, so
read the bill by hand until it is active.

### The CLI pin, and the schema pin under it

The CDK CLI is pinned to 2.1142.0 in three places: `scripts/aws_guard.sh`,
`pipeline/infra/Makefile` and the bootstrap command above. The CLI has to be able
to read the cloud assembly the pinned library writes. The manifest format, and
the oldest CLI that can read it, are declared by the `aws-cdk.cloud-assembly-schema`
package rather than by aws-cdk-lib, which only asks for a schema in the range
`>=54.11.0,<55.0.0`. The 2.1032.0 pinned here until Oct 9 stops right after synth
with "Cloud assembly schema version mismatch: Maximum schema version supported is
48.x.x, but found 54.0.0", so the deploy that night named the CLI on the command
line instead.

Until Oct 9 `requirements.txt` pinned aws-cdk-lib and constructs only, so the
schema floated. This checkout's venv had frozen 54.24.0, which declares 2.1142.0,
and the deploy ran with it. The hosted Audit run on dcb27a1 installed the range
fresh, took a newer 54.x declaring 2.1144.0, and failed the CLI pin test there
while `make ci` passed it here. `requirements.txt` now pins the schema at
54.24.0, and with it the two other requirements aws-cdk-lib declares as ranges:
jsii 1.140.0, the bridge every construct runs through, and the node proxy agent
asset 2.1.3, whose hash can reach the template. Each is the version the Oct 9
deploy ran with. `pipeline/tests/test_aws_guard.py` checks that the three CLI
places agree, that the CLI meets the minimum the installed schema declares, and
that each of the three pins is the version installed in the venv running the
tests, so a fresh install and `make ci` test one set of packages.

When aws-cdk-lib moves, move the schema, jsii and the proxy agent with it, then
the CLI if the new schema declares a newer minimum, then `make sbom`: the CDK
bill of materials lists every line of `requirements.txt` by line number, so it
changes whenever that file does.

### Optional, before the first deploy: CloudFront signed URLs

Without this the distribution serves the delivery bucket to anyone with the
URL. With it, only a URL signed by your private key plays. The Oct 9 stack was
deployed without it.

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
player, which is the right default: publishing nothing beats putting a private
key in the cloud.

To let titles built on AWS go all the way to a signed map, give the task a key
of its own, made for the cloud and for nothing else. Never the release key, and
never `team_key.pem`. This is what was done on Oct 9:

```
.venv/bin/python -m flashmap keygen --out ~/.calm-frames/keys/cloud_demo_2026-10
aws ssm put-parameter --name /calm-frames/cloud-signing-key --type SecureString \
  --value file://$HOME/.calm-frames/keys/cloud_demo_2026-10.pem \
  --tags Key=Project,Value=calm-frames
```

Then deploy with `SIGNING_KEY_PARAMETER=/calm-frames/cloud-signing-key`.
`scripts/aws_guard.sh` passes it to the CDK as
`-c calmframes:signingKeyParameter=/calm-frames/cloud-signing-key`. The task
role can then read that one parameter, and decrypt it only through SSM.

**Leave the variable off and the deploy takes the key away again.** The stack
only wires a key in when the context is passed, so a deploy without it removes
the task's read on the parameter and the task goes back to publishing nothing.
Every deploy and diff prints which way it is going, starting `Signing key:`.

The app does not trust this key, by design: its key id is none of the keys
compiled into the build, so a map it signs is refused on the TV. A title signed
in the cloud shows the pipeline running on AWS; it is not a title the TV plays.
Read "A signing key in the cloud" in docs/SECURITY.md before changing any of
that.

## The deploy

```
export AWS_REGION=us-east-1
export PATH="$HOME/.local/share/fnm/aliases/default/bin:$PATH"
make deploy CHECKPOINT_D=confirmed \
    BUDGET_EMAIL=you@example.com \
    SIGNING_KEY_PARAMETER=/calm-frames/cloud-signing-key
```

Run it from the repository root, in your own terminal. The `PATH` line puts
fnm's Node 22 first, because `scripts/aws_guard.sh` does not set up Node the way
`make synth` does. The guard puts the checkout's own `.venv` first for
`python3`; a checkout without one, like the detached worktree used on Oct 9,
needs the main checkout's `.venv/bin` on `PATH` as well. `GITHUB_REPO` is left
out on purpose: setting it creates the GitHub OIDC provider and deploy role, and
the Oct 9 deploy did without them (docs/DECISIONS.md).

That runs two steps, in this order, both behind the same locks:

1. `cdk deploy CalmFramesStack`, which stops to ask you to approve the IAM
   changes. The prompt is deliberate. Read the table: it is the only time anyone
   sees what permissions are being created. **It needs a terminal.** The CDK
   asks only when it has a TTY to ask on; run from a script or an agent's shell,
   it fails instead, because the stack includes security changes. On Oct 9 Alex
   ran both deploys in his own terminal and typed the `y` himself.
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
the pipeline broken. It is what the first upload on Oct 9 did, before the key
was wired in: the log ends "verify did not pass ... so nothing is published".

Never upload a `HAZARD_` file to try it. The calm marker clip
(`media/markers_packed.mp4`, made by `eval/marker_clip.py`) is what was used.

## Taking it down

The stack stays up until the results are announced, about Dec 3, 2026, so that
judges can check it (docs/DECISIONS.md). Then:

```
make destroy CHECKPOINT_D=confirmed
```

Every stateful resource in the stack has `RemovalPolicy.DESTROY` and the buckets
have `auto_delete_objects`, so nothing in the stack is left billing. A test
asserts that (`test_destroying_the_stack_leaves_nothing_behind`).

A few things live outside the stack and stay behind. Remove them by hand:

- **Two log groups under `/aws/lambda/`.** The CDK's own handlers for the bucket
  notifications and for emptying the buckets create them when they first run,
  outside the stack and with no retention set. List them with
  `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/CalmFramesStack-`
  and delete each with `aws logs delete-log-group --log-group-name <name>`.
- **The cloud demo key.** `make destroy` does not touch SSM:

  ```
  aws ssm delete-parameter --name /calm-frames/cloud-signing-key
  rm ~/.calm-frames/keys/cloud_demo_2026-10.pem ~/.calm-frames/keys/cloud_demo_2026-10.pub.pem
  ```

- **The CDK bootstrap, `CDKToolkit`**, worth removing if this was the only stack
  in the account:

  ```
  aws cloudformation delete-stack --stack-name CDKToolkit
  ```

  The bootstrap template keeps its asset bucket,
  `cdk-<qualifier>-assets-<account>-<region>`, when the stack is deleted, and
  the bucket is versioned. Empty it of every version (the S3 console's Empty
  does that) and then delete it.
- **The ECS service-linked role** costs nothing and can stay.

Check the bill a day later either way. A budget alarm is a warning, not a brake,
and this one only warns once the `Project` tag is active.

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
