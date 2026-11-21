# PHP reviews

Load this for any PHP codebase (see step 1). It adds PHP checks to "Simpler or existing code" and "Conventions" in step 8, on top of any framework reference such as `references/drupal.md`.

## Style nits

Raise these as nits: they don't change behavior.

- `array_merge()` for a fixed number of arrays, where unpacking (`[...$a, ...$b]`) reads better and behaves the same on PHP 8.1 and later: lists are appended, and later string keys replace earlier ones. `array_merge(...$listOfArrays)` for a variable number of arrays is fine. In Drupal, `NestedArray::mergeDeep()` is the choice when nested arrays should be merged rather than replaced.

These are conventions many PHP projects share. Where the project's own code or docs do it differently, the project wins (see "Conventions" in step 8).
