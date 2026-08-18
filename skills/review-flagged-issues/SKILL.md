---
name: review-flagged-issues
description: Use when the user wants to review the GitHub issues in a repo that carry the requires-review flag — sweeping every open flagged issue, checking each draft against the current repo, updating bodies with facts now known, and clearing the flag only on the ones whose hold is genuinely resolved, holding the rest with a named blocker, and lifting it from the ones flagged for a reason the flag never covered. Triggered by /review-flagged-issues, optionally followed by owner/repo and specific issue numbers. To create a new work order use create-work-issue, and for a new bug report use create-github-bug-issue.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - mcp__github__issue_write
  - mcp__github__issue_read
  - mcp__github__get_label
---

# Review Flagged Issues (review-flagged-issues)

Sweep every open issue carrying **`requires-review`** in a repo, review each one against the
repo as it stands **now**, and clear the flag on the issues whose hold is genuinely resolved —
holding the rest with a concrete blocker.

`requires-review` is a hold on **arming** and an **ordering** hold: `create-work-issue` and
`create-github-bug-issue` set it when a draft was written against something that has not landed —
an open PR, an open issue, an unmerged branch — or when it sits in a batch whose order matters. Its
banner names the blocker on a `Blocked by:` line, and that is what this sweep resolves against.
**This skill is the only sanctioned way the flag comes off on evidence** — everywhere else,
removing it takes an explicit user toggle.

The flag is *not* a "a human should think about this" hold. Judgement calls belong under
`## Known ambiguities` with a stated lean, and an un-root-caused symptom belongs in the body — so
an issue flagged for one of those was **mis-flagged** under an older reading of the trigger list.
This sweep has a third verdict for exactly that case.

Clearing the flag does **not** arm the issue. It makes the issue armable: a human still adds
`claude/pickup`. This skill never applies that label.

## The default is HOLD

The failure this skill exists to prevent is the tidy sweep that clears ten flags without checking
any of them. A held issue with a named blocker is a **successful** outcome, not an unfinished one.

| Thought | Reality |
|---|---|
| "The dependency probably landed by now" | Probably is not evidence. Read the PR state or the code. No read, no clear. |
| "This one looks fine on a reread" | The flag was set for a stated reason. Resolve *that* reason, or hold. |
| "The rest of the batch is blocked, so clear the easy ones for progress" | Clearing an issue whose upstream is still held is exactly the ordering bug the flag encodes. |
| "The banner has no `Why:`, so there is nothing to resolve" | A missing or generic `Why:` is unresolvable by definition. Hold it and report the defect. |
| "The user asked me to review them, so they want them cleared" | They asked for a review. Clearing is one of three valid answers. |
| "Ten issues, ten clears — a tidy result" | A sweep that clears everything is the signature of not having checked. |
| "I read the issue carefully, that is the evidence" | Reading the *issue* is not evidence. The evidence is in the repo or the PR. |
| "Nothing in this banner names a dependency, so it is mis-flagged" | Only if there **is** a banner and neither it nor the body names an issue, PR, or branch. A vague `Why:` on a real dependency is a HOLD, and a label with no banner at all is a HOLD. |

## The evidence bar

A **CLEAR** requires a positive fact read during **this run**, statable in one line:

- a PR that is merged — `gh pr view <n> --repo <owner/repo> --json state,mergedAt`
- an issue that is closed — `gh issue view <n> --repo <owner/repo> --json state`
- a `file:line` on the default branch that confirms (or corrects) the claim the draft was written
  against

A merged PR alone is not enough for a dependency hold: read the code it landed. Issues are
flagged because a body's claims may not survive the landing, and a merged PR that did something
slightly different is the case this check catches.

**HOLD** is the default. It needs no justification beyond the reason still being unresolved.

## Reason taxonomy

The three `requires-review` triggers, and what resolves each:

| Flag reason | Resolves when | Check |
|---|---|---|
| Unlanded dependency | The PR is merged / the issue is closed **and** the change is visible on the default branch | `gh pr view` / `gh issue view` state, then Read the changed file |
| Batch ordering | Every upstream issue is itself cleared **and** landed | The dependency graph from Step 4 |
| Fact read from an unlanded source | The fact is now on the default branch and matches — or the body is corrected to what is actually there | Grep/Read the named file, symbol, or path on the default branch |

A corrected body clears the third trigger just as a confirmed one does — the hold is on the draft
resting on something that had not landed, and reading the landed version resolves it either way.
What does not clear is a fact you could not find at all.

