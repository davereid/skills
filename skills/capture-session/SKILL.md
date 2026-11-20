---
name: capture-session
description: Capture a session's lessons, decisions and open work in notes or issues.
---

# Capture session

At the end of a working session, finds what's worth keeping from the conversation, such as corrections, preferences, conventions, decisions and unfinished work, and proposes where each belongs. It also finds notes the session made outdated. Nothing is written until the user approves it, except what their instructions allow without asking.

Arguments: nothing. It works on the current conversation and the checkouts the session worked in: the current one, and any other it edited or committed to.

## 1. Find the rules

Read the user's instruction files (global and project, such as `AGENTS.md`, `CLAUDE.md` and any project-local notes file they use) for how they want things captured: which file holds what, what may be added without asking, and the wording style. If they say nothing, use these places:

- **Global instructions:** the user's preferences for every project (how they work, their tools, their writing style).
- **Project instructions** (committed, e.g. the project's `AGENTS.md`): conventions anyone working on the project should follow. No personal preferences or in-progress notes.
- **Project-local notes** (not committed): the user's notes and current work for this project.
- **Local backlog** (not committed, e.g. `BACKLOG.local.md`): work that isn't active.
- **An open PR's or MR's remaining tasks, or an issue:** work others should see, in a project the user maintains.
- **A skill's files**, when the session corrected or extended how a skill the user maintains works (a skill whose directory is a checkout or a link to one they can edit).

## 2. Go through the session

Read the conversation from the start, including the summary of any earlier part, and list each candidate:

- **Corrections:** something that had to be undone or redone, by the agent or the user, and how to avoid it next time.
- **Preferences and conventions** the user stated or confirmed, especially ones they repeated.
- **Decisions** and their reasons, which the code or commit history won't show.
- **Facts** about the project or setup found the hard way (a command that needs a flag, a host quirk, an account's access).
- **Open work:** tasks started but not finished, untested changes, follow-ups the user agreed to, and questions still open.
- **Skill improvements:** steps a skill got wrong or missed, or something the user asked for that a skill could do next time.

Drop what only mattered to this session, what's already written down, and what the repository already records (code, commits, docs). To check what's written down, search every file from step 1 for the same rule, not just the target file, including the files they import or point to (such as a conventions file the global instructions name) and shared checklists a skill uses. If another file already has it, propose nothing, or a change to that file if the session refined the rule.

## 3. Find outdated notes

Check the files from step 1, in every checkout the session worked in, that this session touched, or that cover work done in it, for entries that are now wrong: tasks it finished, plans it changed, facts it disproved, and items a merged PR covers. Check the remaining tasks of the open PRs or MRs the session worked on as well.

Also look for rules that appear in more than one of these files, in the same or different words. Propose keeping each in the narrowest file that fits its scope (step 1) and removing the other copies, or replacing them with a short pointer when a reader of that file needs to know the rule exists. Rules in shared files, such as a committed `AGENTS.md` or a skill's checklist, stay there even when a personal file repeats them: remove the personal copy instead. Flag copies that disagree, and ask which wording is right.

## 4. Propose

Show one table per target (file, PR or issue): the item (a few words), the exact text to add, change or remove, and why it belongs there. Mark items the user's rules allow without asking (e.g. correction notes) as already applied, and apply them before showing the table.

For open work, offer where it should go:

- **Local backlog**, as a self-contained prompt: what to do, the files or classes involved, and how to check it's done, so a later session can start from it without this conversation.
- **A PR's or MR's remaining tasks, or an issue:** if the `project-backlog` skill is installed, offer to run it after this step, which moves backlog items into PRs and issues; otherwise draft the task or issue here.

Ask which to apply (multi-select per table, with "none"). Change any draft the user edits.

## 5. Apply

- Edit each file only with approved items. Keep its structure: add items under the heading they belong to, and update any list of headings the file keeps.
- For a PR or MR, read the live description first and keep everything in it. Follow the user's instructions for updating descriptions, such as saving a copy.
- For a skill, edit its files in its checkout, and say which branch they're on. Don't commit or push unless the user's instructions or answer say to.
- Public text (a PR, an issue, committed files) must not name clients, client projects or their content.

## 6. Report

List what was added, changed and removed, and where (with links for PRs and issues), what was skipped, and anything left for `project-backlog`.
