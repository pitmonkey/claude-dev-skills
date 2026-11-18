---
name: create-github-bug-issue
description: Use when the user wants to capture a bug or problem from the current conversation as a GitHub bug-report issue, including choosing the model tier the worker would run the fix on (model/mini, model/mid or model/max — pinning the root cause in the session first so the fix lands at mid or below), screening whether the fix needs human intervention and flagging it non-autonomous, and screening the draft itself and flagging it requires-review when it was written ahead of an unlanded dependency. Also use when asked to rewrite, restructure, or review an existing bug issue against this template. Triggered by /create-github-bug-issue, optionally followed by owner/repo. For a work order for the autonomous issue-worker, use create-work-issue instead. To sweep issues that already carry requires-review and clear the ones now verifiable, use review-flagged-issues instead.
allowed-tools:
  - Bash
  - mcp__github__issue_write
  - mcp__github__issue_read
  - mcp__github__get_label
---
## Host compatibility

This skill supports Claude Code and Codex. Explicit invocation may use the host’s native syntax (for example `/sc` or `$sc`). Follow repository instructions and host permissions; Claude `allowed-tools` metadata does not grant Codex permissions. When composing bundled skills, use the native skill mechanism when available; otherwise read and follow the sibling `SKILL.md` relative to this installed skill directory, carrying the stated arguments. Never require a Claude `Skill` tool in Codex. Do not add assistant attribution to generated commits, issues, or requests.
In Codex, pick the GitHub transport as described in `references/transport.md` (read it before Step 1).


# Create GitHub Bug Issue

Summarise the specific problem or bug discussed in this conversation and create a structured
GitHub issue. Always shows a draft for review before creating.

A human may later arm the issue for the autonomous github-dispatcher issue-worker by adding
`agent/pickup`. So this skill also screens for the opposite case: a fix the headless agent
**cannot** perform, which gets stamped **`non-autonomous`** and says so at the top of its own body.

It also screens the **draft itself** for one specific hazard: a report written against a change
that has not landed yet — an open PR, an open issue, an unmerged branch. That draft gets stamped
**`requires-review`** so a human re-checks it against what actually shipped before
`agent/pickup`.

It also picks the **model tier** the worker would fix it on, stamped as exactly one `model/*` label. This session has the conversation's context; it should pin down the root cause while it can, so the fix lands on a cheaper model. See **The model tier**.

The dispatcher's pickup labels are `agent/pickup`, `agent/pickup-large` and `agent/backlog`. The older `claude/*` spellings (`claude/pickup` and so on) are exact aliases that still work, so wherever this skill talks about an issue carrying `agent/pickup`, it means any of these, in either spelling.

## Labels

One mandatory marker, one content label, one mandatory tier label, two independent flags, one prohibition. Do not conflate them.

| Label | Rule |
|---|---|
| `claude-drafted` | **ALWAYS.** Every issue this skill creates or rewrites, no exceptions. |
| content label | One of `bug` / `enhancement` / `question` / `documentation`, chosen from the issue content. The user may skip it — `claude-drafted` may not be skipped. |
| `non-autonomous` | Only when the non-autonomous screen fires. |
| `requires-review` | Only when the review screen fires. Independent of `non-autonomous`, and not a content label. |
| `model/mini` \| `model/mid` \| `model/max` | **ALWAYS exactly one.** The tier this skill chose — see **The model tier**. A modifier: it picks the model and never starts a run on its own. Not a content label; skipping labels never drops it. |
| `agent/pickup`, `agent/pickup-large`, `agent/backlog` (and their `claude/*` aliases) | **NEVER.** Arming for the autonomous worker is the human's step. |

The prohibition is scoped to the pickup (trigger) labels alone. It is **not** a ban on labelling: `model/*` is a modifier, not a trigger, and the skill applies it. It never touches `ai/*` (harness choice) or `agent/research`; those stay the human's call when arming. Creating an
issue without `claude-drafted` is a skill failure — the marker is the only way a human later finds
skill-created issues to triage.

### If you are about to skip the marker

