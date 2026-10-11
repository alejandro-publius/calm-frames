# Security

What secrets this project has, where they live, and how to change them. This
repository goes public on Oct 21, so everything here is written to be read by
strangers.

## The short version

| Secret | Where it lives | In the repo? |
|---|---|---|
| Map signing private key | `~/.calm-frames/keys/team_key.pem`, on one machine, mode 600 | never |
| Map signing public key | `~/.calm-frames/keys/team_key.pub.pem`, and compiled into the app as `OFFLINE_PUBLIC_KEY_BASE64` | the public half only |
| Cloud demo signing key, made Oct 9, 2026 | an SSM SecureString in the AWS account, and `~/.calm-frames/keys/cloud_demo_2026-10.pem` on one machine, mode 600. The app does not trust it | never |
| AWS access | the operator's own AWS CLI credentials, in his terminal, for the one deploy so far. The stack's GitHub OIDC role was not created | never, there are no stored keys |
| PyPI upload | trusted publishing, an OIDC token minted per run | never, there is no API token |
| Parent area PIN | set on the device, stored only as a salted hash (`app/src/calmframes/parentGate.ts`) | never, there is no default |

There is no `.env` to copy and no secret to paste into CI. Two things can be
rotated or removed: the map signing key, and the cloud demo key, which is
deleted when the stack comes down (see "A signing key in the cloud").

## What this has to withstand

The threat model covers map integrity, prepared media, local settings and build
dependencies. Cryptographic verification authenticates a map and its binding;
it does not establish that the detector found every flashing interval.

| What an attacker wants | How they would try | What stops them |
|---|---|---|
| Make the player show flashing it should hide | change a flash map | the signature, the file binding and fail closed |
| Crash or take over the analyzer | hand it a hostile video | it runs on our machines and in one task with a narrow role |
| Turn the protection off | get past the parent PIN | a rate limited, salted, iterated hash, and settings that can only add hides |
| Take the video | leak a CloudFront signed URL | the URL reaches a kid safe rendition and nothing else |
| Get code into the build | a dependency, an action, an image | hashes, digests, a lock file, an audit with written exceptions, gitleaks |

### A tampered map

The map records the intervals the analyzer flagged. An attacker who could
change an accepted map could suppress covers. Signatures protect that record,
not the completeness of detection.

Every map is signed with Ed25519 over the canonical bytes of the document with
the signature block removed, and the app checks four things before it will show
a title in kid mode. Each one has a name, a message a parent can read, and a
test:

- **signed by a key we hold.** The map carries its own public key, which proves
  nothing on its own, so the check is against the key compiled into the app. A
  map signed by any other key is `unknown-key`.
- **the signature matches the bytes.** Editing one millisecond of one segment
  invalidates it. That is `bad-signature`.
- **bound to this file.** The map records the SHA-256 of the video it describes.
  A real map for a different title is `wrong-file`.
- **recent enough.** A map older than ninety days is `stale`, because the
  analyzer and the thresholds move.

Missing, unparseable and wrong-version join that list, and every one of them
ends the same way: the picture stays hidden and a card says the title is not
checked. These checks are designed to reject altered delivery records. They
do not guarantee security against every storage or decoder exploit; package
identity checks and the unresolved dependency findings remain relevant.

What this does not defend against: someone who can run code on the device, or
who holds the signing key. The key is why docs/SECURITY.md spends most of its
length on where the key lives.

### Hostile media

A video file is the largest piece of attacker controlled input this project
takes. The analyzer decodes every frame of it with PyAV, which is FFmpeg, and
FFmpeg has a long history of memory safety bugs reached through malformed input.
A file crafted to exploit one would be running inside our analyzer.

Where the analyzer runs decides what that is worth:

- **On a laptop**, over files a person downloaded on purpose and recorded in
  `media/LICENSES.csv` with a checked licence and a SHA-256. Those provenance checks do not prove a decoder input is non-malicious.
- **In the ingest task on AWS**, over whatever landed in the source bucket. That
  is the one place where a stranger's file could reach the decoder, so the task
  is the narrow one: no inbound access at all, a task role that can read one
  prefix of one bucket and write two paths, no long lived credentials, no shell,
  not root, and a container that exits when the title is done. An attacker who
  achieved code execution there would find a task that can read uploads and
  write renditions, in an account with a 20 dollar budget on it. On the stack
  deployed Oct 9 the task can also read the cloud demo signing key, which is why
  that key is one the app does not trust (see "A signing key in the cloud").
