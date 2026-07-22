---
name: claude-allows
description: Use when setting up Claude Code permissions in a repo, or to audit an existing .claude/settings.local.json — adds standard git/test/web permissions for a fresh repo, or categorizes and cleans up a drifted allow/deny list ([add]/[modify]/[remove]/[annotated]).
allowed-tools: [Read, Edit, Write, Glob, Grep, Bash]
---

# claude-allows

Manage the `permissions.allow` / `permissions.deny` arrays in the current repo's
`.claude/settings.local.json`. Two modes:

- **New repo** (allow list absent or empty) — add the standard defaults, sort, report.
- **Existing repo** — **audit** the current lists: categorize into `[add]` / `[modify]` /
  `[remove]` / `[annotated]`, auto-apply safe changes, prompt on judgment calls, and remember
  "keep this one" decisions so the same entries are never re-flagged.

## Standard allow defaults

```json
"Bash(find:*)",
"Bash(gh pr:*)",
"Bash(git add:*)",
"Bash(git checkout:*)",
"Bash(git commit:*)",
"Bash(git diff:*)",
"Bash(git log:*)",
"Bash(git status:*)",
"Bash(glab api:*)",
"Bash(glab mr:*)",
"Bash(glab repo view:*)",
"Bash(grep:*)",
"Bash(ls:*)",
"Bash(pre-commit run:*)",
"Bash(uv add:*)",
"Bash(uv run:*)",
"Bash(uv sync:*)",
"Bash(wc:*)",
"Bash(xargs cat:*)",
"Skill(claude-dev-skills:*)",
"WebFetch(domain:github.com)",
"WebFetch(domain:raw.githubusercontent.com)",
"WebSearch"
```

## Standard deny defaults

```json
"Read(**/__pycache__/**)",
"Read(.venv/**)"
```

## Sidecar annotations — `.claude/claude-allows.json`

Claude Code settings are **strict JSON** — no comments, and unknown keys inside
`settings.local.json` are not guaranteed to survive a rewrite. So "keep this despite the flag"
decisions live in a **separate gitignored** file, `.claude/claude-allows.json`, which Claude Code
never reads:

```json
{
  "keep": {
    "Bash(chmod +x *)": "CI build script",
    "WebFetch(domain:internal.corp)": "prod dashboard, keep"
  }
}
```

- Keys = exact permission strings the user chose to keep. Values = optional note (may be `""`).
- Any entry listed here is **skipped** from `[modify]`/`[remove]` flagging and counted under
  `[annotated]`.

## Step 1 — Read state

1. Read `.claude/settings.local.json` in the current working directory if it exists (do not error
   if missing). Parse `permissions.allow` (default `[]`) and `permissions.deny` (default `[]`).
2. Read the sidecar `.claude/claude-allows.json` if it exists (default `{ "keep": {} }`).

## Step 2 — Detect mode

- `permissions.allow` **absent or empty** → **new-repo mode** (Step 3a).
- Otherwise → **audit mode** (Step 3b).

## Step 3a — New-repo mode

1. Merge the standard allow defaults into `permissions.allow` and the standard deny defaults into
   `permissions.deny` — skip any already present (exact string match).
2. Sort both arrays alphabetically. Write `.claude/settings.local.json`, creating `.claude/` and
   the file if needed.
3. Report which entries were added and which were already present, for both allow and deny.
4. Continue to **Step 4** (gitignore).

## Step 3b — Audit mode

Two wildcard forms are **behavior-identical**: `Bash(git add *)` matches exactly what
`Bash(git add:*)` matches. Treat them as the same entry. The space form is canonical (it is what
Claude Code's permission dialog writes).

**a. Auto-apply safe changes (no prompt):**
   - **[add]** — add any standard allow/deny default not already present (functional match, not
     just exact string).
   - **[modify] collapse** — where the list contains **both** the colon and space form of the same
     command, drop one (keep the form the defaults already use for that command, else the space
     form). Behavior-preserving.

**b. Categorize the remainder** into the two judgment buckets — skipping any entry present in the
   sidecar `keep` set:
   - **[modify]** — scope fixes to propose:
     - *too loose*: a broad entry that is a superset of others or unusually wide
       (e.g. `Bash(git:*)` over `Bash(git add:*)` / `Bash(git status:*)`; a bare `Bash(chmod *)`).
     - *too specific / redundant-narrow*: a narrow entry already covered by a broader one
       (e.g. `Bash(uv run pytest:*)` under `Bash(uv run:*)`; `Skill(claude-dev-skills:update-docs)`
       and `Skill(update-docs)` under `Skill(claude-dev-skills:*)`).
   - **[remove]** — entries that look added for a single task/run and now stale:
     - `WebFetch(domain:...)` for anything other than the standard `github.com` /
       `raw.githubusercontent.com`,
     - complex shell one-liners (contain `sh -c`, quoted `xargs`, chained `&&`),
     - `chmod`, or anything narrowly bound to one specific path or URL.

**c. Print the categorized report**, e.g.:

```
[add]       2 defaults added: Bash(git diff:*), WebSearch
[modify]    3
              collapse (applied): Bash(git add *) + Bash(git add:*) -> one
              tighten? Bash(git:*) is a superset of 3 narrower git entries
              redundant? Skill(update-docs) already covered by Skill(claude-dev-skills:*)
[remove]    2 one-off candidates:
              Bash(chmod +x *)
              Bash(xargs -I {} sh -c '...')
[annotated] 1 kept (skipped): Bash(chmod +x *)   ← only if already in sidecar
```

**d. Ask once** for approval on the `[modify]` (non-collapse) and `[remove]` candidates. The user
   may: approve some/all, reject, or say **"keep <entry>"** (naming the entry). For each "keep", add that exact
   string to the sidecar `keep` map (with an optional note) so it is never re-flagged.

**e. Apply** the approved edits. Sort both arrays alphabetically. Write
   `.claude/settings.local.json` (strict JSON, no comments) and, if it changed,
   `.claude/claude-allows.json`.

## Step 4 — gitignore

Ensure `.claude/claude-allows.json` is ignored: if the repo's `.gitignore` does not already
contain that path, append it. Do not duplicate the line.

## Rules

- **Strict JSON only.** Never write comments or annotation keys into `settings.local.json` —
  annotations live only in `.claude/claude-allows.json`.
- **Never touch entries in the sidecar `keep` set** — they are skipped from flagging and counted
  under `[annotated]`.
- **Behavior-preserving collapse only.** Auto-collapse only genuine colon-vs-space twins of the
  *same* command. Never auto-merge a genuinely broad+narrow pair (e.g. `Bash(git:*)` vs
  `Bash(git add:*)`) — that changes what is allowed; propose it under `[modify]` and ask.
- **Never flag `Bash(grep:*)` or `Bash(find:*)`** — they are intentionally kept alongside the
  dedicated Grep/Glob tools.
- **Audit the deny list the same way** as the allow list.

## Common Mistakes

- Writing annotations into `settings.local.json` (comments or a custom key) — it is strict JSON and
  the key may be stripped on rewrite. Use the sidecar.
- Treating colon vs space (`git add:*` vs `git add *`) as a scope difference — they match
  identically; the pair is a redundant dupe to collapse, not a `[modify]` scope change.
- Removing a one-off the user actually needs. When in doubt, propose it under `[remove]` and let
  the user say "keep" — that is what the sidecar is for.
