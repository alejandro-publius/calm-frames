# Calm Frames interface copy

The approved visual direction stays. The user wants the language to feel as familiar and seamless as a polished Fire TV app. Apply this preference throughout the current native build before recording the demo.

## Voice

Write for someone choosing something to watch or changing a setting. Use familiar labels and natural sentences. Keep each message focused on what the viewer needs to know or do next. A label can be short; an explanation should read as a complete thought.

Avoid paired slogans, repeated sentence fragments, rhetorical contrasts such as “not X, but Y,” decorative descriptions of colors and typography, and statements about how carefully the interface was designed. Keep engineering, design rationale, and prototype instructions in the handoff documentation.

The style takes cues from familiar television interfaces. These are original Calm Frames strings, not quoted or officially approved Amazon copy.

## Preferred labels

| Purpose | Label |
| --- | --- |
| Start a story | Watch now |
| Start the scene-hold demonstration | Watch demo |
| Start the gradient test clip | Play |
| Open title details | More info |
| Main shelf | Your library |
| Protected settings | Parental controls |
| PIN options | PIN settings |
| Return to the shelf | Back to library |
| Close an informational dialog | Close |

Keep visible labels short and give screen-reader labels enough context, such as “Watch Harbor.” Show Resume only when saved playback progress exists. Do not invent durations, ratings, progress, availability, plot details, or medical claims.

## Descriptions

Use the actual story synopsis in the native app. The preview's generic Harbor wording can be replaced once that synopsis is confirmed. Prefer one useful description over several decorative taglines.

For the scene-hold demo:

> This version adds practice holds to Harbor at set times so you can see how a hide works during playback. The holds are practice, not detected flashing.

When explaining the example holds:

> The holds are added at set times to demonstrate how the picture changes while sound and captions continue.

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

## Current direction, Oct 13

Write for someone choosing a story, not someone reviewing a build. Use
"Original story", "Watch now" and specific error messages. Do not add
"checked", "validated" or "verified" as reassurance in browsing labels,
announcements or marketing copy. Explain viewing limits where parents choose
settings; preserve the safety note. Internal status names and technical reports
retain their precise meaning.