- **On the television**, never. The device plays a rendition; it does not
  analyze one. The one file the app parses itself is the map, and that parser is
  ours, refuses anything it does not recognise, and is fuzzed.

The other half of hostile media here is not an attacker at all, and matters
more: a file that is simply hazardous. docs/SAFETY.md covers that, the
`HAZARD_` prefix, and why the pipeline never uploads the original or the cover
model video to anywhere a player can reach.

### Getting past the PIN

The parent area holds the household settings, and the person most likely to
attack it is the child the settings protect. The PIN is four digits, stored as a
salted SHA-512 iterated a thousand times, with five attempts and then a minute's
lockout (`app/src/calmframes/parentGate.ts`).

Say plainly what that buys. A thousand rounds does not make four digits strong:
somebody who can read the device's storage can try all ten thousand in well under
an hour. The rate limit is what stops a child at the keypad, and a child at the
keypad is the threat this is for.

The second half of the design matters more than the PIN. Household settings can
only make the player stricter: a room setting can add hides, never remove one,
red segments always get an opaque cover, and verify models the dim cover before
it allows one. So the worst outcome of a PIN that gets guessed is a player that
hides more than it needed to.

### A leaked signed URL

With signed URLs turned on, a CloudFront URL is a bearer token: whoever holds it
before it expires can fetch that object. They leak in browser history, in logs,
in messages, in screenshots.

What a leaked one reaches is the point: the delivery bucket holds kid safe
renditions, maps, posters and trickplay, and nothing else. The source master
never goes there, and neither does `verify/cover_model_*.mp4`, which is the
original with covers drawn on it and so is exactly as hazardous as the original.
The ingest task's upload list is an allowlist of named paths for that reason,
and the test that proves it has been seen to fail.

So a leaked URL gives away a rendition that is safe to watch. Keep the expiry
short anyway, and note that the CloudFront signing key is RSA 2048 and is not the
Ed25519 key that signs maps. Two keys, two jobs. Mixing them up would be an
outage, not a breach, but it would be a confusing outage.

### The supply chain

The realistic way into a project like this one is not the front door. It is a
package.

- **Python, in the container.** Every package is installed with
  `--require-hashes` from `pipeline/infra/ingest/requirements.txt`, which was
  compiled for aarch64 with `uv pip compile --generate-hashes`. A package
  replaced upstream fails the build rather than shipping.
- **The base image** is pinned by digest, not by tag, so the bytes that were
  reviewed are the bytes that build.
- **Node.** `app/package-lock.json` and `npm ci`, with the Vega SDK and the
  sample pinned to one version each in CLAUDE.md.
- **Advisories.** `make audit-check` runs pip-audit and npm audit and fails on
  anything that has no written exception. See the next section.
- **Secrets.** gitleaks runs before every commit and on every push.
- **AWS.** No access key is stored in CI or in the repository, so there is none
  to steal from either. The stack defines a GitHub OIDC deploy role that can do
  one thing, assume the CDK bootstrap roles, but the Oct 9 deploy left
  `githubRepo` empty and did not create it, and no workflow deploys. A deploy is
  a person at a terminal, approving the IAM changes at the CDK prompt.
- **GitHub Actions.** Since Oct 11, `ci.yml` and `audit.yml` run with a read
  only token (`permissions: contents: read` at the top of each, because no job
  in them writes to the repository or pushes anywhere), and every action in
  them, in the published `flashmap/action.yml` and in the example people copy
  is pinned to a full commit with its release beside it as a comment, the form
  `publish-flashmap.yml` already used. A tag can be moved to new code by
  whoever holds the action's repository; a commit cannot.
  `scripts/check_pins.py` runs in the CI numbers job and fails on any tag or
  branch ref without a written exception, and on an exception that no longer
  matches anything; today there are none.

## The map signing key

Every flash map is signed with an Ed25519 key. The player checks the signature
before it will show a title in kid mode, and fails closed: a missing, stale,
unsigned, unparseable or wrong hash map keeps the picture hidden. That makes the
signing key the one piece of this system where a leak matters.

- The private key lives at `~/.calm-frames/keys/team_key.pem`, outside the
  repository, written with owner only permissions by `flashmap keygen`.
- It never enters the repository. `.gitignore` refuses `*.pem` and allows back
  only `*.pub.pem`, gitleaks runs in CI and as a pre commit hook, and the
  pipeline takes the key as a path argument so it is never pasted anywhere.
- The app ships only the public key. A player needs nothing secret to check a
  signature.
