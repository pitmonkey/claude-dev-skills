---
name: create-work-issue
description: Use when the user wants to create a GitHub issue structured as a work order for autonomous pickup by the github-dispatcher issue-worker (they add the agent/pickup label later), including choosing the model tier the worker runs on (model/mini, model/mid or model/max, aiming for mid and splitting work that would need max), screening work that needs human intervention and flagging it non-autonomous, and screening the draft itself and flagging it requires-review when it was written ahead of an unlanded dependency. Also use when asked to rewrite, restructure, or review an existing issue against the work-order template. Triggered by /create-work-issue, optionally followed by owner/repo and a free-text description of the work. For a bug report from the current conversation, use create-github-bug-issue instead. To sweep issues that already carry requires-review and clear the ones now verifiable, use review-flagged-issues instead.
allowed-tools:
  - Bash
  - mcp__github__issue_write
  - mcp__github__issue_read
  - mcp__github__get_label
---
## Host compatibility

This skill supports Claude Code and Codex. Explicit invocation may use the host’s native syntax (for example `/sc` or `$sc`). Follow repository instructions and host permissions; Claude `allowed-tools` metadata does not grant Codex permissions. When composing bundled skills, use the native skill mechanism when available; otherwise read and follow the sibling `SKILL.md` relative to this installed skill directory, carrying the stated arguments. Never require a Claude `Skill` tool in Codex. Do not add assistant attribution to generated commits, issues, or requests.
In Codex, pick the GitHub transport as described in `references/transport.md` (read it before Step 1).


# Create Work Issue

Author a **work-order** GitHub issue and create it on GitHub. The issue is shaped for
the **github-dispatcher issue-worker**: a headless Claude agent that, once a human adds the
`agent/pickup` label, clones the repo and implements the issue end to end (plan → test-first
→ PR) with **no human in the loop**. The agent reads only the issue **title + body**, and
resolves every gap it hits by making a documented assumption and proceeding.

So **the issue body is the entire spec.** A vague body yields a PR full of guesses; a
well-structured one yields a tight, testable PR. This skill produces the structure.

This skill **creates** the issue and stamps it with the marker label **`claude-drafted`**, so every
skill-created issue stays findable for later triage: list the candidates with
`gh issue list --label claude-drafted`, then arm the ones you pick.

The skill also screens for the opposite case: work the headless agent **cannot** do at all, because
it needs a secret, an infrastructure change, a pipeline change, generated artwork, or some other
human act. That work gets stamped **`non-autonomous`** — the inverse of arming — and says so at the
top of its own body, so nobody wastes a worker run on it.

It also screens the **draft itself** for one specific hazard: an issue written ahead of something
that has not landed yet. That draft gets stamped **`requires-review`** — a hold on arming, not a
hold on the work — so a human re-checks it against what actually shipped before `agent/pickup`
goes on it.

Finally, it picks the **model tier** the worker runs on and stamps it as exactly one `model/*` label. The planning session that runs this skill is the expensive, high-reasoning step; its job is to do the hard thinking up front so the worker can run on a cheaper model. See **The model tier**.

The dispatcher's pickup labels are `agent/pickup`, `agent/pickup-large` and `agent/backlog`. The older `claude/*` spellings (`claude/pickup` and so on) are exact aliases that still work, so wherever this skill talks about an issue carrying `agent/pickup`, it means any of these, in either spelling.

## Labels

One mandatory marker, one mandatory tier label, two independent flags, one prohibition. Do not conflate them.

| Label | Rule |
|---|---|
| `claude-drafted` | **ALWAYS.** Every issue this skill creates or rewrites, no exceptions. |
| `non-autonomous` | Only when the non-autonomous screen fires. |
| `requires-review` | Only when the review screen fires. Independent of `non-autonomous`. |
| `model/mini` \| `model/mid` \| `model/max` | **ALWAYS exactly one.** The tier this skill chose — see **The model tier**. A modifier: it picks the model and never starts a run on its own. |
| `agent/pickup`, `agent/pickup-large`, `agent/backlog` (and their `claude/*` aliases) | **NEVER.** Arming for the autonomous worker is the human's step — the last gate before a bot writes a PR. |

The prohibition is scoped to the pickup (trigger) labels alone. It is **not** a ban on labelling: `model/*` is a modifier, not a trigger, and the skill applies it. It never touches `ai/*` (harness choice) or `agent/research`; those stay the human's call when arming. Creating an
issue without `claude-drafted` is a skill failure — the marker is the only way a human later finds
skill-created issues to triage.

### If you are about to skip the marker

