# Calm Frames submission copy

**Superseded for the submission.** The current description is
[submission/DEVPOST_DRAFT.md](submission/DEVPOST_DRAFT.md), updated on October
17, 2026 for installed source `9cc57ca`. The copy below describes earlier
candidates and is kept as a record. Nothing here authorizes recording,
publication, a main merge, credentials or AWS changes.

Historical draft prepared October 13 for the cinematic design. The text below
is kept as a record and is superseded by
[the current Devpost draft](submission/DEVPOST_DRAFT.md); do not paste this
version into the form. Its references to the current design and pending build
describe October 13.

The current candidate has package 5 from `4016e8d`, with eight journeys
reported by the app's own log on the Vega Virtual Device. Pixels, audio, the
parent settings interior and VoiceView remain unobserved, and recording still
needs separate authorization. [FINAL_HANDOFF.md](../FINAL_HANDOFF.md) carries
the package identity and remaining checks.
[SUBMISSION.md](SUBMISSION.md) retains the detailed field guidance,
technologies, feedback, testing instructions and mini challenges.

## Project name

Calm Frames

## Tagline

A calmer way to watch

## Inspiration

Movie night should be something a family can share. For families affected by
photosensitivity, a flashing scene can make that difficult. Covering the picture
also takes away the visual context of the story. I built Calm Frames to explore
how prepared video, sound, captions and a checked still image can work together
to make those interruptions easier to follow.

## What it does

Calm Frames is a Fire TV accessibility prototype for family entertainment.
Families browse a small library with their remote, choose a title and keep
listening and reading when its picture needs covering. Parents set the viewing
preset and room behind a PIN. A child's profile can make those choices stricter.

The current design brings an illustrated Harbor into the living room: panoramic
art, warm typography and quiet controls with a clear remote focus. Back returns
to the previous choice, Delete makes PIN corrections easy, and parental controls
keep viewing preferences together. Optional artwork motion and selection sounds
leave the default menus still and silent. This latest presentation is implemented
in source and awaits its matching Vega recording.

Harbor is an original, non-flashing film made for the demonstration. Its practice
version has scheduled holds that show a checked still while captions and a
recorded tone continue. These holds are examples, not detected flashing. A
separate prepared version demonstrates the real signed preparation pipeline.

## How I built it

A Python analyzer checks frames against published flash limits. The preparation
pipeline builds a covered rendition, verifies its artifacts and signs the map
with Ed25519. The Vega app checks that map before playback. Missing context
images or uncertain playback fall back to an opaque cover, and transport
controls share the guarded seek path.

The app uses React Native for Vega, Amazon's W3C media player, Media Controls
and captions view. The analyzer, GitHub Action, sidecar specification and player
hook are reusable integration paths. A deployed AWS pipeline has also processed
and published a signed title through S3, Fargate, Lambda, DynamoDB and CloudFront.
That cloud pipeline is separate from the app's compiled local library.

## Challenges and what I learned

An overlay can arrive late when player updates are irregular or JavaScript
stalls. Building a pre-covered rendition makes the prepared picture the first
layer of protection. Signatures establish integrity, but cannot correct a
detector that missed a flash.

That limit matters. The corrected synthetic evaluation measured overall recall
of <!--n results/conformance_current_report_2026-10-02.json:published.flashmap_recall -->0.85<!--/n-->,
falling to <!--n results/conformance_current_report_2026-10-02.json:published.recall_near_limits -->0.469<!--/n-->
near a limit; precision was
<!--n results/conformance_current_report_2026-10-02.json:published.flashmap_precision -->0.649<!--/n-->
overall and
<!--n results/conformance_current_report_2026-10-02.json:published.precision_near_limits -->0.573<!--/n-->
near a limit. Detection can miss flashing. Calm Frames reduces exposure to
flashing above published limits in the videos it plays; not a medical device.
It works with content prepared for this player, and cannot protect other
streaming apps or their DRM content. There is no clinical validation or feedback
from families or clinicians yet.

## Accomplishments

Earlier Vega Virtual Device recordings show the complete family flow: browsing,
PIN correction, saved viewing settings, playback, captions and sound through
Harbor's practice holds, and recovery after interrupted playback. The current
cinematic design builds on that working app and still needs a fresh native run.

The preparation pipeline rejects invalid artifacts before publication. Changed
maps and delivery bytes have rejection checks, and published measurements keep
failed and inconclusive cases visible. The AWS run has its own saved deployment
and publication evidence. Simulator observations do not establish physical
television timing or clinical safety.

## What is next

Finish the matching Vega recording and release, then ask families and
accessibility reviewers whether the experience and its limits are clear.
Further work should improve near-limit detection, evaluate real-video ground
truth and extend signed scene images across prepared preset combinations.
