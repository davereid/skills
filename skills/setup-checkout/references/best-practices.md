# Best practices for a drupal.org project

What `setup-checkout` compares a project against. Each item says what to check and what to suggest when it's missing.


## CI (`.gitlab-ci.yml`)

- **Uses drupal.org's templates.** It includes `/includes/include.drupalci.main.yml`, `include.drupalci.variables.yml` and `include.drupalci.workflows.yml` from `$_GITLAB_TEMPLATES_REPO` at `$_GITLAB_TEMPLATES_REF`. Without a `.gitlab-ci.yml`, suggest starting from the [current template](https://git.drupalcode.org/project/gitlab_templates/-/raw/default-ref/gitlab-ci/template.gitlab-ci.yml). An existing file may predate parts of that template: compare them, and suggest only what's missing.
- **Tests other core versions.** These variables are set:
  ```yaml
  OPT_IN_TEST_PREVIOUS_MINOR: 1
  OPT_IN_TEST_NEXT_MINOR: 1
  OPT_IN_TEST_NEXT_MAJOR: 1
  OPT_IN_TEST_MAX_PHP: 1
  _AUTORUN_PREVIOUS_MINOR: 'all'
  _AUTORUN_NEXT_MINOR: 'all'
  _AUTORUN_NEXT_MAJOR: 'push-and-mr'
  _AUTORUN_MAX_PHP: 'push-and-mr'
  ```
  Set `OPT_IN_TEST_PREVIOUS_MAJOR: 1` only when `core_version_requirement` allows the previous major version.
- **Spell checking has a dictionary.** `_CSPELL_DICTIONARY` names a committed word list (e.g. `.cspell-words.txt`) for project-specific words. If `_CSPELL_WORDS` lists words inline, suggest moving them to the dictionary file.
- **Next major dependencies are explained.** Each module in `_LENIENT_ALLOW_LIST` (in `composer (next major)`) has a `@todo` comment linking to the issue for its next-major support.
- **Jobs aren't skipped silently.** Each `SKIP_*` variable set to `1` has a comment saying why.


## Composer and `.info.yml`

- **`composer.json` exists**, with the project's name (`drupal/<name>`), type and license.
- **CI can install the dependencies.** CI builds the test site from `composer.json` alone and ignores `.info.yml`, so each `.info.yml` dependency on another drupal.org project (`project:module`) is also in `require-dev`, as `"*"` unless a version is needed. A minimum version goes in `require`, not in `.info.yml`.
- **Optional integrations are installable too.** Modules the code integrates with but doesn't require (e.g. in tests or a submodule) are in `require-dev`.
- **Drush is available.** `require-dev` has `"drush/drush": "*"`, so `ddev drush` works.


## Tests

- **There are tests.** Kernel tests are the best start for most code; unit tests for code that doesn't need Drupal; functional and FunctionalJavascript tests only for what needs a browser. If there are none, offer to add a kernel test for the project's main feature, and don't write one without asking.
- **Tests use PHPUnit attributes**, not annotations: `#[Group('<name>')]`, `#[CoversClass]` (or `#[CoversMethod]`), and `#[RunTestsInSeparateProcesses]` on kernel and functional tests. PHPUnit 12 removed annotations. While `core_version_requirement` allows Drupal 10 (PHPUnit 9, which ignores attributes), keep the annotations alongside the attributes: suggest removing them only once Drupal 10 is dropped, and adding attributes where they're missing (2026-11-22: removing redirect's annotations was suggested, though it still supports `^10.3`).
- **phpstan is configured.** A committed `phpstan.neon` sets the level, with a `phpstan-baseline.neon` if needed. Suggest fixing baseline entries over time, not adding to them.
- **The checks pass**: `ddev phpcs`, `ddev phpstan`, `ddev phpunit`, and `ddev eslint` for JavaScript.


## Docs