| Thought | Reality |
|---|---|
| "The skill says never apply labels" | It says never apply `agent/pickup`. `claude-drafted` is mandatory. |
| "This issue is `non-autonomous`, so no marker" | `non-autonomous` issues get `claude-drafted` too. |
| "The user didn't ask for a label" | The marker is not a user preference; it is how the issue stays findable. |
| "The label doesn't exist in the repo yet" | Create it (local `gh`) or let GitHub auto-create it (remote MCP). Do not drop it. |
| "I'm only rewriting/reviewing an existing issue" | Rewriting applies the marker too. See **Rewrite / review an existing issue**. |
| "Mid is the dispatcher default, so no tier label is needed" | Always apply exactly one `model/*`, even `model/mid`. The label is what makes the choice visible and overridable. |
| "Three labels is a lot — I'll pick the important one" | `claude-drafted` is mandatory and the other two are independent conditions. Applying fewer is not simplification, it is a dropped marker. |

## Rewrite / review an existing issue

"Rewrite issue N with this skill", "review issue N", "fix up this issue", or a pasted issue URL means: apply this skill to that issue and write the result back. **Read `references/rewrite-existing.md` now, before reading the issue.**

## The work-order template

Every issue carries all eight template sections (empty ones `N/A`, never deleted) and a closing **Model tier** line. **Read `references/work-order-template.md` before drafting (Step 2).**

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

When flagged, a verbatim banner is the **first content in the body**, above `## Problem / Context`. **Read `references/banners.md` for its exact text.**

### Human intervention required

Immediately after the banner, a `## Human intervention required` section with one concrete bullet per blocker — what a human must actually do, not the trigger category. The banner and this section appear only when flagged, never as `N/A`. Example: `references/banners.md`.

## The requires-review flag

`non-autonomous` is about the work: a bot **cannot** do it. `requires-review` is about **ordering**:
the work is fine for a bot, but this draft was written against something that has not landed yet, so
its facts may not survive that landing. It is a dependency hold, not a "someone should think about
this" hold. The two flags are independent conditions — an issue can carry both, either, or neither.

### Trigger checklist

Flag the issue **`requires-review`** if any of these is true of the draft:

- it is written against a dependency that is **not merged and not landed** — an open PR, an open
  issue, an unmerged branch; its factual claims may not survive that landing
- it is one of a **batch**, and how the earlier items land changes whether the later ones are still
  right
- a load-bearing fact was **read from an unmerged branch or an open PR** rather than from the
  default branch, so that fact may change before the worker sees it

**The gate: if you cannot name a concrete issue number, PR, or branch, the flag does not apply.**
Every trigger above names an artifact. That is what makes the flag mechanically clearable later —
`review-flagged-issues` resolves the hold by checking whether the named thing landed.

### Does not fire for

- **a design, taste, or balance judgement** — that goes under `## Known ambiguities` with a stated
  lean. `Known ambiguities` always wins for a judgement: the worker resolves gaps by making a
  documented assumption and proceeding, and a lean written for the worker is useless if the flag
  stops the issue being armed at all.
- **a symptom observed but not root-caused** — a diagnosis from a screenshot, an inferred repro.
  State the uncertainty in the body and let the worker verify it against the repo.
- **a fact you inferred from the default branch and could not fully confirm** — same: say so in the
  body. The worker reads the repo; unconfirmed-but-current is not an ordering problem.
- **work that is merely hard, large, or risky.** Difficulty is not a hold.

**Sanity check:** if most of a batch comes out flagged, the label has stopped gating anything. Go
back and re-run each one against the gate — a real ordering hold is the exception, not the norm.

### Banner

When flagged, the body carries a verbatim banner with both `Blocked by:` and `Why:` filled in; banner and label are one unit. When both flags fire, the `non-autonomous` banner comes first, then this one, then `## Human intervention required`. **Read `references/banners.md` for the exact text.**

## The model tier

The dispatcher runs the issue-worker on the model its `model/*` label maps to. As a rough guide: `model/mini` is a Haiku-class model, `model/mid` a Sonnet-class model, `model/max` an Opus-class model. With no label the worker's usual model runs, which is mid. The label changes only the model, never the turn or budget limits.

The mapping is per harness. A `model/*` label takes effect only where the dispatcher's `model_by_tier` maps that harness; on a harness with no entry (by default, `ai/codex`) the label is ignored and the harness's own default model runs. Still apply the label — it records the intended tier and takes effect on Claude, or once the deployment maps the other harness.

The tier is set by **how much reasoning the worker still has to do after reading the body**, not by how big the diff is.

| Tier | When |
|---|---|
| `model/mini` | Fully specified. The body names the exact files and the exact change, acceptance is checkable with one command, and nothing is left to decide. A rename, a config value, a doc fix, a one-function fix whose cause is already known. |
| `model/mid` | **The target.** One coherent body of work with a plan in the body. The worker uses judgement inside it: touches a few files, writes tests, follows patterns the repo already has. |
| `model/max` | The worker would still have to reason hard: open design decisions, a change that cuts across several modules, a root cause nobody has found yet, concurrency/security/data migration, or a pattern with no precedent in the repo. |

