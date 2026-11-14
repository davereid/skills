# Drupal reviews

Load this for any Drupal site or extension, whatever the host (see step 1). It adds Drupal checks to "Simpler or existing code" and "Conventions" in step 8. Search core and contrib as installed in the user's checkout (`web/core`, `web/modules/contrib`; a module set up with ddev-drupal-contrib has them too) to confirm each point before raising it, and cite the core file that does it the right way.

## Static analysis

Read the PR's CI results for phpstan (with phpstan-drupal and the deprecation rules), phpcs (`Drupal` and `DrupalPractice`), ESLint with core's config, and CSpell. drupal.org GitLab CI runs all of them; other projects may not. When CI doesn't, run phpstan and phpcs in the review checkout with the project's own config. Don't repeat in comments what CI already reports.

## Core already does it

Look for code that does by hand what core provides:

- **Services:** `arguments` or tags in `*.services.yml` that `_defaults: { autowire: true, autoconfigure: true }` would supply. Find which interfaces core tags automatically in the installed version, rather than from memory: `grep -rn -A1 "registerForAutoconfiguration" web/core --include="*.php"` (core's `CoreServiceProvider` and core modules' service providers). A tag listed there is redundant in `*.services.yml`; any other tag still has to be written out. A `parent` on an autowired service replaces autowiring, so constructor arguments added later aren't passed.
- **Logging:** an injected logger channel in a service, where `LoggerAwareInterface` and `LoggerAwareTrait` would get `logger.channel.<module>` from core. Hook classes are the exception: core doesn't autoconfigure them, so they inject the channel.
- **Hooks:** procedural hooks in `.module` files, where the core version the project supports has `#[Hook]` classes.
- **Config validation:** custom validation for config values, where core's config schema constraints exist (`grep -rn "<constraint>" web/core --include="*.schema.yml"`), e.g. `ExtensionName` and `ExtensionAvailable` for extension names, as in `core.extension`.
- **Caching:** hand-rolled static caches, where a memory cache bin (`cache.memory`, typed as `CacheBackendInterface`) and `__METHOD__`-based cache IDs would do; caches of data from config entities that may be unsaved, without the entity type's list cache tag.
- **JavaScript:** `DOMContentLoaded`, top-level code or jQuery where `Drupal.behaviors` with `once()` belongs; markup built inline instead of `Drupal.theme` functions; untranslated strings instead of `Drupal.t()`; custom announcements or debouncing instead of `Drupal.announce()` and `Drupal.debounce()`.
- **CSS:** physical properties (`margin-left`) where logical ones (`margin-inline-start`) support right-to-left languages.
- **Tests:** a custom test logger instead of Symfony's `BufferingLogger`; external URLs where the test site's own pages would do; recipe tests that don't use `RecipeRunner`; a functional test where a kernel test would do.

## Patterns core avoids

- Entity storage stored in a property (phpstan-drupal's `drupal.entityStoragePropertyAssignment`): inject the entity type manager and call `getStorage()` where it's used.
- Plugins, forms and controllers that override the constructor to inject services, instead of setting them in `create()`; `readonly` properties a subclass's `create()` can't set.
- Overrides of a parent's method (`defaultConfiguration()`, `buildConfigurationForm()`, `getCacheTags()`) that don't call `parent::`, without a comment saying why.
- Non-static callbacks stored in a form (`#element_validate`, `#validate`, `#entity_builders`); render callbacks (`#pre_render`, `#lazy_builder`) without `#[TrustedCallback]`.
- `$container->has() ? $container->get() : NULL` instead of `ContainerInterface::NULL_ON_INVALID_REFERENCE`.
- Update hooks that load or save entities, or call services that invoke hooks; `hook_deploy_NAME()` in a contributed module (it only runs through Drush).
- Deprecated core APIs, or APIs missing from the lowest core version `core_version_requirement` allows.
- A contrib dependency that's only in `composer.json`, or a version constraint in `.info.yml`: drupal.org builds Composer requirements from `.info.yml`, and CI builds the test site from `composer.json` (`require-dev`).
- A new setting that changes existing sites' behavior, turned on in code rather than only in `config/install`.
- Constraint violations reported on the field list rather than the property they're about (`atPath()`).

These are conventions most Drupal projects share. Where the project's own code or docs do it differently, the project wins (see "Conventions" in step 8).
