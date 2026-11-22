# credit-audit

Finds drupal.org work items fixed in the last two weeks (or any number of days) whose contribution record is missing, still a draft, or doesn't credit you. For each, it shows what you did (merge requests you wrote or merged, commits, comments) and links the record to fix.

## Requirements

- Python 3
- [`glab`](https://gitlab.com/gitlab-org/cli), signed in to `git.drupalcode.org`

## Usage

Ask your agent to "check my drupal.org credit", or run the script yourself:

```sh
python3 skills/credit-audit/scripts/credit_audit.py --user <username> --checkouts ~/code
python3 skills/credit-audit/scripts/credit_audit.py --user <username> --days 30 helper embed
```

It only reads. Only maintainers and collaborators can edit contribution records, so you fix them in the browser.

Projects still on drupal.org's issue queue aren't checked.
