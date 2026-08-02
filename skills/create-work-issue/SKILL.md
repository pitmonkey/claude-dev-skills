---
name: create-work-issue
description: Use when the user wants to create a GitHub issue structured as a work order for autonomous pickup by the github-dispatcher issue-worker (they add the claude/pickup label later), including screening work that needs human intervention and flagging it non-autonomous. Triggered by /create-work-issue, optionally followed by owner/repo and a free-text description of the work. For a bug report from the current conversation, use create-github-bug-issue instead.
allowed-tools:
  - Bash
  - mcp__github__issue_write
  - mcp__github__get_label
---

# Create Work Issue

Author a **work-order** GitHub issue and create it on GitHub. The issue is shaped for
the **github-dispatcher issue-worker**: a headless Claude agent that, once a human adds the
`claude/pickup` label, clones the repo and implements the issue end to end (plan → test-first
→ PR) with **no human in the loop**. The agent reads only the issue **title + body**, and
resolves every gap it hits by making a documented assumption and proceeding.

So **the issue body is the entire spec.** A vague body yields a PR full of guesses; a
well-structured one yields a tight, testable PR. This skill produces the structure.

This skill **creates** the issue and stamps it with the marker label **`claude-drafted`** so
every skill-created issue stays findable for later triage — but it **never applies
`claude/pickup`**. Arming an issue for the autonomous worker (adding `claude/pickup`) stays a
deliberate human step, the last gate before a bot writes a PR: list the candidates with
`gh issue list --label claude-drafted`, then arm the ones you pick.

The skill also screens for the opposite case: work the headless agent **cannot** do at all, because
it needs a secret, an infrastructure change, a pipeline change, generated artwork, or some other
human act. That work gets stamped **`non-autonomous`** — the inverse of arming — and says so at the
top of its own body, so nobody wastes a worker run on it.

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

## The non-autonomous flag

Some work cannot be done by a headless agent no matter how good the spec is. Flag it, and say so
where it cannot be missed.

### Trigger checklist

Flag the issue **`non-autonomous`** if the work needs any of:

- secrets, API keys, tokens, credentials, or a new external account
- infrastructure changes (cloud resources, k8s, DNS, hosting, deployment environments)
- GitHub Actions / CI workflow permissions, repo settings, branch protection, or org-level config
- graphics, art, audio, or design assets, or anything gated on human aesthetic judgement
- configuration in a third-party dashboard (Stripe, Cloudflare, GCP console, …)
- physical hardware, manual QA, paid subscriptions, or a legal/licence decision
- acceptance criteria that are irreducibly qualitative (taste, "reads well", "looks right")
- the actual change landing in a repo or system the worker cannot reach

A trigger fires on what the *work* needs, not on what the issue mentions. "Document how to rotate
the API key" needs no key and is autonomous; "rotate the API key" is not.

### Banner

When flagged, this is the **first content in the body**, above `## Problem / Context`, verbatim:

```
> ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
> Do **not** add `claude/pickup`. See **Human intervention required** below.
```

### Human intervention required

Immediately after the banner, one concrete bullet per blocker — what a human must actually do, not
a restatement of the trigger category:

```
## Human intervention required
- Stripe secret key must be added to repo secrets as `STRIPE_WEBHOOK_SECRET`
- Webhook endpoint must be registered in the Stripe dashboard
```

The banner and this section are **conditional**: they appear only when the issue is flagged. Unlike
the eight template sections, they are never rendered as `N/A` — an unflagged issue simply has
neither.

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

**Then screen for non-autonomous.** Run the gathered work against the trigger checklist above.

- **Any trigger fires** → draft the issue flagged: banner first, then `## Human intervention
  required` with one concrete bullet per blocker, then the eight sections as normal. Add
  `non-autonomous` to the label set.
- **A trigger is suspected but unconfirmed** (e.g. you cannot tell whether the credential already
  exists in the repo) → ask about it, one question at a time like any other gap. Do not assume
  either way.
- **Nothing fires** → draft unflagged. No banner, no section, no label.

### Step 3 — Show draft

Display the full drafted title + body (all eight sections, plus the banner and `## Human
intervention required` if flagged). Then ask:

- **flagged:** state the flag and the triggers that fired above the draft, then ask:

  > **Create this issue, edit it, remove the non-autonomous flag, or cancel?
  > (create / edit / unflag / cancel)**

- **not flagged:**

  > **Create this issue, edit it, mark it non-autonomous, or cancel?
  > (create / edit / flag / cancel)**

### Step 4 — Confirmation loop

- **create** → proceed to Step 5.
- **edit** → the user describes the change in plain text; rewrite the relevant section(s) and
  return to Step 3.
