# Draft: two questions for the organizers, and a list for Office Hours #2

Written Fri Oct 9, 2026, for Alex to send or post. Nothing here is sent by Claude. The same two questions go out once, by email or on the Devpost forum, and section 3 says how to choose. Section 4 is the list for Office Hours #2 on Mon Oct 19.

## 1. Email to the hackathon manager

**To:** janet@devpost.com

**Subject:** Two mini challenge questions from a Fire TV entry (Calm Frames)

---

Hi Janet,

I am Alex, entering the Fire TV track with Calm Frames, a Vega app for families of children with photosensitive epilepsy. I have two questions about the mini challenges.

1. AWS Builder. Our AWS CDK pipeline is deployed and prepares videos before they reach the app. An S3 upload starts a Lambda function, which runs our analyzer on ECS Fargate from an image in ECR. The task signs the result with a key kept in SSM Parameter Store under KMS, records the title in DynamoDB and publishes the checked copy behind CloudFront, with an AWS Budgets alarm on the spend. One calm test clip has gone through it, from upload to a signed, verified copy. The TV app itself does not call AWS, and we use none of the AI services the rules list as examples. Does this count as a project that "incorporates AWS services ... with documented integrations"?

2. Open Source. We plan to open a pull request to AmazonAppDev/vega-video-sample that fixes a hang: when a Shaka load fails, the sample stays on its buffering spinner and never shows an error. Can that pull request be our contribution URL, with our main repository as the project repository URL, even though the main repository is open source as well (Apache-2.0)?

Thank you for your help.

Alex

---

## 2. The same two questions as a Devpost forum post

Post it in the hackathon's Discussions tab.

**Title:** AWS Builder and Open Source: two eligibility questions from a Fire TV entry

---

Hi all, two questions about the mini challenges from a Fire TV track entry. If they have been answered before, a link is plenty.

1. AWS Builder. Our AWS CDK pipeline is deployed and prepares videos before they reach the app. An S3 upload starts a Lambda function, which runs our analyzer on ECS Fargate from an image in ECR. The task signs the result with a key kept in SSM Parameter Store under KMS, records the title in DynamoDB and publishes the checked copy behind CloudFront, with an AWS Budgets alarm on the spend. One calm test clip has gone through it, from upload to a signed, verified copy. The TV app itself does not call AWS, and we use none of the AI services the rules list as examples. Does this count as a project that "incorporates AWS services ... with documented integrations"?

2. Open Source. We plan to open a pull request to AmazonAppDev/vega-video-sample that fixes a hang: when a Shaka load fails, the sample stays on its buffering spinner and never shows an error. Can that pull request be our contribution URL, with our main repository as the project repository URL, even though the main repository is open source as well (Apache-2.0)?

Thanks,
Alex

---

## 3. Before sending

- **Which channel.** One is enough to start with. A forum answer is public, so docs/SUBMISSION.md can link it and other entrants with the same question see it; Janet answers forum topics as the Manager (topic 45310 is one). An email gets a private answer. If there is no answer in three days, try the other channel, and take whatever is still open to Office Hours on Oct 19.
- **The address.** janet@devpost.com is the "Email the hackathon manager" link at the foot of the hackathon's overview page, checked against a copy of that page saved Oct 8. The forum shows her as Janet Fang, Manager.
- **The rule text.** Question 1 quotes the rules page, checked against a copy saved Oct 8. Open the live page before sending and check it still reads: "Any primary track project that incorporates AWS services (i.e. Amazon Bedrock, AgentCore, Strands SDK, Kiro Crew, SageMaker, etc.) with documented integrations."
- **The stack.** Question 1 says the stack is deployed and that one calm test clip went through it. Check both are still true on the day you send it. If the Harbor story has gone through it by then, say that instead of the test clip.
- **The pull request.** If it is open by then, change "We plan to open a pull request" to "We opened a pull request" and add its URL.
- **No account details.** No account ID, bucket names, CloudFront domain, ARNs or registry URI, in the email or the post.
- **Nothing that has not happened.** We have not used Kiro Crew or Bedrock, and nothing here may suggest we have.

## 4. Office Hours #2

Mon Oct 19, 9:00 to 10:00 AM PT. Register at https://amazon.zoom.us/webinar/register/WN_kh9CSYi0QtuN31d8nsTuOQ, the link in the Office Hours Schedule post on the hackathon's Updates page.

Ask in this order, and skip any question the email or the forum has already answered:

1. **AWS Builder.** Does a deployed AWS pipeline with no AI services count, when it prepares videos before they reach the app and the TV app itself does not call AWS? Ours uses S3, Lambda, ECS Fargate, ECR, SSM Parameter Store with KMS, DynamoDB, CloudFront and AWS Budgets.
2. **Open Source.** Can the contribution URL be our pull request to AmazonAppDev/vega-video-sample, with our open-source main repository as the project repository URL?
3. **Fire TV screens in the demo.** We film the demo on a Fire TV stick, so Fire TV system screens such as the Alexa voice overlay can appear. Is that fine under the rule against third-party trademarks, or should we keep system screens out of the shot?
4. **An AI voice.** Is a clearly disclosed AI narration voice acceptable for part of the demo video, with the first and last lines in my own voice?
5. **How judges try it.** Do judges sideload a Release package on a Fire TV stick, use the Vega Virtual Device, or mostly go by the video and the repository? We plan to attach Release packages for armv7, aarch64 and x86_64 with SHA-256 checksums.

## 5. When an answer comes

An organizer's answer is a ruling about the rules, not feedback on the project, so it does not go in docs/VALIDATION.md. Record what was said, who said it and the date in docs/DECISIONS.md, and in docs/SUBMISSION.md section 11 (AWS Builder) or section 12 (Open Source). Link a forum answer; for an email or Office Hours answer, give the date and the channel and keep the summary to what was said.

## Rules these drafts have to keep

- The same two questions in the email and the forum post.
- No AWS account details anywhere.
- No claim about anything that has not happened.
- No em dashes or en dashes, and none of the banned words under Style in CLAUDE.md.
