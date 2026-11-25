#!/usr/bin/env python3
"""Check drupal.org projects' GitLab settings against a standard.

Usage: scripts/drupalorg-audit.py [project ...]

With no arguments, checks every drupal.org project where the logged-in user is
a Maintainer on git.drupalcode.org. Needs `glab` logged in to that host.
Only reads: drupal.org refuses settings changes through the API, so each
deviation is printed with the settings page to change it in.

The standard:
- Unresolved threads block merging ("All threads must be resolved"; SETTINGS).
- Merge trains are off (SETTINGS): a contrib project rarely has merges queued
  at once, and a train reruns the whole pipeline before each merge.
- Merge request titles must be Conventional Commits (TITLE_REGEX), since the
  title becomes the merge commit's first line.
- Each protected branch (the default and the release branches) has an active
  pipeline schedule, so it's tested weekly even without commits, between late
  Sunday and early Monday, before the work week. A missing one is printed with
  a suggested time in that window, spread by project and branch (`cron()`).
- The default branch is protected.
- No `CODEOWNERS` at the root of the default or protected branches: only
  maintainers can merge, so the merge is the review. Code owner approval may
  stay on, since it does nothing without one.
"""
import json
import subprocess
import sys
import zlib
from urllib.parse import quote

HOST = "git.drupalcode.org"
SETTINGS = {
    "only_allow_merge_if_all_discussions_are_resolved": True,
    "merge_trains_enabled": False,
}
TITLE_REGEX = r"^(feat|fix|docs|test|refactor|chore|ci|build|perf|revert)(\([^)]+\))?!?: .+"
TITLE_REGEX_DESCRIPTION = 'Use a Conventional Commit title, e.g. "fix: #1234567 Prevent duplicate log messages"'

# Weekly schedules run between Sunday 22:00 and Monday 06:00.
SCHEDULE_START = (0, 22)  # (cron weekday, hour)
SCHEDULE_MINUTES = 8 * 60
SCHEDULE_DAYS = {"0", "1", "7"}


def cron(name, branch):
    """Return a weekly cron time in the window, stable for each project and branch.

    Spreading schedules out keeps them from all hitting drupal.org's runners at
    once, and a hash rather than random gives the same answer on every audit.
    """
    offset = SCHEDULE_START[1] * 60 + zlib.crc32(f"{name}:{branch}".encode()) % SCHEDULE_MINUTES
    day = (SCHEDULE_START[0] + offset // (24 * 60)) % 7
    return f"{offset % 60} {offset // 60 % 24} * * {day}"


def glab(path, paginate=False, missing_ok=False, raw=False):
    """Return parsed JSON (text if raw) for a GET, None on a 404 if missing_ok, else exit."""
    cmd = ["glab", "api", "--hostname", HOST, path]
    if paginate:
        cmd.insert(2, "--paginate")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        if missing_ok and "404" in r.stdout + r.stderr:
            return None
        sys.exit(f"glab api {path}: {r.stderr.strip()}")
    if raw:
        return r.stdout
    if not paginate:
        return json.loads(r.stdout)
    # --paginate prints one JSON array per page, one after another.
    pages, pos, dec = [], 0, json.JSONDecoder()
    while pos < len(r.stdout.rstrip()):
        page, pos = dec.raw_decode(r.stdout, pos)
        pages.append(page)
        while pos < len(r.stdout) and r.stdout[pos].isspace():
            pos += 1
    return pages


def projects(names):
    if names:
        return [glab("projects/" + quote(f"project/{n}", safe="")) for n in names]
    pages = glab("projects?membership=true&min_access_level=40&per_page=100&simple=false", paginate=True)
    return [p for page in pages for p in page if p["namespace"]["full_path"] == "project"]


def check(p):
    """Yield one line per deviation from the standard."""
    name, pid = p["path"], quote(f"project/{p['path']}", safe="")
    url = f"https://{HOST}/project/{name}/-/settings"
    for key, want in SETTINGS.items():
        if p.get(key) != want:
            yield f"{key} is {p.get(key)}, want {want}: {url}/merge_requests"
    if p.get("merge_request_title_regex") != TITLE_REGEX:
        yield (f"merge request title regex is {p.get('merge_request_title_regex')!r}, want {TITLE_REGEX!r}"
               f" with description {TITLE_REGEX_DESCRIPTION!r}: {url}/merge_requests")
    if not p.get("issues_enabled"):
        yield ("issues are in drupal.org's issue queue, not GitLab work items: request the move on"
               " https://git.drupalcode.org/project/drupalorg/-/work_items/3409678")

    branch = p["default_branch"]
    protected = {b["name"]: b for b in glab(f"projects/{pid}/protected_branches")}
    schedules_url = f"https://{HOST}/project/{name}/-/pipeline_schedules"
    scheduled = {}
    for page in glab(f"projects/{pid}/pipeline_schedules?per_page=100", paginate=True):
        for s in page:
            if s["active"]:
                scheduled[s["ref"].removeprefix("refs/heads/")] = s["cron"]
    for b in sorted({branch} | {n for n in protected if "*" not in n}):
        if b not in scheduled:
            yield f"{b} has no active pipeline schedule, suggest '{cron(name, b)}': {schedules_url}"
        elif scheduled[b].split()[4] not in SCHEDULE_DAYS:
            yield f"{b}'s schedule '{scheduled[b]}' isn't late Sunday or early Monday, suggest '{cron(name, b)}': {schedules_url}"

    if branch not in protected:
        yield f"default branch {branch} isn't protected: {url}/repository"
    # Code owner approval does nothing on a branch without CODEOWNERS.
    for b in sorted({branch} | {n for n in protected if "*" not in n}):
        if glab(f"projects/{pid}/repository/files/CODEOWNERS/raw?ref={quote(b, safe='')}", missing_ok=True, raw=True) is not None:
            yield f"CODEOWNERS at the root of {b}: remove it in a merge request"


def main():
    found = 0
    for p in sorted(projects(sys.argv[1:]), key=lambda p: p["path"]):
        for line in check(p):
            found += 1
            print(f"{p['path']}: {line}")
    if not found:
        print("consistent")


if __name__ == "__main__":
    main()