**Anything else the banner claims is a mis-flag, not a fourth reason.** A `Why:` about a design
judgement, a taste call, an unset threshold, or a screenshot-derived diagnosis names no artifact and
can never be resolved by a sweep — those issues would sit flagged forever. Handle them with the
MIS-FLAGGED verdict below.

## The MIS-FLAGGED verdict

A third verdict, alongside CLEAR and HOLD. It fires when **all** of these hold:

- the body carries a 🔎 banner (so the flag's reason was written down, by a skill), **and**
- neither the banner's `Blocked by:` nor its `Why:` names an issue, PR, or branch, **and**
- scanning the body turns up no `#N`, PR link, or branch name the draft depends on either.

That is a flag applied for a reason the flag never covered. The disposition is to **relocate the
concern and lift the hold**: move it under `## Known ambiguities` with a stated lean (work order) or
into `## Description` / `## ⚠️ Suggested Fix` (bug report), then remove the banner and the label,
and say so in the comment.

Two boundaries keep this from becoming a way to clear the whole sweep:

- **A `requires-review` label with no banner at all is still a HOLD defect**, exactly as before.
  Silence is not evidence the flag was mis-applied — a human may have added the label deliberately,
  and the sweep cannot resolve a reason nobody stated.
- **If the banner or the body names a concrete `#N`, PR, or branch, it is a dependency hold** and
  gets CLEAR or HOLD on the ordinary evidence bar — however vague the `Why:` reads.

MIS-FLAGGED is a disposition of the **flag**, never of the **concern**. The concern must land
somewhere in the body before the banner comes off.

## Banner and label come off together

The creation skills treat the `requires-review` banner and label as one unit. That rule runs both
directions:

- **CLEAR** → remove the banner from the body **and** the label from the issue.
- **MIS-FLAGGED** → same, once the concern has been relocated into the body.
- **HOLD** → keep both, and rewrite the banner's `Blocked by:` and `Why:` to the blocker found this
  run.

A body still carrying the 🔎 banner after the label came off is the same defect the creation
skills guard against, inverted — and the next human to read it will believe a hold that no longer
exists.

## What this skill may change

- **The body** — re-drafted against its own template with the facts read this run. This is the
  rewrite path of the owning creation skill, without its create path. On a MIS-FLAGGED verdict the
  re-draft also relocates the flagged concern into `## Known ambiguities` with a stated lean, or
  into the bug-report body, so lifting the hold loses nothing.
- **`requires-review`** — removed on CLEAR and on MIS-FLAGGED, kept with a sharper `Blocked by:` and
  `Why:` on HOLD.
- **`non-autonomous`** — **add-only**. Re-screen the work; if it now clearly needs a human, add
  the flag, its banner, and `## Human intervention required`. Never remove it: this skill screens
  drafts, and a human may have added that flag deliberately.
- **`claude-drafted`** — applied to every issue it touches, per the creation skills' mandatory
  marker rule.
- **A comment** — one per issue touched, recording the verdict and its evidence.

It never applies `claude/pickup`, never removes a label a human added other than
`requires-review`, and never closes an issue.

## Process

**First, pick the GitHub path.** Same rule as the creation skills — detect once, up front:

```bash
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && echo remote || echo local
```

- **`remote`** — a web / phone / headless session. `gh` repo-scoped calls come back **HTTP 403**
  through the session proxy. Use the **GitHub MCP tools** (`mcp__github__*`).
- **`local`** — a local terminal session. Use the **`gh` CLI**.

Run the whole sweep on **one** path — do not mix. The reviewing steps (3–7) are identical either
way.

### Step 0 — Parse arguments

The argument is an optional leading `owner/repo`, optionally followed by issue numbers
(e.g. `/review-flagged-issues pitmonkey/foo 12 13 14`).

- `owner/repo` present → that is the target repo.
- Issue numbers present → restrict the sweep to those issues. They must still carry
  `requires-review`; report and skip any that do not, rather than reviewing them.
- Neither → sweep every open flagged issue in the detected repo.

### Step 1 — Detect and confirm repo

If an `owner/repo` arg was given, use it. Otherwise:

- **remote (MCP):** the git remote points at the session proxy, so parse it instead:

  ```bash
  git remote get-url origin | sed -E 's#\.git$##' | awk -F/ '{print $(NF-1)"/"$NF}'
  ```

- **local (gh):**

  ```bash
  gh repo view --json nameWithOwner --jq '.nameWithOwner'
  ```

Show the detected repo and ask the user to confirm before continuing. If detection fails, stop and
ask for `owner/repo`. On the local path, if `gh` is not authenticated, stop and tell the user to run
`gh auth login`.

Also record the commit the review is against — it goes in every comment:

```bash
git rev-parse --short HEAD
```

### Step 2 — Collect the flagged set

- **local (gh):**

  ```bash
  gh issue list --repo <owner/repo> --label requires-review --state open \
    --limit 100 --json number,title,labels,url
  ```

- **remote (MCP):** `mcp__github__issue_read` (or the MCP list/search equivalent) filtered to open
  issues with the `requires-review` label.

Then read each body in full:

```bash
gh issue view <number> --repo <owner/repo> --json number,title,body,labels,url
```

- **Nothing flagged** → say so, name the repo, and stop. No writes, no comments.
- **More than 15** → report the count and ask whether to sweep them all before reading the bodies.
  Reviewing sixty issues in one pass degrades every verdict in it.

The repo also has to be readable. If the working tree is not the repo being swept, say so — this
skill's evidence comes from reading code, and a sweep of a repo you cannot read can only produce
HOLDs.

### Step 3 — Classify each issue

For each issue:

1. **Template** — the eight-section work order (`## Problem / Context`, `## Acceptance criteria`, …)
   means `create-work-issue` owns it; the reproduce/expected/actual shape means
   `create-github-bug-issue` owns it. That decides which template the re-draft is written against.
2. **Hold reason** — the 🔎 banner's `Blocked by:` line, falling back to its `Why:` on an older
   banner that has no `Blocked by:`, mapped to the taxonomy above. Then check the gate: does the
   banner or the body name an issue, a PR, or a branch?
   - **Yes** → a dependency hold. It goes to Step 5 for CLEAR or HOLD.
   - **No** → **MIS-FLAGGED**, per the section above. No repo evidence can resolve it, so it does
     not go through the evidence bar; it goes through relocation.
   - `Blocked by: <none — author override>` is neither: the author flagged it deliberately with
     nothing to name. HOLD it and surface it in the report for the author to toggle off.
3. **Defects** — record, do not silently fix:
   - `requires-review` label with **no banner** in the body → the reason was never written down.
     HOLD; the sweep cannot resolve a reason nobody stated, and this is **not** a mis-flag, which
     needs a banner to read.
   - a banner whose `Why:` is generic ("may need review") **and** whose `Blocked by:` names a real
     artifact → HOLD, and report the thin `Why:`.
   - the issue carries **`claude/pickup`** → it is **armed**. Report it and skip it entirely: do not
     edit, comment on, or relabel an armed issue. The worker may be mid-run on it. Ask the user
     what they want to do with it in the report.

### Step 4 — Build the dependency graph

The banner's `Blocked by:` line is the primary edge: it names the issue, PR, or branch this draft
was written ahead of. Then scan every flagged body for further references — `#N`, `owner/repo#N`, PR
links, "depends on", "after … lands", "once #N" — to catch edges an older banner did not record.
Resolve each to an issue or PR, inside or outside the flagged set.

MIS-FLAGGED issues contribute no edges; by definition they name nothing.

Order the review topologically so an upstream verdict is known before its dependents are judged. On
a cycle, report it and HOLD every issue in it — a cycle means the batch ordering is itself unclear
and a human should break it.

### Step 5 — Review each issue in dependency order

Resolve the hold reason against the evidence bar. Gather the facts the body claims, from the repo
and from GitHub, not from memory of what the issue says.

Each issue gets a verdict:

- **CLEAR** — the reason resolved, with a one-line evidence string naming the PR, issue state, or
  `file:line`.
- **HOLD** — the reason unresolved, with a one-line blocker naming what is missing.
- **MIS-FLAGGED** — classified in Step 3, not here: the banner names no artifact and neither does
  the body. It takes no repo evidence, because there is nothing in the repo that could resolve it.
  Record where the concern is being relocated to instead.

An issue whose upstream is still HOLD is **HOLD**, whatever its own reason, and its blocker names
that upstream. This is the ordering the flag exists to protect: the later items in a batch are only
correct once the earlier ones land as written.

### Step 6 — Compute the writes

For every issue in the sweep, cleared and held alike:

1. **Re-draft the body** against its template with the facts read in Step 5 — replace inferred
   claims with what is actually in the repo, fix stale paths and symbol names, sharpen acceptance
   criteria that the landed dependency now makes concrete. Keep the author's facts; do not invent.
   Every section stays present.
2. **Re-screen `non-autonomous`** against the work as re-drafted. It fires now and did not before →
   add the flag, its banner, and a non-empty `## Human intervention required`. It fired before →
   leave it, whatever you now think.
3. **CLEAR** → delete the 🔎 banner from the body.
   **MIS-FLAGGED** → relocate the concern first — a judgement into `## Known ambiguities` with a
   stated lean, an un-root-caused symptom into the body as a stated uncertainty for the worker to
   verify — **then** delete the banner. Never delete the banner without landing its concern
   somewhere; that is the one way this verdict loses information.
   **HOLD** → rewrite its `Blocked by:` and `Why:` to the blocker found this run, e.g.
   `Blocked by: #12` / `Why: the retry loop #12 adds is what this issue's acceptance criteria test.`
   A banner with no `Blocked by:` line gains one.
4. Label set: `claude-drafted` always, plus every label already on the issue, minus
   `requires-review` on a CLEAR or a MIS-FLAGGED.

Where a body needs no change — the facts read match what it already says — say "body unchanged" for
that issue rather than rewriting it for the sake of a diff.

### Step 7 — Show the sweep, confirm once

Print a verdict table:

```
 #   Title                                  Template    Verdict       Evidence / blocker / relocation
 12  Add retry with backoff to poll loop    work-order  CLEAR         PR #40 merged; src/poll.py:88 has the loop
 13  Surface retry count in status line     work-order  CLEAR         depends on #12 (cleared); ui/status.py:22 confirms the field
 14  Cache the poll result across runs      work-order  HOLD          needs #13's field name; #13 not landed
 15  Crash on empty config file             bug         MIS-FLAGGED   banner names no dependency; "fail loudly or default?" moved to the body, leaning fail loudly
```

Then, per issue, the proposed body changes (as a summary of what changes and why, not a full
re-paste of unchanged sections) and the comment that will be posted.

Then ask, verbatim:

> **Apply this review? (apply / edit N / clear N / hold N / misflag N / skip N / cancel)**

- **apply** → Step 8.
- **edit N** → the user describes a change to that issue's re-draft; redo it and re-show the table.
- **clear N** / **hold N** / **misflag N** → override the verdict. A user override is an
  instruction, not an inference — the same carve-out the creation skills already grant. Record it as
  an override, and say so in that issue's comment. On a `misflag N` override, still relocate the
  concern into the body before the banner comes off.
- **skip N** → leave that issue completely untouched this run.
- **cancel** → stop. Nothing is written.

Never write anything before this prompt is answered.

### Step 8 — Apply, in dependency order

Per issue. **local (gh):**

```bash
gh issue edit <number> --repo <owner/repo> --body "$(cat <<'EOF'
<the re-drafted body>
EOF
)" --add-label claude-drafted
```

Add `--add-label non-autonomous` when that screen newly fired. Then, **cleared and mis-flagged
issues only**:

```bash
gh issue edit <number> --repo <owner/repo> --remove-label requires-review
```

This is the one place any skill in this plugin removes `requires-review` without a user toggle, and
it is licensed by the review in Steps 5–7 — never by a reread.

**remote (MCP):** `mcp__github__issue_write` with `method: update`, the issue number, the new body,
and the **full intended label set**. An update carrying the complete set drops `requires-review` by
omission on a CLEAR or a MIS-FLAGGED; on a HOLD the set still contains it.

A failure on one issue does not abort the sweep: record the exact error, carry on with the rest, and
report every failure at the end.

### Step 9 — Comment on every issue touched

One comment per issue, plain English, no AI-attribution footer or 🤖 marker.

**local (gh):**

```bash
gh issue comment <number> --repo <owner/repo> --body "$(cat <<'EOF'
<the comment>
EOF
)"
```

**remote (MCP):** use whichever GitHub MCP comment tool the session exposes. If the session has no
comment tool, still apply the Step 8 edits, then say plainly in the report that comments could not
be posted — do not drop the review to avoid the gap.

Cleared:

> Reviewed against `<owner/repo>@<sha>`. **Cleared `requires-review`** — the dependency it was
> written ahead of (#12) merged in <PR link>, and `src/poll.py:88` now carries the retry loop this
> issue assumed. Body updated with the landed behaviour. Still needs `claude/pickup` from a human
> before the worker picks it up.

Mis-flagged:

> Reviewed against `<owner/repo>@<sha>`. **Cleared `requires-review` as mis-applied** — the banner
> named no unlanded dependency, and nothing in the body does either. The concern was a design
> judgement ("fail loudly or default to an empty config?"), which belongs under Known ambiguities
> with a lean rather than in an arming hold; it is now recorded there, leaning fail loudly. Still
> needs `claude/pickup` from a human before the worker picks it up.

Held:

> Reviewed against `<owner/repo>@<sha>`. **Still held** — #13 is open, and the field name in this
> issue's acceptance criteria is the one #13 introduces. Re-review after #13 lands.

Overridden:

> Reviewed against `<owner/repo>@<sha>`. **Cleared `requires-review` at the author's direction** —
> the sweep held it on <the blocker>; the author cleared it.

### Step 10 — Verify, then report

**Read the labels back, per issue, asserting the direction the verdict implies.** Cleared (and
mis-flagged, which verifies identically):

```bash
gh issue view <number> --repo <owner/repo> --json labels --jq '.labels[].name' \
  | grep -qx requires-review \
  && gh issue edit <number> --repo <owner/repo> --remove-label requires-review
```

Held:

```bash
gh issue view <number> --repo <owner/repo> --json labels --jq '.labels[].name' \
  | grep -qx requires-review \
  || gh issue edit <number> --repo <owner/repo> --add-label requires-review
```

**remote (MCP):** the `issue_write` response carries the applied labels; check them the same way and
re-issue the update if the set is wrong.

Also verify the body matches the label: a cleared or mis-flagged issue must carry no 🔎 banner, a
held one must. On a mis-flagged issue, also confirm the relocated concern is actually present in the
body — a banner deleted with nothing put in its place is a lost requirement, not a clean sweep.
If a re-apply also fails, quote the exact error and say the issue is in the wrong state. Do not
claim success.

**Then report:**

- **Cleared** — number, title, and the evidence that cleared it.
- **Mis-flagged** — number, title, and where the concern was relocated to. Report these **separately
  from Cleared**: they were lifted on definition, not on evidence, and a combined count reads as a
  sweep that verified more than it did.
- **Held** — number, title, and the blocker, grouped so the batch order is visible.
- **Defects** — banner-less labels, generic `Why:` lines, armed issues skipped.
- **Failures** — any write or comment that errored, quoted.
- **Next** — the concrete re-run line, e.g.
  `Re-run /review-flagged-issues after #13 lands.`
- The discovery queries: `gh issue list --label requires-review` for what is still held, and
  `gh issue list --label claude-drafted` for the arming candidates.

## Rules

- NEVER clear `requires-review` without a positive fact read during this run. A reread of the issue
  is not evidence; the repo, the PR state, or the user's answer is.
- NEVER clear an issue whose upstream is still held. The ordering is the thing the flag protects.
- NEVER mark an issue MIS-FLAGGED when its banner or its body names a concrete issue, PR, or branch.
  That is a dependency hold and it goes through the evidence bar, however vague its `Why:` reads.
- NEVER mark an issue MIS-FLAGGED on the strength of a missing banner. No banner is a HOLD defect;
  MIS-FLAGGED needs a banner whose stated reason names no artifact.
- MIS-FLAGGED disposes of the FLAG, never of the CONCERN. Relocate the concern into the body —
  Known ambiguities with a lean, or a stated uncertainty — before the banner comes off.
- ALWAYS treat HOLD as the default and a valid result. A sweep that clears every issue in a batch is
  the signature of a review that did not happen.
- ALWAYS remove the 🔎 banner when the label comes off, and ALWAYS keep both when it does not. They
  are one unit in both directions.
- ALWAYS rewrite a held issue's `Blocked by:` and `Why:` to the blocker found this run, so the next
  sweep starts from better information than this one did.
- NEVER apply `claude/pickup`. Clearing the flag makes an issue armable; arming stays the human's
  step.
- NEVER remove `non-autonomous`, and never remove any label a human added. `requires-review` is the
  only label this skill removes.
- NEVER edit, relabel, or comment on an issue carrying `claude/pickup` — it is armed and the worker
  may be mid-run. Report it and ask.
- ALWAYS show the full verdict table and wait for `apply` before the first write.
- ALWAYS apply `claude-drafted` to every issue this skill edits — it is the marker that keeps
  skill-touched issues findable.
- ALWAYS verify labels and banner state after writing, and say so honestly when a fix-up fails.
- NEVER add a "Generated with Claude Code" footer, "🤖" marker, or `Co-Authored-By: Claude` trailer
  to an issue body or a comment — no AI attribution.
- Pick the GitHub path from `CLAUDE_CODE_REMOTE` and stay on it: MCP tools in remote sessions, `gh`
  locally. Do not fall back to `gh` for writes in a remote session — it returns HTTP 403.
- On the local path, if `gh` is not authenticated, stop immediately and tell the user to run
  `gh auth login`.
