#!/usr/bin/env python3
"""Find recently closed drupal.org work items where a user is missing credit.

Usage:
  credit_audit.py --user USERNAME [--days N] [--checkouts DIR] [PROJECT ...]

Lists work items closed or updated in the last N days (default 14) in each
project, keeps those that were fixed (a state::fixed label or a merged merge
request), and reports the ones whose contribution record is missing, still a
draft, or doesn't credit the user, with the user's part in each: merge
requests written or merged, commits and comments.

Projects are drupal.org machine names (e.g. helper). With --checkouts, every
Git checkout directly under DIR whose origin is a drupal.org project is added.
Needs glab authenticated for git.drupalcode.org. Prints tab-separated rows:
  project, issue, problem, record nid, merged MRs, user's part, title
"""

import argparse
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RECORDS = 'https://new.drupal.org/jsonapi/node/contribution_record'


def glab(path):
    out = subprocess.run(['glab', 'api', '--hostname', 'git.drupalcode.org', path],
                         capture_output=True, text=True, check=True).stdout
    # glab can print more than one line; the JSON is on the first.
    return json.loads(out.splitlines()[0]) if out.strip() else []


def jsonapi(params):
    url = f'{RECORDS}?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.api+json', 'User-Agent': 'credit-audit'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def checkout_projects(directory):
    projects = []
    for d in sorted(Path(directory).expanduser().iterdir()):
        if not (d / '.git').exists():
            continue
        url = subprocess.run(['git', '-C', str(d), 'remote', 'get-url', 'origin'],
                             capture_output=True, text=True).stdout.strip()
        for prefix in ('git.drupal.org:project/', 'git.drupalcode.org/project/'):
            if prefix in url:
                projects.append(url.split(prefix, 1)[1].removesuffix('.git'))
    return projects


def record(project, iid, user):
    """Returns (nid, draft, problem) or None when the issue has no record."""
    source = f'https://git.drupalcode.org/project/{project}/-/work_items/{iid}'
    data = jsonapi({'filter[field_source_link.uri]': source})['data']
    if not data:
        return None
    nid = data[0]['attributes']['drupal_internal__nid']
    # Adding include to the source-link query drops drafts, so read by nid.
    full = jsonapi({'filter[nid]': nid,
                    'include': 'field_contributors,field_contributors.field_contributor_user'})
    draft = bool(full['data'] and full['data'][0]['attributes'].get('field_draft'))
    included = full.get('included', [])
    # 'name' is the drupal.org display name ("dave reid"); the Git username
    # matches the GitLab one.
    names = {i['id']: {str(i['attributes'].get(k, '')).lower() for k in ('name', 'field_git_username')}
             for i in included if i['type'].startswith('user')}
    credit = None
    for item in included:
        if item['type'] != 'paragraph--contributor':
            continue
        ref = (item['relationships'].get('field_contributor_user') or {}).get('data') or {}
        if user.lower() in names.get(ref.get('id'), set()):
            credit = bool(item['attributes'].get('field_credit_this_contributor'))
    if credit is None:
        problem = 'not listed'
    elif not credit:
        problem = 'not credited'
    else:
        problem = 'draft' if draft else ''
    return nid, draft, problem


def part(project, iid, merged, user):
    roles = []
    for mr_iid in merged:
        mr = glab(f'projects/project%2F{project}/merge_requests/{mr_iid}')
        if (mr.get('author') or {}).get('username') == user:
            roles.append(f'wrote !{mr_iid}')
        elif any(c.get('author_name', '').lower() == user.lower()
                 or user.lower() in c.get('author_email', '').lower()
                 for c in glab(f'projects/project%2F{project}/merge_requests/{mr_iid}/commits?per_page=100')):
            roles.append(f'commits in !{mr_iid}')
        if (mr.get('merged_by') or {}).get('username') == user:
            roles.append(f'merged !{mr_iid}')
    notes = glab(f'projects/project%2F{project}/issues/{iid}/notes?per_page=100')
    count = sum(1 for n in notes if not n.get('system') and (n.get('author') or {}).get('username') == user)
    if count:
        roles.append(f'{count} comments')
    return roles


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--user', required=True, help='drupal.org username')
    parser.add_argument('--days', type=int, default=14)
    parser.add_argument('--checkouts', help='directory of project checkouts')
    parser.add_argument('projects', nargs='*')
    args = parser.parse_args()
    projects = list(dict.fromkeys(args.projects + (checkout_projects(args.checkouts) if args.checkouts else [])))
    if not projects:
        parser.error('give projects or --checkouts')
    since = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime('%Y-%m-%dT%H:%M:%SZ')

    for project in projects:
        if not glab(f'projects/project%2F{project}').get('issues_enabled'):
            print(f'# {project}: on the drupal.org issue queue, skipped', file=sys.stderr)
            continue
        page = 1
        while True:
            issues = glab(f'projects/project%2F{project}/issues?state=closed&updated_after={since}&per_page=100&page={page}')
            for issue in issues:
                iid = issue['iid']
                # Release plans link every MR in the release, but get no credit.
                if issue['title'].startswith('Plan for '):
                    continue
                mrs = glab(f'projects/project%2F{project}/issues/{iid}/related_merge_requests')
                merged = [m['iid'] for m in mrs if m.get('state') == 'merged']
                if not merged and 'state::fixed' not in issue['labels']:
                    continue
                rec = record(project, iid, args.user)
                if rec is None:
                    nid, problem = '', 'no record'
                else:
                    nid, _, problem = rec
                    if not problem:
                        continue
                roles = part(project, iid, merged, args.user)
                print('\t'.join([project, f'#{iid}', problem, str(nid),
                                 ','.join(f'!{m}' for m in merged), '; '.join(roles) or '-',
                                 issue['title']]), flush=True)
            if len(issues) < 100:
                break
            page += 1


if __name__ == '__main__':
    main()
