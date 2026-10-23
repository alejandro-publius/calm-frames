# Parents feedback and accessibility polish

Unsubmitted follow-up to frozen source `2cf54e0d168e58daedfde3f15407833d23af4e93`,
on `codex/design-polish-2026-10-23`. The integration owner prepared this bounded
proposal after the stated submission cutoff. It does not replace the canonical
branch, existing Mac package or submitted materials. No push or publication.

## Implemented

- `app/src/calmframes/ParentAreaScreen.tsx`: while a PIN attempt is persisted,
  the existing notice says **Checking your PIN…** through its polite live region.
  Previously the keypad was blocked while the notice still said Enter your PIN.
  The existing privacy detail, colors and layout are retained. Success still
  waits for persistence; failures remain locked and display the existing error.
  The declared UI frame follows the displayed notice, including retries.
- The same screen now labels the viewing-preset radio group with its existing
  section heading, including the selected profile where applicable. This matches
  the room controls and First Run. No setting, PIN or profile data changes.
- The primary-button review found its shared wrapper already supplies the proper
  pressed fill. That suspected contrast issue was rejected after rendering the
  complete component. `CalmButton` remains unchanged; the existing test now also
  checks readability when a press arrives before a focus event.

## Design guidance applied

The upstream text sources and hashes are in
[guidance-sources.json](../../results/design-polish-2026-10-23/guidance-sources.json).
These are freshly retrieved public versions, not claims of access to the Mac's
installed copies or connector runtimes.

| Guidance | Applied here |
|---|---|
| Anthropic frontend-design | Keep the existing subject-specific coastal identity and intentional hierarchy. |
| Anthropic design-critique | Inspect real components and interactions before changing them; reject the false-positive button finding. |
| Anthropic ux-copy | Replace a misleading input instruction with concise waiting feedback. |
| Anthropic accessibility-review | Label the choice group and retain the polite status announcement and focusable keypad. |
| Vercel Web Interface Guidelines | Review the offline guide's browser focus, overflow and loading behavior; apply only relevant principles to native components. |
| Playwright | Render the existing guide and actual exported native component trees for visual inspection. Browser layout is an approximation, not native acceptance. |

The existing tokens remain cream `#F7EACF`, paper `#FFF8E7`, teal `#385C59`,
ink `#193F3E`, clay focus `#A44132` and pale primary `#FFECD6`. Existing Calm
fonts retain their heading, body and control roles. The Parents composition
remains heading above message at left and keypad at right; the status changes
in place. No new font, illustration, animation or decoration.

The other named tools are accounted for in the earlier handoff's section 7.
Taste's script and browser inspector are not needed for this native fix;
image-to-code and awesome-design-md would add no missing input to it. ADHD
exploration, new research and a new design system would expand scope. None is
reported as run or installed here. The requested bounded polish does not require
reinstalling all Mac plugins.

## Evidence and remaining acceptance

[Checks and source hashes](../../results/design-polish-2026-10-23/checks.json)
record the clean locked install, normal typecheck/lint and focused regressions.
New pending-state and grouping assertions failed against the previous source
before passing with the changes. They cover delayed correct and incorrect PIN
attempts, persistence failure, duplicate presses and the existing group label.
No private PIN or household data was used; previews use ephemeral fixtures.

Before/after browser previews use the existing component-export renderer,
packaged fonts and actual host trees at 1080p and 720p. They are labelled as
browser approximations. The separate artifact contains those images, their
hashes, the review script and the patch. A first environment-variable-driven
export reused Babel's cached values; it was invalidated and excluded. Corrected
exports use literal dimensions and distinct fixtures, with the original Parents
component read from the frozen Git commit for the before images.

Mac acceptance still needs the exact proposal's native VoiceView announcement,
D-pad focus and appearance. This cloud pass does not establish those results.
The canonical product's dependency Audit failure, native/human acceptance and
missing final media remain separate outstanding items. Manga and ElevenLabs
production remain parked; no generated media, release acceptance or publication
is implied.
