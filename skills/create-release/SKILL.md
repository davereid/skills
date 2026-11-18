---
name: create-release
description: Tag and publish a drupal.org project release, with notes and docs.
---

# Create release

Prepares and tags a release of a drupal.org project, drafts its release notes, and walks the user through publishing it. Drupal.org has no API for creating release nodes or editing project pages, so those steps end with text for the user to paste and a link to the form.

Never push without asking first, and stop at the first check that fails.


## Steps

1. **Find the project.** The machine name is the main `*.info.yml`'s file name. Check `git remote -v` points at `git@git.drupal.org:project/<name>.git` (or `git.drupalcode.org`).
2. **Check the branch.** It's a release branch such as `1.x` or `2.0.x`, the working tree is clean (untracked files are fine), and it matches `origin` (`git fetch`, then `git status -sb`).
3. **Check the branch's pipeline.** GitLab's API is public for drupal.org projects, so `curl` works without a token (`glab api` with the same path works too):
   ```
   curl -sS "https://git.drupalcode.org/api/v4/projects/project%2F<name>/pipelines?ref=<branch>&sha=<git rev-parse HEAD>"
   curl -sS "https://git.drupalcode.org/api/v4/projects/project%2F<name>/pipelines/<id>/jobs?per_page=100"
   ```
   - No pipeline for `HEAD`: say so and stop. Drupal.org only runs pipelines when the project has GitLab CI set up (`.gitlab-ci.yml`).
   - `running` or `pending`: wait for it, checking every minute or two, or let the user decide to come back later.
   - `failed` or `canceled`: list the failed jobs with their `web_url`, and stop.
   - `success`: still list the jobs with `status: failed` and `allow_failure: true`. Drupal.org's template allows jobs like `phpunit (next major)`, `cspell` and `phpstan` to fail, so a green pipeline can hide them. Show them to the user and ask whether to release anyway.
4. **Suggest the version.** Find the last tag on this branch: `git describe --tags --abbrev=0` (cross-check with `drupalorg project:releases <name>`), and only count tags of the branch's major version (`1.*` on `1.x`, `8.x-1.*` on `8.x-1.x`). Read `git log <last tag>..HEAD` and `git diff --stat <last tag>..HEAD`, then suggest one exact tag with semantic versioning:
   - **Patch** (`1.2.3` → `1.2.4`): bug fixes, docs and test changes only.
   - **Minor** (`1.2.3` → `1.3.0`): new features, settings, public methods, plugins or Drush commands; new update hooks; deprecations; a higher minimum Drupal core version or PHP version.
   - **Breaking changes** (removed or changed public APIs or settings, without a deprecation): don't tag them on this branch. They belong on a new major branch (`2.x`), so say so and stop.
   - **Pre-releases:** after `1.0.0-alpha1`, suggest `1.0.0-alpha2`, or ask whether to move to `-beta1`, `-rc1` or `1.0.0`.
   - **No tag on this branch yet** (`git describe` fails with "No tags can describe", or only finds other branches' tags, such as an old `5.x-1.0`): suggest `<major>.0.0-alpha1` for an unfinished branch or `<major>.0.0` for a stable one, and ask which.
   - Legacy `8.x-` branches have no patch number: `8.x-1.4` → `8.x-1.5`.

   Show the last tag, the suggested tag and a one-line reason (e.g. "minor: adds the Broken links report"), and ask the user to confirm or pick another. Check the tag doesn't already exist (`git ls-remote --tags origin <version>`).
5. **Update the docs.** Run the `update-docs` skill against everything since the previous tag. If it changes `README.md` or `docs/`, show the diff and ask the user to commit it (and push, then wait for that pipeline) before tagging.
6. **Tag.** Create an annotated tag on `HEAD`: `git tag -a <version> -m <version>`. Ask before pushing it with `git push origin <version>`.
7. **Release notes.** Generate them from the tags, as HTML:
   ```
   drupalorg maintainer:release-notes <previous> <version>
   ```
   For a first release with no previous tag, pass the first commit (`git rev-list --max-parents=0 HEAD`). Add a short opening paragraph in plain language on what's new, and call out anything site builders must do: update hooks, changed or removed settings, new requirements or a new minimum Drupal core version. Fix what the generator gets wrong: it lists `Co-Authored-By` trailers, such as an AI agent's, as drupal.org contributors (remove them and fix the count), it leaves out commits with no issue number, and it can list an issue with no title. Save the notes to a temporary file outside the repository and show them.
8. **Change records.** List the project's change records, which are often left as drafts: `https://www.drupal.org/api-d7/node.json?type=changenotice&field_project=<project nid>&limit=50` (the nid is in step 10). A record is a draft when `field_change_record_status` is false; its version is `field_change_to` and its issues are `field_issues[].id`. Flag each draft whose version is this release or an earlier one, or whose issues appear in `git log <previous>..<version>`, and check its version against the release that first shipped the change (`git tag --contains <commit>`). Also suggest a change record for any deprecation or API change in this release that has none. Drupal.org has no API for editing them, so draft any corrected description as HTML for the user to paste (`<h3>` for "Before" and "After", PHP in `<?php … ?>`, no `<p>` tags), and link `https://www.drupal.org/node/<nid>/edit`, where they set it to published.
9. **Notify dependents.** Skip this for releases that only fix bugs. Otherwise, list what other projects may need to act on: deprecations, a higher minimum Drupal core or PHP version, and new or changed public classes, methods, services, plugin types (annotations or attributes), hooks or config schema. Find the projects that use them by searching drupal.org's GitLab for each name (`glab api --hostname git.drupalcode.org "groups/project/search?scope=blobs&per_page=100&search=<url-encoded name>"`, which needs a login). Leave out results under `/contrib/` or `/vendor/`, which are copies bundled in distributions. Also check the projects that list it as a dependency on `https://www.drupal.org/project/<name>/ecosystem`. Each source finds projects the other misses, such as code that extends a class without declaring the dependency. Add any dependents the project's `AGENTS.md` lists under "Known dependents". For each project that's affected, draft an issue for its queue: what changed and in which release, what it should do, and links to the release notes and any change record. Show each draft, and create it only after the user's go-ahead.
10. **Publish.** Give the user:
   - The release form: `https://www.drupal.org/node/add/project-release/<project nid>`. Get the nid from `https://www.drupal.org/api-d7/node.json?field_project_machine_name=<name>` (`list[0].nid`). They choose the tag, paste the notes and choose the release type (new features, bug fixes, security). Also suggest the release's short description: one plain sentence or two under 120 characters (count them with code) on what's new and any new requirement, e.g. "Adds Drupal 12 support and the #[EmbedType] plugin attribute. Requires Drupal 11.3 or later."
   - If `update-docs` changed `README.html` or its summary, the project page's edit form (`https://www.drupal.org/node/<project nid>/edit`) to paste them into.
11. **Check.** Once the user says it's published, `drupalorg project:releases <name>` lists it. Packaging can take a few minutes.
