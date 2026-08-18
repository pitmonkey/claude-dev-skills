---
name: create-github-bug-issue
description: Use when the user wants to capture a bug or problem from the current conversation as a GitHub bug-report issue, including screening whether the fix needs human intervention and flagging it non-autonomous, and screening the draft itself and flagging it requires-review when it was written ahead of an unlanded dependency. Also use when asked to rewrite, restructure, or review an existing bug issue against this template. Triggered by /create-github-bug-issue, optionally followed by owner/repo. For a work order for the autonomous issue-worker, use create-work-issue instead. To sweep issues that already carry requires-review and clear the ones now verifiable, use review-flagged-issues instead.
allowed-tools:
  - Bash
  - mcp__github__issue_write
  - mcp__github__issue_read
  - mcp__github__get_label
---

# Create GitHub Bug Issue

Summarise the specific problem or bug discussed in this conversation and create a structured
GitHub issue. Always shows a draft for review before creating.

A human may later arm the issue for the autonomous github-dispatcher issue-worker by adding
`claude/pickup`. So this skill also screens for the opposite case: a fix the headless agent
**cannot** perform, which gets stamped **`non-autonomous`** and says so at the top of its own body.

It also screens the **draft itself** for one specific hazard: a report written against a change
that has not landed yet — an open PR, an open issue, an unmerged branch. That draft gets stamped
**`requires-review`** so a human re-checks it against what actually shipped before
`claude/pickup`.

## Labels

One mandatory marker, one content label, two independent flags, one prohibition. Do not conflate
them.

| Label | Rule |
|---|---|
| `claude-drafted` | **ALWAYS.** Every issue this skill creates or rewrites, no exceptions. |
| content label | One of `bug` / `enhancement` / `question` / `documentation`, chosen from the issue content. The user may skip it — `claude-drafted` may not be skipped. |
| `non-autonomous` | Only when the non-autonomous screen fires. |
| `requires-review` | Only when the review screen fires. Independent of `non-autonomous`, and not a content label. |
| `claude/pickup` | **NEVER.** Arming for the autonomous worker is the human's step. |

The prohibition is scoped to `claude/pickup` alone. It is **not** a ban on labelling. Creating an
issue without `claude-drafted` is a skill failure — the marker is the only way a human later finds
skill-created issues to triage.

### If you are about to skip the marker

| Thought | Reality |
|---|---|
| "The skill says never apply labels" | It says never apply `claude/pickup`. `claude-drafted` is mandatory. |
| "The user chose to skip labels" | They skipped the *content* label. `claude-drafted` is mandatory, and the flag labels are not content labels — skipping labels never drops them. |
| "This issue is `non-autonomous`, so no marker" | `non-autonomous` issues get `claude-drafted` too. |
| "The label doesn't exist in the repo yet" | Create it (local `gh`) or let GitHub auto-create it (remote MCP). Do not drop it. |
| "I'm only rewriting/reviewing an existing issue" | Rewriting applies the marker too. See **Rewrite / review an existing issue**. |
| "That's a lot of labels — I'll pick the important one" | `claude-drafted` is mandatory, the content label is the user's choice, and the two flags are independent conditions. Applying fewer is not simplification. |

## Rewrite / review an existing issue

"Rewrite issue N with this skill", "review issue N", "fix up this issue", or a pasted issue URL
means: **apply this skill to that issue and write the result back.** It is not a read-only
opinion. Review and rewrite are the same path — reviewing produces the corrected issue.

1. Read the issue (`gh issue view N --repo <owner/repo> --json title,body,labels`, or
   `mcp__github__issue_read` remotely).
2. Re-draft the title and body to the Step 2 template. Keep the author's facts; do not invent. If
   no suggested fix emerged, omit that section rather than inventing one.
3. Run the implied fix against the non-autonomous trigger checklist and the draft against the
   requires-review checklist, exactly as for a new issue. A rewrite is a new draft: re-screen it,
   do not inherit the old verdict.
