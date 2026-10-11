# The rubric we are actually judged against

Everything on this page comes from the hackathon's own pages, fetched and read
on **Thu Sep 17, 2026**, with repository access requirements rechecked on
**Thu Oct 1, 2026**:

- Overview and requirements: <https://amazonappdev2026.devpost.com/>
- Official rules: <https://amazonappdev2026.devpost.com/rules>

Both were fetched over HTTPS on that date and the text below was taken from the
fetched pages, not from memory. The rules page carries a banner reading
"September 16, 2026 UPDATE: Hackathon submission requirements: Code
repository.", so the repository wording is recent and worth re-reading before
submission day.

**Two notes on quoting.** First, our own style rule bans long dashes. Where the
source text uses one as punctuation, this file writes a comma inside square
brackets, like `[,]`. Where it uses one to mean a range, as in a pair of dates,
this file writes the word "to". Second, the source uses curly quotation marks
and this file uses straight ones. Those are the only changes made to any quote
on this page. Nothing else is reworded, shortened without an ellipsis, or
paraphrased while presented as a quote.

**Re-check before submission.** Devpost rules pages change during a hackathon,
and this one already has. Fetch both pages again on Wed Oct 21 during the final
checks and diff them against this file.

---

## 1. Dates

Quoted from the rules page, section 1:

> Submission Period: Monday, August 31, 2026 (10:15 am Pacific Time) to Friday,
> October 23, 2026 (12:00 pm Pacific Time) ("Submission Period").

> Judging Period: Monday, November 9, 2026 (12:00 pm Pacific Time) to Friday,
> November 20, 2026 (12:00 pm Pacific Time) ("Judging Period").

> Winners Announced: On or around Thursday, December 3, 2026 (12:00 pm Pacific
> Time).

The overview page states the deadline as "Oct 23, 2026 @ 12:00pm PDT".

We submit Thu Oct 22, a day early. That is our choice, not a rule.

---

## 2. Stage One: pass or fail

This is the whole of it. Quoted from the rules page, section 6:

> Stage One) The first stage will determine via pass/fail whether the ideas meet
> a baseline level of viability, in that the Project reasonably fits the theme
> and reasonably applies the required APIs/SDKs featured in the Hackathon.

So Stage One is two questions: does it fit the theme, and does it reasonably
apply the required APIs and SDKs. Everything else that can disqualify a
submission lives in the Project Requirements and Submission Requirements, which
a Stage One reviewer is reading at the same time. Those are below as a
checklist, each line traced to the rule it comes from.

### 2.1 The Fire TV track

Overview page, under "What to Build":

> Fire TV
> Launch a demo-ready app on Fire OS or Vega OS. Use React Native, web
> technologies, or Android (Kotlin/Java), any framework is fine, as long as it
> runs on Fire OS or Vega OS.
>
> Priority categories: AI-enhanced viewing, sports, fitness, family
> entertainment, multi-modal UX, and computer vision.

Rules page, Project Requirements:

> Fire TV: Eligible projects for this category have to launch a demo-ready app
> that works on Fire OS or Vega OS. Priority categories: AI-enhanced viewing,
> sports, fitness, family entertainment, multi-modal UX, and computer vision.

Two of the six priority categories are ours by name: **family entertainment**
and **multi-modal UX**. The rules do not say a priority category is required,
and nothing on either page attaches a score to one.

### 2.2 The runtime technology hook, and why Fire TV is exempt

Rules page, Submission Requirements:

> For Alexa+, Bee, and Ring: The repository must demonstrate use of your track's
> required technology at runtime in your code, imported and actually called (a
> library import, an app/backend entry point, or a loaded agent/flow/MCP
> config), not just named in the README. Fire TV is the exception, see below.

> Fire TV: Any framework or language is acceptable (React Native,
> Android/Kotlin/Java, web technologies, etc.). The requirement is that the
> project runs on Fire OS or Vega OS. The demo video must show the project
> running on an actual Fire TV device or the Fire TV/Vega simulator.

