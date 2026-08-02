---
name: create-github-bug-issue
description: Use when the user wants to capture a bug or problem from the current conversation as a GitHub bug-report issue, including screening whether the fix needs human intervention and flagging it non-autonomous. Triggered by /create-github-bug-issue, optionally followed by owner/repo. For a work order for the autonomous issue-worker, use create-work-issue instead.
allowed-tools:
  - Bash
  - mcp__github__issue_write
  - mcp__github__get_label
---

# Create GitHub Bug Issue

Summarise the specific problem or bug discussed in this conversation and create a structured
GitHub issue. Always shows a draft for review before creating.

A human may later arm the issue for the autonomous github-dispatcher issue-worker by adding
`claude/pickup`. So this skill also screens for the opposite case: a fix the headless agent
**cannot** perform, which gets stamped **`non-autonomous`** and says so at the top of its own body.

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

---

> ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
> Do **not** add `claude/pickup`. See **Human intervention required** below.
<omit these two lines entirely unless flagged>

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

Then run the fix against the trigger checklist and, if anything fires, add the banner, the
`## Human intervention required` section, and `non-autonomous` to the label set. If you cannot tell
whether a trigger applies, ask rather than assume.

### Step 3 — Show draft

Display the full draft to the user. Then ask:

- **flagged:** state the flag and the triggers that fired above the draft, then ask:

  > **Create this issue, edit it, remove the non-autonomous flag, or cancel?
  > (create / edit / unflag / cancel)**

- **not flagged:**

  > **Create this issue, edit it, mark it non-autonomous, or cancel?
  > (create / edit / flag / cancel)**

### Step 4 — Confirmation loop

- **create** → proceed to Step 5
- **edit** → user describes the change in plain text; rewrite the relevant section(s) and return to Step 3
- **flag** → add the banner and `## Human intervention required`, and add `non-autonomous` to the
  label set. If you do not already know what the human must do, ask before re-showing. Return to Step 3
- **unflag** → remove the banner, the `## Human intervention required` section, and
  `non-autonomous` from the label set. Return to Step 3
- **cancel** → stop immediately; do not create anything

### Step 5 — Check labels

Decide the final label set: the chosen content label, plus the `claude-drafted` marker, plus
`non-autonomous` when the issue is flagged.

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
    - skip → drop the content label; keep only `claude-drafted`.
    - name one → `get_label` the name they give to confirm it exists, then use it.
- The `claude-drafted` marker needs no pre-check: include it in the label set and it is
  auto-created at issue time if missing. Same for `non-autonomous` when flagged — include it and
  let GitHub create it. Never ask the user to approve these two; they are markers, not content
  labels.

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
- skip → create issue without any content label

**If the repo has labels but the suggested label is missing:**

Ask:

> Label `<label>` doesn't exist in this repo. Create it, skip labels, or choose an existing one?
> Existing: <comma-separated list>

- create → `gh label create <label> --repo <owner/repo> --color <sensible default>`
- skip → create issue without a content label
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

**When the issue is flagged**, ensure `non-autonomous` exists too:

```bash
gh label list --repo <owner/repo> --json name --jq '.[].name' | grep -qx non-autonomous \
  || gh label create non-autonomous --repo <owner/repo> --color d93f0b \
     --description "Needs human intervention — not for autonomous issue-worker pickup"
```

Never recolor or re-describe a label that already exists — take it as it is.

### Step 6 — Create issue

- **remote (MCP):** call `mcp__github__issue_write` with:
  - `method`: `create`
  - `owner` / `repo`: the confirmed target
  - `title`: the drafted title
  - `labels`: the final set — the chosen content label (if kept) plus `"claude-drafted"`, plus
    `"non-autonomous"` when flagged; omit the content label if the user skipped it, but **always
    keep `"claude-drafted"`**. Never `"claude/pickup"`
  - `body`: the drafted body (omit the `## ⚠️ Suggested Fix` section entirely if no fix was
    identified — do not invent one; omit the banner and `## Human intervention required` unless
    flagged):

    ```
    > ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
    > Do **not** add `claude/pickup`. See **Human intervention required** below.

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

Add `--label "non-autonomous"` when flagged; omit the banner and `## Human intervention required`
block entirely when not.
Omit the content `--label "<label>"` (or leave it out of the MCP `labels` set) if the user
chose to skip labels, but **always keep `claude-drafted`**.
Omit the `## ⚠️ Suggested Fix` section entirely if no fix was identified.

### Step 7 — Report

Print the created issue's URL, then note the markers:

- **remote (MCP):** take the URL from the `issue_write` response (its `html_url` / `url` field).
- **local (gh):** take the URL returned by `gh issue create`.

**Not flagged:**

> Stamped `claude-drafted`. List skill-created issues later with
> `gh issue list --label claude-drafted`.

**Flagged:**

> Stamped `claude-drafted` and `non-autonomous` — this one is **excluded from autonomous pickup**;
> it needs a human first. Review them with `gh issue list --label non-autonomous`.

If issue creation fails: quote the exact error and stop.

## Rules

- NEVER create an issue without showing the draft first
- NEVER skip the label check
- ALWAYS apply the `claude-drafted` marker label, even when the content label is skipped, so
  skill-created issues stay findable for triage
- NEVER apply `claude/pickup`. Arming for autonomous pickup is the human's deliberate step — and it
  is never right on a `non-autonomous` issue
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