4. Compute the full intended label set — **including `claude-drafted`**, plus the content label,
   plus `non-autonomous` if that screen fires, plus `requires-review` if the review screen fires,
   plus any pre-existing labels the human already put there. Never `claude/pickup`, and never strip
   a label a human added.
5. Show the re-drafted issue and go through the same confirmation loop (Step 3 / Step 4), with
   **update** in place of create.
6. Write it back and verify:
   - **local:** `gh issue edit N --repo <owner/repo> --title "<title>" --body "<body>" --add-label claude-drafted`
     (add `--add-label` for each other label in the set). Use `--add-label`, never `--remove-label`
     on a label you did not add.
   - **remote:** `mcp__github__issue_write` with `method: update`, the issue number, and the full
     label set.

   Then run the same read-back verification as Step 7.

   The `--add-label`-only rule protects labels a human added. If the user explicitly toggles a flag
   **off** during the confirmation loop on an issue that already carries it, that is an instruction,
   not an inference: `gh issue edit N --repo <owner/repo> --remove-label requires-review` is allowed
   **there and only there**. Never remove a flag on your own judgement that the draft now looks
   fine. The one sanctioned sweep that clears `requires-review` on evidence rather than on a toggle
   is the `review-flagged-issues` skill, which re-checks each flagged draft against the current repo
   and holds anything it cannot verify.

An issue already carrying `claude/pickup` is **armed**. Say so before rewriting, and ask whether to
proceed — the human's gate has already been passed and the worker may pick it up mid-edit.

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
> Do **not** add `claude/pickup`. See **Human intervention required** below.
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
> Do **not** add `claude/pickup` until reviewed.
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

## Process

**First, pick the GitHub path.** This skill talks to GitHub two ways, and which one works
depends on where it runs. Detect it once, up front:

```bash
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && echo remote || echo local
```

- **`remote`** — a web / phone / headless session (Claude Code on the web). The `gh` CLI
  **cannot** create issues or manage labels here: the session's egress proxy serves `gh` only
  a narrow allowlist, and repo-scoped calls (`gh repo view`, `gh issue create`,
  `gh label ...`) come back **HTTP 403** ("GitHub access is not enabled for this session").
  Use the **GitHub MCP tools** (`mcp__github__*`) instead.
- **`local`** — a local terminal session. Use the **`gh` CLI** as before; it authenticates
  with your `gh auth login` credentials.

Every mechanical step below gives the command for both paths. Run the whole flow on **one**
path — do not mix. The drafting steps (0, 2–4) are identical either way.

### Step 0 — Parse arguments

Check if the user provided an `owner/repo` argument (e.g. `/create-github-bug-issue pitmonkey/other-repo`).

- If yes: use that repo for all subsequent steps.
- If no: proceed to Step 1 to auto-detect.

### Step 1 — Detect and confirm repo

If no repo arg was given, detect the target repo:

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

### Step 2 — Extract issue from conversation

Read the current conversation and identify the specific problem or bug being discussed. Do not summarise the entire session — focus on the concrete issue.

Populate the following draft:

```
Title: <concise imperative, e.g. "Fix: token expiry check uses < instead of <=">

Labels: <one of: bug | enhancement | question | documentation — chosen based on issue content>
        <plus non-autonomous if the fix trips a trigger>
        <plus requires-review if the draft trips a review trigger>

---

> ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
> Do **not** add `claude/pickup`. See **Human intervention required** below.
<omit these two lines entirely unless flagged non-autonomous>

> 🔎 **`requires-review`** — a human must review this draft before arming it.
> Do **not** add `claude/pickup` until reviewed.
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
```

Then run the fix against the non-autonomous trigger checklist and the draft against the
requires-review checklist. For each that fires, add its banner and its label to the set (and
`## Human intervention required` for non-autonomous). If you cannot tell whether a trigger applies,
ask rather than assume. A judgement call in the fix, or a cause you inferred rather than read, does
**not** fire `requires-review` — state it in the body and let the worker verify it.