- Each map records which key signed it, as
  `signature.key_id`, which is `sha256:` plus the hex SHA-256 of the 32 raw
  public key bytes. See docs/SIDECAR_SPEC.md.

### Rotate the key and re-sign everything

Do this if the private key could have been seen by anyone, if the machine
holding it is lost or sold, when a person with access leaves, and once before
submission so the judged release is signed by a key that has never been
anywhere else.

Nothing here talks to a server. Rotation is local, and it is finished when
verify passes with the new key.

1. **Make the new pair.** Name it by date, so two keys are never confused.

       .venv/bin/python -m flashmap keygen --out ~/.calm-frames/keys/team_key_2026-10-21

   That writes `team_key_2026-10-21.pem` (private, mode 600) and
   `team_key_2026-10-21.pub.pem`.

2. **Write down the new key id**, so you can tell a re-signed map from an old one:

       .venv/bin/python - <<'PY'
       from flashmap.signing import load_public_key, key_id
       from pathlib import Path
       print(key_id(load_public_key(Path.home() / ".calm-frames/keys/team_key_2026-10-21.pub.pem")))
       PY

3. **Keep the old public key** until everything is re-signed. It is what tells
   you whether a map you are looking at is old or new. Do not keep the old
   private key: move it out of `~/.calm-frames/keys/` and delete it.

4. **Re-sign every title, with `--force`.**

       .venv/bin/python -m pipeline.ingest media/TITLE.mp4 \
           --workdir ~/calm-frames-work \
           --key ~/.calm-frames/keys/team_key_2026-10-21.pem \
           --pub ~/.calm-frames/keys/team_key_2026-10-21.pub.pem \
           --force

   **`--force` is not optional here.** The pipeline skips work it has already
   done, and the fingerprint for the analyze step records only whether a key was
   used, not which key (`pipeline/ingest.py`, the `analyze:<preset>` step, which
   hashes `"signed": bool(options.key)`). Without `--force` the analysis is
   skipped, the map keeps its old signature, and everything downstream looks
   fine until a player with the new public key refuses the title.

5. **Check that it took.** The key id in each map must be the new one:

       .venv/bin/python -m flashmap verify \
           ~/calm-frames-work/titles/<hash>/maps/wcag.json \
           media/TITLE.mp4 \
           --pub ~/.calm-frames/keys/team_key_2026-10-21.pub.pem

   Then run the pipeline's own gate, which is what blocks publishing. It takes
   the source hash of the title, which is the directory name under `titles/`:

       .venv/bin/python -m pipeline.verify \
           --workdir ~/calm-frames-work \
           --sha <the title's source SHA-256> \
           --pub ~/.calm-frames/keys/team_key_2026-10-21.pub.pem

6. **Ship the new public key with the app.** The app carries the public key so
   a device can check a map with no network at all. As of Sep 17, 2026 it is
   one constant:

       app/src/calmframes/offlineTitle.ts   OFFLINE_PUBLIC_KEY_BASE64

   base64 of the 32 raw Ed25519 bytes, the same form `key_id` is computed from.
   `app/src/screens/PlayerScreen.tsx` passes it to the map check, and
   `flashMap.ts` refuses a map whose key does not equal it.

   So a key rotation is a new app build as well as new maps, and the bundled
   offline title (`assets/raw/offline/calm_gradient.flashmap.json`, signed with
   the demo key) has to be re-signed with the new key in the same change, or
   the one title that works with the backend down stops working. That file
   belongs to the app lane. Tell them before rotating, not after.

7. **Prove the old key no longer works.** Take one re-signed map and check it
   against the old public key. It must fail. A rotation nobody has watched fail
   the old way is a rotation that might not have happened.

8. **Record it** in docs/DECISIONS.md: the date, the new key id, why it was
   rotated, and which titles were re-signed.

### If the private key leaks

Assume every map signed with it is untrusted, including any a stranger could
have made. Rotate as above, re-sign everything, and ship a build carrying only
the new public key. The player's fail closed rule is what buys the time: a map
signed by a key the app does not hold keeps the picture hidden rather than
showing an unverified title.

### Revoking a key, and the test that proves it

There is no revocation list, and there should not be one. A player has to decide
with no network at all, and a list it cannot fetch is a list it cannot trust. So
revocation here is the simplest thing that fails closed: the app holds exactly
one public key, and a map signed by anything else is refused. Retiring a key is
rebuilding the app with a new one.

