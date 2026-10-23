# Coastal visual review

Unsubmitted proposal on `codex/design-polish-2026-10-23`, based on frozen
source `2cf54e0d168e58daedfde3f15407833d23af4e93`. The earlier feedback change
is preserved at `41bdeb94ca1c3e8cceabafd821f141587f77c202`; the broader visual
pass follows it on the same local branch. No merge, push or publication.

## Four-island follow-up

The owner approved the visual direction and requested a separate Acadia island.
Home now shows Acadia, McWay Falls, Sea otters and Forest as four full cards on
four islands. The stacked-card layout is removed. Acadia retains its lighthouse;
McWay has a separate cove silhouette and static waterfall motif. The boat follows
each title independently. Acadia still launches its still scene; McWay still
launches its approved five-minute video. Media, signatures and player logic did
not change. The approved Details and Parents layouts remain implemented.

The latest export uses direct PNGs at 1080p and 720p because the chat viewer had
trouble with both the original linked gallery and the larger embedded HTML.
These are browser approximations of native component trees. Native D-pad review
remains pending. See [four-islands-checks.json](../../results/design-polish-2026-10-23/four-islands-checks.json)
for exact source hashes, checks and preview hashes. The earlier gallery below
is historical evidence of the preceding three-island layout.

## Visible changes

- **Home:** a larger wordmark, larger scene photographs, lighter card edges and
  centered Watch / Details controls. Existing islands, labels and selection
  handlers remain. Offline notices keep a separate area beside the actions.
- **Details:** title and runtime, description and coverage summary, then actions.
  The reading column stays inside its panel; panel and photograph borders are
  lighter. Existing imagery, island landmarks and title alignment with the
  opening screen remain. The shared opening panel inherits the lighter border.
- **Parents PIN:** heading, notice and keypad share one framed paper panel.
  The keypad moves up into the safe area without reducing control sizes.
- **Parents settings:** a centered reading column and outlined profile section
  separate profile management from viewing presets. The page remains scrollable.
- The earlier Checking your PIN feedback and labelled preset group remain.
  Authentication, persistence, playback, cover ordering and media are unchanged.

The cream, paper, teal and clay palette and all three packaged Calm fonts are
retained. No generated artwork, new animation or browser product is introduced.
Native spatial focus can change when controls move; that needs a Fire TV review.

## Review artifact

The portable export includes `preview/index.html`, seven before/after states
at 1920 by 1080 and 1280 by 720, and a separate-worktree import handoff.
All screenshots are embedded in the HTML, which opens by itself without an
asset directory, installation or network. The first linked-file delivery did not
resolve images in the chat file viewer; the embedded version replaces it.
Use its screen selector, Before / After buttons and full-size PNG download links.

These are browser approximations of actual exported React Native host trees,
with the existing SVG artwork, fonts and packaged photographs. They are not
native captures or evidence of playback. Robin and Sam are ephemeral test
fixtures. The settings image shows the first viewport of a scrollable page.

Both sides use the corrected preview renderer: inline SVG icons participate in
layout, and image borders are drawn. Those renderer corrections are not app
improvements and must not be presented as such. Before images are from
`41bdeb94ca1c3e8cceabafd821f141587f77c202`; after-image source hashes are in
[visual-checks.json](../../results/design-polish-2026-10-23/visual-checks.json).

## Checks and limits

Normal `npm run typecheck` and `npm run lint` pass using the existing real locked
installation (Node 22.23.2, npm 10.9.8). No TypeScript flags or dependency symlinks
were substituted. Lint retains existing warnings, recorded in the receipt.

The full app run exposed stale surface declarations and unsynced generated
mirrors. The declarations now follow the actual Details paint order, including
retained Harbor pages. `node hook/tools/sync.mjs` refreshed the two affected
mirror sources and their fingerprints. Both failures and the related navigation,
contrast, focus, geometry and opening-alignment checks pass on focused rerun.
The receipt distinguishes the original full run from that final rerun.

Playwright rendered both TV dimensions. The full Parents keypad and Details
primary action stay inside their intended bounds. The gallery was inspected
at desktop and narrow widths; its image links, keyboard order, visible focus,
reduced-motion behavior and lack of external requests were checked. These
browser checks do not certify native Yoga layout, D-pad navigation or VoiceView.

Mac acceptance still needs native Home navigation after centering the actions,
Details / opening alignment, Parents keypad and scrolling, status announcements,
and human comfort. The canonical build's dependency Audit and native/human
acceptance remain separate unresolved items. Narration, manga and replacement
video production remain parked. Submitted materials are frozen.

## Guidance actually applied

[Source versions and hashes](../../results/design-polish-2026-10-23/guidance-sources.json)
record the public guidance retrieved earlier. This pass applies Anthropic
frontend-design and design-critique to composition and hierarchy, ux-copy to
existing status feedback, accessibility-review to focus and readable controls,
and relevant Vercel interface guidance to the offline gallery. Playwright was
used for rendering and browser checks. This does not claim access to the Mac's
plugin runtimes or that every previously discussed plugin was installed.

The earlier feedback-only receipts remain in
[checks.json](../../results/design-polish-2026-10-23/checks.json) and
[native-preview-summary.json](../../results/design-polish-2026-10-23/native-preview-summary.json).
They are historical evidence for the preceding commit, not this visual pass.