### Step 3 — Show draft

Display the full draft to the user. Above it, print the flag status and, for each flag that is on,
the triggers that fired:

```
Flags: `non-autonomous` — <ON: triggers that fired | off>
       `requires-review` — <ON: blocked by #N — what the landing may invalidate | off>
```

Then ask, in every state, verbatim:

> **Create this issue, edit it, or toggle a flag?
> (create / edit / non-autonomous / requires-review / cancel)**

Naming a flag toggles it: on if it is off, off if it is on.

### Step 4 — Confirmation loop

- **create** → proceed to Step 5
- **edit** → user describes the change in plain text; rewrite the relevant section(s) and return to Step 3
- **non-autonomous** → toggle the flag. Turning it **on** adds the banner, `## Human intervention
  required`, and `non-autonomous` to the label set; if you do not already know what the human must
  do, ask before re-showing. Turning it **off** removes all three. Return to Step 3
- **requires-review** → toggle the flag. Turning it **on** adds the banner and `requires-review` to
  the label set; the banner needs a concrete `Blocked by:` and `Why:` — ask if you do not have them.
  If the user turns it on with no artifact to name, take the instruction and write
  `Blocked by: <none — author override>` so the later sweep can tell it apart from a real dependency
  hold. Turning it **off** removes both. Return to Step 3
- **cancel** → stop immediately; do not create anything

The user overrides the screen in either direction: they may turn a flag on that did not fire, or off
that did. Never toggle a flag they did not ask you to. If they just say `flag` or `unflag`, ask which
flag they mean — do not assume `non-autonomous`.

### Step 5 — Check labels

Decide the final label set: the chosen content label, plus the `claude-drafted` marker, plus
`non-autonomous` and/or `requires-review` for each flag that is on.

#### remote (MCP)

MCP has no bulk label list or label-create tool, so the check is per-label and creation
happens implicitly at issue time (GitHub auto-creates a referenced label if it is missing,
because the MCP token has push access — a freshly created label gets a default color, which is
cosmetic).

- Check the chosen content label with `mcp__github__get_label` (owner, repo, name: `<label>`):
  - **found** → keep it in the label set.
  - **not found** → ask the user:
    > Label `<label>` doesn't exist in this repo. Create it (it'll be added when the issue is
    > created), skip labels, or name an existing label to use instead?
    - create → keep `<label>` in the set (auto-created at issue time).
    - skip → drop the content label; keep `claude-drafted` and any flag labels. "Skip labels" means
      the content label only.
    - name one → `get_label` the name they give to confirm it exists, then use it.
- The `claude-drafted` marker needs no pre-check: include it in the label set and it is
  auto-created at issue time if missing. Same for `non-autonomous` and `requires-review` when their
  flags are on — include them and let GitHub create them. Never ask the user to approve these three;
  they are markers and flags, not content labels.

(The "seed the four default labels" convenience below is local-only — MCP can't batch-create
labels. Remotely, just handle the single chosen label as above.)

#### local (gh)

Check what labels exist in the target repo:

```bash
gh label list --repo <owner/repo> --json name --jq '.[].name'
```

**If the repo has no labels at all:**

Offer to seed a default set before continuing:

> Labels `bug`, `enhancement`, `question`, `documentation` don't exist in this repo. Create them now? (yes / skip)

- yes → create each:
  ```bash
  gh label create bug         --repo <owner/repo> --color d73a4a
  gh label create enhancement --repo <owner/repo> --color a2eeef
  gh label create question    --repo <owner/repo> --color d876e3
  gh label create documentation --repo <owner/repo> --color 0075ca
  ```
- skip → create the issue without a content label; the marker and any flag labels still apply

**If the repo has labels but the suggested label is missing:**

