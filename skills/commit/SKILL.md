---
name: commit
description: Generate a commit message and commit staged changes. Never pushes.
---

Commit the currently staged changes to git.

## Process

1. Run `git status` — if nothing is staged, stop and tell the user
2. Invoke the `generating-commit-messages` skill to produce the commit message
3. Commit using the generated message — NEVER amend, NEVER force, NEVER skip hooks
4. Run `git status` to confirm the commit succeeded
5. Report the commit hash and summary

## Rules

- NEVER push — not even if the user explicitly asks within this skill. Pushing is always out of scope.
- NEVER use `--no-verify`
- NEVER use `--amend` unless the user explicitly requests it
- If the pre-commit hook fails, fix the underlying issue and create a NEW commit — do not amend
- Always use a HEREDOC to pass the commit message to avoid shell escaping issues
