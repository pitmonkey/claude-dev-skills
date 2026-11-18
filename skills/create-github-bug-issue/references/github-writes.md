# Create GitHub Bug Issue — labels, create, verify (Steps 5–7)

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Step 5 — Check labels

Decide the final label set: the chosen content label, plus the `claude-drafted` marker, plus exactly
one `model/*` label, plus `non-autonomous` and/or `requires-review` for each flag that is on.

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
  auto-created at issue time if missing. Same for the `model/*` label, and for `non-autonomous` and
  `requires-review` when their flags are on — include them and let GitHub create them. Never ask the
  user to approve these; they are markers, tiers and flags, not content labels.

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

**Always ensure the chosen tier label exists** (the dispatcher creates these in repos it watches; this covers the rest):

```bash
gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx model/<tier> \
  || gh label create model/<tier> --repo <owner/repo> --color c5def5 \
     --description "Run this item on the <tier> model tier (dispatcher)"
```

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

The label set contains **exactly one** `model/*` label, and the body's **Model tier** line names the
same tier. With more than one, the dispatcher runs the highest, which silently undoes the choice.

## Step 6 — Create issue

- **remote (MCP):** call `mcp__github__issue_write` with:
  - `method`: `create`
  - `owner` / `repo`: the confirmed target
  - `title`: the drafted title
  - `labels`: the final set — the chosen content label (if kept) plus `"claude-drafted"` and
    `"model/<tier>"`, plus
    `"non-autonomous"` and/or `"requires-review"` for each flag that is on; omit the content label
    if the user skipped it, but **always keep `"claude-drafted"`** and keep any flag label — a user
    skipping content labels was never asked about the flags. Never `"agent/pickup"`
  - `body`: the drafted body (omit the `## ⚠️ Suggested Fix` section entirely if no fix was
    identified — do not invent one; omit each banner, and `## Human intervention required`, when its
    flag is off):

    ```
    > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
    > Do **not** add `agent/pickup`. See **Human intervention required** below.

    > 🔎 **`requires-review`** — a human must review this draft before arming it.
    > Do **not** add `agent/pickup` until reviewed.
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

    ---
    **Model tier:** `model/<tier>` — <why this tier>
    ```

- **local (gh):**

  ```bash
  gh issue create \
    --repo <owner/repo> \
    --title "<title>" \
    --label "<label>" \
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

  ---
  **Model tier:** `model/<tier>` — <why this tier>
  EOF
  )"
  ```

Add `--label "non-autonomous"` and/or `--label "requires-review"` for each flag that is on; omit
each banner (and the `## Human intervention required` block) when its flag is off.
Omit the content `--label "<label>"` (or leave it out of the MCP `labels` set) if the user
chose to skip labels, but **always keep `claude-drafted` and the `model/*` label, and keep any flag
label** — "skip labels" refers to the content label only.
Omit the `## ⚠️ Suggested Fix` section entirely if no fix was identified.

## Step 7 — Verify labels, then report

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
`Stamped: bug, claude-drafted, model/mid, requires-review`), then the base line, then one addendum per flag
that is on:

- **remote (MCP):** take the URL from the `issue_write` response (its `html_url` / `url` field).
- **local (gh):** take the URL returned by `gh issue create`.

**Always:**

> Stamped `claude-drafted`. List skill-created issues later with
> `gh issue list --label claude-drafted`.
> Tier: `model/<tier>` — change the label before arming if you disagree.

**Plus, if `model/max`:**

> `model/max` — <why: usually that the root cause is still unknown>. Consider debugging this one
> interactively before arming it.

**Plus, if `non-autonomous`:**

> Also `non-autonomous` — **excluded from autonomous pickup**; it needs a human first. Review them
> with `gh issue list --label non-autonomous`.

**Plus, if `requires-review`:**

> Also `requires-review` — <the reason>. Read it before you arm it. Review them with
> `gh issue list --label requires-review`.

If issue creation fails: quote the exact error and stop.
