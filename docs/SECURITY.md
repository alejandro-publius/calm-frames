# Security

What secrets this project has, where they live, and how to change them. This
repository goes public on Oct 21, so everything here is written to be read by
strangers.

## The short version

| Secret | Where it lives | In the repo? |
|---|---|---|
| Map signing private key | `~/.calm-frames/keys/team_key.pem`, on one machine, mode 600 | never |
| Map signing public key | `~/.calm-frames/keys/team_key.pub.pem`, and compiled into the app as `OFFLINE_PUBLIC_KEY_BASE64` | the public half only |
| AWS access | GitHub OIDC, a role assumed by a workflow | never, there are no stored keys |
| PyPI upload | trusted publishing, an OIDC token minted per run | never, there is no API token |
| Parent area PIN | set on the device, stored only as a salted hash (`app/src/calmframes/parentGate.ts`) | never, there is no default |

There is no `.env` to copy, no secret to paste into CI, and nothing to rotate
except the signing key.

## What this has to withstand

A threat model for a project whose whole point is that a child does not see a
flash. The thing being protected is not data. It is the guarantee, and the ways
to break the guarantee are more interesting than the ways to break in.

| What an attacker wants | How they would try | What stops them |
|---|---|---|
| Make the player show flashing it should hide | change a flash map | the signature, the file binding and fail closed |
| Crash or take over the analyzer | hand it a hostile video | it runs on our machines and in one task with a narrow role |
| Turn the protection off | get past the parent PIN | a rate limited, salted, iterated hash, and settings that can only add hides |
| Take the video | leak a CloudFront signed URL | the URL reaches a kid safe rendition and nothing else |
| Get code into the build | a dependency, an action, an image | hashes, digests, a lock file, an audit with written exceptions, gitleaks |

### A tampered map

The map is the whole guarantee: it says which parts of a title flash. A map an
attacker can edit is a player that hides nothing.

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
checked. That is the fail closed rule, and it is what makes the whole design
safe against an attacker who can write to the delivery bucket, the CDN or the
device's own storage. The worst they achieve is a title that will not play.

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
  `media/LICENSES.csv` with a checked licence and a SHA-256. The input is not
  hostile because nobody hostile chose it.
- **In the ingest task on AWS**, over whatever landed in the source bucket. That
  is the one place where a stranger's file could reach the decoder, so the task
  is the narrow one: no inbound access at all, a task role that can read one
  prefix of one bucket and write two paths, no long lived credentials, no shell,
  not root, and a container that exits when the title is done. An attacker who
  achieved code execution there would find a task that can read uploads and
  write renditions, in an account with a 20 dollar budget alarm on it.
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
- **AWS.** GitHub OIDC, so there is no access key to steal from CI. The deploy
  role can do one thing: assume the CDK bootstrap roles.
- **GitHub Actions.** Pinned by tag, not by digest, which is the weak link in
  this list. `make pins` reports every one of them as a note rather than a
  failure, and moving them to digests is the obvious next hardening step. It is
  written here rather than quietly left out.

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

As of the last run:

| | |
|---|---|
| Python packages with an advisory, across the container, the CDK and the venv | <!--n results/audit.json:published.python_packages_with_advisories -->0<!--/n--> |
| npm packages with an advisory in app/ | <!--n results/audit.json:published.npm_packages_with_advisories -->59<!--/n--> |
| npm advisories behind them | <!--n results/audit.json:published.npm_advisories_total -->45<!--/n--> |
| of which critical | <!--n results/audit.json:published.npm_critical -->6<!--/n--> |
| of which high | <!--n results/audit.json:published.npm_high -->25<!--/n--> |
| exception groups, each with its reasons | <!--n results/audit.json:published.exception_groups -->3<!--/n--> |

The three groups, in short. The full reasoning is in the TOML file, in
paragraphs, because a one line reason is how an exception becomes permanent.

1. **The Vega SDK and React Native.** The project pins SDK 0.24.9914 and the
   sample at `v0.24-RN83` because that is what the device runs. There is no
   newer react-native that Vega 0.24 supports, so "upgrade" is not an option
   that leaves a working app. The advisories are denial of service and improper
   authorization reached through input the app never hands them: the only
   outside input it parses itself is the map, through our own reader.
2. **Developer tooling.** jest, metro, the community CLI and their helpers. They
   run on a developer's machine or a CI runner, over this repository's own
   files. This is the build machine's risk, not the television's.
