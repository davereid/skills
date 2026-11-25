---
name: thank-contributors
description: Thank contributors on merged issues and say which release has the fix.
---

# Thank contributors

After a pull request or merge request is merged in a project you maintain, drafts a short comment on its issue that thanks the people who worked on it and says where the fix went and when it ships. Nothing is posted until you approve it.

Arguments: a PR, MR or issue reference, a project, or nothing (the current repository).

## 1. Find the merges

- **A reference:** that merge, and the issue it closes.
- **A project, or nothing:** the PRs or MRs merged since the latest release tag of the branch they target, which are the fixes that aren't released yet. Fixes that are already in a release are covered by its release notes, so skip them.
  - GitHub: `gh pr list --state merged --base <branch> --search "merged:>=<tag date>"`.
  - GitLab, including drupal.org's `git.drupalcode.org`: `glab api "projects/<id>/merge_requests?state=merged&target_branch=<branch>&updated_after=<tag date>"`. Find each MR's issue from its title (`fix: #<number> …`) or its `Closes` or `Issue:` line.

## 2. Decide who to thank

For each merge, list everyone who took part in the PR or MR and its issue: the issue's author (on issues migrated from drupal.org, the "Reported by" line), the PR or MR author, commit authors, reviewers and commenters.

- Leave out yourself (the logged-in user) and bots, such as Renovate, Dependabot, Project Update Bot, `drupalbot` and System Message.
- Skip the merge when nobody is left, or when a comment after the merge already said it was merged.
- Thank each person for what they did: the code, a review, testing, or a report that shaped the fix. Someone who only asked about progress gets thanks for their patience.

## 3. Say when it ships

Name the branch the fix was merged into, then:

- **In a milestone:** link it: "is on track for [2.4.0](<milestone URL>)". If the milestone has a due date, add "planned for release around December 19", in your timezone. Never guess a date.
- **In a release plan issue instead:** link that issue the same way.
- **Otherwise:** "and will be included in the next release".

## 4. Draft

Write one or two sentences in a kind, encouraging maintainer voice, mentioning each person by handle:

> Thanks @alice for reporting this and @bob for the fix! This is now merged into the 2.x branch and is on track for [2.4.0](https://example.com/milestones/3), planned for release around December 19.

- In projects with several maintainers, write the maintainers' next steps as "we".
- Don't restate the change, hedge or add a summary.
- Don't add AI attribution or a disclosure: the thanks is the maintainer's own.
- Post once per merge: on the issue if there is one, otherwise on the PR or MR.

## 5. Ask, then post

Show the drafts in a table: the issue or PR (as a link), the people thanked, and the comment. Ask which to post, allowing several at once, and post only those.

- GitHub: `gh issue comment <number> --body <text>`, or `gh pr comment`.
- GitLab: `glab api -X POST "projects/<id>/issues/<iid>/notes" -f body=<text>`, or `.../merge_requests/<iid>/notes`.
- drupal.org projects still on the drupal.org issue queue can't take comments through an API: give the user each comment with the issue's URL to post themselves.

To change a comment that's already posted, edit it rather than posting a new one: an edit doesn't notify people again.

## 6. Report

List the posted comments with links, and the skipped merges with the reason for each.