Ask:

> Label `<label>` doesn't exist in this repo. Create it, skip labels, or choose an existing one?
> Existing: <comma-separated list>

- create → `gh label create <label> --repo <owner/repo> --color <sensible default>`
- skip → create the issue without a content label; the marker and any flag labels still apply
- choose → user picks from list; use that label

**If the suggested label exists:** proceed directly.

**Always ensure the `claude-drafted` marker label exists** (independent of the content-label
choice above), creating it if missing:

```bash
gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx claude-drafted \
  || gh label create claude-drafted --repo <owner/repo> --color 5319e7 \
     --description "Drafted by a Claude issue-creation skill; awaiting human triage"
```

This marker stamps every skill-created issue so you can later find them with
`gh issue list --label claude-drafted`. It is applied even when the user skips the content label.

**When flagged `non-autonomous`**, ensure that label exists too:

```bash
gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx non-autonomous \
  || gh label create non-autonomous --repo <owner/repo> --color d93f0b \
     --description "Needs human intervention — not for autonomous issue-worker pickup"
```

**When flagged `requires-review`**, ensure it exists too:

```bash
gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx requires-review \
  || gh label create requires-review --repo <owner/repo> --color fbca04 \
     --description "Draft written ahead of an unlanded dependency — review before arming"
```

Never recolor or re-describe a label that already exists — take it as it is.

#### Gate — before you create

If the `requires-review` banner is in the body, `requires-review` is in the label set — and vice
versa. One without the other is a bug. Its `Blocked by:` names a concrete issue, PR, or branch (or
the author-override marker), and its `Why:` says what that landing may invalidate.

The label set you are about to pass contains `claude-drafted`. If it does not, add it. Do not
create the issue without it. Skipping the content label does not skip the marker or the flags.

### Step 6 — Create issue

- **remote (MCP):** call `mcp__github__issue_write` with:
  - `method`: `create`
  - `owner` / `repo`: the confirmed target
  - `title`: the drafted title
  - `labels`: the final set — the chosen content label (if kept) plus `"claude-drafted"`, plus
    `"non-autonomous"` and/or `"requires-review"` for each flag that is on; omit the content label
    if the user skipped it, but **always keep `"claude-drafted"`** and keep any flag label — a user
    skipping content labels was never asked about the flags. Never `"claude/pickup"`
  - `body`: the drafted body (omit the `## ⚠️ Suggested Fix` section entirely if no fix was
    identified — do not invent one; omit each banner, and `## Human intervention required`, when its
    flag is off):

    ```
    > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
    > Do **not** add `claude/pickup`. See **Human intervention required** below.

    > 🔎 **`requires-review`** — a human must review this draft before arming it.
    > Do **not** add `claude/pickup` until reviewed.
    > Blocked by: <#N | owner/repo#N | PR #N | branch-name>
    > Why: <what that landing may invalidate in this draft>.

    ## Human intervention required
    - <what a human must do>

    ## Description
    <description>

    ## Steps to Reproduce
    <steps>

    ## Expected Behaviour
    <expected>

    ## Actual Behaviour
    <actual>

    ## ⚠️ Suggested Fix (Unverified Hypothesis — Question This)
    > This suggestion was generated from conversation context. It has NOT been verified,
    > tested, or confirmed. Treat it as a starting point for investigation only — not a
    > solution. Challenge and test before acting on it.

    <fix>

    ## Environment
    <environment>
    ```