3. **Two leftovers from the sample**, with a review date of Oct 5 rather than a
   shrug. `xmldom` is a direct dependency with sixteen advisories, several
   critical, no fix in the 0.6 line, and zero imports anywhere in `app/src` or
   `app/test`. It should be deleted from `app/package.json`. `lodash` has a fix
   inside the range `package.json` already allows, so `npm update lodash` takes
   it. Both files belong to the app lane, which is why this is a recommendation
   here rather than a change.

The check fails four ways, each one broken on purpose and watched: a package
with no exception, a new advisory against a package that has one, an exception
past its review date, and an exception with nobody's name on it.

### The bills of materials

Three CycloneDX 1.6 documents, written by the CycloneDX project's own tools and
regenerated reproducibly so CI can diff them:

| File | What it covers | Components |
|---|---|---|
| `docs/SBOM.ingest.cdx.json` | the Python packages in the ingest container | <!--n results/sbom.json:published.ingest_components -->12<!--/n--> |
| `docs/SBOM.app.cdx.json` | what the Vega app is built from | <!--n results/sbom.json:published.app_components -->1109<!--/n--> |
| `docs/SBOM.cdk.cdx.json` | what synthesizes and deploys the stack | <!--n results/sbom.json:published.cdk_components -->2<!--/n--> |

What they do not cover: the Debian packages apt installs inside the image.
ffmpeg pulls in a long list of libraries, and listing them properly means
reading the built image with a scanner. That has not been done. What makes the
set knowable at all is that the base image is pinned by digest,
<!--n results/sbom.json:published.base_image_digest -->sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2<!--/n-->,
so the same command gives the same packages until somebody changes that line.

## AWS

No AWS credentials exist in this project and none are stored anywhere. CI reaches
AWS, when it eventually does, through a GitHub OIDC role defined in
`pipeline/infra/calm_frames_stack.py` and scoped to this repository.

Nothing has been deployed. `make deploy` and `make destroy` refuse until two
locks are open: docs/STATUS.md records that the account is on the Paid plan, and
a person sets `CHECKPOINT_D=confirmed` on that one command. `make synth` writes
the template offline and is what to use in the meantime. See
`scripts/aws_guard.sh`.

## PyPI

flashmap publishes through trusted publishing, so there is no API token to
store, leak or rotate. `.github/workflows/publish-flashmap.yml` has the setup
steps and docs/RELEASE.md describes them screen by screen. The publish job needs
a person to start it by hand and type the word, and the `pypi` environment holds
it for a review on top of that.

## What has never been run

The honest half of a security document. Everything below is written, tested as
far as it can be tested without an account, and unproven beyond that.

- **No AWS API call has ever been made from this repository.** Not a deploy, not
  a diff, not a describe. `make deploy` refuses until two locks open, and the
  test for that refusal is `pipeline/tests/test_aws_guard.py`.
- **The stack has never been deployed**, so the IAM policies have never been
  tried against the real service. They are checked against the synthesized
  template instead: no wildcard admin, no IAM user, no access key, the task role
  scoped to one prefix, the starter Lambda scoped to one task definition.
- **The ingest container has not been built end to end on this machine.** The
  build reached unpacking ffmpeg's Debian packages and was stopped, because it
  was helping to push the shared Docker VM into its memory limit and another
  project's container was killed. Which parts are proven is in
  docs/DECISIONS.md. The `image` job in `.github/workflows/audit.yml` builds it
  on a runner with QEMU instead, and that is where the answer will come from.
- **The container entrypoint has never processed a real video.** Its rules are
  tested end to end against moto with the pipeline handed in as a stand in, so
  what is proven is the publishing rule, the allowlist, the hostile key check
  and the key handling, not ffmpeg.
- **CloudFront signed URLs have never been signed.** The stack builds the key
  group when a public key is supplied, and a test reads that from the template.
  No URL has been made or fetched.
- **The GitHub OIDC role has never been assumed.** There is no deploy workflow
  in this repository, on purpose.
- **Nothing here has had an outside security review.**

## Reporting something

Until the repository is public, tell Alex. After that, open a private security
advisory on GitHub rather than an issue, and do not attach media: a clip that
demonstrates a problem with flash detection is a hazard file, and
docs/SAFETY.md applies to it.
