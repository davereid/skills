---
name: credit-audit
description: Find fixed drupal.org issues where you're missing contribution credit.
---

# Credit audit

Checks recently closed drupal.org work items for contribution records that are missing, still drafts, or don't credit the user, and shows what the user did on each so they can fix the records.

Arguments: the user's drupal.org username, the projects (machine names, e.g. `helper`) or a directory of project checkouts, and optionally how many days back to look (default 14).

## Rules

- **Read only.** Only maintainers and collaborators can edit a contribution record, and only in the browser, so the user sets credit and finalizes records themselves. Don't post comments or change issues.
- **Only fixed work counts.** An issue needs credit when it was fixed: a `state::fixed` label, or a merged merge request. Issues closed as won't fix, outdated or duplicate don't.

## 1. Run the scan

```sh
python3 scripts/credit_audit.py --user <username> [--days 14] [--checkouts <dir>] [<project> ...]
```

It needs `glab` signed in to `git.drupalcode.org`. Projects still on drupal.org's issue queue are skipped and named on stderr: say which ones weren't checked. A scan of many projects takes several minutes, so run it in the background if the agent can.

Each output row is tab-separated: project, issue, problem (`no record`, `draft`, `not listed`, `not credited`), record nid, merged merge requests, the user's part, and title.

## 2. Sort the results

Sort the rows into three tables:

1. **Missing credit for the user's own code:** the user wrote a merged merge request or has commits in one, and the record doesn't credit them.
2. **Records to finish:** no record yet, or a draft.
3. **Your call:** the user only commented, reviewed or merged someone else's work. Credit for reviews and merges is the maintainer's judgment.

Leave out rows where the user took no part (`-`), and say how many there were.

For each row, link the issue (`https://git.drupalcode.org/project/<project>/-/work_items/<nid>`) with a few words on what it is, the user's part, and the action:

- To credit or finalize: `https://new.drupal.org/contribution-record/<record nid>`
- To create a missing record: `https://new.drupal.org/contribution-record?source_link=<issue URL>`

Say that on projects the user doesn't maintain, a maintainer has to set the credit.

## 3. Check unexpected states

If an issue looks closed by mistake, such as a release plan that's still in progress, point it out rather than reopening it.
