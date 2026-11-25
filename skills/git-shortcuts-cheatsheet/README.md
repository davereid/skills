# git-shortcuts-cheatsheet

Builds a one-page PDF you can print that lists GitHub and GitLab keyboard shortcuts side by side. It covers working with issues, pull/merge requests and code review, and calls out the shortcuts that work differently on the two hosts.

## Usage

```
/git-shortcuts-cheatsheet
/git-shortcuts-cheatsheet add the shortcut for <command>
```

The skill reads the current GitHub and GitLab shortcut docs, compares them with the sheet, and tells you what changed. It then updates `cheatsheet.html` and renders the PDF.

## Requirements

- Node.js with Playwright, or Chrome/Chromium for the headless fallback
- `pdftoppm` (from poppler) for checking the page layout
