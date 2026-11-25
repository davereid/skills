---
name: setup-checkout
description: "Clone or update a drupal.org project checkout: DDEV, tests and CI."
---

# Set up a checkout

Sets up a drupal.org module or theme for local development with [ddev-drupal-contrib](https://github.com/ddev/ddev-drupal-contrib), the layout drupal.org's GitLab CI uses: the project's repository is the DDEV project root, Composer builds Drupal in `web/` from the project's `composer.json`, and the project is linked into `web/modules/custom/`, in a folder named after the DDEV project.

It then reviews the project's agent instructions (`AGENTS.md`), and compares the project with [best practices](references/best-practices.md) for CI, Composer, tests, docs and project settings, and offers to bring it up to date.

Use it to clone a new project, or on an existing checkout to bring its setup and its project files up to date. Each step checks what's already there, so running it again is safe.

Needs Git with SSH access to `git.drupal.org`, and DDEV. Run it on the host: inside a DDEV container (`IS_DDEV_PROJECT=true`), `ddev` can't run, so stop and give the user the commands instead.

For Drupal core itself (the `drupal` project), follow [Drupal core](#drupal-core) instead of steps 3 to 6.


## Steps

1. **Find the project.** Take its machine name from the user, or from the main `*.info.yml` in an existing checkout. If the user's own instructions (such as their `AGENTS.md`) say where to keep checkouts or which extra DDEV add-ons to install, follow them. Otherwise ask where to clone, suggesting a directory named like the other checkouts next to it (e.g. `drupal-<name>` if they're `drupal-*`), or `<name>`.
2. **Clone or refresh.**
   - New: `git clone git@git.drupal.org:project/<name>.git <directory>`, which checks out the default branch.
   - Existing: `git fetch origin`, then report the current branch, uncommitted changes and how far it is behind its upstream. Don't pull, switch branches or touch uncommitted work without asking.
   - Note the untracked files (`git status --porcelain`) for step 7.
3. **Configure DDEV** without a `name:` in `.ddev/config.yaml`, so the project takes the directory's name (e.g. `drupal-helper`), and two checkouts of the same project can run side by side. ddev-drupal-contrib names the project's folder in `web/modules/custom/` after the DDEV project, with dashes as underscores (e.g. `drupal_helper`); Drupal finds the module by its `.info.yml`, so the folder name doesn't matter. Keep a name only if something depends on the URL (`<name>.ddev.site`): search the checkout for `.ddev.site` first, and ask the user if anything does.
   - If `ddev list` shows another project with the directory's name in a different directory, ask the user before going on.
   - New: `ddev config --project-type=drupal11 --docroot=web`. For a theme, also set `DRUPAL_PROJECTS_PATH=themes/custom` as the add-on's README describes.
   - Every `ddev config` run, including `ddev config --update` in step 5, writes `name:` into `.ddev/config.yaml`, even when it was left out. Remove the line again after each run.
   - Existing, with a `name:` in `.ddev/config.yaml` (e.g. `name: helper` in a `drupal-helper` directory): offer to remove it. Renaming deletes the project's containers and database, so first warn the user that the site's content and settings will be lost, and offer to keep them with a snapshot. Only go on once they agree. Then:
     1. `ddev snapshot`, if they want to keep the database. Snapshots are files in the checkout's `.ddev/db_snapshots/`, and the default name has a timestamp, so it can't clash with an earlier one.
     2. `ddev delete -Oy`, which removes the old project's containers, database and listing, and leaves the code and `.ddev/` alone.
     3. Remove the `name:` line from `.ddev/config.yaml`. If the file is committed, this is a change to the project, so tell the user.
     4. Delete what the old name left behind: `.ddev/traefik/certs/<old_name>.*` and `.ddev/traefik/config/<old_name>.yaml`, which DDEV otherwise warns about on each start, and the generated folder `web/modules/custom/<old_name>` (dashes as underscores), or Drupal finds the project twice.
     5. If a snapshot was taken, restore it with `ddev snapshot restore --latest` after the first `ddev restart` in "Build the site".
4. **Install add-ons.** `ddev add-on get` installs an add-on, or updates it to the latest release:
   - `ddev/ddev-drupal-contrib`;
   - `ddev/ddev-selenium-standalone-chrome`, if the project has FunctionalJavascript or Nightwatch tests (`tests/src/FunctionalJavascript`, `tests/src/Nightwatch`);
   - any add-ons the user's instructions list.
5. **Build the site.** If the project's `.gitlab-ci.yml` sets `_LENIENT_ALLOW_LIST`, set the same for DDEV (`ddev config --web-environment-add="_LENIENT_ALLOW_LIST=<modules>"`, then remove `name:` again), and install the plugin in the web container before `ddev poser`: `ddev exec 'composer global config --no-plugins allow-plugins.mglaman/composer-drupal-lenient true && composer global require mglaman/composer-drupal-lenient'`. Without it, `ddev poser` can't install dependencies that don't declare support for the installed core. Then `ddev restart`, then `ddev poser` (installs Drupal and the project's dependencies, as CI does) and `ddev symlink-project`. Then run `ddev config --update`, which picks the PHP version for the installed core, and `ddev restart` again if it changed `.ddev/config.yaml`. If the project has JavaScript, install core's JavaScript tools for ESLint: `ddev exec -d /var/www/html/web/core yarn install`.
6. **Run the checks.** `ddev phpcs`, `ddev phpstan`, `ddev eslint` if the project has JavaScript, and `ddev phpunit <path>` on one kernel or unit test if it has any. Report failures without fixing them: they can be real problems in the project.
7. **Keep `git status` clean.** Setup leaves files Git doesn't know about: `web/`, `vendor/`, `.ddev/`, Drupal's scaffold files (such as `.editorconfig`), and config the check commands download when the project has none (such as `phpcs.xml.dist`). Compare the untracked files with step 2's list, and offer to add the new ones to `.git/info/exclude`, which is never committed. In an existing checkout, step 2's list may already hold files from an earlier setup, such as `web/` and `.ddev/`: offer those too. Don't change the project's `.gitignore`. Drupal's scaffold changes it during `ddev poser` anyway: it appends `/.editorconfig` and `/.gitattributes` to a committed `.gitignore` (restore it with `git checkout -- .gitignore`, and offer the two entries for `.git/info/exclude` instead), and creates one when the project has none (offer it for `.git/info/exclude`). The next `ddev poser` does it again (2026-11-18: entity_embed's committed `.gitignore` showed as modified after setup).
8. **Find leftovers** from an older setup, in an existing checkout. List them with a suggested fix, and change nothing without asking:
   - untracked config the setup replaces, such as a local phpstan or PHPUnit config that adds extensions or database settings the add-on now provides;
   - instructions for agents or developers (`AGENTS.md`, local notes, the README's development section) that run checks another way, e.g. through a site that includes the project, with `vendor/bin/phpunit` and a core `phpunit.xml`, or with long phpcs and ESLint commands. Suggest the add-on's commands instead, and keep notes that still apply, such as CI quirks;
   - folders in `web/modules/custom/` (or `themes/custom/`) other than the project's own;
   - files that older versions of the other skills in this repository wrote: check each skill's `SKILL.md` for a step that starts "Older versions of this skill wrote", such as `update-docs`' `project.html` and `summary.html`, and hand them to that skill;
   - untracked files in the project's source that the checks report errors in. They may be someone's work in progress, so only point them out.
9. **Review the agent instructions.** Suggest each change and ask before making it:
   - `AGENTS.md` at the repository root: if there isn't one, offer to create it, with a short summary of the project, its architecture (main services, plugin types and base classes), its conventions that differ from Drupal's, and how to run the checks (step 12's commands). Ask whether it should be committed for every contributor, or kept untracked for the user (then add it to `.git/info/exclude`).
   - `CLAUDE.md` at the repository root: Claude Code (v2.1.277 and later) reads `AGENTS.md` on its own, so don't create one. A `CLAUDE.md` that only holds `@AGENTS.md` can be removed once contributors have that version. If it has its own content, suggest moving that to `AGENTS.md` and removing the file.
   - If the user's own instructions describe personal files for each project, such as a local notes file that imports `AGENTS.md` or a backlog file, create the missing ones as those instructions describe. In existing ones, add what the instructions say they should hold and is missing, such as an import, and list what you added. Check Git ignores them (`git check-ignore <file>`), and add any it doesn't to `.git/info/exclude`.
   - Compare the project's `AGENTS.md` and the user's local notes with the instructions the user's agent loads in every project (their global instructions), and with the README and docs. List what repeats them, and suggest removing it, keeping only what's specific to the project. A committed `AGENTS.md` should hold no personal preferences: suggest moving those to the local notes.
10. **Follow the issues the code links to.** Run `scripts/referenced-issues.py <checkout>`. It finds the drupal.org issue links in the files Git tracks, such as `@see` and `@todo` comments about core bugs, and prints the open and closed issues of other projects, each with the files and lines that link to it:
    - Open issues: if the user triages with the `project-triage` skill, add the missing ones to the `watch` list of the checkout's `.claude/project-triage.md` (see that skill's "Profile"), as `- <url> # <title> (referenced in <file>)`, so they show up with the user's own issues. Create the file if needed, and check Git ignores it as in step 9. Otherwise, list them in the report.
    - Closed issues: the code linking to them may hold a workaround or `@todo` that can now go. List them with their files and lines as cleanup candidates, in the backlog file the user's instructions describe if there is one (see step 9), or in the report. Change no code.
11. **Compare with best practices.** Check the project against each item in `references/best-practices.md`, and list what it's missing, each with the change you'd make. Ask which to make, then edit the working copy; project settings are changed as their section says. Don't commit or create branches, since the user may want these in an issue and merge request of their own. Hand docs work to the skills the list names.
12. **Report** the directory, the site's URL, the branch status, the add-ons (`ddev add-on list --installed`), the check results, the issues added to the watch list and the closed ones still linked, and the agent instruction, best-practice and project setting changes made or left to do. Include how to run the checks:
   - on the host: `ddev phpunit <path>` (put the path first, so the command adds core's test bootstrap), `ddev phpstan`, `ddev phpcs` and `ddev eslint`;
   - inside the web container: the same scripts, from `/var/www/html`, e.g. `.ddev/commands/web/phpunit tests/src/Kernel`.


## Drupal core

Core is Drupal itself, so it doesn't use ddev-drupal-contrib. Set it up with [ddev-drupal-core-dev](https://github.com/justafish/ddev-drupal-core-dev), whose README this follows:

1. Clone `git@git.drupal.org:project/drupal.git`, which checks out `main`, where core MRs go. If another core checkout exists, `git clone --reference-if-able <it> --dissociate` saves downloading its history again.
2. `ddev config --omit-containers=db --disable-settings-management --php-version=<version>`, with the PHP version core's `composer.json` requires, then remove `name:` as in step 3. Tests use SQLite, so there's no database container.
3. `ddev start`, `ddev composer install`, then `ddev add-on get justafish/ddev-drupal-core-dev` and any add-ons the user's instructions list, then `ddev restart`.
4. Create `sites/default/files` (`ddev exec mkdir -p sites/default/files`): the add-on's test database is `sites/default/files/db.sqlite`, and kernel tests fail with "unable to open database file" until the directory exists.
5. Run one kernel test with `ddev phpunit <path>`, e.g. `ddev phpunit core/tests/Drupal/KernelTests/Core/Entity/EntityReferenceSelection`. The lint commands (`ddev drupal lint:phpcs`, `lint:phpstan`, `lint:js`, `lint:css`, `lint:cspell`, or `ddev drupal lint` for all) check the whole of core, so only run them when asked.

Then continue with steps 7 and 9, and report as in step 12 with the add-on's commands. Skip steps 8, 10 and 11: they're about contrib projects' setup, their links to core issues, and CI. Don't add Drush, which changes core's Composer dependencies: `ddev drupal install standard` installs a site, and `ddev drupal uninstall` resets it.