| Thought | Reality |
|---|---|
| "The skill says never apply labels" | It says never apply `agent/pickup`. `claude-drafted` is mandatory. |
| "The user chose to skip labels" | They skipped the *content* label. `claude-drafted` is mandatory, and the flag labels are not content labels — skipping labels never drops them. |
| "This issue is `non-autonomous`, so no marker" | `non-autonomous` issues get `claude-drafted` too. |
| "The label doesn't exist in the repo yet" | Create it (local `gh`) or let GitHub auto-create it (remote MCP). Do not drop it. |
| "I'm only rewriting/reviewing an existing issue" | Rewriting applies the marker too. See **Rewrite / review an existing issue**. |
| "Mid is the dispatcher default, so no tier label is needed" | Always apply exactly one `model/*`, even `model/mid`. The label is what makes the choice visible and overridable. |
| "That's a lot of labels — I'll pick the important one" | `claude-drafted` is mandatory, the content label is the user's choice, and the two flags are independent conditions. Applying fewer is not simplification. |

## Rewrite / review an existing issue

"Rewrite issue N with this skill", "review issue N", "fix up this issue", or a pasted issue URL means: apply this skill to that issue and write the result back. Review and rewrite are the same path. **Read `references/rewrite-existing.md` now, before reading the issue** — it covers re-screening, label handling, the write-back commands, and what to do with an issue already carrying `agent/pickup`.

## The non-autonomous flag

Screen the **fix the bug implies**, not the bug report. A trivial-looking report whose fix needs a
rotated credential or a pipeline change is non-autonomous; a scary-looking crash fixed by a
one-line change is not.

### Trigger checklist

Flag the issue **`non-autonomous`** if the fix needs any of:

- secrets, API keys, tokens, credentials, or a new external account
- infrastructure changes (cloud resources, k8s, DNS, hosting, deployment environments)
- GitHub Actions / CI workflow permissions, repo settings, branch protection, or org-level config
- graphics, art, audio, or design assets, or anything gated on human aesthetic judgement
- configuration in a third-party dashboard (Stripe, Cloudflare, GCP console, …)
- physical hardware, manual QA, paid subscriptions, or a legal/licence decision
- acceptance criteria that are irreducibly qualitative (taste, "reads well", "looks right")
- the actual change landing in a repo or system the worker cannot reach

### Banner

When flagged, this is the **first content in the body**, above `## Description`, verbatim:

```
> ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
> Do **not** add `agent/pickup`. See **Human intervention required** below.
```

### Human intervention required

Immediately after the banner, one concrete bullet per blocker — what a human must actually do, not
a restatement of the trigger category:

```
## Human intervention required
- The leaked `SLACK_BOT_TOKEN` must be revoked in the Slack admin console and reissued
- The new token must be written to repo secrets before any code change lands
```

Both are **conditional**: omitted entirely when the issue is not flagged. Never rendered as `N/A`.

## The requires-review flag

`non-autonomous` is about the fix: a bot **cannot** do it. `requires-review` is about **ordering**:
the fix is fine for a bot, but this report was written against something that has not landed yet, so
its facts may not survive that landing. It is a dependency hold, not a "someone should check this"
hold. The two flags are independent conditions — an issue can carry both, either, or neither.

### Trigger checklist

Flag the issue **`requires-review`** if any of these is true of the draft:

- the report or fix depends on a change that is **not merged and not landed** — an open PR, an open
  issue, an unmerged branch; its factual claims may not survive that landing
- it is one of a **batch**, and how the earlier items land changes whether the later ones are still
  right
- a load-bearing fact — the repro steps, the actual behaviour, the file the bug is in — was **read
  from an unmerged branch or an open PR** rather than from the default branch, so it may change
  before the worker sees it

**The gate: if you cannot name a concrete issue number, PR, or branch, the flag does not apply.**
Every trigger above names an artifact. That is what makes the flag mechanically clearable later —
`review-flagged-issues` resolves the hold by checking whether the named thing landed.

### Does not fire for

- **a design, taste, or balance judgement** in the fix — state it in `## Description` or in
  `## ⚠️ Suggested Fix`, so the worker knows which way to lean, rather than blocking the issue.