### Aim for mid

This is a lean, not a rule. Most issues should land at `model/mid`: one coherent piece of work, sized for a Sonnet-class worker.

- **Do the thinking here, not in the worker.** This session runs on a high-reasoning model. Spend it settling what a cheaper worker would otherwise have to work out.
- **Do not fragment mid work into minis.** Five mini issues usually cost more than one mid issue — each run re-clones, re-reads and re-tests the repo. Split only to bring max work down.
- **Take mini when it is natural.** Work that is small by nature, or a clean piece that lifts out of a bigger job (a rename, a constant, a doc line), goes in as `model/mini`. Spot it; do not hunt for it.

### Bringing max down

When a draft reads as `model/max`, or the work changes shared plumbing (a core loop or entry point every path runs through), do not accept max at once. **Read `references/bringing-max-down.md` now.**

## Process

**First, pick the GitHub path** — the GitHub MCP tools in a remote session (`CLAUDE_CODE_REMOTE=true`), the `gh` CLI locally — and run the whole flow on that one path. **Read `references/transport.md` now**: it gives the detection command and the reason `gh` fails remotely. The drafting steps (0, 2–5) are identical on both paths.

### Step 0 — Parse arguments

The argument is an optional leading `owner/repo` followed by a free-text description of the
work (e.g. `/create-work-issue pitmonkey/foo add retry with backoff to the poll loop`).

- If an `owner/repo` token is present: use it as the target repo.
- The remaining text (if any) is the **work description** — the raw material for the draft.

### Step 1 — Detect and confirm repo

If an `owner/repo` arg was given, use it. Otherwise detect it with the command for your path in `references/transport.md`. Show the detected repo to the user and ask them to confirm before continuing. If detection fails, ask for `owner/repo`; on the local path, if `gh` is not authenticated, stop and tell the user to run `gh auth login`.

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

**Surface policy questions; do not leave them unspoken.** When a criterion depends on a security or behaviour policy, the worker should not have to guess it. Examples are which values count as secrets and from which sources, failing closed versus an allow-list, and what happens on a cancel or timeout. Write the question under **Known ambiguities** as a lean: the recommended choice, the alternatives, and a one-line reason. If you cannot form a view, ask the user. A lean stays a suggestion: the worker follows it, or records a documented assumption saying why it chose otherwise. Write the policy as a fixed decision under `## Constraints` only when the user explicitly decides it (or when closing it is what brings a `model/max` draft down; see **Bringing max down**). An issue that asked for "the credentials the run handled" as secrets, with no sources or rule named, cost three review rounds before the owner decided. The missing piece was a written-down lean, not a hard rule.

**Then run both screens.** First run the gathered work against the non-autonomous trigger checklist
above.

- **Any trigger fires** → draft the issue flagged: banner first, then `## Human intervention
  required` with one concrete bullet per blocker, then the eight sections as normal. Add
  `non-autonomous` to the label set.
- **A trigger is suspected but unconfirmed** (e.g. you cannot tell whether the credential already
  exists in the repo) → ask about it, one question at a time like any other gap. Do not assume
  either way.
- **Nothing fires** → draft unflagged. No banner, no section, no label.

Then screen the draft against the **requires-review** trigger checklist, separately — a draft can be
fully autonomous and still be written ahead of an unlanded dependency, or need a human and rest on
nothing unlanded at all.

- **Any trigger fires** → add the `requires-review` banner directly below the `non-autonomous`
  banner if there is one, with a concrete `Blocked by:` and `Why:`, and add `requires-review` to the
  label set.
- **Nothing fires** → no banner, no label. A judgement call goes under `## Known ambiguities` with a
  stated lean and does **not** fire the flag; nor does a fact you inferred from the default branch —
  say so in the body and let the worker verify it.

**Then pick the model tier** (see **The model tier**). If the draft reads as `model/max`, work through **Bringing max down** before showing it: close the open decisions, then propose a split if it is still max. Write the **Model tier** line and add exactly one `model/*` label to the set.

### Step 3 — Show draft

Display the full drafted title + body (all eight sections, plus any banners and `## Human
intervention required` if flagged). Above the draft, print the flag status and, for each flag that
is on, the triggers that fired:

```
Tier:  `model/<tier>` — <the one-line reason>
Flags: `non-autonomous` — <ON: triggers that fired | off>
       `requires-review` — <ON: blocked by #N — what the landing may invalidate | off>
```

