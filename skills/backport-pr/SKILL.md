---
name: backport-pr
description: Backport a PR to a release branch as its own PR, cross-linked.
---

# Backport PR

Makes the same change as a pull request on another branch, usually from the default branch to a release branch such as `1.x`, and opens it as its own PR. Both descriptions link to each other. Nothing is pushed or opened until the user approves.

Hosts: GitHub and GitHub Enterprise (`gh`). For other hosts, say so and stop.

Arguments: a PR number (open or merged) and the target branch, e.g. `113 1.x`. With no target branch, list the repository's release branches and ask. With no PR number, ask for one.

## 1. Check the source PR

- Read the PR: title, state, base branch, head commit, description and changed files (`gh pr view <n> --json …`).
- Check the target branch exists on the remote and differs from the PR's base.
- Search open and merged PRs on the target branch for one that already backports this PR (its number in the title or description). If there is one, show it and stop unless the user says to continue.

## 2. Make the change on a new branch

- `git fetch`, then start a branch named after the source branch with the target appended (e.g. `chore/lf-line-endings-1.x`) from `origin/<target>`, not a local copy of the target, which may be behind. Use the user's checkout only when it has no uncommitted changes; otherwise use a temporary worktree.
- Apply the change from the PR's full diff against its base (the merge commit for a merged PR, or `git diff <merge-base> <head>`), with `git apply -3`, rather than cherry-picking each commit. Cherry-picks copy footers such as `Release-As:` that may be wrong on the target.
- Resolve conflicts by what the target branch needs, not by taking one side. Files that differ between branches (a missing config file, different supported versions, a job the target branch doesn't have) are the usual cause. List each difference from the source PR and why, for the description.
- Repeat any generated step the PR ran rather than copying its output, such as renormalizing line endings, regenerating a lock file or updating snapshots.
- Run the project's own checks for the changed files (linters, the changed code's tests). Workflow changes also get the project's workflow linters, if it has any.

## 3. Commit

Use the source PR's title as the commit message, following the project's commit convention, plus a body if the change needed adapting. Keep the source's author credit: add a `Co-authored-by:` line for each author of the source PR who isn't the committer.

## 4. Draft the description

Start from the source PR's description, keeping its sections and the project's PR template:

- Open with a sentence that says it's the `<target>` version of the source PR, linked by number.
- Keep the change bullets that apply, and remove or reword the ones that don't. Add the differences from step 2.
- Remaining tasks: keep only the ones that apply to the target branch, with branch names and rulesets changed to match. A task to rebase other PRs on the target branch goes here.
- Keep the AI disclosure section if the source has one, reworded for this PR.

Show the draft, the commit and the diff summary, and ask to push and open the PR.

## 5. Push, open and cross-link

- Push the branch, open the PR against the target branch with the drafted description, and check that the PR's head matches the local commit.
- On the source PR, add or tick the backport task in its remaining tasks, linking the new PR (e.g. "- [x] Backport to `1.x` (#114)"). Read its live description first and change nothing else. If the source PR isn't the user's own, ask before editing it, or offer a comment instead.
- If the source PR's milestone has a counterpart for the target branch, offer to add the new PR to it.

## 6. Report

Give both PR links, the differences from the source, the checks run locally, and the remaining tasks left in either PR, such as required-check changes in branch rulesets.