That has a consequence worth saying out loud before it surprises somebody. The
moment a build with the new key reaches a device, every title still signed with
the old key disappears from kid mode, because an unknown key keeps the picture
hidden. The order to do it in is: re-sign every title first, check them, then
ship the build. During the window in between, a device still on the old build
refuses the re-signed titles. Both directions fail the same safe way, which is
the point, and neither is invisible.

What the app does with a revoked key is tested in
`app/test/calmframes/revokedKey.test.ts`. The fixture is a map that is entirely
valid: correctly signed, over the right bytes, by a real key. The first
assertion is that it verifies against the key that signed it, because a map that
was already broken would be refused for the wrong reason and prove nothing. Then
the same map is refused four ways once the app carries a different key, the
reason is `unknown-key` and not `bad-signature`, and the wording a parent reads
says somebody we do not know rather than somebody changed this.

Both fixture keys come from `scripts/make_revoked_key_fixture.py`, which derives
them from phrases written in the script, so there is no private key in the
repository and anybody can rebuild them.

Seen to fail, three ways:

- the app verifies with the public key printed inside the map, which is the
  classic version of this bug. The revoked map is then accepted, `ok` comes back
  true, and four of the six tests go red;
- the key comparison is dropped entirely. The map is still refused, but as
  `bad-signature`, which would tell a parent that someone edited it;
- the wording for `unknown-key` is changed to the wording for a tampered map.

### A signing key in the cloud

The ingest task on AWS signs nothing unless it is handed a key, and an unsigned
map is refused by every player. On Oct 9, 2026 the stack was given one, so that
a title could go all the way from an upload to a signed map, a catalog row and
CloudFront. This is the key it was given and the rules it lives under. The
record of that night is `results/aws_deploy_2026-10-09.json`.

- **It is a throwaway cloud demo key, not the release key.** A separate Ed25519
  pair made that night with `flashmap keygen`, kept as
  `~/.calm-frames/keys/cloud_demo_2026-10.pem` (mode 600) and nowhere in the
  repository. Its key id starts
  <!--n results/aws_deploy_2026-10-09.json:signing_key.key_id_short -->9fa44e490266<!--/n-->.
- **It lives in SSM Parameter Store** as the SecureString
  `/calm-frames/cloud-signing-key`, encrypted with the account's own `aws/ssm`
  KMS key. No customer managed KMS key was made for it.
- **Only the ingest task can read it, and only that.** The task role may call
  `ssm:GetParameter` on that one parameter and `kms:Decrypt` only when the call
  arrives through SSM in us-east-1. Nothing else in the stack has either
  permission. Anyone who administers the account can still read it, which is
  one more reason it is not a key anything trusts.
- **The app does not trust it.** The app accepts a map only when the key that
  signed it is one compiled into the build. The key it checks general maps
  against, `OFFLINE_PUBLIC_KEY_BASE64`, has an id starting
  <!--n results/aws_deploy_2026-10-09.json:signing_key.app_trusted_key_id_short -->9d32df3b18c9<!--/n-->,
  and the Harbor demo key and both prepared library keys differ too. So a map
  the cloud signs is refused on the television as an unknown key and the
  picture stays hidden. The maps the cloud made are evidence that the pipeline
  runs on AWS. They are not titles the TV plays.
- **The judged release is never signed by it.** The release is signed on one
  machine with a key that has never been anywhere else, as "Rotate the key and
  re-sign everything" says. Never compile the cloud key's public half into the
  app: that would turn a key a running task can read into one the TV believes.
- **It goes when the stack goes.** `make destroy` does not touch SSM, so the
  teardown in `pipeline/infra/README.md` deletes the parameter and the local
  copy by hand.

If it leaks, nothing the TV shows changes, because the TV never trusted it.
Delete the parameter, and make a new cloud key only if the cloud demo has to run
again.

## Secret scanning

gitleaks runs in three places, all with the same version and the same
`.gitleaks.toml`:

| Where | Command |
|---|---|
| Before a commit | the hook installed by `make hooks` |
| Before a commit, if you use the pre-commit framework | `.pre-commit-config.yaml` |
| On every push | `.github/workflows/ci.yml`, the `secrets` job |

    make hooks            install the hook into this checkout
    make hooks-selftest   watch it block a planted key, in a throwaway repo
    make scan             scan the whole working tree now

The hook fails closed. If gitleaks is not installed, `make hooks` refuses to
install rather than leaving a hook that blocks every commit. The version is
pinned to 8.30.1, the same one CI downloads, because rules move between versions
and a hook that disagrees with CI teaches people to pass `--no-verify`.

