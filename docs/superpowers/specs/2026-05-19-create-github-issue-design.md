# Design: /create-github-issue Skill

**Date:** 2026-05-19
**Status:** Implemented

## Context

Needed a fast way to turn a conversation-level bug discovery into a tracked GitHub issue without context-switching out of Claude Code. The issue should be well-structured, reproducible, and honest about AI-generated suggested fixes.

## Trigger

`/create-github-issue` — optionally followed by `owner/repo`.

## Design Decisions

### Structured template over freeform prose

Chose a fixed template (Description / Steps / Expected / Actual / Suggested Fix / Environment) so issues are consistent and scannable regardless of what was discussed.

### Suggested fix disclaimer is mandatory and verbatim

The fix section heading is `⚠️ Suggested Fix (Unverified Hypothesis — Question This)` with a blockquote disclaimer. This cannot be softened or omitted when a fix exists — the goal is to prevent the AI-generated suggestion from being treated as authoritative.

### Draft-first, never create silently

The skill always shows a full draft before calling `gh issue create`. Supports an edit loop (plain-text changes → rewrite → re-review) before confirmation.

### Label detection before creation

`gh label list` runs before `gh issue create`. If the suggested label is missing, the user is asked to create it, skip, or choose an existing one. If the repo has no labels at all, a default set (`bug`, `enhancement`, `question`, `documentation`) is offered.

### Repo auto-detect with confirmation

`gh repo view --json nameWithOwner` detects the repo from the current directory. User confirms before proceeding. Explicit `owner/repo` arg overrides auto-detection entirely.

## Issue Template

```
Title: <concise imperative>
Labels: <bug | enhancement | question | documentation>

## Description
## Steps to Reproduce
## Expected Behaviour
## Actual Behaviour
## ⚠️ Suggested Fix (Unverified Hypothesis — Question This)
## Environment
```

## Files

- `skills/create-github-issue/SKILL.md` — skill implementation
- `.claude/settings.local.json` — added `gh issue create *`, `gh label list *`, `gh label create *` permissions
- `README.md` — added skill to table
