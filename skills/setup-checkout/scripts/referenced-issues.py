#!/usr/bin/env python3
"""List the drupal.org issues a checkout's code links to, open and closed.

Usage: scripts/referenced-issues.py [checkout]

Searches the files Git tracks (so not vendor/, node_modules/ or web/) for
drupal.org links (/project/<name>/issues/<nid>, /node/<nid>, /i/<nid>), looks
each node up on drupal.org's API and prints JSON:

  {"open": [...], "closed": [...]}

Each issue has its nid, project machine name, status, title, URL and the
file:line references. Issues in the checkout's own project are left out, as
are nodes that aren't issues (change records, documentation pages) and nodes
the API can't read (unpublished or restricted).

shortcut: GitLab work item links (git.drupalcode.org/.../-/work_items/<n>) are
not looked up; add them when a project's code starts linking to them.
"""
import json
import re
import subprocess
import sys
import urllib.request

LINK = re.compile(r'drupal\.org/(?:project/[\w-]+/issues|node|i)/(\d+)\b')
# The same links in POSIX ERE, for git grep.
GREP = r'drupal\.org/(project/[A-Za-z0-9_-]+/issues|node|i)/[0-9]+'
OPEN = {'1': 'Active', '4': 'Postponed', '8': 'Needs review', '13': 'Needs work',
        '14': 'Reviewed & tested by the community', '15': 'Patch (to be ported)',
        '16': 'Postponed (maintainer needs more info)'}
CLOSED = {'2': 'Fixed', '3': 'Closed (duplicate)', '5': "Closed (won't fix)",
          '6': 'Closed (works as designed)', '7': 'Closed (fixed)',
          '17': 'Closed (outdated)', '18': 'Closed (cannot reproduce)'}


def node(nid, cache={}):
    if nid not in cache:
        request = urllib.request.Request(
            f'https://www.drupal.org/api-d7/node/{nid}.json',
            headers={'User-Agent': 'referenced-issues'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                cache[nid] = json.load(response)
        except Exception:
            cache[nid] = None
    return cache[nid]


def main(checkout):
    git = ['git', '-C', checkout]
    origin = subprocess.run(git + ['remote', 'get-url', 'origin'],
                            capture_output=True, text=True).stdout
    own = re.search(r'project/([\w-]+?)(?:\.git)?$', origin.strip())
    own = own.group(1) if own else None
    grep = subprocess.run(git + ['grep', '-n', '-I', '-E', GREP],
                          capture_output=True, text=True).stdout
    refs = {}
    for line in grep.splitlines():
        path, number, text = line.split(':', 2)
        for nid in LINK.findall(text):
            refs.setdefault(nid, []).append(f'{path}:{number}')

    result = {'open': [], 'closed': []}
    for nid in sorted(refs, key=int):
        issue = node(nid)
        if not issue or issue.get('type') != 'project_issue':
            continue
        project = node(issue['field_project']['id'])
        name = project and project.get('field_project_machine_name')
        status = str(issue.get('field_issue_status'))
        if not name or name == own or status not in OPEN | CLOSED:
            continue
        result['open' if status in OPEN else 'closed'].append({
            'nid': nid,
            'project': name,
            'status': (OPEN | CLOSED)[status],
            'title': issue['title'].strip(),
            'url': f'https://www.drupal.org/project/{name}/issues/{nid}',
            'references': sorted(set(refs[nid])),
        })
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
