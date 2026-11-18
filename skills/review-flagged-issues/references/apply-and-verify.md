# Review Flagged Issues — apply, comment, verify (Steps 8–10)

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Step 8 — Apply, in dependency order

Per issue. **local (gh):**

```bash
gh issue edit <number> --repo <owner/repo> --body "$(cat <<'EOF'
<the re-drafted body>
EOF
)" --add-label claude-drafted
```

Add `--add-label model/<tier>` when the issue has no tier label, or `--remove-label model/<old> --add-label model/<tier>` on a tier change shown in Step 7. Add `--add-label non-autonomous` when that screen newly fired. Then, **cleared and mis-flagged
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

## Step 9 — Comment on every issue touched

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
> issue assumed. Body updated with the landed behaviour. Still needs `agent/pickup` from a human
> before the worker picks it up.

Mis-flagged:

> Reviewed against `<owner/repo>@<sha>`. **Cleared `requires-review` as mis-applied** — the banner
> named no unlanded dependency, and nothing in the body does either. The concern was a design
> judgement ("fail loudly or default to an empty config?"), which belongs under Known ambiguities
> with a lean rather than in an arming hold; it is now recorded there, leaning fail loudly. Still
> needs `agent/pickup` from a human before the worker picks it up.

Held:

> Reviewed against `<owner/repo>@<sha>`. **Still held** — #13 is open, and the field name in this
> issue's acceptance criteria is the one #13 introduces. Re-review after #13 lands.

Overridden:

> Reviewed against `<owner/repo>@<sha>`. **Cleared `requires-review` at the author's direction** —
> the sweep held it on <the blocker>; the author cleared it.

## Step 10 — Verify, then report

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

Also read back the tier: exactly one `model/*` label, matching the body's **Model tier** line.

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