- **The README follows drupal.org's template.** If it's missing sections or is out of date, suggest the `update-docs` skill.
- **Developer documentation has its own place.** If the README has grown developer sections (plugin APIs, hooks, long code examples) and there's no `mkdocs.yml`, suggest the `setup-docs` skill.
- **Docs use the templates' `pages` job.** If `.gitlab-ci.yml` has its own `mkdocs` or `pages` job that only runs `mkdocs build`, suggest `setup-docs`, which removes them.
- **API modules document their API.** If the project has a PHP API other modules use (services, traits, base classes), ask whether to generate API docs from its docblocks into the docs site, with `setup-docs`'s API docs step.


## Project settings

Only when the user maintains the project: `glab api --hostname git.drupalcode.org "projects/project%2F<name>"` shows `permissions.project_access.access_level` 40 or higher. These change the project for everyone, so ask before each one. drupal.org's GitLab doesn't accept API changes to project settings: a `PUT` to `projects/project%2F<name>` redirects to `https://www.drupal.org/git-error` (2026-11-14). Give the user the settings page (`https://git.drupalcode.org/project/<name>/-/settings/merge_requests`) to change it there, and check the API again afterwards.

- **Issues are GitLab work items** (`issues_enabled: true`), so issues, merge requests and labels live in one place. If not, offer to request the move on [drupalorg#3409678](https://git.drupalcode.org/project/drupalorg/-/work_items/3409678) (see drupal.org's [GitLab issues docs](https://www.drupal.org/docs/develop/issues/gitlab-issues-for-drupalorg-projects)). The move can't be undone, so ask first, and mention that projects with hundreds of open issues may want to wait.
- **Unresolved threads block merging** (`only_allow_merge_if_all_discussions_are_resolved: true`; Settings > Merge requests > Merge checks > "All threads must be resolved"), so review feedback left as threads doesn't get lost.
- **Merge request titles are Conventional Commits** (Settings > Merge requests > "Merge request title regex"), since the title becomes the merge commit's first line. Regex `^(feat|fix|docs|test|refactor|chore|ci|build|perf|revert)(\([^)]+\))?!?: .+`, with the description `Use a Conventional Commit title, e.g. "fix: #1234567 Prevent duplicate log messages"`. Check with `merge_request_title_regex` and `merge_request_title_regex_description`. Open merge requests whose titles don't match need a retitle before they can be merged. The project's committed `AGENTS.md` ends with a `## Merge requests` section saying so, so contributors' agents title merge requests to match: "Merge request titles are [Conventional Commits](https://www.conventionalcommits.org/) with the issue number: `<type>[(<scope>)][!]: #<issue> <description>`, e.g. `fix: #1234567 Prevent duplicate log messages`. The types are `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf` and `revert`. The title becomes the merge commit's first line, and GitLab won't merge a merge request whose title doesn't match."
- **Merge trains are off** (`merge_trains_enabled: false`; Settings > Merge requests > Merge options > "Enable merge trains"). A train reruns the whole pipeline on top of the merge requests queued ahead before each merge, which only helps when several are merged at once, rare in a contrib project. With fast-forward merges, the merge request's pipeline already tested what lands. Turning trains off cancels a train pipeline that's running and drops its merge request from auto-merge: start a new pipeline for it (`glab api --hostname git.drupalcode.org -X POST "projects/project%2F<name>/merge_requests/<iid>/pipelines"`) and merge again once it passes (2026-11-18, embed !22).
- **Supported branches are tested weekly**, so breakage from core or dependency releases shows up without a commit: one active pipeline schedule per supported branch (the default branch and each maintained release branch), at `https://git.drupalcode.org/project/<name>/-/pipeline_schedules`. Describe it as `<branch> tests`, with no variables, and run it weekly between Sunday 22:00 and Monday 06:00 in the maintainer's timezone, so failures are waiting at the start of the work week. Spread the minute and hour across that window rather than using `0 3`, so projects and branches don't all hit drupal.org's runners at once: the audit script suggests a time for each branch, stable per project and branch (e.g. `14 1 * * 1`). Check with `projects/project%2F<name>/pipeline_schedules`. Unlike project settings, drupal.org accepts schedule changes through the API, so after asking, create one with `glab api --hostname git.drupalcode.org -X POST "projects/project%2F<name>/pipeline_schedules" -f description="<branch> tests" -f ref=<branch> -f cron="<cron>" -f cron_timezone=<timezone> -f active=true`, or move one with a `PUT` to `pipeline_schedules/<id>` (2026-11-18). The audit script only knows the default and protected branches, so check unprotected supported branches by hand.
- **The default branch and release branches are protected** (Settings > Repository > Protected branches, `https://git.drupalcode.org/project/<name>/-/settings/repository`; check with `projects/project%2F<name>/protected_branches`), so nobody force-pushes or deletes them.
- **No `CODEOWNERS`.** Only maintainers can push to the project's branches or merge, and contributors work in issue forks, so the maintainer's merge is the review: requiring their approval of their own merge requests only adds a click. A root `CODEOWNERS` would also tag a maintainer on co-maintainers' merge requests. If a branch has one, remove it in a merge request. "Code owner approval" on a protected branch can stay on: it does nothing without a `CODEOWNERS` (2026-11-20).

`scripts/drupalorg-audit.py <project>` checks these settings without changing anything.

On GitHub, `scripts/github-audit.py <owner/repo>` checks the same standard. GitHub never counts an author's approval of their own PR, so a sole code owner needs a bypass, and required checks go in a separate ruleset so the bypass can't skip them:

- `.github/CODEOWNERS` with `* @<their GitHub username>`.
- Fork PR workflows need approval only for "first-time contributors who are new to GitHub" (Settings > Actions > General), so the maintainer doesn't approve every contributor's runs. That's only safe while fork PRs can't reach secrets or write access: workflows use `pull_request`, not `pull_request_target` or `workflow_run` with the PR's code, give each job only the permissions it needs, and pass zizmor. If they don't, keep a stricter setting until they're fixed.
- A `main` ruleset (default branch and `<N>.x`): no deletion or force pushes, a PR with code owner approval and resolved threads, and Repository admin in its bypass list in "pull request" mode only. Admins merge their own PRs with "Merge without waiting for requirements to be met (bypass rules)" or `gh pr merge <n> --squash --admin`; nobody can push directly.
- No required checks in `main`. Each branch's required jobs, including the PR title check, go in a `ci` (default branch) or `ci-<N>.x` ruleset with no bypass list, so a bypassed review still waits for passing jobs. A check only some branches run, such as a workflow not backported yet, goes only in those branches' rulesets: a required check that never runs blocks every PR. Leave "Require branches to be up to date before merging" off: auto-merge never updates a branch, and repositories owned by a personal account have no merge queue, so every PR would wait for a manual update. The default branch's CI catches the rare pair of PRs that pass alone but break together.
- Dependency updates come from Renovate, per Lullabot's ADR ([Use Renovate for third-party dependency updates](https://architecture.lullabot.com/adr/20251120-use-renovate/)), not Dependabot: start from the ADR's config for the project type (a non-Drupal project also takes the Drupal config's settings that aren't about Drupal: `group:symfony` and `composerIgnorePlatformReqs`; its `ignorePaths` repeats `config:recommended`'s), and add `"automerge": true` for minor, patch, pin, digest and lock file maintenance updates, plus a `minimumReleaseAge`. Projects that check PR titles for Conventional Commits also extend `:semanticCommits`: Renovate only uses `fix(deps):` and `chore(deps):` titles when it's set or when it detects conventional commits in the history, and its detection can miss them. A library replaces the ADR's `"rangeStrategy": "bump"`, which raises `composer.json` lower bounds on every update: use `"update-lockfile"` (tooling lock files only) with a Composer rule of `"widen"`, so ranges only gain new major versions. Libraries with supported older branches list them in `baseBranchPatterns`. Don't add Renovate Approve: a bot's approval never satisfies code owner review, so each update merges as soon as the code owner approves it and the checks pass. Every file stays owned; don't leave dependency files without a code owner or give automation a code owner's token to skip that click. Turn off Dependabot security updates (keep its alerts, which Renovate reads), and leave `renovate.json` out of a library's package (`export-ignore`).
