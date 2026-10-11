# Outreach drafts

Drafts for Alex to send or post. Claude writes and refreshes them; nothing in this folder is sent by Claude.

Refreshed Fri Oct 9, 2026. The three emails were first written for Fri Sep 18 (HUMAN CHECKPOINT F in docs/BUILD_PROMPT.md) and were not sent then. This refresh replaces the line that said nothing had been measured, because measurements exist now, brings the description up to date with the build, adds one optional question about need, and adds two new drafts: a Discord check-in and the questions for the organizers.

`docs/outreach-kit.md` never arrived on this machine, so the three emails were written from docs/BUILD_PROMPT.md (step 0.9 and the Fri Sep 18 row) and docs/SAFETY.md. Nothing here reports what a kit said.

## The files

| File | Who it is for | Where the address comes from |
|---|---|---|
| `epilepsy-foundation.md` | The Epilepsy Foundation, whose public photosensitivity guidance the project already cites | Their own contact or press page. Address the team if no name is published. |
| `researcher.md` | An academic who works on photosensitive epilepsy and media | The corresponding-author address in a paper you have read, or their department page |
| `accessibility-advocate.md` | An accessibility group or an individual advocate | A contact address they publish themselves |
| `discord-checkin.md` | A Vega developer, in the Devpost Discord channel #amazon-developer-checkin | None: a public post. Link the repository only once it is public. |
| `organizer-questions.md` | The hackathon manager by email, or the Devpost forum, plus a list for Office Hours #2 on Mon Oct 19 | the address behind the "Email the hackathon manager" link on the overview page, the "Email the hackathon manager" link on the hackathon's overview page |

## The optional question about need

Each email now carries one optional question, under a bracketed line saying it is your call:

> Would families you work with use a check like this, and what would it have to do?

Keep it or delete it, and delete the bracketed line either way. It is there because the reviews of the entry scored Potential Impact lowest, and a reply about need is outside evidence that nothing in this repository can supply.

Keeping it changes a rule, so here is what it costs. docs/SAFETY.md rule 6 says outreach asks only for feedback on wording and flow, and the emails were written to ask one thing. The question asks for an opinion, not data, a demo or an endorsement, and it shows nothing, so the safety half of that rule ("Never show anyone flashes") is untouched. It does make each email two questions instead of one. If you keep it, docs/SAFETY.md rule 6 needs a line saying so.

Separately, docs/VALIDATION.md is now out of date whatever you choose: its rule 4 says every draft states that nothing has been measured, and its status table gives Sep 18 as the send date. Neither file is in this folder, and this refresh did not change them.

## Fill in before sending

Every `[square bracket]` in a draft is yours to complete, check or delete. Across the three emails:

1. The recipient, in the greeting. Do not guess a name, a title or an address. If you cannot see it in print, write to the team instead, or do not send that one.
2. The optional question about need: keep it or delete it, as above.
3. The sign-off is "Alex". Add your surname if you want it, for the researcher especially.
4. Whether you are writing as one person or as a team. The drafts say "I" throughout. If Rachel is on the Devpost team, say so in the first line of each.
5. The description paragraph. Re-read it the morning you send and check it still matches the build.
6. In `researcher.md` only: the optional line about their paper. Keep it only if it is specific and true.

The Discord post and the organizer questions have their own notes under "Before posting" and "Before sending".

## Rules that must survive your edits

- Ask for feedback on wording and flow, plus at most the one optional question about need. No demo, no call, no data, no endorsement.
- Never offer to show anyone flashing content, and keep the line in each email that says plainly that nothing we send contains flashing.
- Keep the approved sentence word for word: "reduces exposure to flashing above published limits in the videos it plays; not a medical device." Never "prevents seizures" or "seizure-proof".
- Stay truthful: a student hackathon project, early, not a medical device, and it works only on videos checked in advance.
- No measured numbers in the emails or the Discord post. We have measurements now, and each email has one sentence about them that gives the weaker finding: it misses much of the flashing just over the limits. If someone asks for figures, give the recall near a limit beside the overall recall, from `results/` through the README's "What has been measured" section, never the overall figure alone.
- Under 200 words for each email. Plain and warm. No jargon, no marketing.
- No em dashes or en dashes, and keep to the banned-word list under Style in CLAUDE.md.
- No AWS account details anywhere: no account ID, bucket names, CloudFront domain, ARNs or registry URI.

## If someone replies

Say thank you and answer their question. Do not turn a reply into a further ask.

If you want to quote a reply in docs/VALIDATION.md (due Fri Oct 16), ask that person for permission first, in a separate message. The drafts deliberately do not ask for permission up front, because that would add an ask.

An organizer's answer is different: it is a ruling about the rules, not feedback on the project. `organizer-questions.md` section 5 says where it goes.
