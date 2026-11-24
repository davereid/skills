# recover-work

A skill that finds work left in old Git checkouts, such as a backup drive or an old laptop, and moves what's still wanted into your current checkouts. It handles repositories nested inside others, like contrib modules cloned inside a site.

For each repository, it:

- matches it to a current checkout by its root commit, which works across hosts and mirrors;
- sorts its branches and stashes into already done, probably obsolete, or to decide, checking merged PRs and MRs and whether each change still applies to the default branch;
- checks its uncommitted and untracked files against the current checkout's history;
- finds the upstream issues the work depends on (patches, `@todo` links, commit messages, branch names), checks their status, and tracks the open ones;
- writes one summary for the whole source, with every stash summarized, so a later session can continue;
- moves the items you choose into branches, issues or draft merge requests, following each project's conventions.

It never changes the source: Git runs read-only there, and branches and stashes are copied into the current checkout under refs that can't be pushed. It asks before every push, and never transfers personal data or secrets.


## Requirements

- Git 2.38 or later (for `git merge-tree --write-tree`) and bash.
- The host's CLI (`gh` or `glab`), to check PRs and MRs and open new ones.


## Installation

See the [main README](../../README.md#installation).


## Usage

```
/recover-work /Volumes/Backup/code/site ~/code
```

The first argument is the directory to search, and the second (optional) is where your current checkouts are.

`scripts/recover.sh` can also be run on its own:

| Command | What it does |
|---|---|
| `recover.sh repos <dir>...` | Lists the Git repositories under each directory, with their root commit and remotes |
| `recover.sh inventory <source>` | Lists a repository's branches, stashes, modified and untracked files |
| `recover.sh import <source> <checkout> <name>` | Copies the source's branches and stashes into the checkout, kept apart from other sources under `<name>` |
| `recover.sh triage <checkout> <name> [<base>]` | Sorts one source's copied branches and stashes: already in the base, applies, or conflicts |
| `recover.sh file-in <file> <checkout>` | Shows whether a file's exact content is in the checkout's history |


## Limits

- It can't tell from Git alone whether a squash-merged or rebased branch is done: it checks the host for merged PRs and MRs from a branch of the same name.
- Stashes are compared by their full content against their original base. A stash that conflicts may still be partly useful.