**Read this carefully.** Fire TV entries are exempt from the runtime hook rule.
What Fire TV entries must do instead is **show the project running on an actual
Fire TV device or the Fire TV/Vega simulator in the demo video**. That is the
hard Stage One requirement for our track, and it is a video requirement, not a
code requirement.

Our README's "Required tech at runtime" table goes past what the rules ask of a
Fire TV entry. That is fine and it helps Tech Implementation, but it does not
replace the video.

### 2.3 Stage One checklist

Run this before scoring anything. A no on any line is a fail, with the rule
quoted next to it.

| # | Requirement | Where it comes from | Pass / fail |
|---|---|---|---|
| 1 | The project is a working app that runs on Fire OS or Vega OS | Project Requirements, Fire TV | |
| 2 | The demo video shows it running on an actual Fire TV device or the Fire TV/Vega simulator | Submission Requirements, Fire TV | |
| 3 | The video is less than three minutes, public on YouTube or Vimeo, in English | Submission Requirements, video | |
| 4 | The video carries no third party trademarks and no copyrighted music or footage without permission | Submission Requirements, video | |
| 5 | There is a text description explaining features and functionality | Submission Requirements | |
| 6 | The GitHub repository holds all source code, assets and instructions needed to run the project | Submission Requirements | |
| 7 | The repository is public with a licence detectable and visible in the About box, or private and shared with testing@devpost.com and the named Amazon reviewers | Submission Requirements | |
| 8 | Setup and run instructions are clear, and the project is shown functioning | Project Requirements, Functionality | |
| 9 | Product feedback answers all five questions, for every tool, API and SDK used | Submission Requirements, Product Feedback | |
| 10 | The primary track is named | Submission Requirements | |
| 11 | The mini challenges entered are named | Submission Requirements | |
| 12 | Open Source: contribution URL, project repository URL, GitHub username, and a description of what was done, how it works and why it matters | Submission Requirements, Open Source | |
| 13 | AWS Builder: which AWS services were used and how, inside the Product Feedback answer | Submission Requirements, AWS Builder | |
| 14 | If the project existed before the submission period, what was significantly updated during it is described and demonstrated | Project Requirements, New & Existing | |
| 15 | Third party SDKs, APIs and data are used within their licences | Project Requirements, Third Party Integrations | |
| 16 | Judges can reach the project free of charge, with credentials if anything is private | Testing | |
| 17 | Everything is in English | Language Requirements | |

