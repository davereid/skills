#!/usr/bin/env python3
"""Check GitHub repositories against a standard set of settings and rulesets.

Usage: scripts/github-audit.py owner/repo [owner/repo ...]

Needs `gh` logged in to github.com, with admin access to each repository.
Only reads; prints one line per deviation, or "consistent".

The standard, as the constants below encode it:
- Squash merges only, titled and described from the PR; branches deleted after
  merge; Wiki and Projects off.
- Actions pinned to full commit SHAs; a read-only default token that can open
  and approve PRs; approval required for first-time contributors (public
  repositories only).
- A ruleset named `main` on the default branch and every `<N>.x` branch:
  no deletion or force pushes, a squash-merged PR for every change (0
  approvals, no bypass list), and the "Conventional Commits" check from
  GitHub Actions, with branches required to be up to date.
- Other required checks only in rulesets named `ci` or `ci-<branch>`, also from
  GitHub Actions and up to date. No classic branch protection.
- Every checked branch has `.github/workflows/pr-title.yml` with a job named
  "Conventional Commits" and no filters on `pull_request`.
"""
import base64
import json
import re
import subprocess
import sys

REPO_SETTINGS = {
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
    "squash_merge_commit_title": "PR_TITLE",
    "squash_merge_commit_message": "PR_BODY",
    "delete_branch_on_merge": True,
    "has_wiki": False,
    "has_projects": False,
}
ACTIONS = {"enabled": True, "sha_pinning_required": True}
WORKFLOW = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": True}
FORK_APPROVAL = "first_time_contributors"
TITLE_CHECK = "Conventional Commits"
ACTIONS_APP = 15368
PR_PARAMS = {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews_on_push": False,
    "require_code_owner_review": False,
    "require_last_push_approval": False,
    "required_review_thread_resolution": False,
    "allowed_merge_methods": ["squash"],
}
MAJOR_BRANCH = re.compile(r"^\d+\.x$")


def gh(path):
    """Return parsed JSON for a GET, or None on 404."""
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode:
        # 404: not set; "Upgrade": a private repo without GitHub Pro can't have it.
        if "404" in r.stdout + r.stderr or "Upgrade to GitHub Pro" in r.stderr:
            return None
        sys.exit(f"gh api {path} failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def compare(prefix, actual, expected, out):
    for key, want in expected.items():
        if actual.get(key) != want:
            out.append(f"{prefix}{key} is {actual.get(key)!r}, expected {want!r}")


def audit(repo):
    out = []
    info = gh(f"repos/{repo}")
    default = info["default_branch"]
    compare("setting ", info, REPO_SETTINGS, out)
    compare("actions ", gh(f"repos/{repo}/actions/permissions"), ACTIONS, out)
    compare("workflow token ", gh(f"repos/{repo}/actions/permissions/workflow"), WORKFLOW, out)
    # Private repos have a different fork PR setting; this one applies to public repos only.
    fork = {} if info["private"] else gh(f"repos/{repo}/actions/permissions/fork-pr-contributor-approval") or {}
    if not info["private"] and fork.get("approval_policy") != FORK_APPROVAL:
        out.append(f"fork PR approval is {fork.get('approval_policy')!r}, expected {FORK_APPROVAL!r}")

    branches = [b["name"] for b in gh(f"repos/{repo}/branches?per_page=100")]
    majors = [b for b in branches if MAJOR_BRANCH.match(b)]
    for b in [default] + majors:
        if gh(f"repos/{repo}/branches/{b}/protection") is not None:
            out.append(f"{b}: has classic branch protection")

    rulesets = {}
    for summary in gh(f"repos/{repo}/rulesets") or []:
        rs = gh(f"repos/{repo}/rulesets/{summary['id']}")
        rulesets[rs["name"]] = rs
        if rs["enforcement"] != "active":
            out.append(f"ruleset {rs['name']}: enforcement is {rs['enforcement']}")
        if rs.get("bypass_actors"):
            out.append(f"ruleset {rs['name']}: has a bypass list")
        for rule in rs["rules"]:
            if rule["type"] == "required_status_checks":
                p = rule["parameters"]
                if not p.get("strict_required_status_checks_policy"):
                    out.append(f"ruleset {rs['name']}: branches don't have to be up to date")
                for c in p["required_status_checks"]:
                    if c.get("integration_id") != ACTIONS_APP:
                        out.append(f"ruleset {rs['name']}: check {c['context']!r} isn't limited to GitHub Actions")

    main = rulesets.get("main")
    if not main:
        out.append("no 'main' ruleset")
    else:
        include = main["conditions"]["ref_name"]["include"]
        want_include = ["~DEFAULT_BRANCH"] + (["refs/heads/*.x"] if majors else [])
        if sorted(include) != sorted(want_include):
            out.append(f"ruleset main: applies to {include}, expected {want_include}")
        types = {r["type"]: r for r in main["rules"]}
        for t in ("deletion", "non_fast_forward", "pull_request", "required_status_checks"):
            if t not in types:
                out.append(f"ruleset main: missing rule {t}")
        if "pull_request" in types:
            compare("ruleset main pull_request ", types["pull_request"]["parameters"], PR_PARAMS, out)
        if "required_status_checks" in types:
            checks = [c["context"] for c in types["required_status_checks"]["parameters"]["required_status_checks"]]
            if checks != [TITLE_CHECK]:
                out.append(f"ruleset main: requires {checks}, expected [{TITLE_CHECK!r}]")
        extra = set(types) - {"deletion", "non_fast_forward", "pull_request", "required_status_checks"}
        if extra:
            out.append(f"ruleset main: extra rules {sorted(extra)}")
    for name in rulesets:
        if name != "main" and not (name == "ci" or name.startswith("ci-")):
            out.append(f"ruleset {name}: not a standard name (main, ci, ci-<branch>)")

    # Every required check must be reported by the branch it applies to.
    for b in [default] + majors:
        rules = gh(f"repos/{repo}/rules/branches/{b}") or []
        required = {c["context"] for r in rules if r["type"] == "required_status_checks"
                    for c in r["parameters"]["required_status_checks"]}
        if not required:
            out.append(f"{b}: no required checks")
        wf = gh(f"repos/{repo}/contents/.github/workflows/pr-title.yml?ref={b}")
        if not wf:
            out.append(f"{b}: no .github/workflows/pr-title.yml")
        else:
            text = base64.b64decode(wf["content"]).decode()
            if f"name: {TITLE_CHECK}" not in text:
                out.append(f"{b}: pr-title.yml has no job named {TITLE_CHECK!r}")
            if re.search(r"pull_request:\s*\n\s+(paths|paths-ignore|branches|branches-ignore):", text):
                out.append(f"{b}: pr-title.yml filters pull_request")
    return out


if __name__ == "__main__":
    for repo in sys.argv[1:]:
        problems = audit(repo)
        print(f"== {repo}: {'consistent' if not problems else f'{len(problems)} deviation(s)'}")
        for p in problems:
            print(f"  - {p}")
