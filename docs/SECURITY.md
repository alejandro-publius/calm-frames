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

The allowlist in `.gitleaks.toml` covers only directories of generated or third
party files that are never committed: the Shaka Player checkout, installed
packages, build output. Nothing under our own source, docs, results or
infrastructure is allowlisted. Keep it that way: an allowlist that grows to
silence a real finding is how a key ships.

On a finding, whether from the hook or from CI:

1. take it out of the change;
2. rotate it, whatever it is. A secret that reached a commit is burned even if
   the commit never leaves the machine;
3. if the commit was pushed, rotate first and rewrite history second. Rewriting
   history does not un-leak anything.

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

## Reporting something

Until the repository is public, tell Alex. After that, open a private security
advisory on GitHub rather than an issue, and do not attach media: a clip that
demonstrates a problem with flash detection is a hazard file, and
docs/SAFETY.md applies to it.