`.gitleaks.toml` needs gitleaks 8.19 or later, which is what the pin gives you.

It holds three allowlists and should not grow a fourth without an argument. The
first covers directories of generated or third party files that are never
committed: the Shaka Player checkout, installed packages, build output, the CDK
template. The other two name one value and one line shape, both checked by hand
on Sep 17, 2026 and both false positives on the word "key": the offline demo's
Ed25519 public key, which the app carries on purpose, and `pool_key_sha256` in
`results/realclips_status.json`, which is a digest of the labeling pool's
blinding key file rather than a key.

Nothing under our own source, docs, results or infrastructure is allowlisted by
directory. Keep it that way: an allowlist that grows to silence a real finding is
how a key ships. When a new false positive turns up, name the value or the line,
prove a real secret of the same shape is still caught, and write down what you
checked.

On a finding, whether from the hook or from CI:

1. take it out of the change;
2. rotate it, whatever it is. A secret that reached a commit is burned even if
   the commit never leaves the machine;
3. if the commit was pushed, rotate first and rewrite history second. Rewriting
   history does not un-leak anything.

## Dependencies, and every exception in writing

    make audit          run both audits and write results/audit.json
    make audit-check    the same, and fail on anything without an exception
    make sbom           write the bills of materials
    make sbom-check     fail if a committed bill no longer matches what is installed

The rule is not "no findings". A project pinned to somebody else's SDK will have
findings by Friday, and a rule that cannot be kept gets switched off. The rule is
that every finding is either fixed or written down, in
`scripts/audit_exceptions.toml`, with the packages it covers, the advisory ids
that were read, who accepted it, why, and the date it has to be looked at again.

Oct 11: the audit passes again, and two findings were fixed rather than
excused. `xmldom` 0.6.0, which the generated Shaka `DOMParserPolyfill` imports
and which carried sixteen advisories into the shipped bundle, is now an npm
alias of the maintained fork `@xmldom/xmldom` 0.8.15: the polyfill only
subclasses its `DOMParser`, the 0.8 line keeps the 0.6 parsing behaviour on
malformed input (a partial document rather than an exception), and `npm audit`
reports nothing against it. The app's own `lodash` moved from 4.17.23 to
4.18.1, which clears the `_.omit` and `_.unset` findings from the copy the
bundle carries; the two copies still reported are exact pins inside Node build
tools. Every other finding was re-read and sorted by one mechanical test,
whether the package is in the Metro bundle for the device. A Release and a
Debug bundle were built here for the kepler platform with the SDK's own Metro
configuration and their source maps read; the inventory is
[`results/bundle_packages_2026-10-11.json`](../results/bundle_packages_2026-10-11.json):
<!--n results/bundle_packages_2026-10-11.json:published.flagged_in_release_bundle -->20<!--/n-->
flagged packages are in the Release bundle, react-devtools-core joins them in
Debug, and
<!--n results/bundle_packages_2026-10-11.json:published.flagged_in_neither_bundle -->98<!--/n-->
are in neither. That is a Linux build with the compiled Shaka file stubbed,
which cannot change which npm packages are bundled; it is not a Vega build
or a device run, and the Mac's release build should confirm the same list
once. Both dependency changes still need the Mac's Vega build and a run on
the virtual device, as does everything else that changed app inputs since
Oct 10. The Python scan covers the ingest and CDK requirements; it does not
include a venv freeze.

Historical repair, Sep 29:

**The Sep 29 dependency repair passes the fresh audit gate with unchanged written exceptions.** The earlier
run found a new, unaccounted `image-size@0.6.3` advisory, npm source `1239766`,
[GHSA-w3rx-r6r6-pgpr / CVE-2025-71330](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr).
Malformed ICNS data can hang the legacy build-tool asset parser. The upstream
fix is `2.0.3`, but that API no longer provides the callable CommonJS module
and synchronous filename input expected by the SDK's older Metro dependency.
The SDK's Metro 0.54.1 now resolves a private local API adapter that delegates
every parse to the exact official `image-size@2.0.4`. It restores the callable
Buffer, synchronous filename and callback interfaces without copying parsers.
Reads remain bounded and descriptors close on success or failure. The adapter
keeps its own name; the official parser retains its registry identity and
integrity in the lockfile and SBOM. No advisory suppression, downgrade or new
exception was added. Compatibility and terminating-error regressions pass,
including actual Metro PNG, JPEG and SVG asset handling.

