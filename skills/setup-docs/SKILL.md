---
name: setup-docs
description: Set up a drupal.org project's docs/ directory, published with MkDocs.
---

# Set up docs

Gives a drupal.org project a `docs/` directory for developer documentation, built with [MkDocs](https://www.mkdocs.org/) (Material theme) and published at `https://project.pages.drupalcode.org/<name>/` by the `pages` job of drupal.org's GitLab CI templates. The templates' [Pages job documentation](https://project.pages.drupalcode.org/gitlab_templates/jobs/pages/) is the canonical source for how publishing works: follow it where this skill differs, and only add what it doesn't cover.

Use it when a project's README has grown developer sections (plugin APIs, hooks, data formats, long code examples), or it has `docs/` but no `mkdocs.yml` or `pages` job. The `update-docs` skill suggests it.


## Steps

1. Find the project root (the directory with the main `*.info.yml`) and its machine name, and the default branch (`git ls-remote --symref origin HEAD`). Check it uses drupal.org's GitLab CI templates (`.gitlab-ci.yml` includes `include.drupalci.main.yml`). Without a `.gitlab-ci.yml`, stop: Pages needs CI.
2. Say what you'll add and change, and ask before starting.
3. **Move developer docs** out of the README, if it has any: one Markdown page per topic in `docs/`, the text moved as it is. Check every moved line ends up in exactly one page, and fix "see above"-style references that now point elsewhere.
4. **Add `docs/index.md`**, the home page (MkDocs builds it into `index.html`): one line on what the docs cover, a link back to the README for installing and configuring, and a list linking to each page with a line on what it covers. Link between pages with relative `.md` links.
5. **Add `mkdocs.yml`** at the project root from `templates/mkdocs.yml`, filling in the placeholders. If it already exists, keep it and only check `site_url`, `repo_url` and `edit_uri`. Leave out `site_dir`: the `pages` job builds into `public` itself, and `site_dir: public` makes a local build write `public/` into the checkout.
6. **Use the templates' `pages` job.** It publishes from the default branch whenever `docs/` or `mkdocs.yml` change, once both `mkdocs.yml` and `docs/index.md` exist, and runs manually in issue forks' merge requests. It doesn't run for merge requests from the project's own branches, so add the `mkdocs` job from `templates/gitlab-ci-mkdocs.yml` at the end of `.gitlab-ci.yml`: it builds the docs with `--strict` on those branches, only when the docs change, so a broken build fails the merge request, and keeps the site as a "Docs preview" artifact. If `.gitlab-ci.yml` already has a `pages` job that only runs `mkdocs build`, offer to remove it: a project's `pages` job replaces the template's rules and script, which drops its merge request previews, `_PAGES_FORCE_REBUILD`, `SKIP_PAGES`, `_MKDOCS_EXTRA`, `_MKDOCS_STRICT` and logo handling. Add `mkdocs.yml` to `_CSPELL_IGNORE_PATHS` in `.gitlab-ci.yml`'s `variables` (comma-separated, if the variable is already set). Words in `docs/` that CSpell flags go in the project's `_CSPELL_DICTIONARY` file. Ask the user to check that _Deploy > Pages > Domains & settings > Use unique domain_ is off, or the site is published at another URL than `site_url`.
7. **Offer API docs**, for projects with a PHP API other modules use (services, traits, base classes), such as [Helper](https://git.drupalcode.org/project/helper): Markdown pages generated from the PHP code's docblocks into `docs/api/`, built into the same site. Ask first; most projects don't need them. Helper is the example to copy from:
   - `require-dev`: `phpdocumentor/shim` (allowed in `config.allow-plugins`) and `saggre/phpdocumentor-markdown`. Call out both new dependencies for the user to confirm.
   - A `docs` Composer script that runs `phpdoc` with the Markdown template on `src` (and other public code, such as test traits) into `docs/api`, then a PHP script (Helper's `.gitlab/fix-api-docs.php`) that fixes the generated pages for MkDocs: `index.md`, and links with `.md`. Adapt its namespaces to the project. Pass every documented path with `-d`, including single files such as `<module>.api.php` (`-d src -d <module>.api.php`): phpDocumentor ignores `-d` when `-f` is given, so `-d src -f <module>.api.php` documents only the file (2026-11-21: analytics !40's API docs had only the hooks).
   - `/docs/api` and `/.phpdoc` in `.gitignore`: the pages are generated, never committed. Link `api/index.md` from `docs/index.md`.
   - The `pages` job override from `templates/gitlab-ci-api-docs.yml` at the end of `.gitlab-ci.yml`, with the documented paths filled in. It needs PHP, and its rules add those paths, so code changes republish the docs. Change the `mkdocs` job (step 6) to match, as Helper's does: the same image, `needs: [{job: composer}]`, `composer run docs` before `pip install`, and `changes: *api-docs-changed-files`.
   - Delete `docs/api` and run `composer run docs` before the local build. Since the pages are never committed, CI only has the ones the script generates, but a local build also uses any older ones left in `docs/api`, and those can hide pages the script no longer generates. Check that `docs/api` has a page for each documented class and file.
8. **Build it locally** with strict mode, in a virtual environment in a temporary directory outside the repository:
   ```
   python3 -m venv <tmp>/venv
   <tmp>/venv/bin/pip install mkdocs-material
   <tmp>/venv/bin/mkdocs build --strict -f mkdocs.yml --site-dir <tmp>/site
   ```
   Fix warnings (usually broken links), then delete the temporary directory. The `pages` job also builds with `--strict`, so broken links fail it. If installing isn't possible, say the merge request preview (below) will check it instead.
9. **Link the README to the docs:** a short "Developer documentation" section that links to the docs site and to each page with relative links (`docs/<page>.md`). Then run `update-docs`, which builds `README.html` with `--docs` so those links go to the docs site.
10. Tell the user:
   - the site appears at `https://project.pages.drupalcode.org/<name>/` after the first pipeline on the default branch that changes `docs/` or `mkdocs.yml`; until then, its links 404;
   - in a merge request from an issue fork, the `pages` job is manual: run it to publish a preview, at the URL its log prints;
   - to check the `pages` job after merging.
