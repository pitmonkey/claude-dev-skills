---
name: claude-allows
description: Use when setting up Claude Code in a new repo and you want to add standard git, test, and web permissions to .claude/settings.local.json
---

Add the following standard permissions to the current repo's `.claude/settings.local.json`:

```json
"Bash(find:*)",
"Bash(git add:*)",
"Bash(git diff:*)",
"Bash(git log:*)",
"Bash(git status:*)",
"Bash(grep:*)",
"Bash(uv add:*)",
"Bash(uv run pytest:*)",
"Bash(uv sync:*)",
"Bash(wc:*)",
"Bash(xargs cat:*)",
"WebFetch(domain:github.com)",
"WebFetch(domain:raw.githubusercontent.com)",
"WebSearch"
```

Also add the following standard deny entries to `permissions.deny`:

```json
"Bash(git push:*)",
"Glob(**/__pycache__/**)",
"Glob(.venv/**)",
"Read(**/__pycache__/**)",
"Read(.venv/**)"
```

## Steps

1. Read `.claude/settings.local.json` in the current working directory if it exists (do not error if missing).
2. Parse the existing `permissions.allow` array (default to empty if not present) and `permissions.deny` array (default to empty if not present).
3. Merge in the standard allow entries above — skip any that are already present (case-sensitive exact match).
4. Merge in the standard deny entries above — skip any that are already present (case-sensitive exact match).
5. Sort both the allow and deny lists alphabetically, then write back to `.claude/settings.local.json`, creating the file (and `.claude/` directory) if needed.
6. Report which entries were added and which were already present (for both allow and deny).
7. Review the full resulting allow list and flag anything notable as observations — do not remove anything, just comment. Examples of things worth flagging:
   - Entries that overlap or are made redundant by others (e.g. `Bash(git:*)` is a superset of `Bash(git add:*)` and `Bash(git status:*)`) — note: `Bash(grep:*)` and `Bash(find:*)` are intentionally included alongside the dedicated Grep/Glob tools and should NOT be flagged
   - Entries that look like one-off research domains that may now be stale (e.g. `WebFetch(domain:docs.somelib.ai)`)
   - Unusually broad or potentially risky permissions
   - Duplicate or near-duplicate entries