- **flag** → add the banner and `## Human intervention required`, and add `non-autonomous` to the
  label set. If you do not already know what the human must do, interview it (one question at a
  time) before re-showing. Return to Step 3.
- **unflag** → remove the banner, the `## Human intervention required` section, and
  `non-autonomous` from the label set. Return to Step 3.
- **cancel** → stop immediately; do not create anything.

### Step 5 — Quality gate

Before creating, verify:

1. The **Acceptance criteria** section is non-empty and non-trivial (real, testable conditions —
   not a restated title). If it is missing or empty, do **not** create the issue; loop back to
   interview it, then re-show the draft (Step 3).
2. If the issue is flagged `non-autonomous`, the **Human intervention required** section is
   non-empty and names concrete human actions ("add `STRIPE_WEBHOOK_SECRET` to repo secrets"), not
   trigger categories ("needs secrets"). If it is thin, interview the blockers and re-show
   (Step 3).

### Step 6 — Ensure the label set exists

The label set is `claude-drafted`, plus `non-autonomous` when the issue is flagged.

- **remote (MCP):** No separate create step is needed — pass the whole set in the `labels` array
  when you create the issue (Step 7) and GitHub auto-creates any missing label (the MCP token has
  push access, so a label is created on first use). Optionally check first with
  `mcp__github__get_label` (owner, repo, name) so you can tell the user whether a label is brand
  new. A freshly auto-created label gets a default color — that is cosmetic and fine; recolor it
  later if you care.
- **local (gh):** create each label in the set if it does not already exist:

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx claude-drafted \
    || gh label create claude-drafted --repo <owner/repo> --color 5319e7 \
       --description "Drafted by a Claude issue-creation skill; awaiting human triage"
  ```

  Only when the issue is flagged:

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx non-autonomous \
    || gh label create non-autonomous --repo <owner/repo> --color d93f0b \
       --description "Needs human intervention — not for autonomous issue-worker pickup"
  ```

  Never recolor or re-describe a label that already exists — take it as it is.

### Step 7 — Create issue

- **remote (MCP):** call `mcp__github__issue_write` with:
  - `method`: `create`
  - `owner` / `repo`: the confirmed target
  - `title`: the drafted title
  - `labels`: `["claude-drafted"]`, or `["claude-drafted", "non-autonomous"]` when flagged —
    **never `claude/pickup`**, on either kind of issue
  - `body`: the full eight-section body (all sections; empty ones marked `N/A`), preceded by the
    banner and `## Human intervention required` **only when flagged**:

    ```
    > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
    > Do **not** add `claude/pickup`. See **Human intervention required** below.

    ## Human intervention required
    - <what a human must do>

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
  > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
  > Do **not** add `claude/pickup`. See **Human intervention required** below.

  ## Human intervention required
  - <what a human must do>

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

When flagged, add `--label "non-autonomous"` as well. The banner and `## Human intervention
required` block are omitted entirely on an unflagged issue.

**Apply `claude-drafted` (plus `non-autonomous` when flagged) — never `claude/pickup`.** The marker
keeps the issue findable; arming stays the human's step.

### Step 8 — Report

Print the created issue's URL, then the appropriate reminder:

- **remote (MCP):** take the URL from the `issue_write` response (its `html_url` / `url` field).
- **local (gh):** take the URL returned by `gh issue create`.

**Not flagged:**

> Stamped `claude-drafted`. List candidates later with `gh issue list --label claude-drafted`,
> then add `claude/pickup` to the ones you want the issue-worker to implement.

**Flagged:**

> Stamped `claude-drafted` and `non-autonomous` — this one is **excluded from autonomous pickup**;
> it needs a human first. Review them with `gh issue list --label non-autonomous`.

If issue creation fails: quote the exact error and stop.

## Rules

- NEVER apply `claude/pickup`. Arming for autonomous pickup is the human's deliberate step;
  creating an armed issue would skip the last review gate before a bot opens a PR. This holds for
  `non-autonomous` issues too — they are not armed and not "armed but warned".
- ALWAYS screen the work against the non-autonomous trigger checklist before finalizing. Catching it
  at creation is the whole point; a label added days later has already cost a wasted worker run.
- NEVER apply `non-autonomous` without a non-empty `## Human intervention required` naming concrete
  human actions. A bare label tells the next reader nothing.
- The banner text is verbatim and is the FIRST content in the body, above `## Problem / Context`.
- The banner and `## Human intervention required` are conditional — omitted entirely when the issue
  is not flagged. Never render them as `N/A`.
- ALWAYS apply the `claude-drafted` marker to every issue so skill-created issues stay findable
  for triage. This marker is not `claude/pickup` and does not arm anything.
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
