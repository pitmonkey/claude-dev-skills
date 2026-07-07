---
name: create-work-issue
description: Use when the user wants to create a GitHub issue structured as a work order for autonomous pickup by the github-dispatcher issue-worker (they add the pickup/claude label later). Triggered by /create-work-issue, optionally followed by owner/repo and a free-text description of the work. For a bug report from the current conversation, use create-github-bug-issue instead.
allowed-tools:
  - Bash
---

# Create Work Issue

Author a **work-order** GitHub issue and create it via the `gh` CLI. The issue is shaped for
the **github-dispatcher issue-worker**: a headless Claude agent that, once a human adds the
`pickup/claude` label, clones the repo and implements the issue end to end (plan → test-first
→ PR) with **no human in the loop**. The agent reads only the issue **title + body**, and
resolves every gap it hits by making a documented assumption and proceeding.

So **the issue body is the entire spec.** A vague body yields a PR full of guesses; a
well-structured one yields a tight, testable PR. This skill produces the structure.

This skill **creates** the issue but **never applies a label** — arming an issue for the
autonomous worker (adding `pickup/claude`) stays a deliberate human step, the last gate
before a bot writes a PR.

## The work-order template

Every issue carries all eight sections. Each exists to kill one class of bad assumption the
headless agent would otherwise make. Empty sections are marked `N/A` (never deleted).

```
Title: <concise imperative — e.g. "Add retry with backoff to the GitHub poll loop">

## Problem / Context
<why this work exists — what's wrong, missing, or needed. 2–4 sentences.>

## Goal / Outcome
<what "done" looks like, 1–2 sentences.>

## Acceptance criteria
<checklist of testable conditions — the spec the agent's test-first implementation writes tests against>
- [ ] ...
- [ ] ...

## Scope / Non-goals
<explicit fences — what NOT to touch or build. There is no human to say "stop, too far".>

## Pointers
<relevant files/dirs/functions, related issues/PRs. Saves the agent grep turns; its turn budget is finite. N/A if none.>

## Constraints
<deps, API/back-compat, performance, style rules not already in the target repo's CLAUDE.md. N/A if none.>

## Known ambiguities
<forks you already see — pre-decide them or say which way to lean, so the agent does not guess blindly. N/A if none.>
```

**Load-bearing sections:** *Acceptance criteria* (turns a vague ask into tests) and
*Scope / Non-goals* (fences an unsupervised agent). Do not finalize an issue without real
acceptance criteria.

## Process

### Step 0 — Parse arguments

The argument is an optional leading `owner/repo` followed by a free-text description of the
work (e.g. `/create-work-issue pitmonkey/foo add retry with backoff to the poll loop`).

- If an `owner/repo` token is present: use it as the target repo.
- The remaining text (if any) is the **work description** — the raw material for the draft.

### Step 1 — Detect and confirm repo

If no repo arg was given:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Show the detected repo to the user and ask them to confirm before continuing.

If `gh` is not authenticated: stop and tell the user to run `gh auth login`.
If the command fails or returns nothing: stop and ask the user to provide the repo manually.

### Step 2 — Adaptive gather (this is the key step)

Assess how much of the template the description already supplies. Score it against the four
**required** sections: Problem/Context, Goal/Outcome, Acceptance criteria, Scope/Non-goals.

- **Rich** — the description clearly covers the Problem and Goal and at least sketches what
  "done" means → produce a **one-shot draft** filling all eight sections, then ask **only**
  about the gaps you detected. Always confirm acceptance criteria and non-goals if they are
  thin or inferred — those are the sections the autonomous agent most needs pinned down.
- **Thin** — the description is a one-liner or missing the core → **interview** the missing
  sections, **one question at a time** (do not dump a form): start with Problem/Context, then
  Goal/Outcome, then Acceptance criteria, then Scope/Non-goals.
- Optional sections (Pointers, Constraints, Known ambiguities) → fill from the description if
  present, otherwise mark `N/A`. Do not interview for these; at most offer once, briefly.

Do not invent facts to fill a section. Where something is genuinely unknown, ask (thin path)
or record the fork under **Known ambiguities** so the agent is told which way to lean.

### Step 3 — Show draft

Display the full drafted title + body (all eight sections). Then ask:

> **Create this issue, edit it, or cancel? (create / edit / cancel)**

### Step 4 — Confirmation loop

- **create** → proceed to Step 5.
- **edit** → the user describes the change in plain text; rewrite the relevant section(s) and
  return to Step 3.
- **cancel** → stop immediately; do not create anything.

### Step 5 — Quality gate

Before creating, verify the **Acceptance criteria** section is non-empty and non-trivial
(real, testable conditions — not a restated title). If it is missing or empty, do **not**
create the issue; loop back to interview it, then re-show the draft (Step 3).

### Step 6 — Create issue

```bash
gh issue create \
  --repo <owner/repo> \
  --title "<title>" \
  --body "$(cat <<'EOF'
## Problem / Context
<...>

## Goal / Outcome
<...>

## Acceptance criteria
- [ ] <...>

## Scope / Non-goals
<...>

## Pointers
<... or N/A>

## Constraints
<... or N/A>

## Known ambiguities
<... or N/A>
EOF
)"
```

**Do not pass `--label`.** This skill applies no label — and never `pickup/claude`.

### Step 7 — Report

Print the issue URL returned by `gh issue create`, then the arming reminder:

> Add the `pickup/claude` label to this issue when you want the issue-worker to implement it.

If `gh issue create` fails: quote the exact error and stop.

## Rules

- NEVER apply any label — especially not `pickup/claude`. Arming for autonomous pickup is the
  human's deliberate step; creating an armed issue would skip the last review gate before a
  bot opens a PR.
- NEVER create an issue without showing the draft first.
- NEVER finalize without real acceptance criteria — they are the spec the agent tests against.
- NEVER add a "Generated with Claude Code" footer, "🤖" marker, or `Co-Authored-By: Claude` trailer to the issue body — no AI attribution.
- Every issue carries all eight sections; empty ones are marked `N/A`, never deleted.
- Do not invent facts to fill sections. Ask (thin path) or record the fork under Known
  ambiguities.
- If `gh` is not authenticated, stop immediately and tell the user to run `gh auth login`.