- **local (gh):**

  ```bash
  gh issue create \
    --repo <owner/repo> \
    --title "<title>" \
    --label "<label>" \
    --label "claude-drafted" \
    --body "$(cat <<'EOF'
  > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
  > Do **not** add `claude/pickup`. See **Human intervention required** below.

  > 🔎 **`requires-review`** — a human must review this draft before arming it.
  > Do **not** add `claude/pickup` until reviewed.
  > Blocked by: <#N | owner/repo#N | PR #N | branch-name>
  > Why: <what that landing may invalidate in this draft>.

  ## Human intervention required
  - <what a human must do>

  ## Description
  <description>

  ## Steps to Reproduce
  <steps>

  ## Expected Behaviour
  <expected>

  ## Actual Behaviour
  <actual>

  ## ⚠️ Suggested Fix (Unverified Hypothesis — Question This)
  > This suggestion was generated from conversation context. It has NOT been verified,
  > tested, or confirmed. Treat it as a starting point for investigation only — not a
  > solution. Challenge and test before acting on it.

  <fix>

  ## Environment
  <environment>
  EOF
  )"
  ```

Add `--label "non-autonomous"` and/or `--label "requires-review"` for each flag that is on; omit
each banner (and the `## Human intervention required` block) when its flag is off.
Omit the content `--label "<label>"` (or leave it out of the MCP `labels` set) if the user
chose to skip labels, but **always keep `claude-drafted`, and keep any flag label** — "skip labels"
refers to the content label only.
Omit the `## ⚠️ Suggested Fix` section entirely if no fix was identified.

### Step 7 — Verify labels, then report

**First, read the labels back.** A silently dropped marker is invisible otherwise.

- **local (gh):**

  ```bash
  gh issue view <number> --repo <owner/repo> --json labels --jq '.labels[].name' \
    | grep -qx claude-drafted \
    || gh issue edit <number> --repo <owner/repo> --add-label claude-drafted
  ```

- **remote (MCP):** the `issue_write` response carries the applied labels. If `claude-drafted` is
  absent, call `mcp__github__issue_write` with `method: update`, the issue number, and the full
  intended `labels` array.

If the re-apply also fails, quote the exact error and say the issue was created **without** the
marker so the user can fix it by hand. Do not claim success.

**Then, when flagged `requires-review`, read that back too** — separately, after the marker check
above. Do not merge the two into one loop; the marker check is unconditional and stands alone.

- **local (gh):**

  ```bash
  gh issue view <number> --repo <owner/repo> --json labels --jq '.labels[].name' \
    | grep -qx requires-review \
    || gh issue edit <number> --repo <owner/repo> --add-label requires-review
  ```

- **remote (MCP):** if `requires-review` is absent from the `issue_write` response labels, call
  `mcp__github__issue_write` with `method: update`, the issue number, and the full intended `labels`
  array.

A body carrying the `requires-review` banner with no `requires-review` label is the exact failure
this check exists to catch.

**Then report.** Print the created issue's URL, the labels actually present (e.g.
`Stamped: bug, claude-drafted, requires-review`), then the base line, then one addendum per flag
that is on:

- **remote (MCP):** take the URL from the `issue_write` response (its `html_url` / `url` field).
- **local (gh):** take the URL returned by `gh issue create`.

**Always:**

> Stamped `claude-drafted`. List skill-created issues later with
> `gh issue list --label claude-drafted`.

**Plus, if `non-autonomous`:**

> Also `non-autonomous` — **excluded from autonomous pickup**; it needs a human first. Review them
> with `gh issue list --label non-autonomous`.

**Plus, if `requires-review`:**

> Also `requires-review` — <the reason>. Read it before you arm it. Review them with
> `gh issue list --label requires-review`.

If issue creation fails: quote the exact error and stop.

## Rules

- ALWAYS apply `claude-drafted` to every issue this skill creates or rewrites — flagged or not,
  content label or not. See **Labels**. It is a marker, not an arming label; it triggers nothing
- NEVER apply `claude/pickup`. Arming for autonomous pickup is the human's deliberate step — and it
  is never right on a `non-autonomous` issue, nor on a `requires-review` issue until a human has
  reviewed it. This prohibition covers `claude/pickup` only — it never licenses dropping
  `claude-drafted`
- ALWAYS verify the marker landed after creating (Step 7) and re-apply it if it did not
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
