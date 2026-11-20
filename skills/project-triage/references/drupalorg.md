# drupal.org

Host details for `project-triage` on drupal.org projects. Their code and merge requests are on drupal.org's GitLab (`git.drupalcode.org`), so use `gitlab.md` for everything, with the changes below. Sections named like `gitlab.md`'s replace or add to them; the others are drupal.org only. Also uses the [drupalorg CLI](https://github.com/mglaman/drupalorg-cli) (`drupalorg`) where it covers something.

## Who and where

- The remote is either SSH (`git@git.drupal.org:project/<name>.git`, usual for maintainers) or HTTPS (`https://git.drupalcode.org/project/<name>.git`, usual for everyone else). Either way the API host is `git.drupalcode.org`: always use `--hostname git.drupalcode.org` and `-R https://git.drupalcode.org/project/<name>`.
- The project path is `project/<name>` (`:id` is `project%2F<name>`). If the remote is an issue fork (`issue/<name>-<nid>`), triage `project/<name>`, where its MRs and issues live.
- If `glab` run inside a checkout with the SSH remote says no remote points to a known GitLab host, it needs `glab config set api_host git.drupalcode.org --host git.drupal.org`. Passing `-R` and `--hostname` as above avoids that.
- `$ME` is the user's GitLab username on `git.drupalcode.org`, which follows their drupal.org username.

## Ownership

Owned when the user's access level on `project/<name>` is Maintainer (40) or higher: drupal.org gives that to the project's maintainers with write access to the repository. Personal namespaces and direct members below Maintainer don't apply. Maintainers without repository access don't get it, so they don't count: say so if the user expected the project to be theirs.

## Two kinds of issue tracker

Check the project's `issues_enabled` (`glab api --hostname git.drupalcode.org "projects/project%2F<name>"`):

- **true:** the project's issues moved to GitLab work items (`https://git.drupalcode.org/project/<name>/-/work_items/<nid>`). The work item's `iid` is the drupal.org issue number (nid). Use `gitlab.md`'s issue commands.
- **false:** issues are still in drupal.org's issue queue (`https://www.drupal.org/project/issues/<name>`), as for Drupal core. The GitLab issue API returns nothing for them. Read them with `drupalorg` instead (below). Writing isn't possible from here.

## Issue status

drupal.org issues have a status, which says whose turn it is. Show it in the issue tables, and use it on top of the comment-based A/B rules:

- Work items carry it as a scoped label (`state::needsReview`, `state::rtbc`, `state::needsWork`, `state::postponed`, `state::toBePorted`, …; _Active_ is `state::accepted`, e.g. on issues migrated as _Active_). Category and priority are `category::…` and `priority::…` labels.
- Issue-queue projects: `field_issue_status` numbers. Open ones: 1 _Active_, 8 _Needs review_, 13 _Needs work_, 14 _RTBC_, 4 _Postponed_, 16 _Postponed (maintainer needs more info)_, 15 _Patch (to be ported)_.

In an owned project, _Needs review_ and _RTBC_ issues are listed as B even if the user has commented, when there's no comment from the user since the status changed: they're waiting on the maintainer. _Needs work_ and _Postponed_ issues whose latest comment is the user's stay hidden.

Sort every table by status first: _RTBC_, then _Needs review_, then the rest, most recently updated first within each. An MR takes its issue's status, so an MR whose issue is _RTBC_ comes first among the PRs too. Show the status in each row.

## Migrated issues

Issues migrated from drupal.org's issue queue to work items are authored by `drupalbot` on GitLab. Find who really opened them, and when, before classifying:

- **Reporter:** the description's `Reported by: [<name>](https://www.drupal.org/user/<uid>)` line. Use it as the issue's author for skipping the user's own issues and for `exclude.authors`. Compare the drupal.org user ID with the user's (their drupal.org profile URL), not the name: the display name ("dave reid") differs from the GitLab username (`davereid`).
- **Comments:** migrated comments keep their real GitLab authors, but `created_at` is the migration time. The original date is in the `_Migrated from comment #N posted <date>_` line: show that date, and say that "last updated" on migrated issues reflects the migration.
- **Ignore** `drupalbot`'s "Issue tools" notes and `System_Message` commit notes when finding the latest comment.

## Merge requests belong to issues

drupal.org MRs are made from issue forks (`issue/<name>-<nid>`, source branch `<nid>-<slug>`) and the issue is where the discussion and status live. MR reviewers and approvals are rarely used.

- List the project's open MRs as in `gitlab.md` (they target `project/<name>`), and find each one's issue from its source project or branch.
- An MR and its issue are excluded together: when the profile's `exclude` drops either one (e.g. the issue's `v7.x-*` version label, or the MR's `7.x-*` target branch), drop both.
- When an MR's issue is also in the triage list, show the MR in that issue's row (MR number, pipeline state) instead of a separate PR row, and handle them together: the PR summary steps for the code, the issue steps for the reply.
- "The user's latest review" includes their latest comment on the issue, not only notes on the MR.
- Pipeline state and failed jobs: `drupalorg mr:status 'project/<name>!<iid>'` and `drupalorg mr:logs 'project/<name>!<iid>'` (quote it in zsh).
- MR titles: use drupal.org's commit message header, `<type>: #<issue nid> <one-line summary>` (e.g. `fix: #3354345 Pathologic breaks srcset when used with multipliers`), with type `fix`, `feat`, `ci`, `docs`, `perf`, `refactor`, `test`, `task` (not `chore`) or `revert` ([format](https://www.drupal.org/node/3586390)). The contribution record suggests the commit message but not its type, so a title in this format gives the maintainer the whole header. When an MR's title doesn't follow it, suggest one; in an owned project offer **Retitle** (see "Actions"). The format is core's: for a contrib project whose history uses another format, follow its history.
- `--mine`: the user's own MRs as in `gitlab.md`; also show the issue's status, since _Needs work_ set by someone else means feedback is waiting.

## Contribution records

Each issue has a contribution record on `new.drupal.org`, listing who gets credit. Read it with the public JSON:API in two calls. First find the record's nid: `curl -sS -G -H 'Accept: application/vnd.api+json' "https://new.drupal.org/jsonapi/node/contribution_record" --data-urlencode "filter[field_source_link.uri]=https://git.drupalcode.org/project/<name>/-/work_items/<nid>" | jq '.data[].attributes.drupal_internal__nid'`. Then read it with `--data-urlencode "filter[nid]=<record nid>" --data-urlencode "include=field_contributors,field_contributors.field_contributor_user"`. Adding `include` to the URL filter returned no record for a draft (2026-11-18, embed #3612594). Don't look a record up by `https://www.drupal.org/node/<nid>`: a work item created on GitLab has an iid that can match an unrelated drupal.org node, which has its own record. Each `paragraph--contributor` has `field_credit_this_contributor` and a `field_contributor_user` (its `display_name`); `field_draft` true means it isn't finalized.

In an owned project's MR summary, and before every merge, show a table of everyone who took part: issue commenters, commit authors on every MR for the issue (including closed ones it replaces) and reviewers, with what each did and a credit recommendation (Yes, No, or "Your call" with a reason). Alert the user to anyone who contributed but isn't credited (the user decides; `System Message` is never credited). Only the project's maintainers and collaborators can edit the record, at `https://new.drupal.org/contribution-record/<record nid>`, so setting credit and finalizing it is a manual step for the user. Its "Git commit message" is built in the browser and can't be read from the API.

Before closing an issue as a duplicate, or an MR whose issue was fixed elsewhere, compare its contributors (MR authors, reviewers, useful commenters) with the record of the issue where the fix landed. Tell the user who isn't credited there, and whether the committed fix used their work. The user decides. A finalized record can still be edited, but the commit message stays as it was (2026-11-18: embed !20 and !21 on #3462292, a duplicate of #3430097).

## Change records

Owned projects only. Change records are often left as drafts after the change ships. List them with `curl -sS "https://www.drupal.org/api-d7/node.json?type=changenotice&field_project=<project nid>&limit=50"` (the project nid is `list[0].nid` from `https://www.drupal.org/api-d7/node.json?field_project_machine_name=<name>`). A record is a draft when `field_change_record_status` is false; `field_change_to` is its version and `field_issues[].id` its issues. In step 5, add a **Draft change records** table (nid, title, version, created) for drafts whose version has been released (see "Supported branches"), or whose issues are fixed. When an A or B MR's issue has a draft record, mention it in the summary. Drupal.org has no API for editing them: draft corrections as HTML for the user to paste at `https://www.drupal.org/node/<nid>/edit`, where they also publish it.

## Issue-queue projects (`issues_enabled` false)

- List: `drupalorg project:issues <name> all --limit 100 --format=json 2>/dev/null` (`nid`, `title`, `field_issue_status`). It doesn't return authors, assignees or comments.
- The list can return fewer issues than are open (2026-11-18: 50 for entity_embed, without the open _Needs review_ #3531672). Also read the issue of each open MR whose nid isn't in the list, and say the list may be incomplete.
- Owned projects only: keep the open statuses, then read each with `drupalorg issue:show <nid> --with-comments --format=llm` to classify it. That's one call per issue: say how many, and ask first if it's more than about 20.
- Projects the user doesn't own, such as Drupal core: their issue queues are too big to read. Only triage MRs the user commented on (from `gitlab.md`'s events search), and say issues aren't covered there.
- `drupalorg` can't comment or change statuses: draft the comment and the new status, and give the user the issue link to post it themselves.

## Searching upstream

For any drupal.org project. Drupal core (`drupal/core`, `web/core`) is the project `drupal`; a `drupal/<name>` package, or code under `modules/contrib/<name>` or `themes/contrib/<name>`, is the project `<name>`.

Searching needs no login or extra tools: the `curl` commands below read public pages and APIs, so they also work when the user's own project is on another host and `glab` or `drupalorg` isn't set up. To tell which tracker a project uses without a login (the API leaves out `issues_enabled` then): `curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' https://www.drupal.org/project/issues/<name>` redirects (301) to `git.drupalcode.org/project/<name>/-/work_items` for work-item projects, and returns 200 for projects still on drupal.org's queue.

- Issue-queue projects (such as core): drupal.org's issue search, which matches words anywhere in the title, in any order: `curl -sSL -G "https://www.drupal.org/project/issues/<project>" --data-urlencode "text=<words>" --data-urlencode status=All | grep -oE 'href="/project/<project>/issues/[0-9]+"[^>]*>[^<]+'`.
- Work-item projects: `gitlab.md`'s "Searching upstream" (`:id` is `project%2F<name>`), which also searches descriptions.
- `drupalorg issue:search <project> "<words>" --limit 50 2>/dev/null` covers both, but only finds exact phrases, and smaller `--limit` values miss matches (drupalorg 0.11.0: `--limit=10` missed an issue that 20 and 50 found). Use it only for an exact identifier, such as a function name, and don't treat an empty result as "no issue".
- Use two or three distinctive words (a class or function name, a key phrase from the error), and try several.
- Read a candidate with `drupalorg issue:show <nid> --with-comments --format=llm`.
- Commenting upstream: work-item projects as in "Actions", which needs `glab` logged in to `git.drupalcode.org`; issue-queue projects (such as core), or without that login, give the user the text and the issue link.

## Supported branches

`drupalorg project:releases <name>` lists the latest release of each supported branch (e.g. `2.1.0`, `8.x-1.51`, `7.x-1.9` → `2.x`, `8.x-1.x`, `7.x-1.x`).

## Closing keywords

drupal.org MRs come from issue forks, but the work item is in `project/<name>`, so `Closes #<nid>` works; the full form `Closes https://git.drupalcode.org/project/<name>/-/work_items/<nid>` is clearer. Take `<nid>` from the source branch (`<nid>-<slug>`). When a merge doesn't close the work item (no closing reference, or merged into a non-default branch such as `8.x-1.x`), close it as in "Actions" ("Fixed by a merge").

Project Update Bot issues (reported by `project update bot`, e.g. "Automated Drupal 12 compatibility fixes for <name>") stay open after a merge: the bot keeps posting new fixes to them as its rules change. Don't set `state::fixed` or close them, and don't flag an MR for lacking a closing reference to one. Refer to it with "Related to" instead of `Closes`, which would close it on a merge into the default branch (2026-11-18, embed #3606280). After a merge that covers the bot's fixes, read the issue and its MRs again. Offer to close the bot's MR the merge superseded. When no open MR is left, offer to move the issue to _Active_ (`state::accepted`) with a comment linking the merged MR, so it waits for the bot's next fixes. If a merge already closed the issue, offer to reopen it (`glab issue reopen`) as well.

## Actions

### Issue status and metadata

After each action, update the issue to match, and show the change alongside the action:

- Status: opening an MR or pushing a fix → _Needs review_; a review that asks for changes, or a pipeline failing on the MR's own changes → _Needs work_; a new MR replacing a reviewed one → _Needs review_, even if the issue was _RTBC_; blocked on another issue → _Postponed_, with a comment linking it; merged → _Fixed_.
- Metadata: the version matches the MR's target branch (e.g. `8.x-1.x-dev`); the category (bug report, feature request, task) matches the change; the component fits the code it touches; the priority fits the impact; the title describes the problem; tags are added or removed as the work changes. Use drupal.org's [special tags](https://www.drupal.org/docs/develop/issues/fields-and-other-parts-of-an-issue/issue-tags-special-tags) where one fits, spelled exactly as that page lists them, such as "Needs tests", "Needs change record", "Needs release note", "Needs issue summary update", "Needs title update", "Needs manual testing", "Needs screenshots", "Needs reroll", "Needs upstream bugfix", "Regression", "API addition", "API change", "JavaScript", "Accessibility" and "Novice", rather than inventing one. The core committer review tags (such as "Needs framework manager review") are for core only.
- Read the current values first, and don't lower _RTBC_ or change a priority someone else set without saying why.
- Work items carry these as labels: `state::…`, `category::…`, `priority::…`, unscoped version labels (`v8.x-1.x-dev`), and component and tag labels. Set them as in "Work items" below. Issue-queue projects can't be updated with `drupalorg`: list each change as a step for the user, with the issue's full URL.

### Merge requests

As in `gitlab.md`, plus:

- Rebase: when an MR the user approves, retargets or wants to merge has `detailed_merge_status` `need_rebase` and `has_conflicts` false, offer **Rebase** with `gitlab.md`'s command. It rewrites the issue fork's branch (like a force-push), so ask first. Issue forks only accept pushes from accounts that requested push access on that issue, whatever "Allow commits from members" says: a `403 Cannot push to source branch` means the user hasn't. Offer `drupalorg issue:get-access <name>#<nid>` (it posts a public `/do:access` comment, so show it and ask first), or the issue page's **Get push access** button, then retry. The rebase may reset approvals: check them before saying the MR is ready to merge.
- Retitle: `glab mr update <iid> -R <repo> --title "<title>"`, shown first.
- Merge (only when the user asks): first have the user review and finalize the contribution record (see "Contribution records") and copy its "Git commit message". Its first line comes from the issue's title, so replace it with the MR's title when that's the better summary (e.g. a Conventional Commit title), keeping the `By:` credit lines after a blank line. Merge with that message: `glab mr merge <iid> -R <repo> --squash --squash-message "<message>"` (or `--message` without squashing). Check `gitlab.md`'s "Merge" first: in a fast-forward-only project, an MR behind its target needs **Rebase** (above), which rewrites the issue fork's branch. If the user can't edit the record, say so and leave the merge to a maintainer. Merge trains block this: with them on, the merge API refuses the MR (405) and the merge train API takes no squash message, so the record's credit lines can't be set without rewording the MR's commit and force-pushing it. If the project has merge trains on, suggest turning them off in its merge request settings.

### Work items

- Comment: `glab issue note <nid> -R https://git.drupalcode.org/project/<name> -m "<text>"`.
- Change status: drupal.org changes labels through `/do:` commands in comments. `drupalorg issue:label <nid> state::needsWork` posts one (the new `state::` label replaces the old one). Offer **Comment and set status** alongside **Comment**, with the new status shown first.
- Upstream issue not confirmed yet: `state::postponed` with a comment linking it.
- Close: set the closing state with a reason, e.g. `drupalorg issue:label <nid> state::closed why::duplicate` (reasons: `why::duplicate`, `why::wontFix`, `why::worksAsDesigned`, `why::cannotReproduce`, `why::outdated`, `why::needsInfo`), or `state::fixed`. Not verified: check the label changed afterwards, and if it didn't, give the user the link to change it.
- Fixed by a merge: set `state::fixed`, and close the work item with `glab issue close <nid> -R https://git.drupalcode.org/project/<name>` when the MR didn't (no closing reference, or merged into a non-default branch such as `8.x-1.x`). It keeps the `state::fixed` label (helper #3247948, 2026-11-13). For other closing reasons, use the `state::closed why::…` labels above.

## Security

- Published advisories: `https://www.drupal.org/security` (core and contrib).
- Private reports go to the Drupal Security Team: `https://www.drupal.org/drupal-security-team/security-team-procedures` explains how. Its process covers projects with security advisory coverage; for projects without it, say what the project page says about coverage and let the user decide.

### Private security issues

Owned projects only. Each report is a private project, `security/<nid>-<name>-security`: the security team's private fork of the project, whose one issue, `issues/1`, holds the discussion. Only the project's maintainers and the security team can see them, and maintainers get Developer access, so they can push branches and open MRs there.

- List: `glab api --hostname git.drupalcode.org "groups/security/projects?search=<name>-security&simple=true&per_page=100"`, and keep only paths matching `security/<digits>-<name>-security` exactly: the search matches substrings, so `embed` also returns `url_embed` and `entity_embed`. An empty list means no reports, or no access: say that it can't tell which.
- For each, read `projects/security%2F<nid>-<name>-security/issues/1` and keep the open ones. Read its `/notes` (skip `system` notes) to classify it as in step 4: `security-team-bot`'s "no activity" reminders and comments addressed to the maintainers count as waiting on the user. Its `Security status::…` label (e.g. `postponed`) is its status.
- In step 5, show a **Private security issues** table first, above the others: link, title, status, last updated, who commented last, and whether it waits on the user. Flag "no activity" reminders: the team marks a project unsupported when they go unanswered. Say how many closed ones were skipped.
- Coordinated disclosure: never quote these issues or describe the vulnerability in drafts for public issues, MRs, commit messages or public issue forks. Before acting on a public issue or MR that touches the same code, say whether it could disclose the report (e.g. a public fix for it), and suggest raising it in the private issue first. Don't commit a fix to the project until the security team says so.
- Fix branches go to the private project (e.g. a `security` remote, `git@git.drupal.org:security/<nid>-<name>-security.git`), never to `origin` or a public issue fork. The private project's branches can lag the public ones: base fix branches on the public branch, and check the MR's commit list before opening it.
- Comment: `glab issue note 1 -R https://git.drupalcode.org/security/<nid>-<name>-security -m "<text>"`, shown first, as for any comment.

## AI disclosure

drupal.org's [AI policy](https://www.drupal.org/docs/develop/issues/issue-procedures-and-etiquette/policy-on-the-use-of-ai-when-contributing-to-drupal) requires disclosing significant AI-generated text or code in issues and MRs. When a draft comment is more than a short reply, remind the user before posting that they should rewrite it in their own words, or add a disclosure naming the tool and what it produced.

## Token permissions

Same as `gitlab.md`: a `git.drupalcode.org` personal access token with `read_api` to triage, and `api` to comment or post `/do:` commands. `drupalorg` reads drupal.org's public API and needs no token.
