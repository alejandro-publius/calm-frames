# Calm Frames

**A calmer way to watch: a native Fire TV prototype for prepared media.**

Calm Frames is being built for people with photosensitive epilepsy and their
caregivers. It explores choosing prepared nature scenes, watching through a
native Vega OS player, and keeping a still picture at the end. Offline analysis,
signed flash maps, artifact hashes, scheduled covers and guarded seeking support
that workflow.

**This is a prototype, not a medical device. It has not been clinically validated
and cannot guarantee seizure prevention or safe viewing for any individual.**
Its analysis and playback checks are engineering evidence, not clinical evidence.
It works with its own prepared catalog; it does not intercept other Fire TV apps,
Prime Video, DRM content or arbitrary streams system-wide.

## Start here

| What you can inspect | Provenance and limits |
|---|---|
| [Public October source snapshot](https://github.com/alejandro-publius/calm-frames/tree/37d10c2db57fc0868499adc133cff7560600d5cc) | Public native-validation handoff at `37d10c2`. Includes the earlier product tree and its handoff record. It predates the latest local native repairs. |
| [Build preparation instructions for that snapshot](https://github.com/alejandro-publius/calm-frames/blob/37d10c2db57fc0868499adc133cff7560600d5cc/docs/RELEASE.md) | Developer instructions, not a downloadable accepted build. Use the source and instructions from the same snapshot. Preparation still requires the documented SDK and media verification inputs. |
| [Earlier demo video](https://www.youtube.com/watch?v=6lAP1FH16vc) | Historical demonstration of an earlier build on the Vega Virtual Device. The video description names `claude/ocean-layout-fix-2026-10-19`, without pinning an exact build; its private-repository access note is stale. The video does not establish that the latest repairs passed. |
| [Documentation guide](docs/README.md) | Separates current public status from the September engineering record. |
| [Submission status note](docs/SUBMISSION.md) | Repository documentation only. A draft is not a submitted Devpost answer. |

Checked on October 26, 2026: the default branch's application source still comes
from the September tree. The October overview previously placed above it did not
update that code. The pinned public handoff above is a more recent source
reference; it is not final release acceptance. The newer local native repair
branch has not been published. There is no public downloadable GitHub release
verified for this revision.

## What the prototype does

- Prepares eligible media offline and records source/rendition identity, signed
  analysis maps and verification reports.
- Uses a native Vega media player with a cover layer and a shared guarded seek
  path. Unresolved verification or playback uncertainty keeps the picture covered.
- Offers remote-driven scene selection and local caregiver preferences. The
  continuous McWay edition and other prepared still scenes have different media
  behavior; a Forest label does not establish a newly integrated Forest video.
- Provides a separate analyzer and preparation tools for developers. A signed map
  binds an analysis result to an artifact; it does not certify medical safety.

## What remains open

Newer local work has bounded native observations for pale opening transitions and
Reading comfort visibility/focus. The latest Reading comfort observations used
Debug with VoiceView off. They do not establish final Release or VoiceView-enabled
acceptance. Pause announcements remain unreliable in the recorded Release retest.
Dependency audit findings remain unresolved. New Forest media preparation and
new demo assets are work in progress, not an integrated catalog or a finished
native demo. No complete acceptance or clinical validation is claimed.

## Engineering record on this branch

The [results directory](results/), [evaluation plan](docs/EVAL_PLAN.md) and
[historical gate log](docs/GATES.md) retain the measurements, failures and
limitations of the September work. Their dates and source scope matter: old
passing checks do not validate a different build. Earlier roadmap, safety and
submission language is superseded by the limits above. History is retained in Git.

<details>
<summary>September source navigation on this branch</summary>

These links describe the source in this checkout, not the October snapshot.
Symbol names are included so the existing line-link check can detect drift.

| Component | Source |
|---|---|
| Native player construction | [VideoHandler](app/src/utils/VideoHandler.ts#L147), `new VideoPlayer()` |
| Native player import | [VideoHandler import](app/src/utils/VideoHandler.ts#L5), `VideoPlayer` |
| Shaka attachment | [Player attachment](app/src/utils/VideoHandler.ts#L274), `new ShakaPlayer(...)` |
| Video surface | [PlayerScreen surface](app/src/screens/PlayerScreen.tsx#L546), `KeplerVideoSurfaceView` |
| Surface import | [PlayerScreen import](app/src/screens/PlayerScreen.tsx#L17), `KeplerVideoSurfaceView` |
| Media control focus | [Control focus](app/src/utils/VideoHandler.ts#L158), `setMediaControlFocus` |
| Transport handler | [Handler](app/src/calmframes/SafeMediaControlHandler.ts#L49), `SafeMediaControlHandler` |
| Seek handler | [Seek](app/src/calmframes/SafeMediaControlHandler.ts#L68), `handleSeek` |
| Fast-forward handler | [Fast forward](app/src/calmframes/SafeMediaControlHandler.ts#L89), `handleFastForward` |
| Seek plan | [Seek planner](app/src/calmframes/seekSafety.ts#L113), `planSeek` |
| Captions | [Caption view](app/src/screens/PlayerScreen.tsx#L563), `KeplerCaptionsView` |

</details>

Code is licensed under [Apache 2.0](LICENSE). Media has separate permissions and
credits recorded in [the media license register](media/LICENSES.csv). The
historical presentation assets remain in the repository with their existing
provenance; they are not screenshots of the latest local repair build.
