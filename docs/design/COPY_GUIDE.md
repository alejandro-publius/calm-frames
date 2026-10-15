# Calm Frames interface copy

The approved visual direction stays. The user wants the language to feel as familiar and seamless as a polished Fire TV app. Apply this preference throughout the current native build before recording the demo.

## Voice

Write for someone choosing something to watch or changing a setting. Use familiar labels and natural sentences. Keep each message focused on what the viewer needs to know or do next. A label can be short; an explanation should read as a complete thought.

Avoid paired slogans, repeated sentence fragments, rhetorical contrasts such as “not X, but Y,” decorative descriptions of colors and typography, and statements about how carefully the interface was designed. Keep engineering, design rationale, and prototype instructions in the handoff documentation.

The style takes cues from familiar television interfaces. These are original Calm Frames strings, not quoted or officially approved Amazon copy.

## Preferred labels

| Purpose | Label |
| --- | --- |
| Start a video | Play |
| Start the practice demonstration | Play demo |
| Start the gradient check clip | Play |
| Open a video's page | Details |
| Open the practice demonstration's page from a video's page | Try the demo |
| The explanation page, from Home | How it works |
| Protected settings, from Home | Parents |
| Protected settings, as a page title | Parental controls |
| PIN options | PIN settings |
| Return one level | Back |
| Close an informational dialog | Close |

The Oct 15 copy pass uses **picture pause** to explain the demonstration and
**hidden scene** to explain flashing removed during playback. The viewer does
not need to learn the internal word “hold.” Keep **the picture stays hidden**
for playback that cannot be verified, with the specific reason. Use **video**
for content. Say each fact once per screen.

Keep visible labels short and give screen-reader labels enough context, such as “Play: Harbor.” Show Resume only when saved playback progress exists. Do not invent durations, ratings, progress, availability, plot details, or medical claims.

## Descriptions

Use the actual story synopsis in the native app. The preview's generic Harbor wording can be replaced once that synopsis is confirmed. Prefer one useful description over several decorative taglines.

For the scene-hold demo:

> The picture pauses twice while sound and captions continue. This demo contains no flashing.

When explaining the demo timing:

> This demo has no flashing. The picture pauses 2 times, for 8 seconds in total.

Keep the demo labeled and retain the full evidence limits in submission materials. Do not imply the scheduled holds were detected hazards or that a prepared title guarantees safety.

## Native states to review

Use these patterns only when they match the actual state and available action:

- PIN entry: “Enter your PIN to open parental controls.”
- Wrong PIN: “That PIN isn’t correct. Try again.” Keep lockout timing and attempt information data-driven.
- Saving: “Saving your changes…”
- Save failure: “Your changes couldn’t be saved. Try again.” Offer Retry only when the action is implemented.
- Unavailable title: Explain the actual reason and the available next step; never imply that an unchecked title can play.
- Empty library: Explain why no titles are available for the current settings and direct the parent to the relevant control.
- Offline state: State which titles remain available based on the actual verified local library.

## Preview documentation

The explanatory block under the artboard now reads:

> Browse the library, view title details, and explore parental controls. Use the arrow keys to move, Enter to select, and Esc to go back.

The preview's limitations and implementation links sit under “About this preview.” They are not product copy.

## Acceptance

Read each complete native screen aloud. Remove duplicated labels, unexplained technical terms, and marketing language that interrupts the task. Check wrapping at the real TV font size, preserve remote focus and accessibility labels, and keep all state-dependent messages truthful.

Carry this copy direction through onboarding, library, details, playback, PIN, settings, errors, and empty states while preserving the already approved visual design.

## Historical direction, Oct 13 (superseded)

The paragraph below records the earlier direction. The Oct 15 vocabulary and
preferred labels above take precedence; "Original story" and "Watch now" are
not current interface labels.

Write for someone choosing a story, not someone reviewing a build. Use
"Original story", "Watch now" and specific error messages. Do not add
"checked", "validated" or "verified" as reassurance in browsing labels,
announcements or marketing copy. Explain viewing limits where parents choose
settings; preserve the safety note. Internal status names and technical reports
retain their precise meaning.
