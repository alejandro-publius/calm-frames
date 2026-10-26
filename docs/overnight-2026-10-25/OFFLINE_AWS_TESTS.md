# Keep mocked ingest tests independent of host identity

The cloud runner intentionally selects an unavailable AWS profile to prevent
ambient account access. The ingest tests used global `boto3.client`, which tried
to load that profile before Moto could answer a request. The reproduced failure
was a test-setup dependency on host identity; production ingest behavior was not
changed.

The correction begins at `78b6de1808dbd43a1cc20dafecc91cc36013d086`. The
[receipt](../../results/overnight-2026-10-25/offline-aws/receipt.json) records the
checked test-file hash, tool versions and a small provider-fixture refinement.

## Isolation boundary

The fixture uses stateful Moto S3, DynamoDB and SSM backends with explicit dummy
credentials and a profile held only in memory. It also supplies that configuration
to Moto's lazy SDK region lookups. The actual `AWS_PROFILE`, identity files and
`boto3.DEFAULT_SESSION` remain unchanged. Moto's default environment and global
session patching are disabled.

Configuration-file loads and credential-provider fallback raise immediately.
Bearer-token providers are empty. An HTTP transport guard refuses any SDK request
that escapes Moto; DNS and socket guards provide a second boundary. Endpoint
overrides and proxy fallback are disabled only for these fixture clients. All
patches are scoped to the test context. The fixture compares the complete process
environment before and after, excluding only pytest's changing current-test
marker, without printing values on failure.

## Recorded checks and limits

The complete test file passes, including the existing publication allowlist,
refused-title, temporary signing-key, container and CDK-template assertions. The
new cases model an unavailable ambient profile without replacing the real guard,
exercise all mocked services, disable Moto to prove transport refusal, and probe
identity fallbacks.

Each negative control was observed failing: ordinary file-backed session config,
removed HTTP refusal, removed configuration-file refusals, and removed credential
provider refusal. The HTTP mutation stopped at the socket boundary. The file
mutation used a missing path in pytest's temporary directory; it did not consult
a real AWS config. Original source was restored after every mutation.

The [final log](../../results/overnight-2026-10-25/offline-aws/final.log) also
records unchanged process environment, AWS profile and global session after the
run. Ruff and the staged secret scan pass. These results are offline contracts,
not evidence of account access, deployed AWS behavior, hosted CI or native
playback. No AWS permissions, application code or dependency policy changed.
