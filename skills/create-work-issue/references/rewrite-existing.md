# Create Work Issue — rewrite or review an existing issue

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Rewrite / review an existing issue

"Rewrite issue N with this skill", "review issue N", "fix up this issue", or a pasted issue URL
means: **apply this skill to that issue and write the result back.** It is not a read-only
opinion. Review and rewrite are the same path — reviewing produces the corrected issue.

1. Read the issue (`gh issue view N --repo <owner/repo> --json title,body,labels`, or
   `mcp__github__issue_read` remotely).
2. Re-draft the title and body to the full template — every section present, empty ones `N/A`.
   Keep the author's facts; do not invent. Genuine gaps are asked about (thin path) or recorded
   under **Known ambiguities**.
3. Run **both** screens — non-autonomous and requires-review — against the work as re-drafted,
   exactly as for a new issue, and re-pick the model tier. A rewrite is a new draft: re-screen it,
   do not inherit the old verdict.
4. Compute the full intended label set — **including `claude-drafted`**, plus `non-autonomous` if
   that screen fires, plus `requires-review` if the review screen fires, plus any pre-existing
   labels the human already put there, plus exactly one `model/*` label. Never `agent/pickup`, and
   never strip a label a human added.

   If the issue already carries a `model/*` label that differs from the tier you picked, show both
   in Step 3 and let the user choose — the existing label may be a human's deliberate call. Only
   when they pick yours do you swap it (`--remove-label model/<old> --add-label model/<new>`); that
   instruction is the one exception to the add-only rule below, alongside the flag toggles.
5. Show the re-drafted issue and go through the same confirmation loop (Step 3 / Step 4), with
   **update** in place of create.
6. Write it back and verify:
   - **local:** `gh issue edit N --repo <owner/repo> --title "<title>" --body "<body>" --add-label claude-drafted`
     (add `--add-label non-autonomous` and/or `--add-label requires-review` for each flag that
     fires). Use `--add-label`, never `--remove-label` on a label you did not add.
   - **remote:** `mcp__github__issue_write` with `method: update`, the issue number, and the full
     label set.

   The `--add-label`-only rule protects labels a human added. If the user explicitly toggles a flag
   **off** during the confirmation loop on an issue that already carries it, that is an instruction,
   not an inference: `gh issue edit N --repo <owner/repo> --remove-label requires-review` is allowed
   **there and only there**. Never remove a flag on your own judgement that the draft now looks
   fine. The one sanctioned sweep that clears `requires-review` on evidence rather than on a toggle
   is the `review-flagged-issues` skill, which re-checks each flagged draft against the current repo
   and holds anything it cannot verify.

   Then run the same read-back verification as Step 8.

An issue already carrying `agent/pickup` is **armed**. Say so before rewriting, and ask whether to
proceed — the human's gate has already been passed and the worker may pick it up mid-edit.
