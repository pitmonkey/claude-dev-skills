---
name: issue-batch-coordinator
description: Coordinate a batch of GitHub issues through the autonomous agent/pickup
  issue-worker — order by dependency, probe external ground truth, arm one issue at
  a time, wait for the dispatcher to release it, review each PR against the issues
  that follow it, patch, merge. Use when the user asks to run a batch of issues
  through the worker, or invokes /issue-batch-coordinator.
user-invocable: true
---
## Host compatibility

This skill supports Claude Code and Codex. Explicit invocation may use the host’s native syntax (for example `/issue-batch-coordinator` or `$issue-batch-coordinator`). Follow repository instructions and host permissions; Claude `allowed-tools` metadata does not grant Codex permissions. When composing bundled skills, use the native skill mechanism when available; otherwise read and follow the sibling `SKILL.md` relative to this installed skill directory, carrying the stated arguments. Never require a Claude `Skill` tool in Codex. Do not add assistant attribution to generated commits, issues, or requests.

The waits in Step 5 are plain shell loops and run on either host. In Codex, run them in the active session with interruptible waits and report the issue and PR URLs on each poll; never claim a persistent watcher, background monitor or scheduled wakeup unless the host exposes one. Where a step names a Claude capability (a subagent, `SendMessage`, `/code-review`), use the host's equivalent; Step 8 names the Codex one.


# Issue Batch Coordinator

You are the coordinator over an autonomous issue-worker. The worker picks up any
issue labelled `agent/pickup`, implements it, and opens a PR. You choose the
order, establish the ground truth, review what comes back, fix it, and merge.

Two facts drive everything below:

1. The worker implements its own issue faithfully and tests what it built. Its
   tests are self-consistent with its own implementation, so they pass. It cannot
   know what the *next* issue needs.
2. The worker does not reliably read comments posted to an issue while it is
   already in flight.

Every rule in this skill follows from those two facts.

---

## Step 0: Scope The Batch

Ask the user:

> "How many issues should I take in this batch?"

**STOP.** Do not proceed until the user answers. Do not pick a number yourself.

Review cost scales with the number of *seams* between issues, not with the number
of issues. Say so if the user asks for a large batch, then take the number they
give you.

---

## Step 1: Read The Batch

List open issues oldest-first, then read the **full body** of every issue in the
batch. Not the titles, not the first paragraph — the whole body, including
acceptance criteria and any labels.

You cannot order issues you have not read, and you cannot review a PR against a
later issue you have not read.

---

## Step 2: Order By Dependency

Work out the real dependency order and state it explicitly:

- The order itself.
- The reason each edge exists — what issue B needs from issue A.
- Which pairs **cannot** be parallelised, named as pairs.

**Issue text can be wrong.** Issues drafted before their dependencies shipped can
contradict later issues. A `requires-review` label flags some of these, but
unlabelled issues have been wrong too — one specified a data key path that
directly contradicted a later issue's constraint.

When an issue is wrong, **fix the issue body**, not just the code that will be
written from it. The worker reads the issue, not your reasoning.

---

## Step 3: Probe External Reality — Before Arming Anything

This is the highest-leverage step in the workflow. Do it for the **whole batch**
before arming the first issue.

Hit the real API, service, database, or filesystem that the batch depends on and
record what is actually true. Look specifically for things invisible from the
code:

- What an empty or edge-case input actually returns — an error status, not
  necessarily a success with an empty payload.
- Whether fields the issues name **actually exist** on the real response. A field
  that does not exist yields nulls everywhere while passing every test, and can
  silently remove a key that downstream issues depend on.
- Real status codes, error shapes, pagination behaviour, rate limits.

A handful of real requests is usually enough.

**Write every finding into the issue bodies** of the issues that need it.

**Say where each fact lives.** For structured data, give the nesting level (a top-level record type, or a `payload.type` inside one) and the source (which program, CLI or SDK path, and version). A probe note once listed two inner payload types beside the top-level record types; read as top-level, they became a wrong fix.

> **Comments posted to an issue already in flight are ignored.** Probe first, or
> accept that the finding is review-only and you will be fixing it in the PR.

---

## Step 4: Build The Invariant Checklist

Before arming anything, scan the repo's `CLAUDE.md` (and any equivalent contract
docs) for invariants stated emphatically.

**An invariant is stated emphatically because it is easy to get wrong.** Prose is
not enough: a single invariant has recurred in three different disguises across
three PRs, each shape passing its own tests.

Write the invariant's cases out explicitly as a checklist — enumerate the states,
not the principle. Keep the checklist for the whole batch and run it against
every PR that touches those cases.

---

## Step 5: Arm One Issue And Wait For Release

