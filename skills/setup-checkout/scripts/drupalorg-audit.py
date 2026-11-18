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
- A `CODEOWNERS` at the root of the default branch that names the user.
- When the user is the only maintainer (drupal.org's `root-admin` aside): the
  default branch is protected, and every protected branch requires code owner
  approval. With other maintainers, that's for the user to decide, so it's
  only reported as a note.
"""
import json
import subprocess
import sys
from urllib.parse import quote

HOST = "git.drupalcode.org"
SETTINGS = {
    "only_allow_merge_if_all_discussions_are_resolved": True,
    "merge_trains_enabled": False,
}


SYSTEM_ACCOUNTS = {"root-admin"}


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


def check(p, me):
    """Yield one line per deviation from the standard."""
    name, pid = p["path"], quote(f"project/{p['path']}", safe="")
    url = f"https://{HOST}/project/{name}/-/settings"
    for key, want in SETTINGS.items():
        if p.get(key) != want:
            yield f"{key} is {p.get(key)}, want {want}: {url}/merge_requests"

    branch = p["default_branch"]
    owners = glab(f"projects/{pid}/repository/files/CODEOWNERS/raw?ref={quote(branch, safe='')}", missing_ok=True, raw=True)
    if owners is None:
        yield f"no CODEOWNERS at the root of {branch}"
    elif f"@{me}" not in owners.split():
        yield f"CODEOWNERS on {branch} doesn't name @{me}"

    members = glab(f"projects/{pid}/members/all?per_page=100", paginate=True)
    others = sorted({m["username"] for page in members for m in page
                     if m["access_level"] >= 40 and m["username"] not in SYSTEM_ACCOUNTS | {me}})
    if others:
        yield f"note: other maintainers ({', '.join(others)}), so code owner approval is your call"
        return
    protected = {b["name"]: b for b in glab(f"projects/{pid}/protected_branches")}
    if branch not in protected:
        yield f"default branch {branch} isn't protected: {url}/repository"
    for b in protected.values():
        if not b.get("code_owner_approval_required"):
            yield f"{b['name']} doesn't require code owner approval: {url}/repository"


def main():
    me = glab("user")["username"]
    found = 0
    for p in sorted(projects(sys.argv[1:]), key=lambda p: p["path"]):
        for line in check(p, me):
            found += 1
            print(f"{p['path']}: {line}")
    if not found:
        print("consistent")


if __name__ == "__main__":
    main()