- **a symptom observed but not root-caused** — a diagnosis from a screenshot, an inferred repro, a
  file you guessed at. State the uncertainty in the body and let the worker verify it against the
  repo. This is the normal condition of a bug report, not an ordering problem.
- **an unverified suggested fix.** `## ⚠️ Suggested Fix (Unverified Hypothesis)` is unverified by
  design on every issue this skill creates and carries its own disclaimer.
- **a fix that is merely hard, large, or risky.** Difficulty is not a hold.

**Sanity check:** if most of a batch comes out flagged, the label has stopped gating anything. Go
back and re-run each one against the gate — a real ordering hold is the exception, not the norm.

### Banner

When flagged, this goes in the body verbatim, with both fields filled in. It is the **first content
in the body**, above `## Description` — below the `non-autonomous` banner if that one is present
too:

```
> 🔎 **`requires-review`** — a human must review this draft before arming it.
> Do **not** add `agent/pickup` until reviewed.
> Blocked by: <#N | owner/repo#N | PR #N | branch-name>
> Why: <one line — what in this draft that landing may invalidate>.
```

The banner and the label are **one unit**. Never write the banner without adding `requires-review`
to the label set, and never add the label without the banner. `Blocked by:` names a real artifact —
if you have nothing to put there, the flag does not apply. `Why:` says what the landing may
invalidate; "may need review" is not a reason.

There is no separate body section: unlike `non-autonomous`, which lists actions a human must
perform, `requires-review` states one reason, and the reason lives in the banner.

**When both flags fire**, the `non-autonomous` banner comes first, then the `requires-review`
banner, then `## Human intervention required`, then `## Description` and the rest.

## The model tier

The dispatcher runs the issue-worker on the model its `model/*` label maps to. As a rough guide: `model/mini` is a Haiku-class model, `model/mid` a Sonnet-class model, `model/max` an Opus-class model. With no label the worker's usual model runs, which is mid. The label changes only the model, never the turn or budget limits.

For a bug, the tier turns mostly on **whether the root cause is pinned down**:

| Tier | When |
|---|---|
| `model/mini` | Cause known and the fix site named — file and function — and the fix is small and mechanical. An off-by-one, a wrong comparison, a missing null check, a bad constant. |
| `model/mid` | **The target.** Cause known or narrowed to one area; the fix needs some judgement — a few files, a regression test, following existing patterns. |
| `model/max` | Only symptoms are known, or the fix cuts across several modules, or it touches concurrency, security or data migration. Diagnosis is part of the job. |

### Pin the cause before filing

This is a lean, not a rule: aim for `model/mid` or below. This session has the conversation's context and runs on a high-reasoning model; the worker starts cold. So when the cause is not yet known, try to find it **before** filing — read the code the symptom points at, trace the path, check the obvious suspects — and write what you found into `## Description` and the suggested fix. A bug whose cause is pinned rarely needs max.

If the cause still cannot be pinned, file it as `model/max` and say so in the **Model tier** line. A `model/max` bug is a hint that the human may prefer to debug it interactively before arming it; the report says so.

Bugs are usually one issue. Split only when the fix has genuinely independent parts, and then into mid-sized pieces — never fragment a mid fix into minis, since each run re-clones, re-reads and re-tests the repo.

`model/max` is not `non-autonomous`, and an un-root-caused symptom is still not a `requires-review` trigger — the tier is where that uncertainty shows. A `non-autonomous` issue still gets a tier for when it is eventually armed.

## Process

**First, pick the GitHub path** — the GitHub MCP tools in a remote session (`CLAUDE_CODE_REMOTE=true`), the `gh` CLI locally — and run the whole flow on that one path. **Read `references/transport.md` now**: it gives the detection command and the reason `gh` fails remotely. The drafting steps (0, 2–4) are identical on both paths.

### Step 0 — Parse arguments

Check if the user provided an `owner/repo` argument (e.g. `/create-github-bug-issue pitmonkey/other-repo`).

