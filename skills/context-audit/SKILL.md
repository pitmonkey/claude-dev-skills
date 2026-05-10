---
name: context-audit
description: Use when the user runs /context-audit or explicitly asks to audit
  their Claude Code setup for token waste, context bloat, or CLAUDE.md structure
  issues. Do not auto-trigger.
user-invocable: true
---

# Context Audit

Bloated context costs more and produces worse output. This skill finds the waste
and tells you what to cut. Run only when explicitly invoked — never suggest proactively.

## Step 1: Get /context Data

Check the conversation for /context output. If not present, say:

> "Run /context in your session terminal and paste the output here. I can't run
> slash commands myself, but once I can see the breakdown I'll audit everything it flags."

**STOP.** Do not proceed to Step 2 until /context output is in the conversation.

## Step 2: Audit (run checks in parallel where possible)

Audit each category from largest to smallest based on /context output.

### CLAUDE.md Structure

Read every CLAUDE.md file: project root, `.claude/`, `~/.claude/`. Classify every
section using **semantic reasoning — not keyword matching**:

**Universal context** (keep — needed for virtually every task):
- Project purpose and one-line description
- Core commands (run, test, lint)
- Architecture overview and non-obvious technical decisions
- Workflow instructions that apply to all tasks

**Task-specific reference material** (should live in a sub-file with a pointer):
- Deployment steps, CI pipeline details, container/k8s config
- Testing conventions beyond the run command
- API standards and conventions
- Environment variable tables that duplicate content in a docs file
- Any section only needed when working on that specific topic

Run three checks:

### Reference Patterns (Best Practices)

Structure CLAUDE.md by moving task-specific topics into docs with pointer lines.
Common patterns:

| Topic | File | Reference Line |
|-------|------|-----------------|
| API conventions, request/response standards | `docs/api-standards.md` | `For API conventions, read docs/api-standards.md` |
| Testing framework setup, test patterns, fixtures | `docs/testing.md` | `For testing guidelines, read docs/testing.md` |
| Deployment procedures, environment config, infrastructure | `docs/deployment.md` | `For deployment rules, read docs/deployment.md` |
| Database schema, migrations, queries | `docs/database.md` | `For database schema and migrations, read docs/database.md` |
| Security policies, encryption, auth | `docs/security.md` | `For security policies, read docs/security.md` |
| Architecture decisions, trade-offs | `docs/architecture.md` | `For architecture decisions, read docs/architecture.md` |

Use reference lines instead of full content. This keeps CLAUDE.md focused on
universal context and lets Claude load task-specific details only when needed.

**Direction A — Task-specific content in CLAUDE.md:** Flag each task-specific
section with why it doesn't need to load for every task, and the reference line
to replace it with:
`For deployment and CI, read docs/deployment.md`

**Direction B — Orphaned docs:** Scan `docs/` for `.md` files, excluding
`docs/superpowers/`. For each, check whether any CLAUDE.md references it by
name. Flag unreferenced files — Claude won't know to read them.

**Direction C — Duplicated content:** Compare CLAUDE.md content against docs
files. Flag identical or near-identical information appearing in both — this is
the strongest signal to move content.

### MCP Servers

Each server loads full tool definitions into context every turn (~15,000–20,000
tokens each).

- Count configured servers from settings.json
- Flag any with CLI alternatives (Playwright, Google Workspace, GitHub all have
  CLIs that cost zero tokens when idle)
- Report total MCP overhead from /context output

### Skills

Scan `.claude/skills/*/SKILL.md`. For each:
- Count lines (flag >200, critical >500)
- Apply five filters: **Default** (Claude already does this without being told),
  **Contradiction**, **Redundancy**, **Bandaid** (added to fix one bad output),
  **Vague** (interpreted differently each time)
- Flag synonymous instructions ("be concise" + "keep it short" + "don't be verbose")

### Settings

| Setting | Flag if | Recommended |
|---------|---------|-------------|
| `autocompact_percentage_override` | Missing or >80 | 75 |
| `BASH_MAX_OUTPUT_LENGTH` (env) | At default (30–50K) | 150000 |

### File Permissions

Check `settings.json` for `permissions.deny`. If missing, check for bloat directories:

| If this exists | Should deny |
|----------------|-------------|
| `package.json` | `node_modules`, `dist`, `build`, `.next`, `coverage` |
| `Cargo.toml` | `target` |
| `go.mod` | `vendor` |
| `pyproject.toml` / `requirements.txt` | `__pycache__`, `.venv`, `*.egg-info` |

## Step 3: Score and Report

Score starts at 100. Deductions:

| Issue | Points |
|-------|--------|
| CLAUDE.md >200 lines | -10 |
| CLAUDE.md >500 lines | -20 |
| Per 5 rules flagged by filters | -5 |
| Contradictions between files | -10 |
| Task-specific section that should move to sub-file | -5 each |
| Orphaned docs file (not referenced in CLAUDE.md) | -5 each |
| Duplicated content block between CLAUDE.md and docs | -10 each |
| Missing autocompact override | -10 |
| Missing bash output override | -5 |
| Skill >200 lines | -5 each |
| Skill >500 lines | -10 each |
| Per MCP server | -3 each |
| No deny rules + bloat dirs exist | -10 |

Floor: 0. Labels: 90–100 CLEAN · 70–89 NEEDS WORK · 50–69 BLOATED · 0–49 CRITICAL.
Severity: CRITICAL >10pts · WARNING 5–10pts · INFO <5pts.

**Sum all deductions carefully before computing the final score.** List each deduction in the score breakdown table before subtracting from 100.

Output this format:

```
# Context Audit

Score: {N}/100 [{CLEAN|NEEDS WORK|BLOATED|CRITICAL}]

## Context Breakdown (from /context)
{Key numbers from /context output}

---

## Project
Issues scoped to this repository.

### [{severity}] CLAUDE.md Structure

#### Sections to move out of CLAUDE.md
- `## {Section}` → replace with: `For {topic}, read docs/{file}.md`
  Reason: {why this is task-specific, not universal context}

#### Orphaned docs (exist but not referenced in CLAUDE.md)
- `docs/{file}.md` — no pointer in any CLAUDE.md file

#### Duplicated content
- `## {Section}` in CLAUDE.md duplicates content in `docs/{file}.md`
  Fix: remove from CLAUDE.md, add reference line

### [{severity}] File Permissions
{Findings}

---

## Global
Issues affecting every conversation regardless of project.

### [{severity}] MCP Servers
{Count, overhead, any with CLI alternatives}

### [{severity}] Skills
{Per-skill findings}

### [{severity}] Settings
{autocompact_percentage_override, BASH_MAX_OUTPUT_LENGTH}

### [{severity}] Global CLAUDE.md (~/.claude/CLAUDE.md)
{Findings if applicable}

---

## Rules to Cut
{Each flagged rule: rule text · filter · one-line reason}

## Top 3 Fixes
1. {Highest-impact fix}
2. {Second}
3. {Third}
```

## Step 4: Offer to Fix

After the report:

> "Want me to fix any of these? I can:
> - Show you a restructured CLAUDE.md with task-specific sections replaced by
>   reference lines (confirm before applying)
> - Add reference lines for orphaned docs files
> - Add the missing settings.json configs (auto-applied, safe to revert)
> - Add permissions.deny rules for build artifacts (auto-applied)
> - Show which skills to compress"

**Auto-apply** (safe, reversible): settings.json changes, permissions.deny rules,
adding reference lines for orphaned docs.

**Confirm before applying:** Any removal or restructuring of CLAUDE.md content,
any skill edits. Never modify instruction files without explicit user confirmation.