The image-size repair remains in place. It does not resolve the new findings
below. GitHub runners now work; latest CI passed and Audit failed three jobs
on dcb27a1. Only simulator validation is required for this submission.

| | |
|---|---|
| Python packages with an advisory in the scanned ingest and CDK requirements | <!--n results/audit.json:published.python_packages_with_advisories -->0<!--/n--> |
| npm packages with an advisory in app/ | <!--n results/audit.json:published.npm_packages_with_advisories -->119<!--/n--> |
| npm advisories behind them | <!--n results/audit.json:published.npm_advisories_total -->33<!--/n--> |
| of which critical | <!--n results/audit.json:published.npm_critical -->6<!--/n--> |
| of which high | <!--n results/audit.json:published.npm_high -->83<!--/n--> |
| exception groups, each with its reasons | <!--n results/audit.json:published.exception_groups -->2<!--/n--> |

The two groups, in short. The full reasoning is in the TOML file, in
paragraphs, because a one line reason is how an exception becomes permanent.

1. **What ships: the Vega SDK runtime and React Native.** The project pins SDK
   0.24.9914 and the sample at `v0.24-RN83` because that is what the device
   runs, and no newer react-native is supported by Vega 0.24. None of the
   Amazon packages carries an advisory of its own; npm lists them for what
   they depend on, and each chain was read: a code generation tool behind the
   TurboModule API, build and test tools behind react-native-kepler, the deep
   link parser behind react-navigation (the app configures no deep links), and
   the DevTools backend that only a Debug build carries. The only outside
   input the app parses itself is the map, through our own reader.
2. **What does not ship: build and test tooling.** jest, babel, Metro, the
   community CLI, the Vega CLI platform, API Extractor and the utilities under
   them. Four advisories published in October 2026 (braces, sprintf-js,
   shell-quote, handlebars) sit under tools everything else depends on, which
   is why npm lists
   <!--n results/audit.json:published.npm_packages_with_advisories -->119<!--/n-->
   packages for
   <!--n results/audit.json:published.npm_advisories_total -->33<!--/n-->
   advisories. They run on a developer's machine or a CI runner, over this
   repository's own files. This is the build machine's risk, not the
   television's.

The group that held `xmldom` and `lodash` is gone, because both were fixed:
the October 10 review had found that the generated
`app/src/w3cmedia/polyfills/DOMParserPolyfill.ts` imports `xmldom`, so a
replacement had to keep that import working, and an npm alias does. Both
remaining groups are due for review on Oct 21, the day of the final checks, so
the release build is made with the words re-read. That review should move the
dates past judging (Dec 3) once it is done, or the Monday audit after the tag
will go red for a reason that has nothing to do with a new advisory.

Scanner execution and report validation also fail closed: empty output, error
JSON, unexpected exit statuses, incomplete records and skipped dependencies
cannot be accepted as a clean scan. The October 10 cloud receipt records the
regression tests and compatibility checks against real scanner responses in
`results/cloud_continuation_2026-10-10.json`.

The original exception-policy checks fail four ways, each one broken on purpose and watched: a package
with no exception, a new advisory against a package that has one, an exception
past its review date, and an exception with nobody's name on it.

### The bills of materials

Three CycloneDX 1.6 documents, written by the CycloneDX project's own tools and
regenerated reproducibly so CI can diff them:

| File | What it covers | Components |
|---|---|---|
| `docs/SBOM.ingest.cdx.json` | the Python packages in the ingest container | <!--n results/sbom.json:published.ingest_components -->12<!--/n--> |
| `docs/SBOM.app.cdx.json` | what the Vega app is built from | <!--n results/sbom.json:published.app_components -->1110<!--/n--> |
| `docs/SBOM.cdk.cdx.json` | what synthesizes and deploys the stack | <!--n results/sbom.json:published.cdk_components -->5<!--/n--> |

What they do not cover: the Debian packages apt installs inside the image.
ffmpeg pulls in a long list of libraries, and listing them properly means
reading the built image with a scanner. No bill of materials has been made
that way. ECR's basic scan did read the image pushed on Oct 9, 2026, and what
it found is under AWS below. What makes the
set knowable at all is that the base image is pinned by digest,
<!--n results/sbom.json:published.base_image_digest -->sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2<!--/n-->,
so the same command gives the same packages until somebody changes that line.

## AWS

No AWS credentials are stored in this repository or in CI. The one deploy so far
ran from a person's terminal, with that person's own CLI credentials.