- If yes: use that repo for all subsequent steps.
- If no: proceed to Step 1 to auto-detect.

### Step 1 — Detect and confirm repo

If no repo arg was given, detect it with the command for your path in `references/transport.md`. Show the detected repo to the user and ask them to confirm before continuing. If detection fails, ask for `owner/repo`; on the local path, if `gh` is not authenticated, stop and tell the user to run `gh auth login`.

### Step 2 — Extract issue from conversation

Read the current conversation and identify the specific problem or bug being discussed. Do not summarise the entire session — focus on the concrete issue.

Populate the following draft:

```
Title: <concise imperative, e.g. "Fix: token expiry check uses < instead of <=">

Labels: <one of: bug | enhancement | question | documentation — chosen based on issue content>
        <plus non-autonomous if the fix trips a trigger>
        <plus requires-review if the draft trips a review trigger>
        <plus exactly one of model/mini | model/mid | model/max>

---

> ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
> Do **not** add `agent/pickup`. See **Human intervention required** below.
<omit these two lines entirely unless flagged non-autonomous>

> 🔎 **`requires-review`** — a human must review this draft before arming it.
> Do **not** add `agent/pickup` until reviewed.
> Blocked by: <#N | owner/repo#N | PR #N | branch-name>
> Why: <what that landing may invalidate in this draft>.
<omit these four lines entirely unless flagged requires-review>

## Human intervention required
<one concrete bullet per blocker — omit this whole section unless flagged>

## Description
<2–4 sentences describing the problem clearly>

## Steps to Reproduce
<numbered list, or "N/A" if not applicable>

## Expected Behaviour
<what should happen>

## Actual Behaviour
<what currently happens>

## ⚠️ Suggested Fix (Unverified Hypothesis — Question This)
> This suggestion was generated from conversation context. It has NOT been verified,
> tested, or confirmed. Treat it as a starting point for investigation only — not a
> solution. Challenge and test before acting on it.

<suggested fix if one emerged in conversation — omit this entire section if none>

## Environment
<repo, branch, language versions, or other relevant context from the conversation>

---
**Model tier:** `model/<mini|mid|max>` — <one line: why this tier>
```

The closing **Model tier** line is always present and always matches the `model/*` label. It tells a human why the tier was chosen, so they can disagree before arming.

Then run the fix against the non-autonomous trigger checklist and the draft against the
requires-review checklist. For each that fires, add its banner and its label to the set (and
`## Human intervention required` for non-autonomous). If you cannot tell whether a trigger applies,
ask rather than assume. A judgement call in the fix, or a cause you inferred rather than read, does
**not** fire `requires-review` — state it in the body and let the worker verify it.

**Then pick the model tier** (see **The model tier**). If the cause is not pinned, try to pin it first (**Pin the cause before filing**) and update the draft with what you found. Write the **Model tier** line and add exactly one `model/*` label to the set.

### Step 3 — Show draft

Display the full draft to the user. Above it, print the flag status and, for each flag that is on,
the triggers that fired:

```
Tier:  `model/<tier>` — <the one-line reason>
Flags: `non-autonomous` — <ON: triggers that fired | off>
       `requires-review` — <ON: blocked by #N — what the landing may invalidate | off>
```

Then ask, in every state, verbatim:

> **Create this issue, edit it, change the tier, or toggle a flag?
> (create / edit / mini / mid / max / non-autonomous / requires-review / cancel)**

Naming a flag toggles it: on if it is off, off if it is on. Naming a tier sets it.

### Step 4 — Confirmation loop

**create** → Step 5. **cancel** → stop and create nothing. For **edit**, a tier, or a flag toggle, **read `references/confirmation-loop.md` now** and follow it, then return to Step 3. Never toggle a flag the user did not ask for.

### Step 5 — Check labels

The final label set is the chosen content label, plus `claude-drafted`, plus exactly one `model/*` label, plus `non-autonomous` and/or `requires-review` for each flag that is on. A missing content label needs the user's create / pick / skip choice; "skip" drops only the content label. **Read `references/github-writes.md` now** — it has the label checks, the user prompts, and the commands for Steps 5, 6 and 7 on both paths.

