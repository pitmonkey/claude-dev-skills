---
name: pr
description: Use when the user wants to push the current branch and open a GitHub pull request or a GitLab merge request. Triggered by /pr.
---

# Pull Request (pr)

Push current branch and open a change request on the remote's forge — a **pull request** on
GitHub (`gh`) or a **merge request** on GitLab (`glab`) — with a generated title and
description. Typically run after `/sc`.

The forge is detected once (Step 0) and every forge-specific command comes from the table
below. Everything else — branch safety, push, title/body rules — is identical either way.

## Forge command table

| Purpose | GitHub (`gh`) | GitLab (`glab`) |
|---|---|---|
| Existing request? | `gh pr view` | `glab mr view` |
| Create | `gh pr create --title … --body …` | `glab mr create --title … --description … --yes` |
| Auth hint | `gh auth login` | `glab auth login --hostname <host>` |
| Noun in output | PR | MR |

## Process

### Step 0 — Detect forge

Extract the hostname from `git remote get-url origin` — handles both
`git@HOST:owner/repo.git` and `https://HOST/owner/repo.git`. Then walk this ladder and
**stop at the first hit**. Self-hosted GitLab and GitHub Enterprise both use arbitrary
hostnames, so URL substring matching alone is not enough.

1. Host is `github.com` (or `*.github.com`) → **GitHub**. Free, offline, certain.
2. **Ask the CLIs which hosts they know** — offline, exact, and unaffected by whether the
   token is currently valid:
   - Host appears in `glab auth status 2>&1` → **GitLab**
   - Host appears in `gh auth status 2>&1` → **GitHub**

   Use the commands, not the config files: a snap-installed `glab` keeps its config under
   `~/snap/glab/current/.config/glab-cli/`, not `~/.config/glab-cli/`, so a hard-coded path
   silently finds nothing.
3. Tiebreak on repo contents — `.gitlab-ci.yml` at root → **GitLab**;
   `.github/workflows/` → **GitHub**. If both exist, it is not a tiebreak; go to 4.
4. Probe the repo (costs a network call):
   `glab repo view >/dev/null 2>&1` succeeds → **GitLab**;
   `gh repo view >/dev/null 2>&1` succeeds → **GitHub**.
5. Still ambiguous → **stop and ask the user** which forge this remote is. Do not guess.

A probe failure at step 4 is not proof the forge is wrong — it also fires on an expired
token or no network. That is exactly why steps 2 and 3 run first, and why step 5 asks
rather than defaulting. If the user names the forge, say so in the report and use it.

If the resolved forge is GitLab and `glab` is not on PATH, say so and tell the user to
install it (`https://gitlab.com/gitlab-org/cli`) rather than falling back to `gh`.

Remember the answer for the whole run — do not re-detect at each step.

### Step 1 — Branch check

Run `git branch --show-current`.

If on `main` or `master`: stop and tell the user — there is nothing to open a request from
on the default branch.

### Step 2 — Check for unpushed commits

Run `git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log --oneline -10`.

If no commits ahead of remote (and the branch already has an open request): tell the user
and stop.

### Step 3 — Push branch

```bash
git push -u origin $(git branch --show-current)
```

If push fails due to no upstream: the `-u` flag sets it. If it fails for another reason,
report the error and stop.

### Step 4 — Analyse changes

Gather context for the description:

```bash
git log $(git merge-base HEAD origin/main)..HEAD --oneline
git diff $(git merge-base HEAD origin/main)..HEAD --stat
```

Use this to understand: what changed, and why (from commit messages).

### Step 5 — Create the request

First check one does not already exist for the branch. Pin the read to the URL field so the answer
is a bare URL, not a page of prose:

```bash
gh pr view --json url --jq '.url'          # GitHub
glab mr view --output json | jq -r '.web_url'   # GitLab
```

If one is open, report its URL and skip creation.

**GitHub:**

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <test step>
EOF
)"
```

**GitLab:**

```bash
glab mr create --title "<title>" --yes --description "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <test step>
EOF
)"
```

`--yes` (`-y`) skips the submit confirmation so the command is non-interactive. Do not use
`glab mr create` without it — it drops into a prompt. Do NOT use `--fill`: it overwrites the
generated title/description with raw commit info and re-pushes the branch. Flags verified on
`glab` 1.108.0 (`-t/--title`, `-d/--description`, `-y/--yes`); if a prompt still appears, add
`--target-branch <default branch>`.

Content rules are the same on both forges:

- Title: ≤70 chars, imperative mood, describes what the change does
- Summary: 2–4 bullets covering what changed and why
- Test plan: concrete steps to verify the change works
- Do NOT include implementation noise (file names, line counts)

### Step 6 — Report

Print the URL returned by `gh pr create` / `glab mr create`. Call it a **PR** on GitHub and
an **MR** on GitLab.

If that stdout was not captured, re-read the URL with the same pinned commands as Step 5 rather than
reporting without one — callers such as `gitgo` need the URL as a value, not just on screen.

## Rules

- NEVER force-push
- NEVER push to `main` or `master`
- NEVER add a "Generated with Claude Code" footer, "🤖" marker, or `Co-Authored-By: Claude`
  trailer to the body — no AI attribution. Applies to both forges.
- If the forge CLI is not authenticated, tell the user to run `gh auth login` or
  `glab auth login --hostname <host>` for the self-hosted host
- Do not re-create a request if one already exists for the branch — check with
  `gh pr view` / `glab mr view` first
- Detect the forge once (Step 0) and reuse that answer; never mix `gh` and `glab` in one run