### Select dispatcher labels

`agent/*` names are canonical. Older `claude/*` names remain exact aliases with
no removal date; the spellings can be mixed freely. Add canonical names and
recognise both when reading labels. The dispatcher creates trigger and modifier
labels in watched non-public repos. Public-repo items are deferred as
`public_repo` and left untouched; do not arm them or wait for a run there.

| Trigger | Target and effect |
| --- | --- |
| `agent/pickup` | Issue: plan, implement, and open a PR. Default for this batch. |
| `agent/pickup-large` | Issue: same route with 5x the turns and 5x the budget for hard issues. |
| `agent/backlog` | Issue: queues for a rundown window; inert outside it and only created while rundown mode is enabled. Do not use for immediate batch dispatch. |
| `agent/fix-pr` | Failing PR: diagnose CI and push a fix. |
| `agent/review` | PR: read-only review and a review comment; overrides automatic bot routing. |

Triggers are removed when a run starts. Priority when several are present is
`agent/fix-pr` > `agent/review` > bot routing > `agent/pickup-large` >
`agent/pickup` > `agent/backlog`. Dependabot and Renovate PRs are picked up
automatically without a trigger. Inspect existing triggers under both spellings
before arming and leave only the intended trigger.

Modifiers persist across retries and never start a run themselves:

| Modifier | Selection rule |
| --- | --- |
| `agent/research` | Add alongside a pickup trigger for web search and fetch on that issue-worker run. |
| `model/mini`, `model/mid`, `model/max` | Select the model mapped by `DISPATCHER_MODEL_BY_TIER` on any route, including dependabot. Highest tier wins; absent a tier, use the worker default. Changes only the model, never limits or budget gates. |
| `ai/claude`, `ai/codex` | Select that item's harness. |

