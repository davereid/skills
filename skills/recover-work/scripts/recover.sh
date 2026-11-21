#!/usr/bin/env bash
# Inventories and imports work left in an old Git checkout (a backup, another
# machine), without changing it.
#
#   recover.sh repos     <dir> [<dir>...]  Git repositories under each <dir>, with their root commit and remotes.
#   recover.sh inventory <source>          Branches, stashes and uncommitted files in one repository.
#   recover.sh import    <source> <target> Fetches the source's branches and stashes into <target>.
#   recover.sh triage    <target> [<base>] Sorts the imported branches and stashes against <base>.
#   recover.sh file-in   <file> <target>   Whether a file's exact content is anywhere in <target>'s history.
#
# Only "import" writes, and only to <target>: a "backup-source" remote that
# can't push, and refs/backup-stash/<n>. Remove them with:
#   git -C <target> remote remove backup-source
#   git -C <target> for-each-ref --format='delete %(refname)' refs/backup-stash | git -C <target> update-ref --stdin
set -euo pipefail

# Read-only Git on the source: no index refresh or other optional writes.
export GIT_OPTIONAL_LOCKS=0
# Files that copies to other file systems add, such as macOS metadata.
NOISE='(^|/)(\._[^/]*|\.DS_Store)$'

die() { echo "$*" >&2; exit 1; }

cmd_repos() {
  local dir git root
  for dir in "$@"; do
    find "$dir" \( -name node_modules -o -name vendor \) -prune -o -name .git -print 2>/dev/null | while read -r git; do
      root=$(dirname "$git")
      # The first root commit identifies a project across hosts and mirrors.
      printf '%s\t%s\t%s\n' "$root" \
        "$(git -C "$root" rev-list --max-parents=0 HEAD 2>/dev/null | tail -1)" \
        "$(git -C "$root" remote -v 2>/dev/null | awk '$3 == "(fetch)" { print $1 "=" $2 }' | tr '\n' ' ')"
    done
  done
}

cmd_inventory() {
  local src=$1
  git -C "$src" rev-parse --git-dir >/dev/null || die "Not a Git repository: $src"
  echo "## Current branch"
  git -C "$src" branch --show-current
  echo
  echo "## Branches (name, upstream, ahead/behind, last commit date, subject)"
  git -C "$src" for-each-ref --format='%(refname:short)	%(upstream:short)	%(upstream:track)	%(committerdate:short)	%(subject)' refs/heads
  echo
  echo "## Stashes (index, date, message, files)"
  git -C "$src" stash list --format='%gd	%cs	%gs' | while IFS=$'\t' read -r ref date msg; do
    printf '%s\t%s\t%s\t%s\n' "$ref" "$date" "$msg" "$(git -C "$src" stash show --name-only "$ref" 2>/dev/null | tr '\n' ' ')"
  done
  echo
  echo "## Modified tracked files (mode-only changes ignored)"
  git -C "$src" -c core.fileMode=false diff --stat HEAD 2>/dev/null | grep -Ev "$NOISE" || true
  echo
  echo "## Untracked files (not ignored)"
  git -C "$src" ls-files --others --exclude-standard 2>/dev/null | grep -Ev "$NOISE" || true
}

cmd_import() {
  local src=$1 target=$2 n sha
  git -C "$target" rev-parse --git-dir >/dev/null || die "Not a Git repository: $target"
  if ! git -C "$target" remote get-url backup-source >/dev/null 2>&1; then
    git -C "$target" remote add backup-source "$src"
    git -C "$target" remote set-url --push backup-source DISABLED
  fi
  git -C "$target" fetch --quiet backup-source '+refs/heads/*:refs/remotes/backup-source/*'
  # Stashes aren't fetchable refs, so fetch each commit by its hash.
  n=0
  git -C "$src" stash list --format='%H' | while read -r sha; do
    git -C "$target" fetch --quiet \
      --upload-pack='git -c uploadpack.allowAnySHA1InWant=true upload-pack' \
      backup-source "${sha}:refs/backup-stash/${n}"
    n=$((n + 1))
  done
  echo "Branches: $(git -C "$target" for-each-ref refs/remotes/backup-source | wc -l | tr -d ' ')"
  echo "Stashes: $(git -C "$target" for-each-ref refs/backup-stash | wc -l | tr -d ' ')"
}

# Whether a commit's changes still apply to the base: NOOP (already there),
# APPLIES or CONFLICT. A stash is compared through its first parent.
merge_status() {
  local target=$1 base=$2 commit=$3 parent=$4 tree
  if ! tree=$(git -C "$target" merge-tree --write-tree --merge-base="$parent" "$base" "$commit" 2>/dev/null | head -1); then
    echo CONFLICT
  elif [ "$tree" = "$(git -C "$target" rev-parse "${base}^{tree}")" ]; then
    echo NOOP
  else
    echo APPLIES
  fi
}

cmd_triage() {
  local target=$1 base=${2:-} ref name unique where status
  [ -n "$base" ] || base=$(git -C "$target" symbolic-ref --short refs/remotes/origin/HEAD)
  echo "## Branches (name, status vs $base, commits not on any other branch, where the tip already is)"
  git -C "$target" for-each-ref --format='%(refname)' refs/remotes/backup-source | while read -r ref; do
    name=${ref#refs/remotes/backup-source/}
    [ "$name" = HEAD ] && continue
    # Commits that aren't on any of the target's own branches or remotes.
    # Squash merges and rebases still count here: check PRs for those.
    # shellcheck disable=SC2046
    # awk rather than grep -v, which fails when it filters out every line.
    unique=$(git -C "$target" rev-list --count "$ref" --not $(git -C "$target" for-each-ref --format='%(refname)' refs/heads refs/remotes | awk '!/^refs\/remotes\/backup-source\//'))
    where=$(git -C "$target" for-each-ref --contains "$ref" --format='%(refname:short)' refs/heads refs/remotes | awk '!/^backup-source\// && n++ < 3' | tr '\n' ' ')
    status=$(merge_status "$target" "$base" "$ref" "$(git -C "$target" merge-base "$base" "$ref")")
    printf '%s\t%s\t%s\t%s\n' "$name" "$status" "$unique" "$where"
  done
  echo
  echo "## Stashes (ref, status vs $base, message)"
  git -C "$target" for-each-ref --sort=refname --format='%(refname)	%(subject)' refs/backup-stash | sort -t/ -k3 -n | while IFS=$'\t' read -r ref msg; do
    printf '%s\t%s\t%s\n' "${ref#refs/}" "$(merge_status "$target" "$base" "$ref" "${ref}^1")" "$msg"
  done
}

cmd_file_in() {
  local file=$1 target=$2 blob
  blob=$(git hash-object "$file")
  # --find-object lists commits that add or remove that exact content.
  git -C "$target" log --all --format='%h %cs %s' --find-object="$blob" -1 | grep . || echo "not found"
}

case "${1:-}" in
  repos) shift; [ $# -ge 1 ] || die "Usage: $0 repos <dir>..."; cmd_repos "$@" ;;
  inventory) [ $# -eq 2 ] || die "Usage: $0 inventory <source>"; cmd_inventory "$2" ;;
  import) [ $# -eq 3 ] || die "Usage: $0 import <source> <target>"; cmd_import "$2" "$3" ;;
  triage) [ $# -ge 2 ] || die "Usage: $0 triage <target> [<base>]"; cmd_triage "$2" "${3:-}" ;;
  file-in) [ $# -eq 3 ] || die "Usage: $0 file-in <file> <target>"; cmd_file_in "$2" "$3" ;;
  *) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
