# Create Work Issue — the work-order template

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## The work-order template

Every issue carries all eight sections. Each exists to kill one class of bad assumption the
headless agent would otherwise make. Empty sections are marked `N/A` (never deleted).

```
Title: <concise imperative — e.g. "Add retry with backoff to the GitHub poll loop">

## Problem / Context
<why this work exists — what's wrong, missing, or needed. 2–4 sentences.>

## Goal / Outcome
<what "done" looks like, 1–2 sentences.>

## Acceptance criteria
<checklist of testable conditions — the spec the agent's test-first implementation writes tests against>
- [ ] ...
- [ ] ...

## Scope / Non-goals
<explicit fences — what NOT to touch or build. There is no human to say "stop, too far".>

## Pointers
<relevant files/dirs/functions, related issues/PRs. Saves the agent grep turns; its turn budget is finite. N/A if none.>

## Constraints
<deps, API/back-compat, performance, style rules not already in the target repo's CLAUDE.md. For any code change, always include "Format only the files you change." N/A if none.>

## Known ambiguities
<forks you already see — pre-decide them or say which way to lean, so the agent does not guess blindly. N/A if none.>

---
**Model tier:** `model/<mini|mid|max>` — <one line: why this tier>
```

The closing **Model tier** line is not one of the eight sections; it is always present and always matches the `model/*` label. It tells a human why the tier was chosen, so they can disagree before arming.

**Load-bearing sections:** *Acceptance criteria* (turns a vague ask into tests) and
*Scope / Non-goals* (fences an unsupervised agent). Do not finalize an issue without real
acceptance criteria.

**An equivalence criterion names its proof.** A criterion that claims the new code matches existing code ("matches X", "byte for byte with X", "same output as X") must say how that is proven. The default is a differential test: commit a frozen copy of X under `tests/` and run both over the same inputs. Without it the worker writes example tests against its own implementation, which pass whether or not the two diverge.

**Heuristic work gets proposed property tests.** When the work infers facts by parsing another program's text (shell commands, scripts, logs, transcripts) or scrubs or matches text, propose two more acceptance criteria. The first is a randomised property or fuzz test of the key invariants, for example "found after any realistic prefix; never found inside quoted text". The second is a sweep over a real corpus, where one exists, with its expected results stated. These are recommendations, not requirements: the user can drop them when reviewing the draft. Without them such work tends to go through round after round of example-based fixes that never converge.

**Probe facts say where they live.** When you write facts you checked against real data into a body, give each one its location: the nesting level (a top-level record type, or a `payload.type` inside one) and the source (which program, CLI or SDK path, and version). A worker reads an unlocated name at the wrong level.

**Formatting stays local.** For any code change, `## Constraints` says "Format only the files you change." A worker that runs the formatter over the whole tree buries the real change under unrelated churn.
