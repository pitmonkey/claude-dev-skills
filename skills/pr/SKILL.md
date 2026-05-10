---
name: pr
description: Use when the user wants to push the current branch and open a GitHub pull request. Triggered by /pr.
---

# Pull Request (pr)

Push current branch and create a GitHub PR with a generated title and description. Typically run after `/sc`.

## Process

### Step 1 — Branch check

Run `git branch --show-current`.

If on `main` or `master`: stop and tell the user — there is nothing to PR from the default branch.

### Step 2 — Check for unpushed commits

Run `git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log --oneline -10`.

If no commits ahead of remote (and branch already has a PR): tell the user and stop.

### Step 3 — Push branch

```bash
git push -u origin $(git branch --show-current)
```

If push fails due to no upstream: the `-u` flag sets it. If it fails for another reason, report the error and stop.

### Step 4 — Analyse changes

Gather context for the PR description:

```bash
git log $(git merge-base HEAD origin/main)..HEAD --oneline
git diff $(git merge-base HEAD origin/main)..HEAD --stat
```

Use this to understand: what changed, and why (from commit messages).

### Step 5 — Create PR

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <test step>

🤖 Generated with [Claude Code](https://claude.ai/claude-code)
EOF
)"
```

- Title: ≤70 chars, imperative mood, describes what the PR does
- Summary: 2–4 bullets covering what changed and why
- Test plan: concrete steps to verify the change works
- Do NOT include implementation noise (file names, line counts)

### Step 6 — Report

Print the PR URL returned by `gh pr create`.

## Rules

- NEVER force-push
- NEVER push to `main` or `master`
- If `gh` is not authenticated, tell the user to run `gh auth login`
- Do not re-create a PR if one already exists for the branch — use `gh pr view` to check first
