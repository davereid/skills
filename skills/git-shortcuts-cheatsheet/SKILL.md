---
name: git-shortcuts-cheatsheet
description: Build a printable GitHub and GitLab keyboard shortcuts cheatsheet PDF.
allowed-tools: Bash, Read, Edit, WebFetch
---

# GitHub & GitLab shortcuts cheat sheet

Build a one-page, US Letter PDF that compares GitHub and GitLab keyboard shortcuts for working with issues, pull/merge requests (PRs/MRs) and code review. The current sheet is `cheatsheet.html` in this skill's directory. Edit that file and render it. Don't rebuild the sheet from scratch.

## 1. Check the docs

Shortcuts change, so fetch both pages every time and list every shortcut by section:

- https://docs.gitlab.com/user/shortcuts/
- https://docs.github.com/en/get-started/accessibility/keyboard-shortcuts

Compare them with the rows in `cheatsheet.html`. Note anything added, removed or changed that fits the sheet's scope (step 2). If the user asked for specific commands, confirm they're in the docs before you add them. Show the user the list of changes before you edit.

## 2. Scope and layout

Keep only shortcuts that help with issues, PRs/MRs and code review. Leave out project boards, network graphs, Actions logs and the rich-text editor's formatting keys.

The left column has these sections:

- **Getting around**
- **Issue & PR/MR lists**
- **Inside an issue or PR/MR**
- **Watch out when switching platforms**: for shortcuts that differ between hosts, such as the swapped keys for submitting review comments, what `c` does on each host, and GitLab's case-sensitive keys.

The right column has these sections:

- **Code review (diffs)**
- **Writing comments**
- **Browsing code**

Every section is a table with three columns: Action | GitHub | GitLab.

Conventions already used in the HTML:

- `Mod` means Cmd on Mac and Ctrl on Windows/Linux. `Alt` means Option on Mac.
- A sequence is written `<kbd>g</kbd><span class="then">→</span><kbd>i</kbd>`.
- Use `<td class="na">—</td>` when a shortcut isn't in that host's docs.
- Use `<span class="note">` for small qualifiers such as "issues" or "MRs".
- Bold the action names of rows that differ between hosts in a way that would trip someone up.
- Update the "Compiled <Month Year>" date in the footer.

## 3. Render

From this skill's directory, write the PDF to the user's current working directory, or to wherever they asked for it:

```bash
node -e "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+process.argv[1]);await p.pdf({path:process.argv[2],format:'Letter',preferCSSPageSize:true,printBackground:true});await b.close();})()" "$PWD/cheatsheet.html" "<output>/git-shortcuts-cheatsheet.pdf"
```

If Playwright isn't installed, use headless Chrome instead:

```bash
"<chrome binary>" --headless --no-pdf-header-footer --print-to-pdf=<output>.pdf cheatsheet.html
```

## 4. Verify

Render the PDF to PNG with `pdftoppm -r 110 -png <pdf> prev`, then look at the result and check that:

- it's exactly one page, so `prev-1.png` is the only file
- no key combination overflows its cell
- the two columns end at about the same height

If the sheet spills onto a second page, first remove the least useful rows. If that isn't enough, reduce the `td` padding or the `section` margins. Keep body text at 8pt or larger.

## 5. Report

Give the user the PDF and a summary of what changed. Point out anything they should check on the live docs, such as the submit keys that are swapped between hosts, or a shortcut that works but isn't listed in the docs (GitHub's `?`).
