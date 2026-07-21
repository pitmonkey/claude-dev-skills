---
name: create-work-issue
description: Use when the user wants to create a GitHub issue structured as a work order for autonomous pickup by the github-dispatcher issue-worker (they add the pickup/claude label later). Triggered by /create-work-issue, optionally followed by owner/repo and a free-text description of the work. For a bug report from the current conversation, use create-github-bug-issue instead.
allowed-tools:
  - Bash
  - mcp__github__issue_write
  - mcp__github__get_label
---

# Create Work Issue

Author a **work-order** GitHub issue and create it on GitHub. The issue is shaped for
the **github-dispatcher issue-worker**: a headless Claude agent that, once a human adds the
`pickup/claude` label, clones the repo and implements the issue end to end (plan → test-first
→ PR) with **no human in the loop**. The agent reads only the issue **title + body**, and
resolves every gap it hits by making a documented assumption and proceeding.

So **the issue body is the entire spec.** A vague body yields a PR full of guesses; a
well-structured one yields a tight, testable PR. This skill produces the structure.

This skill **creates** the issue and stamps it with the marker label **`claude-drafted`** so
every skill-created issue stays findable for later triage — but it **never applies
`pickup/claude`**. Arming an issue for the autonomous worker (adding `pickup/claude`) stays a
deliberate human step, the last gate before a bot writes a PR: list the candidates with
`gh issue list --label claude-drafted`, then arm the ones you pick.

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

**First, pick the GitHub path.** This skill talks to GitHub two ways, and which one works
depends on where it runs. Detect it once, up front:

```bash
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && echo remote || echo local
```

- **`remote`** — a web / phone / headless session (Claude Code on the web). The `gh` CLI
  **cannot** create issues here: the session's egress proxy serves `gh` only a narrow
  allowlist, and repo-scoped calls (`gh repo view`, `gh issue create`, `gh label ...`) come
  back **HTTP 403** ("GitHub access is not enabled for this session"). Use the **GitHub MCP
  tools** (`mcp__github__*`) instead — that is the sanctioned GitHub path in remote sessions.
- **`local`** — a local terminal session. Use the **`gh` CLI** as before; it authenticates
  with your `gh auth login` credentials.

Every mechanical step below gives the command for both paths. Run the whole flow on **one**
path — do not mix. The drafting steps (0, 2–5) are identical either way.

### Step 0 — Parse arguments

The argument is an optional leading `owner/repo` followed by a free-text description of the
work (e.g. `/create-work-issue pitmonkey/foo add retry with backoff to the poll loop`).

- If an `owner/repo` token is present: use it as the target repo.
- The remaining text (if any) is the **work description** — the raw material for the draft.

### Step 1 — Detect and confirm repo

If an `owner/repo` arg was given, use it. Otherwise detect the target repo:

- **remote (MCP):** `gh repo view` does **not** work here — the git remote points at the
  session proxy, not github.com. Parse owner/repo from the remote URL instead:

  ```bash
  git remote get-url origin | sed -E 's#\.git$##' | awk -F/ '{print $(NF-1)"/"$NF}'
  ```

- **local (gh):**

  ```bash
  gh repo view --json nameWithOwner --jq '.nameWithOwner'
  ```

Show the detected repo to the user and ask them to confirm before continuing.

If detection fails or returns nothing: stop and ask the user to provide the repo manually
(`owner/repo`). On the **local** path, if `gh` is not authenticated: stop and tell the user to
run `gh auth login`.

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

### Step 6 — Ensure the marker label exists

The `claude-drafted` marker must end up on the issue.

- **remote (MCP):** No separate create step is needed — pass `claude-drafted` in the `labels`
  array when you create the issue (Step 7) and GitHub auto-creates the label if it is missing
  (the MCP token has push access, so the label is created on first use). Optionally check
  first with `mcp__github__get_label` (owner, repo, name: `claude-drafted`) so you can tell
  the user whether the marker is brand new. A freshly auto-created label gets a default color —
  that is cosmetic and fine; recolor it later if you care.
- **local (gh):** create the label if it does not already exist:

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx claude-drafted \
    || gh label create claude-drafted --repo <owner/repo> --color 5319e7 \
       --description "Drafted by a Claude issue-creation skill; awaiting human triage"
  ```

### Step 7 — Create issue

- **remote (MCP):** call `mcp__github__issue_write` with:
  - `method`: `create`
  - `owner` / `repo`: the confirmed target
  - `title`: the drafted title
  - `labels`: `["claude-drafted"]` — **only this, never `pickup/claude`**
  - `body`: the full eight-section body (all sections; empty ones marked `N/A`):

    ```
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
    ```

- **local (gh):**

  ```bash
  gh issue create \
    --repo <owner/repo> \
    --title "<title>" \
    --label "claude-drafted" \
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

**Apply the `claude-drafted` label only — never `pickup/claude`.** The marker keeps the issue
findable; arming stays the human's step.

### Step 8 — Report

Print the created issue's URL, then the arming reminder:

- **remote (MCP):** take the URL from the `issue_write` response (its `html_url` / `url` field).
- **local (gh):** take the URL returned by `gh issue create`.

> Stamped `claude-drafted`. List candidates later with `gh issue list --label claude-drafted`,
> then add `pickup/claude` to the ones you want the issue-worker to implement.

If issue creation fails: quote the exact error and stop.

## Rules

- NEVER apply `pickup/claude`. Arming for autonomous pickup is the human's deliberate step;
  creating an armed issue would skip the last review gate before a bot opens a PR.
- ALWAYS apply the `claude-drafted` marker to every issue so skill-created issues stay findable
  for triage. This marker is not `pickup/claude` and does not arm anything.
- NEVER create an issue without showing the draft first.
- NEVER finalize without real acceptance criteria — they are the spec the agent tests against.
- NEVER add a "Generated with Claude Code" footer, "🤖" marker, or `Co-Authored-By: Claude` trailer to the issue body — no AI attribution.
- Every issue carries all eight sections; empty ones are marked `N/A`, never deleted.
- Do not invent facts to fill sections. Ask (thin path) or record the fork under Known
  ambiguities.
- Pick the GitHub path from `CLAUDE_CODE_REMOTE` (Process preamble) and stay on it: MCP tools
  in remote sessions, `gh` locally. Do not fall back to `gh` for issue/label writes in a remote
  session — it returns HTTP 403.
- On the local path, if `gh` is not authenticated, stop immediately and tell the user to run
  `gh auth login`.
