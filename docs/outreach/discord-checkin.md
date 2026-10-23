# Draft: Devpost Discord check-in, asking a Vega developer to try the hook

Written Fri Oct 9, 2026, for Alex to post in the Devpost Discord, channel #amazon-developer-checkin. Nothing here is posted by Claude. The post is the one paragraph between the lines.

---

Checking in from the Fire TV track: I'm Alex, building Calm Frames, a Vega app whose kid mode is built for families of children with photosensitive epilepsy. It comes with a small hook for Vega video apps that play through Amazon's W3C media player. The hook reads a signed flash map, covers the picture during flagged parts while sound and captions keep playing, and routes every seek (seek bar, D-pad, Alexa) through one guarded function. Could one Vega developer try adding it to a clean vega-video-sample checkout (tag v0.24-RN83) and tell me what broke or was unclear? The steps are in hook/README.md and the whole change is in docs/INTEGRATION_DIFF.md: [repo link, add it only once the repo is public]. No flashing video is needed: the first check is that a title with no signed map stays covered and says it is not checked yet. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device. Happy to try your project in return.

---

## Before posting

- **The channel.** #amazon-developer-checkin in the Devpost Discord, whose invite (discord.gg/devpost) is on the hackathon's Updates page. The channel name comes from the finish plan, so check that it exists before posting.
- **The repo link.** Add it only once the repository is public. If you post before then, replace the sentence that ends in the placeholder with: "The repo goes public before the deadline, and I will post the link here the day it opens." Do not add anyone to the private repository to speed this up: it still holds working notes, these drafts among them, that were never meant for the public.
- **The last sentence** is an offer of your time. Delete it if you cannot keep it.
- **Size of the change, if you want to mention it.** The post has no numbers on purpose. The diff against a clean sample checkout is <!--n results/integration_diff.json:lines_added -->32<!--/n--> added lines across <!--n results/integration_diff.json:files_touched -->4<!--/n--> files, from `results/integration_diff.json`. Type the figures in by hand rather than copying this line, so the hidden markers stay out of the post.

## Rules this post has to keep

- One ask: try the hook against a clean sample checkout and say what broke or was unclear.
- No flashing content offered or sent, and the post says none is needed. Never suggest comparing with the guard turned off: the sample streams third-party titles nobody here has checked, and a title with no map has to stay covered.
- The approved sentence word for word. Never "prevents seizures" or "seizure-proof".
- No repository link until the repository is public, and no numbers in the post.
- No em dashes or en dashes, and none of the banned words under Style in CLAUDE.md.

## If someone tries it

Thank them, and fix what they found. What they said goes into docs/VALIDATION.md only with their permission, and only at the level of detail they agree to: name, first name, role, or anonymous.