If you are proposing a split, show the whole batch: one line per issue (title, tier, what it builds on), then each draft in order.

Then ask, in every state, verbatim:

> **Create this issue, edit it, change the tier, or toggle a flag?
> (create / edit / mini / mid / max / non-autonomous / requires-review / cancel)**

Naming a flag toggles it: on if it is off, off if it is on. Naming a tier sets it.

### Step 4 — Confirmation loop

**create** → Step 5. **cancel** → stop and create nothing. For **edit**, a tier, or a flag toggle, **read `references/confirmation-loop.md` now** and follow it, then return to Step 3. Never toggle a flag the user did not ask for.

### Step 5 — Quality gate

Before creating, verify:

1. The **Acceptance criteria** section is non-empty and non-trivial (real, testable conditions —
   not a restated title). If it is missing or empty, do **not** create the issue; loop back to
   interview it, then re-show the draft (Step 3).
2. If the issue is flagged `non-autonomous`, the **Human intervention required** section is
   non-empty and names concrete human actions ("add `STRIPE_WEBHOOK_SECRET` to repo secrets"), not
   trigger categories ("needs secrets"). If it is thin, interview the blockers and re-show
   (Step 3).
3. If the `requires-review` banner is in the body, `requires-review` is in the label set — and vice
   versa. One without the other is a bug: the banner without the label is invisible to
   `gh issue list`, and the label without the banner tells the next reader nothing. Its
   `Blocked by:` names a concrete issue, PR, or branch (or the author-override marker), and its
   `Why:` says what that landing may invalidate — not "may need review".
4. The label set you are about to pass contains `claude-drafted`. If it does not, add it. Do not
   create the issue without it.
5. The label set contains **exactly one** `model/*` label, and the body's **Model tier** line names
   the same tier. With more than one, the dispatcher runs the highest, which silently undoes the
   choice.

### Step 6 — Ensure the label set exists

The label set is `claude-drafted`, plus exactly one `model/*` label, plus `non-autonomous` and/or `requires-review` for each flag that is on. **Read `references/github-writes.md` now** — commands and report text for Steps 6–8.

### Step 7 — Create issue

Create the issue with the full body — banners and `## Human intervention required` only for the flags that are on, then all eight sections — and the full label set. **Never `agent/pickup`.** For a confirmed split, create the issues earliest first so each later body can name the real number of the one it builds on. Commands: `references/github-writes.md`.

### Step 8 — Verify labels, then report

Read the labels back: `claude-drafted` first, then `requires-review` if flagged, then exactly one `model/*`, re-applying any that are missing. Then report the URL, the labels actually present, and the addenda that apply. If the marker cannot be applied, quote the error and do not claim success. If issue creation fails, quote the exact error and stop. Commands and report text: `references/github-writes.md`.

## Rules

- ALWAYS apply `claude-drafted` to every issue this skill creates or rewrites — flagged or not.
  See **Labels**. It is a marker, not an arming label; it triggers nothing.
- NEVER apply `agent/pickup`. Arming for autonomous pickup is the human's deliberate step;
  creating an armed issue would skip the last review gate before a bot opens a PR. This holds for
  `non-autonomous` and `requires-review` issues too — they are not armed and not "armed but
  warned". This prohibition covers `agent/pickup` only — it never licenses dropping
  `claude-drafted`.
- ALWAYS apply exactly one `model/*` label, and write a matching **Model tier** line at the end of
  the body. Aim for `model/mid`; bring `model/max` down by closing decisions and splitting before
  accepting it; never fragment mid work into minis.
- NEVER apply `non-autonomous` without a non-empty `## Human intervention required` naming concrete
  human actions. A bare label tells the next reader nothing.
- The banner text is verbatim and is the FIRST content in the body, above `## Problem / Context`.
- ALWAYS verify the marker landed after creating (Step 8) and re-apply it if it did not.
- NEVER create an issue without showing the draft first.
- NEVER finalize without real acceptance criteria — they are the spec the agent tests against.
- NEVER add a "Generated with Claude Code" footer, "🤖" marker, or `Co-Authored-By: Claude` trailer to the issue body — no AI attribution.
- Do not invent facts to fill sections. Ask (thin path) or record the fork under Known
  ambiguities.
- The `requires-review` label and its banner are ONE UNIT — never the banner without the label,
  never the label without the banner. A banner with no label is invisible to `gh issue list`.
- The `requires-review` banner carries BOTH `Blocked by:` and `Why:`. "May need review" is not a
  reason, and a `Blocked by:` naming nothing leaves the flag unclearable by the later sweep.
- NEVER clear `requires-review` from an existing issue in this skill on your own judgement. Clearing
  it on evidence is the `review-flagged-issues` skill's job; here it takes an explicit user toggle.