Every worker in the dispatcher's `HARNESS_SUPPORT` table (pitmonkey/github-dispatcher,
`dispatcher/dispatcher/routes_registry.py`) supports `ai/codex`. Check that table
rather than assume. Always set `ai/claude` or `ai/codex` explicitly: a worker
can be configured to pick its harness round-robin (opt-in per worker,
pitmonkey/github-dispatcher#344), so an unset label is unpredictable.
`model/*` labels may map to nothing on a harness without a `model_by_tier` entry,
so the tier you picked may silently not apply. Conflicting, unknown, or
unsupported harness choices defer the item with a visible reason. Resolve these
before arming or continuing the wait. If the user requires a harness the table
does not list for that worker, report the unsupported route rather than silently
choosing another. Inspect persistent modifiers before each retry.

**Before arming a batch on a non-default harness**, confirm that harness has a
recent successful run on that worker, or arm one issue and watch it before the
rest. An auth failure (for example a Codex CLI login 401) means stop and report
to the user. Do not wait out the automatic retry: it hits the same failure.

**Smoke-test the harness before the first arm on it.** Confirm it can log in and run a shell command inside the worker pod: a trivial throwaway run, or a check the owner does. If neither is possible, tell the user that the first armed run is the smoke test. Both early Codex failures showed up in the first minute of a real run, one batch apart: a login 401, then `bwrap: Failed to make / slave: Permission denied` from Codex's own sandbox in the pod.

The dispatcher sets status labels: `agent/in-progress` means a worker is running,
`agent/done` means the run finished, and `agent/failed` means it errored. Do not
add status labels yourself. Re-add a trigger to retry a failed run.

**First, clear stale terminal labels.** The dispatcher never removes `agent/done`
or `agent/failed` — it only removes the trigger labels at spawn and
`agent/in-progress` at completion. An issue that has been through the worker
before still carries its old terminal label, and the wait below would fire
immediately on that stale label. Strip both before arming, so the label that
appears next is unambiguously from *this* run:

```bash
# Remove existing terminal labels under either spelling.
while IFS= read -r label; do
  gh issue edit N --remove-label "$label" || exit 1
done < <(gh issue view N --json labels --jq '.labels[].name' |
  grep -E '^(agent|claude)/(done|failed)$')
```

**Then arm.** Add `agent/pickup` (or `agent/pickup-large` for a hard issue) to exactly **one** issue — the next one in the
order. Never arm two at once.

### Wait for the PR *and* for the dispatcher to let go

**A PR appearing does not mean the worker has finished.** Two windows overlap the
PR's existence:

- After opening the PR, the worker polls that PR's checks **in-process** for up to
  ten minutes and can still push for the whole window. `gh pr list` sees the PR
  from its first second.
- If the run errors, the dispatcher gives it **one automatic retry**: the trigger
  label goes back on the issue and a *fresh* worker run pushes to the same branch.
  A rate-limited run re-arms with no bound at all.

Review or patch inside either window and two agents are editing one branch. This
has already happened — the coordinator fixing a defect a second agent was
concurrently fixing.

The dispatcher releases the issue by adding `agent/done` or `agent/failed` and
removing `agent/in-progress`. Wait for that, not for the PR.

```bash
# Gate 1: a PR exists
until gh pr list --head claude/issue-N --json number --jq '.[0].number' | grep -q .; do
  sleep 60
done

# Gate 2: the dispatcher has released the issue
ready() {
  labels=$(gh issue view N --json labels --jq '.labels[].name')
  grep -qE '^(agent|claude)/(done|failed)$' <<<"$labels" &&
  ! grep -qE '^(agent|claude)/in-progress$' <<<"$labels" &&
  ! grep -qE '^(agent|claude)/(pickup|pickup-large|backlog|fix-pr|review)$' <<<"$labels"
}
until ready; do sleep 60; done
```

All three conditions are load-bearing. A stale `agent/failed` can sit on the
issue *while a live run holds `agent/in-progress`*, so the terminal label alone
proves nothing. A trigger label back on the issue with no `agent/in-progress` is
the automatic-retry window — keep waiting, it is not yours yet.

### Then the checks gate — which one depends on the label

- **`agent/done`** — wait for the gating checks to settle green before Step 6.
  `agent/done` is **not** proof of green: when checks fail to settle inside the
  worker's ten-minute poll it records `ci_status: unconfirmed` and still exits
  successfully. The worker's comment on the issue says which it was.
- **`agent/failed`** — do **not** wait for green; those checks are red or absent
  by definition. Go to Step 6 and treat the PR as one arriving with known
  defects. The branch is uncontested: the dispatcher has given up and no second
  agent will race you. Read the worker's comment on the issue first — it names
  the failing checks, or reports `skipped` / `max_turns` / `max_budget`, and is
  the cheapest account of what went wrong.
- **`agent/failed` with no PR at all** — the run died before opening one. There
  is nothing to review. Report it to the user and stop.

Mechanics that cost time if missed:

- **Filter out non-gating checks** from the wait condition. A job that is not a
  merge gate will never reach the state you are waiting for, and the loop waits
  forever.
- **`agent/done` is not a merge signal.** It means the worker's run exited
  successfully and the branch is now yours. The PR is still open and merging is
  your call.
- **Red checks before the terminal label are not yours to fix.** They are what the
  worker's own retry exists for. Do not diagnose them, do not push to the branch
  — wait for the label.
- **Do not arm the next issue until this one is labelled.** The one-at-a-time rule
  runs to the terminal label, not to the PR.
- **Watch for deferral.** Read the visible reason for a deferred item, such as an
  unsupported harness or public repo. Resolve or report it instead of waiting
  indefinitely for status labels.
- **Cap the wait.** Several paths leave an issue with no terminal label ever: a
  failed label write at completion, an unbounded rate-limited re-arm cycle, a lost
  dispatcher ledger row. On expiry, stop and report — an unlabelled issue may
  still have a live agent on it. Do not take the branch.
- **A trigger label sitting alongside a terminal label** means the spawn-time
  label flip failed. The dispatcher cannot re-arm that issue at all. Hand it to
  the user rather than working around it.

### Cross-harness batches

When the batch runs on a harness other than the one you coordinate from:

- Codex reads `AGENTS.md`, not `CLAUDE.md`. Link `AGENTS.md` to `CLAUDE.md` in
  the repo so the worker sees the same conventions.
- Claude plugins and skills may not load on Codex. Do not rely on a skill being
  available to the worker; put what it needs in the issue body.
- Codex's own `bwrap` sandbox cannot start on nodes with `kernel.apparmor_restrict_unprivileged_userns=1`. A worker's Codex arm runs there only where the deployment turned that sandbox off (as of pitmonkey/github-dispatcher#347: issue-worker and pr-fixer). Check before arming any other worker on `ai/codex`.
- Your review is the same either way: Steps 6 to 9 do not change with the
  harness.

---

## Step 6: Review The PR

- **Run `/code-review` on the worker's PR before writing any fixes.** In the
  ai-harness-bridge transcripts batch it found about 75% of the real defects.
  Then review your own fixes as Step 8 says.
- **Green CI is not evidence.** The worker's tests are self-consistent with the
  worker's implementation. Every PR in the trial batch arrived green; every one
  had 2–3 real defects.
- **Review against the issues that come *after* this one**, not just this issue's
  own acceptance criteria. That is where the defects are — all of them, in the
  trial batch, lived in the seams between issues.
- **Run the Step 4 invariant checklist**, case by case.
- **Verify worker claims about external reality** against your Step 3 probe.
  Claims have been wrong in both directions — work asserted as unverified that
  was in fact verified, and vice versa. You only know which by checking.
- **Check a reviewer's data claim against a real sample before adopting it.** A suggested redesign rests on facts like any probe does. One proposed reading Codex's native `item_completed` records instead of parsing commands; those records exist in CLI rollouts, but the Python SDK path the library uses writes none.
- **For parsers, tokenisers, scrubbers and matchers, write a randomised property or fuzz test before the first fix round.** In three batches running, rounds of example-based fixes did not converge until one arrived, and then it caught bugs review had missed. When a generated case fails, check it against the real program first (for example `bash -n`): the generator can be wrong.
- **Reproduce every suspected defect with a failing test before fixing it.**
  Things that look like style nits have been real defects. A code comment
  asserting the opposite of what a stdlib function returns is a one-line defect
  that changes runtime behaviour everywhere it is relied on.

---

## Step 7: Fix It On The Branch

**Patching the branch directly is the correct default.**

There is no cheap way to hand a semantic defect back. `agent/fix-pr` is for a PR
that is **failing CI** — diagnose CI, push a fix. It is not a channel for
review feedback on a green PR. The only hand-back mechanism is a new issue armed
with `agent/pickup`: a full round trip.

`agent/fix-pr` is also **explicitly applied**. The dispatcher never reads CI and
never arms a fixer on its own, so a red PR stays red until someone labels it —
which is why patching the branch directly is the correct default and not merely
the cheap one. If you do arm a fixer, it takes the same lifecycle labels **on the
PR** (`agent/in-progress`, then `agent/done` or `agent/failed`), so apply the
Step 5 wait discipline to the PR before touching the branch again.

Open a follow-up issue only when the fix is large enough to be its own ticket.

**Hold the PR while you work on it.** When you start reviewing or fixing a worker PR, mark it draft or post a "review in progress, hold the merge" comment, and lift the hold when you merge or hand it back. The owner once merged a PR at the first fix commit while the second round was still local, and that round had to go out as a follow-up PR.

- **Before changing a public contract on the branch, read the issue that will
  consume it.** A contract designed without its consumer's issue has been wrong.
- **Format only the files you changed.** Whole-tree formatter churn buries the
  real diff and has been left in the working tree before.
- **Check `git status` is clean before switching branches.**
- **Fix seam problems in the PR where they surface.** Deferring a cross-cutting
  change to the issue that appears to "own" it costs a round trip: the next PR
  will not do it, and you make the change one PR later anyway, plus a wasted CI
  cycle.
- **The worker pushes commits mid-review.** `git fetch` and rebase before
  pushing, and re-check for new commits immediately before you commit.

---

## Step 8: Review Your Own Code — Mandatory

This is the largest gap in the coordinator model: your fixes go in unreviewed
unless you force a review.

Before merging, run the host's code review on your own fix commits:
`/code-review` in Claude Code, `/review` in Codex. In Claude Code, if a review
subagent is stopped by a usage limit, resume it with `SendMessage`; do not
restart it. In Codex, if the review is interrupted, rerun it in the session on
the same commits.

**Know when to stop.** Review rounds on text heuristics (parsing shell or scripts, scrubbing secrets) find narrower cases every round and do not converge on their own.

- If two rounds reverse each other on a trade-off (fail-closed versus by-name redaction, swallowing versus propagating a cancel), it is policy, not a defect: stop and ask the owner.
- If a round finds only edge cases (rare constructs, input that is already malformed), document the remaining limits in the repo's docs and merge.
- Regressions, and misses on common inputs, are fixed before merging.

If a fix changes a **shared contract** — an interface, Protocol, base class, or
schema that every future implementation must satisfy — do not self-merge it
inside the worker's PR. Put it up as a **separate PR for a human**.

---

## Step 9: Merge And Write Forward

1. Post your review findings as a PR comment, with evidence — the failing test,
   the actual response, the contradicting line.
2. Squash-merge with `--delete-branch`.
3. Write a real commit body describing **behaviour**, not a diff summary.
4. **Write any new contract this PR established into the next issue's body**
   before arming it. Whatever you learned or changed here is invisible to the
   next worker unless it is in the issue. Do the same for consumer issues in
   other repos, not only the next issue in the batch.

---

## Step 10: Repeat

Return to Step 5 for the next issue in the order. One at a time, always.

---

## Why This Works

The worker is competent inside the boundary of its own issue and blind outside
it. Ordering, ground truth, seam review, and forward-written contracts are all
ways of moving information across that boundary before the worker needs it —
because after it starts, you cannot.
