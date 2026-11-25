# capture-session

At the end of a working session, it finds what's worth keeping: corrections, preferences, conventions, decisions and unfinished work. It proposes where each belongs, such as your global or project instructions, your local notes or backlog, a PR's remaining tasks, an issue, or the skill that should learn from it. It also finds notes the session made outdated.

Unfinished work can go in your backlog as a self-contained prompt that a later session can pick up, or into PRs and issues through [project-backlog](../project-backlog/README.md).

It follows the capture rules in your instruction files, such as `AGENTS.md`, where you have them. It shows every change first and writes only what you approve, plus anything your rules allow without asking (such as notes on corrections).

Usage: `/capture-session` before you end a session.