Line 7 was rechecked on **Thu Oct 1, 2026** against both linked pages. Public
repositories need an open-source licence visible in GitHub's About section.
Private repositories must be shared with `testing@devpost.com` and these Amazon
reviewer accounts: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`
and `emersonsklar`. Add reviewers at submission, then confirm their invitations
are accepted; invitations expire after seven days. The older single-account
reference was replaced by the current list. No repository access was changed.

Line 16 verbatim, because it has a clause about hardware that concerns us:

> The project must be accessible to judges for evaluation (via code repository
> and demo video). Projects do not need to be publicly available to all
> hackathon participants or viewers. If Entrant's website is private, Entrant
> must include login credentials in its testing instructions. The Entrant must
> make the Project available free of charge and without any restriction, for
> testing, evaluation and use by the Sponsor, Administrator and Judges until the
> Judging Period ends. Judges are not required to test the Project and may
> choose to judge based solely on the text description, images, and video
> provided in the Submission.

> If the Project includes software that runs on proprietary or third party
> hardware that is not widely available to the public, including software
> running on devices or wearable technology other than smartphones, tablets, or
> desktop computers, the Sponsor and/or Administrator reserve the right, at
> their sole discretion, to require the Entrant to provide physical access to
> the Project hardware upon request.

A Fire TV stick is widely available, so we read that clause as not applying to
us. That reading is ours, not the rules', and it is worth one line in the
testing instructions saying the app runs on a retail stick.

The last sentence of the first block is the one that should shape our whole
submission: **judges are not required to test anything.** The video and the
written description have to carry the project on their own.

---

## 3. Stage Two: the four criteria

Quoted from the rules page, section 6. The overview page carries the same four
with slightly shorter wording.

> Stage Two) All Submissions that pass Stage One will be evaluated in Stage Two
> based on the following equally weighted criteria (the "Judging Criteria"):

> Entries will be judged on the following equally weighted criteria, and
> according to the sole and absolute discretion of the judges:

**1. Tech Implementation**

> Tech Implementation: How well is the project built, and how effectively does it
> use the required tech? Does it effectively leverage the required APIs, SDKs, or
> device capabilities for the specified track (Fire TV, Alexa+, Bee, or Ring) or
> mini-challenge (AWS Builder, Open Source)?

**2. Design**

> Design: Does the project deliver a complete, coherent product experience? Is
> the interaction model intuitive and well-considered for the target device or
> platform?

**3. Potential Impact**

> Potential Impact: Does the project make a credible, specific case for solving
> customer needs? Could it realistically serve an audience beyond the hackathon?
> (Examples: Fire TV Appstore, Ring Appstore)

**4. Quality of the Idea**

> Quality of the Idea: Is this a creative, imaginative use of the required tools?
> Does the team demonstrate a genuine understanding of the developer ecosystem
> and the end-user needs within their chosen track? Judges should distinguish
> creative ideas from obvious ones:

> Fire TV: Obvious: basic streaming UI, simple video player, remote-controlled
> game. Creative: AI-enhanced viewing that adapts to household patterns, computer
> vision fitness app using the TV camera, multi-modal UX combining voice + D-pad
> + visual in a single flow.

> AWS Builder: Obvious: single Bedrock call for text generation, S3 for storage.
> Creative: multi-service pipeline (Bedrock + AgentCore + Strands), agentic
> architecture with Claude/Kiro for development workflow, agent orchestration
> patterns.

> Open Source: Obvious: README update, typo fix, minor formatting. Creative:
> meaningful feature addition with tests, bug fix that unblocks other developers,
> new integration pattern (e.g., adding Vega support to a popular React Native
> library).

Note the Fire TV example of a creative idea: "multi-modal UX combining voice +
D-pad + visual in a single flow". That is the third thing our one seek function
does, and the submission should say so in those words.

### 3.1 Tie breaking

> For each Prize listed below, if two or more Submissions are tied, the tied
> Submission with the highest score in the first applicable criterion listed
> above will be considered the higher scoring Submission.

So the order matters after all. On a tie, **Tech Implementation** breaks first,
then Design, then Potential Impact, then Quality of the Idea.

### 3.2 The 1 to 5 scale is ours, not Amazon's

**Amazon publishes no numeric scale, no points per criterion and no rubric
bands.** The rules say only "equally weighted" and "the sole and absolute
discretion of the judges", and mention "the submission's final spreadsheet
score" without saying what is in the spreadsheet. Everything in this section is
our own instrument for finding our own gaps.

For our mock judging, score each criterion 1 to 5:

| Score | What it means |
|---|---|
| 5 | Nothing a judge could reasonably ask for is missing. Claims are evidenced and the evidence is reachable in a few clicks. |
| 4 | Strong, with one named gap that does not undercut the main claim. |
| 3 | The case is made but a judge has to take something on trust that could have been shown. |
| 2 | A central claim is unevidenced, or the experience has a hole a judge will hit. |
| 1 | The criterion is not really addressed. |

A score has to come with the sentence a judge would write, and a gap has to name
the file or the field that would fix it.

---

## 4. The friction log bonus, worth up to 10%

Quoted from the rules page, section 6:

> Bonus Points: During Stage 1 downselection, Amazon's internal review team
> assesses each submission's friction log entries (if provided) and passes a
> recommended bonus[,] up to 10%[,] to the Stage 2 judging panel along with the
> shortlisted projects. The Stage 2 panel applies this bonus to the submission's
> final spreadsheet score.

And from the Submission Requirements, the six fields every entry needs:

> Optional, Friction Log Entries: specific task attempted, steps taken, expected
> vs. actual result, severity rating, workaround used, and actionable
> suggestion. Participants who submit friction logs score higher in judging (up
> to 10% bonus).

The overview page says the same in different words:

> Optional: Friction log entries for each one: the task you attempted, the steps
> you took, what you expected vs. what actually happened, a severity rating, any
> workaround you used, and an actionable suggestion. Submissions with friction
> logs can earn up to a 10% judging bonus.

**The six fields, to check each entry against:**

1. The specific task attempted
2. The steps taken
3. Expected result versus actual result
4. A severity rating
5. The workaround used
6. An actionable suggestion

A mock judge should walk `docs/FRICTION_LOG.md` entry by entry and mark any
entry that is missing one of the six. The bonus is assessed at Stage 1 by
Amazon's internal review team, which means it is read by someone doing
downselection at speed, so a missing field in one entry is a real cost.

Feature requests are a separate optional item with three fields:

> Optional, Feature Requests: description, why it matters to their project, and
> priority rating (Critical / Important / Nice-to-have)

No bonus is attached to feature requests anywhere on either page.

---

## 5. The two mini challenges

Overview page:

> Mini Challenges (additional opportunities alongside your primary track)

> AWS Builder
> Use AWS services (Bedrock, AgentCore, Strands SDK, Kiro Crew, SageMaker, etc.)
> in your project with documented integrations, and you're in.
>
> Building with Kiro Crew qualifies on its own, you don't also need to call a
> separate AWS runtime service.

> Open Source
> Ship a new, additional open-source project (include an open-source license) or
> a contribution (a branch, a fork, or a pull request) to a public repository
> during the hackathon window, alongside your primary-track submission. PRs don't
> need to be merged; a forked, unmerged version is fine.
>
> Include the contribution URL, your repo URL, your GitHub username, and a short
> description of what you did, how it works, and why it matters.

Rules page, Project Requirements:

> AWS Builder (Mini Challenge): Any primary track project that incorporates AWS
> services (i.e. Amazon Bedrock, AgentCore, Strands SDK, Kiro Crew, SageMaker,
> etc.) with documented integrations.

> Kiro Crew qualifies on its own as a development tool used during the
> hackathon[,] a submission does not need to also call a runtime AWS service
> (Bedrock, AgentCore, SageMaker, Strands SDK) to count for this mini-challenge.

> Open Source (Mini Challenge): Create a new, additional open-source project or
> contribute to an existing public repository during the hackathon window,
> alongside a primary track submission. Contributions can be a new repo (with
> open-source license), a branch, a fork, or a pull request. PRs do not need to
> be merged; share your forked version if unmerged. Required: contribution URL,
> project repository URL, GitHub username, and a description of what you did,
> how it works, and why it matters.

**Two things to watch on our own entry.**

**AWS Builder says "incorporates AWS services ... with documented integrations".**
The earlier undeployed-stack question was superseded by the saved October 9
deployment and successful preparation run in
[`aws_deploy_2026-10-09.json`](../results/aws_deploy_2026-10-09.json).
The integration prepares and publishes titles; the TV app still plays its
bundled library and does not trust the separate cloud demo key. State that
boundary and the observed results in the submission's AWS services field.
This is evidence of the integration, not a guarantee of a judging outcome.
Credit coverage and current budget visibility still need the billing check in
the completion checklist. Kiro Crew remains unused and must not be claimed.

**Open Source says "new, additional".** Our reading is that the primary-track
repository alone is not the mini challenge entry, and that the upstream pull
request in `docs/OPEN_SOURCE_PR.md` is. That pull request has to exist, from a
fork under a real account, inside the hackathon window, which is why STATUS.md
dates it Mon Oct 12. The rules are explicit that it does not have to be merged.

Overview page, on winning:

> You can layer a mini challenge onto the same project for extra ways to win, but
> each project can only win one track prize and one mini challenge prize.

---

## 6. The submission form, field by field

From the Submission Requirements on the rules page. Our copy for each field is
in `docs/SUBMISSION.md`, which is Lane H's file.

| Field | What the rules ask for |
|---|---|
| Text description | "a text description that should explain the features and functionality of your Project" |
| Repository URL | GitHub, all source, assets and run instructions; public with a visible licence, or private and shared with testing@devpost.com and the named Amazon reviewers |
| Demo video URL | Under three minutes, YouTube or Vimeo, public, English, shows the project on the device |
| Product feedback | The five questions below, for every tool, API and SDK used |
| Track | Fire TV |
| Mini challenges | Open Source, AWS Builder |
| Open Source fields | Contribution URL, project repository URL, GitHub username, description of what, how and why |
| AWS Builder | Which AWS services and how, inside the product feedback answer |
| Feature requests | Optional. Description, why it matters, priority |
| Friction log | Optional. Six fields per entry, up to a 10% bonus |

The product feedback questions, verbatim:

> Which developer tools, apis and SDKs did you use and for what?

> What worked well? (i.e. setup, documentation, docs, testing, performance,
> reliability)

> What needs work? (i.e. system errors, docs sections, missing features,
> compatibility issues, tool limitations, required workarounds)

> How was your onboarding experience (getting from zero to hello world)

> Would you build with these devices and services again? Yes/No and please tell
> us why

That last one is a yes or no question and it needs an explicit yes or no in the
answer.

---

## 7. Rules that shape how we build, not just how we submit

**Original work, and open source inside it.** Rules page, Intellectual Property:

> An Entrant may submit a Submission that includes the use of open source
> software or hardware, provided the Entrant complies with applicable open source
> licenses and, as part of the Submission, creates software that enhances and
> builds upon the features and functionality included in the underlying open
> source product.

Our `app/` is derived from AmazonAppDev/vega-video-sample under MIT-0, and the
whole point of the entry is what we added on top of it. That is the shape the
rule describes. The licence files and the credit have to stay where they are.

**New and existing.** Rules page, Project Requirements:

> New & Existing: Projects must be either newly created by the Entrant or, if
> the Entrant's Project existed prior to the Hackathon Submission Period, must
> have been significantly updated after the start of the Hackathon Submission
> Period. Entrants must explain how their Project was significantly updated,
> clearly describe and demo the feature updates during the Submission Period.

Calm Frames was started inside the window, so this does not bind us. The
derivation from the sample app is worth naming anyway, in the description as
well as the licence table, so nobody has to wonder.

**Functionality.** Rules page, Project Requirements:

> Functionality: The Project's code repository must include clear setup and run
> instructions, and the Project must be shown functioning in the demonstration
> video, as depicted in the video, URL and/or expressed in the text description.

---

## 8. What this page could not verify

Said plainly, rather than guessed at.

1. **There is no published numeric scale, no points per criterion and no score
   bands.** The rules say "equally weighted" and refer to a "final spreadsheet
   score" without describing it. Our 1 to 5 scale in section 3.2 is our own.
2. **How the 10% friction log bonus is computed is not published.** The rules
   say Amazon's internal review team "assesses each submission's friction log
   entries" and "passes a recommended bonus". What makes a log worth 10% rather
   than 3% is not stated anywhere on either page.
3. **Whether a synthesized but undeployed CDK stack counts for AWS Builder is
   not answerable from the page.** See section 5. This one has a cost attached
   and should go to the hackathon manager as a question.
4. **The judges are not named.** The overview page says "A qualified panel of
   judges will be announced soon!" and the rules say judges "may or may not be
   listed individually on the Hackathon Website, and may change before or during
   the Judging Period", so we cannot know whether an accessibility specialist,
   or anyone with clinical knowledge, will read our claims. We should write for
   a reader who has neither.
5. **Whether a priority category matters to a score is not stated.** The six
   Fire TV priority categories are listed as priorities, and no criterion
   mentions them.
6. **Nothing on either page says how the project gallery, likes or any public
   vote affect judging.** As far as both pages go, they do not.
7. **The Stage One reviewer's identity is only partly described.** The rules say
   judging "may utilize expert panels, peer review, automated AI-driven
   analysis, or any combination thereof", so part of Stage One may be automated.
   A submission that only makes sense to a careful human reader is a risk.

---

## 9. How to use this file

`docs/MOCK_JUDGE_1.md` and `docs/MOCK_JUDGE_2.md` are two runs of this rubric
against the repository by judges who did not write any of it. Each one runs the
Stage One checklist in section 2.3, scores the four criteria in section 3 on the
1 to 5 scale in section 3.2, walks the friction log against the six fields in
section 4, and ends with a ranked list of gaps.
