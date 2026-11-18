# Create Work Issue — confirmation loop (Step 4)

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Step 4 — Confirmation loop

- **create** → proceed to Step 5.
- **edit** → the user describes the change in plain text; rewrite the relevant section(s) and
  return to Step 3.
- **non-autonomous** → toggle the flag. Turning it **on** adds the banner, `## Human intervention
  required`, and `non-autonomous` to the label set; if you do not already know what the human must
  do, interview it (one question at a time) before re-showing. Turning it **off** removes all
  three. Return to Step 3.
- **requires-review** → toggle the flag. Turning it **on** adds the banner and `requires-review` to
  the label set; the banner needs a concrete `Blocked by:` and `Why:` — ask if you do not have them.
  If the user turns it on with no artifact to name, take the instruction and write
  `Blocked by: <none — author override>` so the later sweep can tell it apart from a real dependency
  hold. Turning it **off** removes both. Return to Step 3.
- **mini / mid / max** → set the tier: swap the `model/*` label in the set and rewrite the **Model
  tier** line (the reason becomes "set by author" unless they gave one). Return to Step 3.
- **cancel** → stop immediately; do not create anything.

The user overrides the screen in either direction: they may turn a flag on that did not fire, or off
that did. Never toggle a flag they did not ask you to. If they just say `flag` or `unflag`, ask which
flag they mean — do not assume `non-autonomous`.
