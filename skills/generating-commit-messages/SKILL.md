---
name: generating-commit-messages
description: Generate conventional commit messages. Use before every git commit.
---

## CRITICAL REQUIREMENT

**THIS SKILL MUST BE USED FOR EVERY SINGLE COMMIT**

---

## Mandatory Process

**BEFORE ANY `git commit` COMMAND:**

1. ALWAYS run `git diff --staged` first to see changes
2. IF no changes are staged, STOP and do NOT proceed
3. ALWAYS analyze the staged changes thoroughly
4. ALWAYS generate a commit message following the format below
5. NEVER commit without following this process

---

## Core Principle

**Why over what.** The diff already shows what changed. The commit message should explain why it changed — what problem it solves, what decision was made, what impact it has.

---

## Required Commit Message Format

```
<type>(<optional-scope>): <summary>

<optional body>
```

### 1. Summary Line

- Prefer 50 characters or fewer; hard cap at 72
- Use present tense imperative mood: "add", "fix", "remove" — not "added", "fixes", "adding"
- Must describe the PRIMARY change
- Start with a valid type
- No trailing period
- Match the project's convention for capitalization after the colon

### 2. Valid Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change without behavior change
- `docs`: Documentation only
- `test`: Tests added or updated
- `chore`: Maintenance, tooling, dependencies
- `perf`: Performance improvements
- `build`: Build system or external dependency changes
- `ci`: CI configuration and scripts
- `style`: Formatting, whitespace — no logic change
- `revert`: Reverts a prior commit

### 3. Scope (Optional but Recommended)

Use when changes affect a specific area or component.

Examples:
- `feat(auth): add token refresh logic`
- `fix(api): handle null response`

---

## Detailed Description (Body)

Include a body when the subject line alone does not tell the full story.

### When to include a body:

- The *why* behind the change is not obvious from the subject
- The commit introduces a breaking change
- The commit includes migration or upgrade notes
- The commit references or closes an issue or PR

### Formatting:

- Wrap lines at 72 characters
- Use bullet points with `-` (not `*`) for multiple items
- Focus on intent and impact, not file names
- Reference issues and PRs at the end of the body:
  - `Closes #42` — when this commit resolves the issue
  - `Refs #17` — when this commit is related but does not close it

### When to omit the body:

The body MAY be omitted when the subject line is completely self-explanatory and no issues or migrations apply.

---

## Handling Multiple Changes

If a commit includes multiple changes:
- Choose the PRIMARY purpose for the summary line
- List secondary changes as bullet points in the body

---

## Breaking Changes

If the change introduces a breaking change:

```
<type>!: <summary>

BREAKING CHANGE: <description of what changed and the impact>
```

The `BREAKING CHANGE:` note in the body is required — do not omit it.

---

## Always Include a Body For

Some changes always need a body regardless of subject-line length. Never compress these into subject-only:

- **Breaking changes** — future consumers need migration context
- **Security fixes** — document the vulnerability class and its scope
- **Data migrations** — downstream operators need to know what runs and when
- **Reverts** — explain which commit is being reverted and why

---

## Best Practices

- Always include the "why", not just the "what"
- Keep commits focused and atomic when possible
- Prefer multiple small commits over one large commit
- Use clear, specific language

---

## Forbidden Elements

**Never include AI attribution:**
- `Generated with [Claude Code](https://claude.ai/code)`
- `Co-Authored-By: Claude <noreply@anthropic.com>`
- Any AI attribution trailer — this rule is unconditional

**Never use vague messages:**
- "Update files"
- "Fix stuff"
- "Misc changes"

**Never use noise phrases — the diff already says these things:**
- "This commit does X"
- "I", "we", "now", "currently"
- Restating the file name when the scope already covers it

**Never add:**
- Emoji (unless the project convention explicitly requires them)

---

## Examples

### Simple feature with linked issue

```
# ❌ Too verbose — over 50 chars, says "what" not "why"
feat: add a new endpoint to get user profile information from the database

# ✅
feat(api): add GET /users/:id/profile

Mobile client needs profile data without the full user payload
to reduce LTE bandwidth on cold-launch screens.

Closes #128
```

### Breaking change

```
# ✅
feat(api)!: rename /v1/orders to /v1/checkout

BREAKING CHANGE: clients on /v1/orders must migrate to /v1/checkout
before 2026-06-01. Old route returns 410 after that date.
```

### Small, self-explanatory fix (body omitted)

```
# ✅
fix(auth): prevent double token refresh on 401
```

---

## Scope of This Skill

This skill generates commit messages only. It does not run `git commit`, stage files, or amend commits. Use the generated message as a code block to paste into your commit command.

---

## Comparison: generating-commit-messages vs caveman-commit

The table below documents the deliberate comparison performed as part of issue #19. Each caveman-commit feature is marked adopted or rejected with a reason.

| Feature | caveman-commit | Our skill (before) | Decision | Reason |
|---|---|---|---|---|
| Mandatory `git diff --staged` check | ❌ absent | ✅ present | **Keep (not a gap)** | Our process step prevents empty commits; caveman lacks it and that's a gap in caveman, not ours. |
| Types list | feat/fix/refactor/perf/docs/test/chore/**build/ci/style/revert** | feat/fix/refactor/docs/test/chore/perf | **Adopt** | `build`, `ci`, `style`, `revert` are standard CC types covering real cases. |
| Subject hard cap | ≤50 preferred, **hard cap 72** | max 50 | **Adopt** | Hard 50 truncates meaningful summaries; soft 50 / hard 72 is more realistic. |
| No trailing period | ✅ explicit | ❌ not stated | **Adopt** | Consistent with Conventional Commits; avoids ambiguity. |
| Capitalization after colon | "match project convention" | ❌ not stated | **Adopt** | Makes the skill adaptable to different project styles. |
| Body: when to include | specific conditions (non-obvious why, breaking, migration, linked issues) | "when not trivial" | **Adopt** | More actionable criteria than "not trivial". |
| Body: bullet style | `-` not `*` | "bullet points" (unspecified) | **Adopt** | Removes ambiguity; `-` is the markdown convention. |
| Issue/PR trailers (`Closes #42`, `Refs #17`) | ✅ explicit | ❌ absent | **Adopt** | Common, useful; connecting commits to issues improves traceability. |
| Banned filler ("This commit does X", "I/we/now/currently") | ✅ explicit | ❌ not stated | **Adopt** | These phrases add noise without adding information. |
| Restating filename when scope covers it | ✅ forbidden | ❌ not stated | **Adopt** | Redundant with the scope; wastes subject-line budget. |
| Emoji prohibition | ✅ (unless project requires) | ❌ not stated | **Adopt** | Consistent and professional default. |
| Always-body for security/data-migration/revert | ✅ explicit | ❌ partial (breaking only) | **Adopt** | Security fixes and data migrations need body context for the same reason breaking changes do. |
| Concrete ✅/❌ examples | ✅ present | ❌ absent | **Adopt** | Examples make abstract rules actionable. |
| "Why over what" as stated principle | ✅ explicit | ❌ implicit | **Adopt** | Worth stating clearly since it drives every other rule. |
| AI attribution exception (`Assisted-by` trailer when user rule requires) | ✅ conditional allowance | ❌ unconditional ban | **Reject** | Our unconditional ban is intentional; issue guidance says keep it strict. |
| "Stop caveman-commit / normal mode" boundary | ✅ present | N/A | **Reject** | Caveman-mode toggle is irrelevant to our skill's identity and trigger contract. |
