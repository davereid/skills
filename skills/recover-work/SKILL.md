---
name: recover-work
description: Recover branches, stashes and uncommitted files from an old Git checkout.
---

# Recover work

Finds work left in old Git checkouts, such as a backup drive, an old laptop or a copy of a site with contrib modules cloned inside it. It matches each repository to a current checkout, sorts the branches, stashes and uncommitted files into what's already done, what can move over, and what the user should decide, and moves the chosen work over as branches, issues or merge requests.

Arguments: the directory to search (e.g. `/Volumes/Backup/code/site`), and optionally where current checkouts live (e.g. `~/code`).

`scripts/recover.sh` does the mechanical parts. Run it with no arguments for its usage.

## Rules

- **Never change the source.** Don't check out, stash, commit, fetch or run tools there. Use read-only Git with `GIT_OPTIONAL_LOCKS=0` (the script sets it), and copy files out rather than moving them. A drive or folder can disconnect: check it's still there before each step.
- **Work in the current checkouts**, in temporary worktrees from their default branch (`git worktree add <temp dir> origin/<default>`), so the user's branches and uncommitted files aren't touched. Remove each worktree when done.
- **Ask before every push**, and before skipping commit hooks.
- **Never transfer personal data or secrets:** exports of users, `.env` files, keys, database dumps. List them as "don't transfer" with the reason.
- Public text (issues, merge requests in open source projects) must not name client projects or their content.

## 1. Find and match repositories

- `recover.sh repos <source dir>` lists every repository under it, including ones nested inside another (e.g. contrib modules cloned in a site's `web/modules`), with their first root commit and remotes. Hidden directories (e.g. `.entity_usage`) are often old copies, but check them like any other: they can hold uncommitted work. Only skip a repository once its inventory shows nothing to recover.
- Match each one to a current checkout by root commit: `recover.sh repos <checkouts dir>` and compare. The root commit matches across hosts and mirrors where remote URLs differ (`git.drupal.org` and `git.drupalcode.org`, GitHub and an enterprise mirror).
- For a repository with no current checkout, run step 2's inventory on it first. If it has nothing to recover (no branches beyond ones already on its remote, no stashes, no uncommitted files), skip it without asking. Otherwise show what it has and ask whether to clone a checkout, following the user's conventions for where checkouts go, or skip it.
- Record every skipped repository in the summary, with the reason, so none is forgotten.
- List the matches to the user before going on. For many repositories, go through them one at a time or in groups, asking after each.

## 2. Inventory

`recover.sh inventory <source repo>` lists the current branch, every local branch with its upstream and last commit, every stash with its files, modified tracked files (mode-only changes ignored, as copies between file systems change modes) and untracked files. macOS metadata files (`._*`, `.DS_Store`) are left out.

## 3. Import and sort branches and stashes

If the source's summary file (step 5) already exists, read it first: keep the items already decided or transferred, with their links, and only ask about new ones. Triage can't tell that work was ported with changes, so without the file it offers finished items again.

`recover.sh import <source repo> <checkout> <name>` fetches the source's branches as `recover-<name>/*` (a remote that can't push) and its stashes as `refs/recover-stash/<name>/<n>`, numbered as in `git stash list`. Use the summary file's name for `<name>` (e.g. `md-cms-backup`), so the same project from several sources, such as a contrib module cloned in several sites, can sit in one checkout side by side. The script refuses a name already used for a different source. Everything after this works in the current checkout, and the source isn't needed again.

`recover.sh triage <checkout> <name> [<base>]` sorts one source's branches and stashes against the default branch:

- **NOOP:** the change is already in the base.
- **APPLIES:** it would merge cleanly.
- **CONFLICT:** it needs porting by hand.

For branches it also counts commits that aren't on any of the checkout's own branches and remotes, and shows where the tip already is.

Then sort each one:

- **Nothing to transfer:** NOOP; the tip is on another branch or remote; or a merged PR or MR from a branch of that name has the same commits (squash merges and rebases don't show up in the count). Check with the host's CLI (`gh pr list --head <branch> --state all`, `glab mr list --source-branch <branch> --all`).
- **Probably obsolete:** the code it changes has since been removed or rewritten, or a later branch or stash supersedes it. Say what shows that.
- **To decide:** everything else. Read each stash's diff (`git stash show -p refs/recover-stash/<name>/<n>`, or `git diff <stash>^1 <stash>`, which includes the index) and summarize it in a sentence. Group stashes that are copies of the same change. Note when one stash mixes unrelated changes: they become separate branches.
## 4. Uncommitted and untracked files

These exist only in the source, so check each against the current checkout:

- `recover.sh file-in <file> <checkout>` shows whether that exact content is in the checkout's history, on any branch or remote.
- If not, check whether the code moved: search the default branch for its class or function names, and diff it with a file of the same path.
- Sort each file: already there; personal data or secrets (don't transfer); local-only scripts and settings (scratch PHP files, local `settings.php`, data exports); evidence for a ticket (attach it there, don't commit it); or work in progress to decide.

Untracked files and imported branches or stashes are often halves of the same work, so search both ways:

- For each untracked file still to decide, search the imported refs for the classes, functions, hooks and plugin IDs it defines (`git grep <name> <ref>` over `recover-<name>/*` and `refs/recover-stash/<name>/*`).
- For each branch or stash, look for names it uses but never defines (e.g. a plugin ID registered with no plugin class), and search the untracked files for them.

Treat a match as one item to decide, and note what links them (e.g. "stash 9 registers `helper_coalesce_date`; untracked `CoalesceDateFilter.php` defines it"). A match is a guess until the user confirms it in step 6.

## 5. Write the summary

Write the findings to one Markdown file for the whole source, outside every checkout, so the notes for all its repositories stay together and can't be committed. Put it in the notes directory the user's instructions name, named after the source (e.g. `<notes>/recover/<source>.md`), or ask where. If an earlier run left notes elsewhere, offer to merge them into this file. Say where the file is at the start and end of each run. List skipped repositories at the top, each with its path and reason (nothing to recover, or the user chose to skip it with what it still holds). Give each other repository a section with:

- how the imported refs are kept, and the commands to remove them (from the script's header);
- new branches, with commit, source (branch, stash or file) and a summary;
- branches with nothing to transfer, grouped by reason;
- branches, stashes and files to decide, as checkboxes with a summary each and their status; list a step 4 match as one item, saying what links its parts;
- every stash in a table (number, date, original branch, status, summary), so none needs reading again;
- next steps, and what a new session needs to know to continue: where the refs are, the project's branch and commit conventions, which items the user has decided.

Keep it up to date as work moves, so a later session can pick up from it.

## 6. Choose and transfer

Ask the user which "to decide" items to transfer, using the agent's question prompt with multiple choice if it has one. Recommend the obvious ones and say why.

Before transferring a step 4 match, show its parts and what links them, and ask whether to transfer them together or separately. Transfer confirmed matches onto one branch; record split ones as separate items in the summary.

For each chosen item:

- **Site or client projects:** create a branch in a temporary worktree from the default branch. Apply the change (`git cherry-pick`, `git stash apply refs/recover-stash/<name>/<n>`, or copy files) and split unrelated changes into separate branches. Follow the project's branch naming and commit message conventions (its `AGENTS.md`, contributing docs and commit hooks), and ask for a ticket number when the convention needs one. Fix bugs found while reviewing the old code, and say what changed from the original. Run the project's checks. If its commit hooks can't run in the worktree (e.g. they run through a container that only mounts the main checkout), run the checks by hand and ask before committing without hooks.
- **Open source projects the user maintains or contributes to:** search the issue queue first. File an issue for work that has none, push the branch to the issue's fork or a branch, and open a draft merge request. Remaining work goes in the merge request's tasks. Leave old work already on a pushed branch or open merge request alone, but list it.
- Files copied from FAT or exFAT drives all look executable: reset modes (e.g. `chmod 644`, and `755` for scripts) before committing.
- Ask before each push, and write PR or MR descriptions following the user's conventions.

Mark each transferred item in the summary with its branch, PR, MR or issue.

A branch left local, with no PR or MR yet, is invisible to later sessions in that project. Add it to the project's notes on current work, where the user's instructions say those go (such as an uncommitted local notes file), with its commit, what it does, what it's waiting on, and a link to the summary file. Ask first if the instructions don't say. Remove the entry once the branch has a PR or MR, or is deleted.

## 7. Clean up

Once everything wanted has moved, remove this source's imported refs from each checkout (commands in the script's header), leaving other sources' alone, and the temporary worktrees, and ask whether the summary file can go, or should keep only its links to open issues, PRs and MRs. The source stays as it was: tell the user it's safe to archive or delete as far as these repositories go, and list anything left behind on purpose.
