---
name: create-github-issue
description: Use when the user wants to capture a bug or problem from the current conversation as a GitHub issue. Triggered by /create-github-issue, optionally followed by owner/repo.
allowed-tools:
  - Bash
---

# Create GitHub Issue

Summarise the specific problem or bug discussed in this conversation and create a structured GitHub issue via `gh` CLI. Always shows a draft for review before creating.

## Process

### Step 0 — Parse arguments

Check if the user provided an `owner/repo` argument (e.g. `/create-github-issue pitmonkey/other-repo`).

- If yes: use that repo for all subsequent steps.
- If no: proceed to Step 1 to auto-detect.

### Step 1 — Detect and confirm repo

If no repo arg was given:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Show the detected repo to the user and ask them to confirm before continuing.

If `gh` is not authenticated: stop and tell the user to run `gh auth login`.
If the command fails or returns nothing: stop and ask the user to provide the repo manually.

### Step 2 — Extract issue from conversation

Read the current conversation and identify the specific problem or bug being discussed. Do not summarise the entire session — focus on the concrete issue.

Populate the following draft:

```
Title: <concise imperative, e.g. "Fix: token expiry check uses < instead of <=">

Labels: <one of: bug | enhancement | question | documentation — chosen based on issue content>

---

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

### Step 3 — Show draft

Display the full draft to the user. Then ask:

> **Create this issue, edit it, or cancel? (create / edit / cancel)**

### Step 4 — Confirmation loop

- **create** → proceed to Step 5
- **edit** → user describes the change in plain text; rewrite the relevant section(s) and return to Step 3
- **cancel** → stop immediately; do not create anything

### Step 5 — Check labels

Before creating the issue, check what labels exist in the target repo:

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
- skip → create issue without any label

**If the repo has labels but the suggested label is missing:**

Ask:

> Label `<label>` doesn't exist in this repo. Create it, skip labels, or choose an existing one?
> Existing: <comma-separated list>

- create → `gh label create <label> --repo <owner/repo> --color <sensible default>`
- skip → create issue without labels
- choose → user picks from list; use that label

**If the suggested label exists:** proceed directly.

### Step 6 — Create issue

```bash
gh issue create \
  --repo <owner/repo> \
  --title "<title>" \
  --label "<label>" \
  --body "$(cat <<'EOF'
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

Omit `--label` if the user chose to skip labels.
Omit the `## ⚠️ Suggested Fix` section entirely if no fix was identified.

### Step 7 — Report

Print the issue URL returned by `gh issue create`.

If the command fails: quote the exact error and stop.

## Rules

- NEVER create an issue without showing the draft first
- NEVER skip the label check
- If `gh` is not authenticated, stop immediately and tell the user to run `gh auth login`
- The suggested fix disclaimer must appear verbatim — do not soften or shorten it
- If no fix emerged from the conversation, omit the fix section entirely — do not invent one