### Step 6 — Create issue

Create the issue with the full body — banners and `## Human intervention required` only for the flags that are on — and the final label set. **Never `agent/pickup`.** Commands: `references/github-writes.md`.

### Step 7 — Verify labels, then report

Read the labels back: `claude-drafted` first, then `requires-review` if flagged, then exactly one `model/*`, re-applying any that are missing. Then report the URL, the labels actually present, and the addenda that apply. If the marker cannot be applied, quote the error and do not claim success. If issue creation fails, quote the exact error and stop. Commands and report text: `references/github-writes.md`.

## Rules

- ALWAYS apply `claude-drafted` to every issue this skill creates or rewrites — flagged or not,
  content label or not. See **Labels**. It is a marker, not an arming label; it triggers nothing
- NEVER apply `agent/pickup`. Arming for autonomous pickup is the human's deliberate step — and it
  is never right on a `non-autonomous` issue, nor on a `requires-review` issue until a human has
  reviewed it. This prohibition covers `agent/pickup` only — it never licenses dropping
  `claude-drafted`
- ALWAYS verify the marker landed after creating (Step 7) and re-apply it if it did not
- ALWAYS apply exactly one `model/*` label, and write a matching **Model tier** line at the end of
  the body. Aim for `model/mid` or below; try to pin the root cause before settling for `model/max`
- NEVER apply a pickup label (`agent/pickup`, `agent/pickup-large`, `agent/backlog`, or a `claude/*`
  alias) and never touch `ai/*` or `agent/research`
- NEVER create an issue without showing the draft first
- NEVER skip the label check
- ALWAYS screen the implied fix against the non-autonomous trigger checklist before finalizing.
  Catching it at creation is the whole point; a label added days later has already cost a wasted
  worker run
- NEVER apply `non-autonomous` without a non-empty `## Human intervention required` naming concrete
  human actions. A bare label tells the next reader nothing
- The banner text is verbatim and is the FIRST content in the body, above `## Description`. The
  banner and `## Human intervention required` are conditional — omitted entirely when not flagged,
  never rendered as `N/A`
- NEVER add a "Generated with Claude Code" footer, "🤖" marker, or `Co-Authored-By: Claude` trailer to the issue body — no AI attribution
- Pick the GitHub path from `CLAUDE_CODE_REMOTE` (Process preamble) and stay on it: MCP tools
  in remote sessions, `gh` locally. Do not fall back to `gh` for issue/label writes in a remote
  session — it returns HTTP 403.
- On the local path, if `gh` is not authenticated, stop immediately and tell the user to run
  `gh auth login`
- The suggested fix disclaimer must appear verbatim — do not soften or shorten it
- If no fix emerged from the conversation, omit the fix section entirely — do not invent one
- ALWAYS screen the draft against the requires-review trigger checklist too — separately from the
  non-autonomous screen. They answer different questions: can a bot do this, versus was this draft
  written ahead of something that has not landed
- `requires-review` is an ORDERING hold, not a "a human should check this" hold. It NEVER fires on a
  judgement call in the fix, on a symptom observed but not root-caused, on a cause inferred from the
  conversation rather than read, or on a fix that is merely hard. Those go in the body
- A suggested fix being unverified is not a requires-review trigger — that section is unverified by
  design and carries its own disclaimer
- If you cannot name a concrete issue, PR, or branch in `Blocked by:`, the flag does not apply. Do
  not flag an issue to express unease
- The `requires-review` label and its banner are ONE UNIT — never the banner without the label,
  never the label without the banner. A banner with no label is invisible to `gh issue list`
- The `requires-review` banner carries BOTH `Blocked by:` and `Why:`. "May need review" is not a
  reason, and a `Blocked by:` naming nothing leaves the flag unclearable by the later sweep
- If most of a batch comes out flagged, stop and re-screen. A label that fires on the majority
  gates nothing
- NEVER clear `requires-review` from an existing issue in this skill on your own judgement. Clearing
  it on evidence is the `review-flagged-issues` skill's job; here it takes an explicit user toggle
