---
name: stage
description: Use when you want to stage changed files before a commit, safely skipping .env files, credentials, and other sensitive files
---

Run `git status` to see what has changed, then stage files for commit — but carefully.

## Process

1. Run `git status` to see all modified, new, and deleted files
2. Identify any sensitive files that must NOT be staged:
   - `.env`, `.env.*`, `.env.local`, `.env.production`, etc.
   - Any file containing secrets, credentials, or tokens
   - Private keys (`*.pem`, `*.key`, `id_rsa`, etc.)
3. Stage everything EXCEPT sensitive files using explicit `git add <file>` calls — do NOT use `git add -A` or `git add .` blindly
4. Run `git status` again to confirm what is staged
5. Report what was staged and what (if anything) was deliberately skipped

## Rules

- NEVER stage `.env*` files unless the user explicitly asks for a specific one
- NEVER stage files with secrets or credentials
- If unsure whether a file is sensitive, skip it and mention it to the user
- Prefer adding files by name rather than directory globs
- If there is nothing to stage, say so and stop
