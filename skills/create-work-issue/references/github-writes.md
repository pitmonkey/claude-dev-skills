# Create Work Issue — labels, create, verify (Steps 6–8)

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Step 6 — Ensure the label set exists

The label set is `claude-drafted`, plus exactly one `model/*` label, plus `non-autonomous` and/or
`requires-review` for each flag that is on.

- **remote (MCP):** No separate create step is needed — pass the whole set in the `labels` array
  when you create the issue (Step 7) and GitHub auto-creates any missing label (this covers
  `claude-drafted`, the `model/*` label, `non-autonomous` and `requires-review` — the MCP token has push access,
  so a label is created on first use). Optionally check first with
  `mcp__github__get_label` (owner, repo, name) so you can tell the user whether a label is brand
  new. A freshly auto-created label gets a default color — that is cosmetic and fine; recolor it
  later if you care.
- **local (gh):** create each label in the set if it does not already exist:

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx claude-drafted \
    || gh label create claude-drafted --repo <owner/repo> --color 5319e7 \
       --description "Drafted by a Claude issue-creation skill; awaiting human triage"
  ```

  The chosen tier label (the dispatcher creates these in repos it watches; this covers the rest):

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx model/<tier> \
    || gh label create model/<tier> --repo <owner/repo> --color c5def5 \
       --description "Run this item on the <tier> model tier (dispatcher)"
  ```

  Only when flagged `non-autonomous`:

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx non-autonomous \
    || gh label create non-autonomous --repo <owner/repo> --color d93f0b \
       --description "Needs human intervention — not for autonomous issue-worker pickup"
  ```

  Only when flagged `requires-review`:

  ```bash
  gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx requires-review \
    || gh label create requires-review --repo <owner/repo> --color fbca04 \
       --description "Draft written ahead of an unlanded dependency — review before arming"
  ```

  Never recolor or re-describe a label that already exists — take it as it is.

## Step 7 — Create issue

- **remote (MCP):** call `mcp__github__issue_write` with:
  - `method`: `create`
  - `owner` / `repo`: the confirmed target
  - `title`: the drafted title
  - `labels`: `["claude-drafted", "model/<tier>"]`, plus `"non-autonomous"` and/or `"requires-review"`
    for each flag that is on — **never `agent/pickup`**, on any kind of issue
  - `body`: the full eight-section body (all sections; empty ones marked `N/A`), preceded by the
    banner(s) and `## Human intervention required` **only for the flags that are on**:

    ```
    > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
    > Do **not** add `agent/pickup`. See **Human intervention required** below.

    > 🔎 **`requires-review`** — a human must review this draft before arming it.
    > Do **not** add `agent/pickup` until reviewed.
    > Blocked by: <#N | owner/repo#N | PR #N | branch-name>
    > Why: <what that landing may invalidate in this draft>.

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

    ---
    **Model tier:** `model/<tier>` — <why this tier>
    ```

- **local (gh):**

  ```bash
  gh issue create \
    --repo <owner/repo> \
    --title "<title>" \
    --label "claude-drafted" \
    --label "model/<tier>" \
    --body "$(cat <<'EOF'
  > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
  > Do **not** add `agent/pickup`. See **Human intervention required** below.

  > 🔎 **`requires-review`** — a human must review this draft before arming it.
  > Do **not** add `agent/pickup` until reviewed.
  > Blocked by: <#N | owner/repo#N | PR #N | branch-name>
  > Why: <what that landing may invalidate in this draft>.

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

  ---
  **Model tier:** `model/<tier>` — <why this tier>
  EOF
  )"
  ```

For a confirmed split, create the issues in order, earliest first, so each later body can name the real number of the one it builds on — fill those numbers in before creating the next.

Add `--label "non-autonomous"` and/or `--label "requires-review"` for each flag that is on. Each
banner, and the `## Human intervention required` block, is omitted entirely when its flag is off.

**Apply `claude-drafted` and the `model/*` label (plus any flag labels that are on) — never `agent/pickup`.** The marker
keeps the issue findable; arming stays the human's step.

## Step 8 — Verify labels, then report

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

**Then read the tier back** — exactly one `model/*` label, the one you chose:

- **local (gh):**

  ```bash
  gh issue view <number> --repo <owner/repo> --json labels --jq '.labels[].name' | grep '^model/'
  ```

  If `model/<tier>` is missing, `gh issue edit <number> --repo <owner/repo> --add-label model/<tier>`. If another `model/*` label is there that you did not intend, report it rather than removing it.

- **remote (MCP):** check the `issue_write` response labels the same way; re-apply with
  `method: update` and the full intended `labels` array if needed.

**Then report.** Print the created issue's URL, the labels actually present (e.g.
`Stamped: claude-drafted, model/mid, non-autonomous, requires-review`), then the base line, then one
addendum per flag that is on. For a batch, print one line per issue (number, title, tier) first.

- **remote (MCP):** take the URL from the `issue_write` response (its `html_url` / `url` field).
- **local (gh):** take the URL returned by `gh issue create`.

**Always:**

> Stamped `claude-drafted`. List candidates later with `gh issue list --label claude-drafted`,
> then add `agent/pickup` to the ones you want the issue-worker to implement.
> Tier: `model/<tier>` — change the label before arming if you disagree.

**Plus, if `model/max`:**

> `model/max` — <why splitting did not help>. Consider working this one interactively before
> arming it.

**Plus, if the work is long but not hard** (many files or acceptance criteria at mid or mini): suggest the human arm it with `agent/pickup-large` (more turns and budget, same model). Suggest only — never apply it.

**Plus, if `non-autonomous`:**

> Also `non-autonomous` — **excluded from autonomous pickup**; it needs a human first. Review them
> with `gh issue list --label non-autonomous`.

**Plus, if `requires-review`:**

> Also `requires-review` — <the reason>. Read it before you arm it. Review them with
> `gh issue list --label requires-review`.

If issue creation fails: quote the exact error and stop.
