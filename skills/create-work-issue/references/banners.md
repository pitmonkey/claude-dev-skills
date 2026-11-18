# Create Work Issue — flag banners

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## `non-autonomous` banner

When flagged, this is the **first content in the body**, above `## Problem / Context`, verbatim:

```
> ⚠️ **`non-autonomous`** — requires human intervention; not for autonomous pickup.
> Do **not** add `agent/pickup`. See **Human intervention required** below.
```

## `non-autonomous` — Human intervention required

Immediately after the banner, one concrete bullet per blocker — what a human must actually do, not
a restatement of the trigger category:

```
## Human intervention required
- Stripe secret key must be added to repo secrets as `STRIPE_WEBHOOK_SECRET`
- Webhook endpoint must be registered in the Stripe dashboard
```

The banner and this section are **conditional**: they appear only when the issue is flagged. Unlike
the eight template sections, they are never rendered as `N/A` — an unflagged issue simply has
neither.

## `requires-review` banner

When flagged, this goes in the body verbatim, with both fields filled in:

```
> 🔎 **`requires-review`** — a human must review this draft before arming it.
> Do **not** add `agent/pickup` until reviewed.
> Blocked by: <#N | owner/repo#N | PR #N | branch-name>
> Why: <one line — what in this draft that landing may invalidate>.
```

The banner and the label are **one unit**. Never write the banner without adding `requires-review`
to the label set, and never add the label without the banner. `Blocked by:` names a real artifact —
if you have nothing to put there, the flag does not apply. `Why:` says what the landing may
invalidate; "may need review" is not a reason.

There is no separate body section: unlike `non-autonomous`, which lists actions a human must
perform, `requires-review` states one blocker, and it lives in the banner.

**When both flags fire**, the `non-autonomous` banner comes first, then the `requires-review`
banner, then `## Human intervention required`, then `## Problem / Context` and the rest.
