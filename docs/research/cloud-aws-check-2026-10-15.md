# Cloud AWS checks, October 15, 2026

The offline AWS checks passed: **100 tests, zero failures and zero skips**;
the stack synthesized successfully and the image-context check passed.
Current billing, cost-tag activation, credits and deployed-image findings
remain **blocked**, not passed. This environment has no configured AWS access.

The tested checkout was `85dedefd85daea0bb8d774dd189dcf5af5490b83`, the
documentation reconciliation based on application candidate
`a3368a9e4dbfde52153d586d97d8c6da5ab5c8fd`. No infrastructure or ingest code
changed in this check. The machine-readable receipt, exact commands and
installed package versions are in
[`results/cloud-aws-check-2026-10-15.json`](../../results/cloud-aws-check-2026-10-15.json).

## Executed checks

Dependencies were installed into `/tmp/calm-aws-venv` using the repository's
infrastructure requirements and the Audit workflow's exact pytest, moto and
boto3 pins. Python was 3.12.14. Node was the supplied v24.19.0, rather than the
project's Node 22 major; the project pins were preserved.

| Check | Result | Meaning and limits |
|---|---|---|
| `test_infra.py` | 27 passed | Assertions against synthesized templates |
| `test_infra_ingest.py` | 31 passed | Publisher rules against moto with a controlled pipeline stub; Dockerfile and context assertions |
| `test_aws_guard.py` | 42 passed | Existing guard, pin, SBOM and sanitized receipt assertions; guarded commands use stubs |
| Offline `pipeline/infra/app.py` synthesis | Exit 0 | Default-context template: 41 resources, no NAT gateways or elastic IPs, one budget and one task definition |
| `python3 scripts/build_context.py --quiet` | Exit 0 | 59 files, 740,162 bytes (reported as 723 kB); zero files from media, results, app, .venv or docs |

The initial test run failed during collection and the initial synthesis failed
because jsii tried to create a cache under the unwritable home directory.
Setting its supported `JSII_RUNTIME_PACKAGE_CACHE_ROOT` to
`/tmp/calm-aws-jsii-cache` resolved both. These initial errors are retained in
the receipt. The successful tests took 27.10 seconds. AWS credential/config
files were pointed at `/dev/null` and instance metadata was disabled for
tests and synthesis. Synthesis used the dummy account and `us-east-1`.

The template hash is
`c3130c74ad8d7bcf1ad8b971488a730dfb1b0e0459a03c255b166fe8109f86f8`.
It uses default context, without the cloud signing parameter, budget email or
GitHub OIDC configuration; it is not a comparison with the live deployment.
The task image still ends in the mutable `:latest` tag.

Docker CLI and daemon 28.4.0 were present. No image was built, pushed or
scanned: this pass executed the requested image-context check and existing
static image tests. The context script is a repository implementation of
Docker's matcher. These checks cannot establish which digest ECS pulled,
whether a deployed image omitted the old CDK context cache, or whether image
vulnerabilities are fixed.

## Live-state blocker

There was no AWS CLI on PATH, no `AWS_` or `CDK_` environment variable,
`/workspace/.aws` was empty and the home `.aws` directory was absent. No
preexisting authorized AWS session was available. No AWS calls, credential
setup, permission changes or alternate-account attempts were made.

The historical October 9 receipt remains the available cloud evidence:
the `Project` cost-allocation tag was inactive; the filtered budget read
$0.00, which did **not** prove zero spend; the image scan reported **8 critical
and 56 high** findings. No later billing or scan observation is implied here.

## Bounded owner read-only checklist

Use an already authorized AWS Console session for the existing account.
If it is unavailable or any view denies access, record that exact blocker
and stop that item. This checklist does not ask for new credentials,
permission grants, paid resources or cost-setting changes. Record observation
times in UTC and redact account identifiers, ARNs, bucket names, domains,
repository URIs and personal data before adding evidence to the repository.

1. **Billing and credits.** In Billing, inspect the October 2026 bill to date,
   its latest update time, service charges, credits and net charges. Include
   the unfiltered account/service view because an inactive project tag can
   omit this stack's spend. Separate costs that can actually be attributed
   to Calm Frames from uncertain shared costs. Verify applied credits from
   the bill itself; an available credit balance is not proof of application.
   Use existing console views; do not enable a paid service or invoke a
   potentially charged Cost Explorer API as part of this pass.
2. **Allocation tag and budget.** Inspect the current status of the `Project`
   user-defined cost-allocation tag and any recorded activation time. Do not
   activate or backfill it. Inspect `calm-frames-monthly`: amount, filters,
   reported actual/forecast amounts, last update and alert configuration.
   Record separately whether historical untagged costs remain excluded. An
   active tag or a zero filtered budget alone does not establish total spend.
3. **Actual image identity.** In `us-east-1`, read the existing stack resources,
   starter Lambda's task-definition reference and the referenced ECS task
   definition. Check the container image reference and ARM64 runtime platform.
   For retained task executions, inspect each container's resolved
   `imageDigest` and correlate it with the task-definition revision and run
   time. Separately record the digest currently behind ECR `latest` and any
   source-commit tag. A tag today does not prove the digest used by the two
   October 9 tasks. If their task records are no longer retained, mark that
   historical digest unverified; do not start a new task or upload a clip.
4. **Findings for that digest.** Read existing ECR scan status, scan completion
   and vulnerability-source update timestamps, and severity counts for the
   identified digest, including all finding pages. If enhanced scanning is
   already enabled, inspect its existing Inspector findings for the same
   digest. Preserve package/version, finding identifier, fix availability and
   status needed to assess the historical 8 critical/56 high findings. Record
   missing, expired or incomplete scans as such. Do not initiate a scan,
   enable scanning, rebuild, push or deploy under this read-only checklist.
5. **Close only the observed claim.** Reconcile digest-specific findings with
   the historical receipt. New source pins or a clean local dependency audit
   do not fix the deployed image. Verifying removal of the historical bundled
   `cdk.context.json` needs inspection of that actual image's contents or a
   reviewed digest-linked build receipt. If unavailable, leave it unverified.

AWS has demonstrated **cloud video preparation**, not end-to-end TV delivery.
The TV plays its packaged library and does not trust the cloud demo signing
key. No native build/run was attempted, no Mac was accessed, and no screenshot
or recording was captured. Package 5 and its app-log observations remain
historical evidence; these tests establish nothing new about pixels, sound,
VoiceView, parent-settings interiors or caption-menu contents.
