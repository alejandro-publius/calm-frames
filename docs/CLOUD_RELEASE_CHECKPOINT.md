# Cloud release candidate checkpoint

October 22, 2026. Fire TV only, with the original native coastal design. UX, DX and AX mean user, developer and agent experience; accessibility remains separately protected. This is an isolated integration candidate, not a published or human-accepted release.

## Integrated inputs

Branch: `codex/cloud-release-candidate-2026-10-22`. Start from this checkpoint when asked to continue. The exact final documentation commit is returned in the task handoff; [validation.json](../results/cloud-integration-2026-10-22/validation.json) names the source commit checked before that documentation commit.

| Input | Source identity | Candidate identity |
|---|---|---|
| Claude's existing work | `d9f8d296bbc5766fbe6bb496990cfd9e68d6ae3e` → `f61d99386abfa4790e48b0b0aa436f4d72d10766` → `0e9241a478abdda980b272f6654aa2745beabd45` | Retained as ancestors, without recreating their changes |
| Combined locked-install check | `69259f309448e82a1bb00df1ba702c2d572f2031` | `0371ebaa85b2978a47407f4b4c9ab57d04a60827` |
| Combined evidence-write check | `7e9188b7829309a7d4738a41fee553b23f6ba198` | `5ef3b0d176d2bab46bd320723c07a5a4b629f894` |
| Combined hazard self-test caller check | `9cdb333f460338baddd478c8ce978660dc1d6559` | `3bcfe54216f75ceb95d8d4f7b9bf9eb52a349f7b` |
| Completed judging package | `9ad7bb7a2efd0a3b95f84fcefbeaca19d3eabcf2` | `a61c83c59e558093a3fc64ca5b13d1419431e06f`; identical package tree |

Both supplied ZIPs were read locally and matched their expected size and SHA256. Bundle prerequisites, exact commit sequences, changed paths and Claude's file inventory were verified before integration. The inputs had no overlapping changed paths. Original branches and worktrees remain intact.

Only the combined release-check series was applied. The separate `63122a1` and `32cf1f7` commits are superseded, not additional inputs. Rejected browser UI `76223f99cf8543ffe1e75d54c9873b56a0c23318` and its archive are excluded. The `app`, `hook`, `pipeline`, `flashmap` and `media` Git trees remain identical to base `13551e45bd853c392489dbecce7158a04036f615`.

## Behavior checked here

- Locked `npm ci` failure preserves its exit status and stops the workflow before later commands. The regression harness rejects the previous unlocked-install fallback.
- A video gate cannot print success when its evidence record cannot be written. That case returns exit `2`; a measured failure remains exit `1` with a failed record.
- The hazard self-test accepts only a measured rejection. An inconclusive evidence-write result cannot count as the expected rejection or produce a passing self-test. The successful hazard/calm path remains accepted.
- Focused tests use command stubs and text fixtures. No actual installation, hazardous content, video processing or analyzer run occurred. Bash syntax, workflow YAML, Python parsing, repository style and published-number synchronization passed. Independent review found no material regression in the combined checks.

See the [machine-readable validation](../results/cloud-integration-2026-10-22/validation.json) for commands, scope and omissions. Local checks do not establish hosted CI success, app performance or a native audiovisual result.

## Reconciled evidence and claims

The imported native and demo receipts identify source `d96c088`; they are not fresh native observations of this integrated candidate. The unchanged application tree preserves the implementation, not a new observation or human review.

| Topic | What is now available | Boundary retained |
|---|---|---|
| Original judging guide | [The preserved guide](judging-package/index.html), its existing renders and evidence remain byte-identical to `9ad7bb7`. | It describes the `13551e4` snapshot. Its statements that newer benchmarks/video were unavailable refer to that snapshot. This addendum supplies the later evidence; the guide was not rebuilt or silently relabelled. |
| Preparation benchmark | [Claude's recorded benchmark](../results/preparation-benchmark-2026-10-22/benchmark.json), tested at `d9f8d296`, is now present. Timing summaries agree with their recorded sample arrays. | One owned clip on one Mac with a real analyzer, one injected interruption point and a wrapper before the kill. These are recorded terminal experiments, not native screen observations, new cloud measurements or general throughput claims. |
| Import demonstration | [The imported record](../results/preparation-benchmark-2026-10-22/import-demonstration.json) documents preparation and package refusals. | The developer demonstration title was not activated on the TV. No new catalog, key, budget or trust approval follows. |
| Native review | [The second-session receipt](../results/native-review-2026-10-22/native-review.json), traces and committed crops are present; crop hashes match. The receipt describes reading stops and return focus. | The receipt includes a scripted expectation mismatch explained by returning to the actual opener card. Do not turn the session into an unqualified all-inputs-passed claim. Original uncropped captures and recordings are not included. |
| Replacement demo | [Demo receipt](../results/replacement-demo-2026-10-22/demo.json) and [gate receipt](../results/replacement-demo-2026-10-22/video_check.json) agree on recorded file hash, byte count and duration. | The actual MP4 is outside this transfer. We checked receipt consistency, not the video's bytes, picture or sound. The saved gate ran before the combined fixes; this task did not rerun it on the external video. |
| Audio and picture acceptance | The imported demo receipt explicitly says audio was not listened to and full real-time viewing was not established. | Human listening, palette review and full replacement-video acceptance remain pending. General authorization to integrate does not provide those reviews. |

The later Mac coordination message reports an installed hash match and fresh Home/Details/Back traces. Those fresh trace files were not attached, so that update remains attributed coordination context. Emulator shell-session lifetime is suspected, not proved. It adds no fresh playback, ending, picture or audio acceptance here. No medical outcome or safety claim is inferred from any receipt.

## Blockers and next action

The transfer blocker for these two packages is resolved. No application rebuild is justified by this integration because its application tree is unchanged.

Next cloud action, if asked to continue: use this candidate and its receipt, inspect any newly supplied evidence against its exact identity, and address only a demonstrated inconsistency or regression. Do not reapply old fix archives or rebuild the judging guide. Current official-rule verification remains open because the source was blocked in the earlier cloud review; no new rule wording is asserted here.

Mac-only work remains native capture when authorized, human audio/palette/full-video review, and confirming any intended installed artifact against its receipt. External demo/media files are not assumed accessible from cloud paths. The submitted `bf2f615` fallback and public demo remain unchanged. No push, merge, publication, workflow dispatch or live-submission edit occurred.