**Deployed once, on Oct 9, 2026.** Alex confirmed HUMAN CHECKPOINT D that night
(docs/GATES.md). From a detached worktree at commit c5724de he ran `make deploy`
in his own terminal at 00:21 PDT and approved the IAM changes at the CDK prompt
himself:
<!--n results/aws_deploy_2026-10-09.json:iam_approval.statement_rows -->20<!--/n--> statement rows,
<!--n results/aws_deploy_2026-10-09.json:iam_approval.managed_policy_rows -->3<!--/n--> managed policy attachments and
<!--n results/aws_deploy_2026-10-09.json:iam_approval.security_group_rows -->1<!--/n--> security group rule.
CalmFramesStack in us-east-1 was created by 00:25 and updated at 00:33 to wire
in the cloud demo signing key, and stands at
<!--n results/aws_deploy_2026-10-09.json:stack_status -->UPDATE_COMPLETE<!--/n--> with
<!--n results/aws_deploy_2026-10-09.json:stack.resources_total -->42<!--/n--> resources and
<!--n results/aws_deploy_2026-10-09.json:stack.nat_gateways -->0<!--/n--> NAT gateways.
`results/aws_deploy_2026-10-09.json` is the record, with every account id,
bucket name, domain, ARN and repository URI left out, and
`pipeline/tests/test_aws_guard.py` fails if one of those shapes appears in it,
in this file or in `pipeline/infra/README.md`.

What that deploy did not make, on purpose:

- **No GitHub OIDC provider and no deploy role.** `githubRepo` was left empty,
  so the role in `pipeline/infra/calm_frames_stack.py` was not created and no
  workflow can reach the account. That is recorded rather than fixed with a
  redeploy (docs/DECISIONS.md, Oct 9).
- **No CloudFront signed URLs.** No signing public key was passed, so the
  distribution serves the delivery bucket to anyone who has a title's path.
  What that bucket holds is the kid safe rendition, the map, the plan, posters
  and trickplay, never the source, which is the exposure "A leaked signed URL"
  above describes.

The locks are still in place. `make deploy` and `make destroy` refuse until
docs/STATUS.md records the Paid plan and a person sets `CHECKPOINT_D=confirmed`
on that one command. The committed docs/STATUS.md never says the line, and a
test keeps it that way: on Oct 9 the line lived only in the deploy worktree's
copy, which was never committed. See `scripts/aws_guard.sh`.

Three things the deploy showed that are not fixed by a commit:

- **The budget alarm cannot fire yet.** The
  <!--n results/aws_deploy_2026-10-09.json:budget.limit_usd -->20<!--/n--> US dollar
  monthly budget filters on the cost allocation tag `Project=calm-frames`, and
  at 02:50 PDT Cost Explorer listed no cost allocation tag named `Project`. A
  new tag can take up to a day to show up there after it is first put on a
  resource, and it then has to be activated in Billing. Until it is, the
  filter matches no cost, and the bill has to be read by hand.
- **The pushed image has known vulnerabilities in its Debian packages.** ECR's
  basic scan on push reported
  <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.findings_total -->101<!--/n--> findings,
  <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.critical -->8<!--/n--> critical and
  <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.high -->56<!--/n--> high,
  all in Debian packages from the base image or the pinned ffmpeg (ffmpeg,
  perl, openssl, libssh and others), none in the Python packages pip-audit
  covers. The task takes uploads from the source bucket only, which only the
  account can write to, so these are the "hostile media" risk above rather
  than an open door. A rebuild on a newer base image is the fix.
- **The pushed image carries the CDK lookup cache.** The deploy wrote
  `pipeline/infra/cdk.context.json`, which holds an availability zone lookup
  keyed by the account id, into the checkout minutes before the image build
  read it. The image sits in a private ECR repository in that same account, and
  `.dockerignore` now keeps the file out of the next build.

## PyPI

flashmap publishes through trusted publishing, so there is no API token to
store, leak or rotate. `.github/workflows/publish-flashmap.yml` has the setup
steps and docs/RELEASE.md describes them screen by screen. The publish job needs
a person to start it by hand and type the word, and the `pypi` environment holds
it for a review on top of that.

## What has never been run

The honest half of a security document. Until Oct 9, 2026 everything on the AWS
side was written, tested as far as it can be tested without an account, and
unproven beyond that. That night some of it ran once, so each entry below says
what has run, how often, and what still has not.

