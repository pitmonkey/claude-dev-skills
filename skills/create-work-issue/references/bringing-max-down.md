# Create Work Issue — bringing max down

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Bringing max down

**Shared plumbing is a split signal.** A work item that changes shared plumbing (a core loop or entry point that every path runs through) and more than one implementation of an interface and a shared test suite is a split candidate even when every decision is closed: the worker gets each piece right in isolation and the defects land in the seams between them. Split it per implementation on top of a plumbing-only issue. If it cannot be split, it is `model/max`.

When a draft reads as `model/max`, do not accept that at once. In order:

1. **Close the open decisions.** Each design fork the worker would have to resolve — settle it now, by asking the user (one question at a time) or by reading the repo, and write the answer into the body as a decision (under `## Constraints` or `## Scope / Non-goals`), not as a lean under `## Known ambiguities`. Fewer open forks, lower tier.
2. **Split.** If it is still max, propose an ordered batch of **mid-sized** issues (with a mini only where a piece is naturally that small). Each gets its own acceptance criteria and its own tier, and each later issue names the earlier one it builds on under `## Pointers`. Run the requires-review screen on each: a later issue written ahead of an earlier one that has not landed is exactly that flag's batch trigger.
3. **Accept max** only when splitting does not help — a change that must land atomically, or a diagnosis that cannot be cut into parts. Say which in the **Model tier** line. A `model/max` issue is a hint that the human may prefer to work it interactively before arming it; the report says so.

A split is a proposal: show it in the draft (Step 3) and create nothing until the user confirms the breakdown.

**Sanity checks, both ways.** If most of a batch comes out `model/max`, stop and re-plan — the thinking has not been done yet. If one piece of work has become a handful of `model/mini` issues, merge them back into one `model/mid` issue.

`model/max` is not `non-autonomous`. Max means the worker can do it but needs the most capable model; non-autonomous means a bot cannot do it at all. The two are independent, and a `non-autonomous` issue still gets a tier for when it is eventually armed.
