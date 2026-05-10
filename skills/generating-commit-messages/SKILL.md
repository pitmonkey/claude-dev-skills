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

## Required Commit Message Format

<type>(optional-scope): <summary>

### 1. Summary line
- Maximum 50 characters
- Use present tense imperative mood
- Must describe the PRIMARY change
- Start with a valid type

### 2. Valid Types
- feat: New feature
- fix: Bug fix
- refactor: Code change without behavior change
- docs: Documentation only
- test: Tests added or updated
- chore: Maintenance, tooling, dependencies
- perf: Performance improvements

### 3. Scope (Optional but Recommended)
- Use when changes affect a specific area/component

Examples:
- feat(auth): add token refresh logic
- fix(api): handle null response

---

## Detailed Description (Body)

Include a body when the change is not trivial.

### Requirements:
- Explain WHAT was changed
- Explain WHY it was changed
- Include relevant context
- Wrap lines at ~72 characters

### Guidelines:
- Use bullet points for multiple changes
- Focus on intent and impact, not just file names

### Trivial Changes:
The body MAY be omitted if:
- Change is small and self-explanatory
- Only one file/component is affected

---

## Handling Multiple Changes

If a commit includes multiple changes:
- Choose the PRIMARY purpose for the summary
- List secondary changes as bullet points in the body

---

## Breaking Changes

If the change introduces a breaking change:

Format:
<type>!: <summary>

Body MUST include:
BREAKING CHANGE: <description of what changed and impact>

---

## Best Practices

- Use clear, specific language
- Always include the "why", not just the "what"
- Keep commits focused and atomic when possible
- Prefer multiple small commits over one large commit

---

## Forbidden Elements

- NEVER include "Generated with [Claude Code] (https://claude.ai/code)"
- NEVER include "Co-Authored-By: Claude <noreply@anthropic.com>"
- NEVER use vague messages like:
  - "Update files"
  - "Fix stuff"
  - "Misc changes"