- **AWS has been called on one night, from one Mac, and never from CI.** On
  Oct 9, 2026: the CDK bootstrap, the ECS service-linked role, the deploy and
  one update (both run by Alex in his own terminal), the image push, the cloud
  key's SSM parameter, two uploads and read-only describe calls. `make deploy`
  still refuses until two locks open; the test for that refusal is
  `pipeline/tests/test_aws_guard.py`.
- **The stack has been deployed once and has run one title**, so the IAM
  policies have now met the real service, for the calm 12 second marker clip
  and nothing else. The first run, before the key was wired in, did the whole
  analysis in
  <!--n results/aws_deploy_2026-10-09.json:runs.0.steps_run -->11<!--/n--> steps, failed
  verify on the missing signature, published
  <!--n results/aws_deploy_2026-10-09.json:runs.0.published_objects -->0<!--/n--> objects and exited
  <!--n results/aws_deploy_2026-10-09.json:runs.0.exit_code -->1<!--/n-->: fail closed, on AWS. The
  signed run took
  <!--n results/aws_deploy_2026-10-09.json:runs.1.steps_run -->12<!--/n--> steps, published
  <!--n results/aws_deploy_2026-10-09.json:runs.1.published_objects -->16<!--/n--> objects and
  <!--n results/aws_deploy_2026-10-09.json:runs.1.catalog_rows -->1<!--/n--> catalog row, and exited
  <!--n results/aws_deploy_2026-10-09.json:runs.1.exit_code -->0<!--/n-->. No long title, no real
  footage and nothing hostile has been through it.
- **The ingest container has been built end to end on this Mac**, on Oct 9 at
  commit c5724de, and the build `make deploy` made was pushed at
  <!--n results/aws_deploy_2026-10-09.json:image.size_mb -->279<!--/n--> MB. It does not yet have the
  Oct 2 pipeline changes, and the `image` job in `.github/workflows/audit.yml`
  remains the check that builds it from a fresh clone.
- **CloudFront signed URLs have never been signed.** The stack builds the key
  group when a public key is supplied, and a test reads that from the template.
  The Oct 9 stack was deployed without one, so no URL has been signed or
  fetched that way. CloudFront has served the delivered title unsigned: the
  entry, a poster and the HLS master playlist with HTTP 200.
- **The GitHub OIDC role has never been assumed, and does not exist.** It was
  not created on Oct 9, and there is no deploy workflow in this repository, on
  purpose.
- **The budget alarm has never fired, and cannot yet.** Its tag filter matches
  no cost until `Project` is activated as a cost allocation tag (see AWS above).
- **`make destroy` has never been run.** The stack stays up until the results
  are announced, about Dec 3 (docs/DECISIONS.md), and the teardown steps are in
  `pipeline/infra/README.md`.
- **Nothing here has had an outside security review.**

## Reporting something

Until the repository is public, tell Alex. After that, open a private security
advisory on GitHub rather than an issue, and do not attach media: a clip that
demonstrates a problem with flash detection is a hazard file, and
docs/SAFETY.md applies to it.


## Publication review: Amazon sample license notices

The generated `DOMParserPolyfill.ts` and the tracked
`app/src/w3cmedia/shakaplayer/ShakaPlayer.ts` carry an
"AMAZON PROPRIETARY/CONFIDENTIAL" notice referring to LICENSE.TXT. An October 10
check of the official pinned upstream source confirmed the same inconsistency:
the sample root LICENSE grants MIT-0, while <!--n results/cloud_continuation_2026-10-10.json:license_review.notice_source_files -->13<!--/n--> source files inside its supplied
Shaka archive carry the file-specific notice. The local archive is byte-identical
to upstream, contains no license file, and the upstream root LICENSE.TXT URL
returns 404. Replacing `xmldom` alone does not resolve these notices.

See [`AMAZON_SAMPLE_LICENSE_REVIEW.md`](AMAZON_SAMPLE_LICENSE_REVIEW.md) for exact
URLs, hashes, affected integration paths, and an unsent clarification request.
Preserve the notices and resolve their scope before public source release; this
review does not establish that redistribution is prohibited or that the root
license supersedes them. The review bundle is uploaded to a private draft release.

## October 10 pushed checkpoint

Hosted, Oct 11: on the push that repaired the audit, the Audit workflow is
green in all four jobs and CI in all six; the run ids are in
`results/github_push_2026-10-11.json`. The first Oct 11 push failed the bills
of materials job for one line, the npm version the app bill records, and the
bill was regenerated under the runner's npm. The Oct 10 record,
`results/github_push_2026-10-10.json`, keeps the earlier failure as it was.
