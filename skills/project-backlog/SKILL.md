---
name: project-backlog
description: Move local backlog notes into PR or MR tasks and issues.
---

# Project backlog

Moves the work in a checkout's local notes, such as a backlog file that isn't committed, into places others can see and that last: an open PR's or merge request's remaining tasks, an existing issue, or a new one. What can't go public stays local.

Arguments: nothing (the current checkout), or the path of the notes file.

## 1. Gather

- **Notes:** the local backlog file the user's instructions name (e.g. `BACKLOG.local.md` at the project root), and the current-work section of their project-local notes file, if any. If no file is named and none is given, ask.
- **Host:** from the `origin` remote (GitHub, GitLab, drupal.org). Use its CLI (`gh`, `glab`) or API to read and write PRs, MRs and issues. If `project-triage` is installed, its `references/<host>.md` has the commands.
- **Maintainer check:** confirm the user maintains the project: they can merge to the default branch, or the project lists them as a maintainer. If not, say so and stop: other people's projects keep local notes, or get issues filed by hand.
- **Open PRs/MRs:** list them with their branches and authors. Only those the user opened, or is pushing commits to, can take remaining tasks.
- **Local branches:** `git branch` and each branch's upstream, to match notes that name a branch.

## 2. Sort

Read each item (a bullet with its sub-bullets, or a section that's one piece of work) and put it in one group:

- **PR/MR task:** the item is work left on a branch that has an open PR or MR the user owns. Draft it as a `- [ ]` item for the description's `## Remaining tasks` section.
- **Existing issue:** search the project's issues (open and closed) for the item's key words, classes and methods first. If one covers it, link it. If the item adds something, draft a comment for it.
- **New issue:** draft a title (the project's format) and a short description: the problem or idea, the code it's about, and the suggested approach from the note.
- **Keep local:** the item names a client, a client project or its content (titles, domains, people), is about the user's own setup, is too vague to act on, or is upstream work in another project. Give the reason. Upstream items can become issues in that project: suggest it, but don't file there without asking.
- **Outdated:** the code or a merged PR already does it. Say what shows that (a commit, a method, a merged PR).

Check every draft for client names and details before it goes in the plan: public text must not have them.

## 3. Plan

Show the plan as one table per group: the item (a few words), where it goes, and the draft text or reason. Then ask which to apply, per group (multi-select, with "none"). Change drafts the user edits. Nothing is posted before this step's approval.

## 4. Apply

For each approved item:

- **PR/MR task:** read the live description first and keep everything in it. Add the task under `## Remaining tasks` (create the section at the end, before any footer such as a disclosure or "Generated with" line). Follow the user's instructions for updating descriptions, such as saving a copy. Update each description once, after all its edits are drafted.
- **Issue:** file it, or post the comment, and note the link.
- **Local notes:** replace each moved item with a one-line link to where it went, or remove it when the user prefers. Delete outdated items. Keep links to open upstream work. If a heading empties, remove it, and update any list of headings in the project-local notes file.

## 5. Report

List what moved where, with links, what stayed local and why, and what was deleted.
