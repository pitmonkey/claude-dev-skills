---
name: sc
description: Use when the user wants to stage and commit current git changes, including keeping documentation up to date before committing. Triggered by /sc.
---

# Stage Commit (sc)

Stage current changes, update documentation, and commit — all in one step. Never pushes.

## Process

Run these steps in order:

### Step 0 — Branch check

Run `git branch --show-current` to get the current branch name.

If the current branch is `main` or `master`:
1. Ask the user: **"You're on `main`. Create a new branch? (y/n)"**
2. If **no**: continue to Step 1 on main.
3. If **yes**:
   - Look at `git diff HEAD` and any staged changes to understand what the work is about.
   - Generate a short, kebab-case branch name that describes the changes (e.g. `feat/add-login-page`, `fix/webhook-timeout`).
   - Run `git checkout -b <branch-name>` to create and switch to it.
   - Check if there are commits on main that should move to the new branch: run `git log origin/main..HEAD --oneline`. If any commits exist, they are already on the new branch (since we branched from main) — no action needed, just inform the user.
   - Continue to Step 1.

If already on a feature branch (anything other than `main`/`master`): proceed directly to Step 1.

### Step 1 — Update documentation

Invoke the `update-docs` skill. Always. Every `/sc` invocation, without exception.

This step syncs documentation against the **current state of the whole codebase** — not against the pending diff. Doc drift accumulates across every commit that never touched docs, and this is the checkpoint where it gets reconciled.

- An empty or clean working tree is **not** a reason to skip this step. There may be hundreds of prior commits that never updated the docs.
- A small diff is not a reason to skip it either.
- Do not gate this step on `git status`, `git diff`, or commit size. Run it first, unconditionally.

### Step 2 — Check for changes

Now run `git status`. If the working tree is still clean after Step 1 — meaning `update-docs` also found nothing to change — stop and tell the user.

### Step 3 — Stage changes

Follow the `stage` skill to safely stage all modified files:
- Run `git status` to see all modified, new, and deleted files
- Stage files explicitly by name — do NOT use `git add -A` or `git add .` blindly
- Skip `.env*` files, private keys, and any file containing secrets or credentials
- Include any documentation files updated in Step 1
- Run `git status` again to confirm what is staged

### Step 4 — Commit

Invoke the `generating-commit-messages` skill to produce the commit message, then commit:
- NEVER amend unless the user explicitly requests it
- NEVER use `--no-verify`
- NEVER skip hooks — if a hook fails, fix the issue and create a NEW commit
- Always pass the commit message via HEREDOC to avoid shell escaping issues
- Run `git status` after committing to confirm success and report the commit hash

## Rules

- **ALWAYS run `update-docs`** — on every invocation, before the clean-tree check. Never skip it because the working tree is clean, because there is nothing to commit, or because the diff is small.
- **NEVER push** — not under any circumstances, even if asked. Pushing is always out of scope for this skill.
- NEVER stage sensitive files (`.env*`, `*.pem`, `*.key`, credentials)
- If there is nothing to stage after Step 3, stop and tell the user
- If a pre-commit hook fails, fix the underlying issue and create a NEW commit — do not amend
